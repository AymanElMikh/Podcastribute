"""Celery task definitions for the podcast processing pipeline.

The process_episode task is the main entry point — it runs the full
LangGraph pipeline synchronously within the Celery worker context.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

import structlog

from worker.celery_app import celery_app

log = structlog.get_logger(__name__)


@celery_app.task(bind=True, name="worker.tasks.process_episode")
def process_episode(_self: object, episode_id: str) -> dict:
    """Run the full podcast processing pipeline for a single episode.

    Entry point for Celery — bridges the sync Celery world to the async
    LangGraph pipeline using asyncio.run().

    Args:
        episode_id: UUID string of the episode to process.

    Returns:
        Dict with "status" and "episode_id" on completion.
    """
    return asyncio.run(_run_pipeline(episode_id))


async def _run_pipeline(episode_id: str) -> dict:
    """Execute the full async pipeline for an episode.

    Pipeline steps:
    1. Load episode from DB
    2. Convert audio to WAV if needed
    3. Transcribe with Whisper
    4. Load user's voice profile from DB
    5. Invoke LangGraph graph (Phase 7)
    6. Save results to DB
    7. Update episode status

    Args:
        episode_id: UUID string of the episode to process.

    Returns:
        Dict with "status" and "episode_id" after pipeline completes.
    """
    # Import here to avoid circular imports at module load time
    from sqlalchemy import select

    from api.db.models import Episode, VoiceProfile
    from api.db.session import _get_session_factory
    from api.ingestion.audio_processor import AudioProcessor

    async with _get_session_factory()() as session:
        # 1. Load episode
        result = await session.execute(
            select(Episode).where(Episode.id == uuid.UUID(episode_id))
        )
        episode = result.scalar_one_or_none()
        if episode is None:
            log.error("episode_not_found", episode_id=episode_id)
            raise ValueError(f"Episode {episode_id} not found in DB")

        log.info("pipeline_start", episode_id=episode_id, source_type=episode.source_type)

        # Update status to transcribing
        episode.status = "transcribing"
        episode.processing_started_at = datetime.utcnow()
        await session.commit()

        try:
            processor = AudioProcessor()
            audio_path = episode.audio_path or ""

            # 2. For YouTube/RSS sources, audio is downloaded by the worker first
            if episode.source_type == "youtube" and episode.source_url:
                audio_path = await _download_youtube(episode.source_url, episode_id)
                episode.audio_path = audio_path
                await session.commit()

            elif episode.source_type == "rss" and episode.source_url:
                audio_path = await _download_rss(episode.source_url)
                episode.audio_path = audio_path
                await session.commit()

            # 3. Convert to WAV for best Whisper accuracy
            if audio_path and not audio_path.endswith(".wav"):
                audio_path = await processor.convert_to_wav(audio_path)

            # 4. Transcribe
            if audio_path:
                transcript = await processor.transcribe(audio_path)
                episode.transcript = transcript.text
                episode.duration_seconds = transcript.duration_seconds
            else:
                log.warning("no_audio_path", episode_id=episode_id)

            # 5. Load voice profile
            vp_result = await session.execute(
                select(VoiceProfile).where(VoiceProfile.user_id == episode.user_id)
            )
            voice_profile = vp_result.scalar_one_or_none()
            voice_dict = voice_profile.__dict__ if voice_profile else {}

            episode.status = "detecting"
            await session.commit()

            # 6. Invoke LangGraph pipeline (wired in Phase 7)
            await _run_graph(episode, voice_dict, session)

            # 7. Mark complete
            episode.status = "ready"
            episode.processing_completed_at = datetime.utcnow()
            await session.commit()

            log.info("pipeline_complete", episode_id=episode_id)
            return {"status": "ready", "episode_id": episode_id}

        except Exception as exc:
            log.error("pipeline_failed", episode_id=episode_id, error=str(exc))
            episode.status = "error"
            episode.error_message = str(exc)
            await session.commit()
            raise


async def _download_youtube(url: str, episode_id: str) -> str:
    """Download audio from a YouTube URL for the given episode.

    Args:
        url: YouTube video URL.
        episode_id: UUID string used to create an isolated output directory.

    Returns:
        Local path to the downloaded MP3 file.
    """
    from api.config import settings
    from api.ingestion.youtube_downloader import YouTubeDownloader

    output_dir = Path(settings.UPLOADS_DIR) / "youtube" / episode_id
    output_dir.mkdir(parents=True, exist_ok=True)

    downloader = YouTubeDownloader()
    return await downloader.download(url, str(output_dir))


async def _download_rss(feed_url: str) -> str:
    """Download the latest episode audio from an RSS feed.

    Args:
        feed_url: Podcast RSS feed URL.

    Returns:
        Local path to the downloaded audio file.
    """
    from api.ingestion.rss_parser import RSSParser

    parser = RSSParser()
    rss_episode = await parser.get_latest_episode(feed_url)
    return rss_episode.audio_path


async def _run_graph(episode: object, voice_dict: dict, session: object) -> None:
    """Invoke the LangGraph pipeline to detect moments and generate content.

    Runs the full graph: moment_detector → content_factory → quality_checker.
    Saves detected moments and the content pack to the database.

    Args:
        episode: Episode ORM object with transcript populated.
        voice_dict: Voice profile as a plain dict.
        session: Active AsyncSession for saving results.
    """
    import uuid as _uuid

    from api.agent.graph import podcast_graph
    from api.agent.state import PodcastState
    from api.db.models import ContentPack, Moment

    session_id = str(episode.id)

    initial_state: PodcastState = {
        "session_id": session_id,
        "user_id": str(episode.user_id),
        "episode_id": str(episode.id),
        "source_type": episode.source_type or "upload",
        "audio_path": episode.audio_path or "",
        "transcript": episode.transcript or "",
        "speaker_segments": [],
        "voice_profile": voice_dict,
        "moments": [],
        "content_pack": {},
        "status": "detecting",
        "error": None,
    }

    log.info("graph_invoke_start", episode_id=str(episode.id))
    final_state = await podcast_graph.ainvoke(initial_state)
    log.info("graph_invoke_done", episode_id=str(episode.id), status=final_state.get("status"))

    # Save detected moments
    for i, m in enumerate(final_state.get("moments") or []):
        moment = Moment(
            id=_uuid.uuid4(),
            episode_id=episode.id,
            start_time=m.get("start_time", ""),
            end_time=m.get("end_time", ""),
            text=m.get("text", ""),
            moment_type=m.get("type", ""),
            shareability_score=m.get("shareability_score", 0.0),
            one_line_hook=m.get("one_line_hook", ""),
            position=i,
        )
        session.add(moment)

    # Save content pack
    pack = final_state.get("content_pack") or {}

    twitter = pack.get("twitter") or {}
    linkedin = pack.get("linkedin") or {}
    newsletter = pack.get("newsletter") or {}
    short_video = pack.get("short_video") or {}
    blog_post = pack.get("blog_post") or {}
    youtube = pack.get("youtube") or {}
    quote_cards = pack.get("quote_cards") or {}
    email_seq = pack.get("email_sequence") or {}

    content_pack = ContentPack(
        id=_uuid.uuid4(),
        episode_id=episode.id,
        twitter_thread=twitter.get("main_thread"),
        twitter_hooks=twitter.get("standalone_hooks"),
        twitter_listen_tweet=twitter.get("listen_tweet"),
        linkedin_post=linkedin.get("post"),
        linkedin_carousel_outline=linkedin.get("carousel_outline"),
        newsletter_section=newsletter.get("section_body"),
        newsletter_subject_lines=newsletter.get("subject_lines"),
        short_video_scripts=short_video.get("clips"),
        blog_post_title=blog_post.get("title"),
        blog_post_body=blog_post.get("body"),
        blog_post_meta=blog_post.get("meta_description"),
        youtube_description=youtube.get("description"),
        youtube_chapters=youtube.get("chapters"),
        quote_cards=quote_cards.get("quotes"),
        email_sequence=email_seq.get("emails"),
    )
    session.add(content_pack)
    await session.commit()

    log.info("content_pack_saved", episode_id=str(episode.id))
