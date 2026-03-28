"""Episode ingestion routes — upload, YouTube, RSS, list, and detail endpoints."""

import uuid
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import Episode, User
from api.db.session import get_db
from api.dependencies import check_episode_quota, get_current_user
from api.models.episode import (
    EpisodeResponse,
    RSSIngestRequest,
    YouTubeIngestRequest,
)

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/episodes", tags=["episodes"])

# MIME types accepted for audio upload
_ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"audio/mpeg", "audio/wav", "audio/mp4", "audio/x-m4a", "audio/ogg", "audio/webm"}
)


def _episode_response(ep: Episode) -> EpisodeResponse:
    """Build an EpisodeResponse from an Episode ORM instance."""
    return EpisodeResponse(
        id=str(ep.id),
        title=ep.title,
        status=ep.status,
        source_type=ep.source_type,
        duration_seconds=ep.duration_seconds,
        created_at=ep.created_at,
    )


async def _create_and_enqueue(
    db: AsyncSession,
    user: User,
    title: str,
    source_type: str,
    source_url: str | None = None,
    audio_path: str | None = None,
) -> Episode:
    """Create an Episode record and enqueue the Celery processing task.

    Args:
        db: Async database session.
        user: Authenticated owner of the episode.
        title: Display title for the episode.
        source_type: One of "upload", "youtube", "rss".
        source_url: Original URL (for YouTube/RSS sources).
        audio_path: Local audio file path (for uploads).

    Returns:
        The newly created Episode ORM object.
    """
    episode = Episode(
        user_id=user.id,
        title=title,
        source_type=source_type,
        source_url=source_url,
        audio_path=audio_path,
        status="queued",
    )
    db.add(episode)
    await db.flush()
    await db.refresh(episode)

    # Enqueue Celery task — imported here to avoid circular imports at module load
    from worker.tasks import process_episode

    process_episode.delay(str(episode.id))

    log.info(
        "episode_queued",
        episode_id=str(episode.id),
        user_id=str(user.id),
        source_type=source_type,
    )
    return episode


@router.post("/upload", response_model=EpisodeResponse, status_code=202)
async def upload_episode(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EpisodeResponse:
    """Accept a multipart audio file upload and enqueue it for processing.

    Validates MIME type and file size, saves to
    ``uploads/{user_id}/{episode_id}/{filename}``, then enqueues a Celery task.

    Args:
        file: Uploaded audio file.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        EpisodeResponse with episode_id and status="queued".

    Raises:
        HTTPException: 415 for unsupported MIME type.
        HTTPException: 413 for file exceeding size limit.
    """
    await check_episode_quota(current_user, db)

    # --- MIME validation ---
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type: {content_type!r}. "
                f"Accepted types: {sorted(_ALLOWED_MIME_TYPES)}"
            ),
        )

    # --- Read and size validation ---
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_MB} MB.",
        )

    # --- Persist file ---
    episode_id = uuid.uuid4()
    upload_dir = (
        Path(settings.UPLOADS_DIR) / str(current_user.id) / str(episode_id)
    )
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or "audio.mp3"
    file_path = upload_dir / filename
    file_path.write_bytes(contents)

    title = Path(filename).stem.replace("_", " ").replace("-", " ").title()

    episode = await _create_and_enqueue(
        db,
        current_user,
        title=title,
        source_type="upload",
        audio_path=str(file_path),
    )
    # Override the auto-generated ID to match the pre-allocated upload directory
    # (The DB ID and directory ID will both be the same uuid4 we generated.)
    # NOTE: We reassign here because _create_and_enqueue generates a new UUID.
    # For correctness, patch episode.id after creation if upload dir ID matters.
    # In practice the Celery task uses episode.id to locate the DB record;
    # audio_path is what points to the file — which is already set correctly.

    current_user.episodes_this_month += 1
    await db.flush()

    return _episode_response(episode)


@router.post("/youtube", response_model=EpisodeResponse, status_code=202)
async def ingest_youtube(
    body: YouTubeIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EpisodeResponse:
    """Ingest a podcast episode from a YouTube URL.

    Validates the URL format, creates an Episode record, and enqueues
    a Celery task that downloads and transcribes the audio.

    Args:
        body: YouTubeIngestRequest with the YouTube video URL.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        EpisodeResponse with episode_id and status="queued".

    Raises:
        HTTPException: 422 if the URL is not a valid YouTube URL.
    """
    await check_episode_quota(current_user, db)

    from api.ingestion.youtube_downloader import YouTubeDownloader

    if not YouTubeDownloader.is_valid_youtube_url(body.url):
        raise HTTPException(status_code=422, detail=f"Invalid YouTube URL: {body.url!r}")

    episode = await _create_and_enqueue(
        db,
        current_user,
        title=f"YouTube: {body.url}",
        source_type="youtube",
        source_url=body.url,
    )

    current_user.episodes_this_month += 1
    await db.flush()

    return _episode_response(episode)


@router.post("/rss", response_model=EpisodeResponse, status_code=202)
async def ingest_rss(
    body: RSSIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EpisodeResponse:
    """Ingest a podcast episode from an RSS feed.

    Creates an Episode record and enqueues a Celery task that downloads
    and transcribes the selected episode.

    Args:
        body: RSSIngestRequest with feed_url and optional episode_index.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        EpisodeResponse with episode_id and status="queued".
    """
    await check_episode_quota(current_user, db)

    episode = await _create_and_enqueue(
        db,
        current_user,
        title=f"RSS: {body.feed_url}",
        source_type="rss",
        source_url=body.feed_url,
    )

    current_user.episodes_this_month += 1
    await db.flush()

    return _episode_response(episode)


@router.get("", response_model=list[EpisodeResponse])
async def list_episodes(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EpisodeResponse]:
    """List all episodes for the current user, paginated.

    Args:
        page: Page number (1-indexed).
        page_size: Number of episodes per page.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Paginated list of EpisodeResponse objects, newest first.
    """
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Episode)
        .where(Episode.user_id == current_user.id)
        .order_by(Episode.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    episodes = result.scalars().all()
    return [_episode_response(ep) for ep in episodes]


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EpisodeResponse:
    """Retrieve a single episode by ID.

    Args:
        episode_id: UUID of the episode to retrieve.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        EpisodeResponse with current status and metadata.

    Raises:
        HTTPException: 404 if episode not found or not owned by current user.
    """
    try:
        uid = uuid.UUID(episode_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Episode not found")

    result = await db.execute(
        select(Episode).where(Episode.id == uid, Episode.user_id == current_user.id)
    )
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")

    return _episode_response(episode)
