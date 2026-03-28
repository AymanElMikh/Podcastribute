"""LangGraph node: runs all 8 content generators in parallel.

Invokes every generator concurrently using asyncio.gather, handles
partial failures gracefully, and emits SSE progress events.
"""

import asyncio

import structlog

from api.agent.state import PodcastState
from api.generators.blog_post import BlogPostGenerator
from api.generators.email_sequence import EmailSequenceGenerator
from api.generators.linkedin import LinkedInGenerator
from api.generators.newsletter import NewsletterGenerator
from api.generators.quote_cards import QuoteCardGenerator
from api.generators.short_video import ShortVideoGenerator
from api.generators.twitter import TwitterGenerator
from api.generators.youtube_description import YouTubeDescriptionGenerator

log = structlog.get_logger(__name__)

# Ordered list of (format_name, GeneratorClass) pairs — order determines pack keys
_GENERATOR_REGISTRY: list[tuple[str, type]] = [
    ("twitter", TwitterGenerator),
    ("linkedin", LinkedInGenerator),
    ("newsletter", NewsletterGenerator),
    ("short_video", ShortVideoGenerator),
    ("blog_post", BlogPostGenerator),
    ("youtube", YouTubeDescriptionGenerator),
    ("quote_cards", QuoteCardGenerator),
    ("email_sequence", EmailSequenceGenerator),
]


async def _emit(session_id: str, event_type: str, data: dict) -> None:
    """Fire-and-forget SSE event emission.

    Delegates to api.streaming.emit_event when available.  Silently
    swallowed if SSE is not yet wired (Phase 8) so the node never
    crashes due to a missing redis connection.

    Args:
        session_id: Session identifier for the pub/sub channel.
        event_type: Event type string (e.g. "generating_content").
        data: Arbitrary payload dict attached to the event.
    """
    try:
        from api.streaming import emit_event  # noqa: PLC0415

        await emit_event(None, session_id, event_type, data)
    except Exception:
        # SSE not yet wired or redis unavailable — log and continue
        log.debug("sse_emit_skipped", session_id=session_id, event_type=event_type)


async def content_factory(state: PodcastState) -> dict:
    """Generate all 8 content formats concurrently from detected moments.

    Uses asyncio.gather so all generators run in parallel. A failed generator
    does not stop the pipeline — its error is recorded in the content pack.
    Emits SSE events at start and on completion.

    Args:
        state: Current pipeline state with moments, transcript, and voice_profile.

    Returns:
        Dict with keys "content_pack" (all format outputs) and "status".
    """
    session_id = state.get("session_id", "")
    episode_id = state.get("episode_id", "")
    voice = state.get("voice_profile") or {}
    moments = state.get("moments") or []
    transcript = state.get("transcript") or ""

    await _emit(
        session_id,
        "generating_content",
        {"formats": len(_GENERATOR_REGISTRY), "message": "Generating all content formats..."},
    )

    log.info(
        "content_factory_start",
        episode_id=episode_id,
        formats=len(_GENERATOR_REGISTRY),
        moments=len(moments),
    )

    generators = [(name, cls(voice)) for name, cls in _GENERATOR_REGISTRY]

    results = await asyncio.gather(
        *[gen.generate(moments, transcript) for _, gen in generators],
        return_exceptions=True,
    )

    pack: dict = {}
    success_count = 0

    for (name, _), result in zip(generators, results):
        if isinstance(result, Exception):
            pack[name] = {"error": str(result), "content": None}
            log.warning("generator_failed", format=name, error=str(result), episode_id=episode_id)
        else:
            pack[name] = result.model_dump()
            success_count += 1

    log.info(
        "content_factory_done",
        episode_id=episode_id,
        success=success_count,
        total=len(_GENERATOR_REGISTRY),
    )

    await _emit(
        session_id,
        "content_ready",
        {"formats_generated": success_count, "episode_id": episode_id},
    )

    return {"content_pack": pack, "status": "ready"}
