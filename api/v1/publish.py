"""Content publishing routes — publish to platforms and view publish history."""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import ContentPack, Episode, PublishLog
from api.db.session import get_db
from api.dependencies import get_current_user
from api.publisher.beehiiv_client import BeehiivClient
from api.publisher.buffer_client import BufferClient
from api.publisher.linkedin_client import LinkedInClient

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/publish", tags=["publish"])

# ---------------------------------------------------------------------------
# Supported platforms and their routing
# ---------------------------------------------------------------------------

SUPPORTED_PLATFORMS: frozenset[str] = frozenset(
    {"twitter", "linkedin", "newsletter"}
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class PublishRequest(BaseModel):
    """Request body for publishing content to one or more platforms."""

    episode_id: str
    platforms: list[str]
    content_overrides: dict[str, Any] = {}
    schedule_at: str | None = None


class PublishLogResponse(BaseModel):
    """Single publish log entry."""

    id: str
    platform: str | None
    content_type: str | None
    status: str | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    error: str | None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_episode_for_user(
    episode_id: str, user_id: uuid.UUID, db: AsyncSession
) -> Episode:
    """Load an episode that belongs to the current user.

    Args:
        episode_id: UUID string of the target episode.
        user_id: Authenticated user's UUID.
        db: Async database session.

    Returns:
        The Episode ORM object.

    Raises:
        HTTPException: 422 if episode_id is not a valid UUID.
        HTTPException: 404 if episode not found or not owned by user.
    """
    try:
        ep_uuid = uuid.UUID(episode_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid episode_id format")

    result = await db.execute(
        select(Episode).where(
            Episode.id == ep_uuid,
            Episode.user_id == user_id,
        )
    )
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


async def _load_content_pack(
    episode_id: uuid.UUID, db: AsyncSession
) -> ContentPack | None:
    """Load the content pack for an episode.

    Args:
        episode_id: Episode UUID.
        db: Async database session.

    Returns:
        ContentPack ORM object, or None if not found.
    """
    result = await db.execute(
        select(ContentPack).where(ContentPack.episode_id == episode_id)
    )
    return result.scalar_one_or_none()


def _extract_platform_text(
    platform: str,
    pack: ContentPack | None,
    overrides: dict[str, Any],
) -> str:
    """Extract the primary text content for a platform from pack or overrides.

    Args:
        platform: Platform name (twitter, linkedin, newsletter).
        pack: ContentPack ORM object, may be None.
        overrides: Client-supplied content overrides.

    Returns:
        Text string ready to publish.
    """
    # Overrides take priority over stored content
    override = overrides.get(platform)
    if override and isinstance(override, dict):
        if platform == "twitter":
            thread = override.get("main_thread", [])
            return "\n\n".join(thread) if thread else ""
        if platform == "linkedin":
            return override.get("post", "")
        if platform == "newsletter":
            return override.get("section_body", "")

    if pack is None:
        return ""

    if platform == "twitter":
        thread = pack.twitter_thread or []
        return "\n\n".join(thread)
    if platform == "linkedin":
        return pack.linkedin_post or ""
    if platform == "newsletter":
        return pack.newsletter_section or ""

    return ""


async def _publish_to_platform(
    platform: str,
    text: str,
    pack: ContentPack | None,
    overrides: dict[str, Any],
    schedule_at: str | None,
) -> str:
    """Route a publish request to the correct platform client.

    In production, platform credentials are loaded from the user's connected
    accounts. Here we raise a clear error if credentials are missing so the
    frontend can prompt the user to connect.

    Args:
        platform: Target platform name.
        text: Content text to publish.
        pack: ContentPack ORM for additional structured data.
        overrides: Client-supplied content overrides.
        schedule_at: Optional ISO timestamp for scheduling.

    Returns:
        "sent" on success.

    Raises:
        ValueError: If platform credentials are missing or platform unsupported.
        httpx.HTTPStatusError: If the platform API rejects the request.
    """
    if platform == "twitter":
        # Buffer is used for Twitter scheduling
        # Credentials would be loaded from user's connected account in production
        raise ValueError(
            "Twitter publishing requires a connected Buffer account. "
            "Connect Buffer in Settings to enable direct publishing."
        )

    if platform == "linkedin":
        # Direct LinkedIn UGC Posts API
        raise ValueError(
            "LinkedIn publishing requires a connected LinkedIn account. "
            "Connect LinkedIn in Settings to enable direct publishing."
        )

    if platform == "newsletter":
        # Beehiiv draft creation
        raise ValueError(
            "Newsletter publishing requires a connected Beehiiv account. "
            "Connect Beehiiv in Settings to enable direct publishing."
        )

    raise ValueError(f"Unsupported platform: {platform!r}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("")
async def publish_content(
    body: PublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    """Publish content to one or more platforms, immediately or on a schedule.

    For each platform requested:
    1. Loads the stored content pack (or uses the provided override).
    2. Calls the appropriate publisher client.
    3. Logs the result to publish_logs.

    Args:
        body: Publish request with episode_id, platforms, overrides, schedule_at.
        db: Async database session.
        current_user: Authenticated user from JWT.

    Returns:
        Dict mapping platform name to status ("sent", "failed", or "scheduled").

    Raises:
        HTTPException: 404 if episode not found.
        HTTPException: 400 if no valid platforms provided.
    """
    episode = await _load_episode_for_user(
        body.episode_id, current_user.id, db
    )

    platforms = [p for p in body.platforms if p in SUPPORTED_PLATFORMS]
    if not platforms:
        raise HTTPException(
            status_code=400,
            detail=f"No supported platforms in request. Supported: {sorted(SUPPORTED_PLATFORMS)}",
        )

    pack = await _load_content_pack(episode.id, db)
    results: dict[str, str] = {}

    for platform in platforms:
        text = _extract_platform_text(platform, pack, body.content_overrides)
        status = "failed"
        error_msg: str | None = None
        sent_at: datetime | None = None

        try:
            await _publish_to_platform(
                platform, text, pack, body.content_overrides, body.schedule_at
            )
            status = "scheduled" if body.schedule_at else "sent"
            sent_at = datetime.now(timezone.utc)
        except Exception as exc:
            error_msg = str(exc)
            log.warning(
                "publish_failed",
                platform=platform,
                episode_id=str(episode.id),
                error=error_msg,
            )

        # Log the attempt regardless of success/failure
        log_entry = PublishLog(
            id=uuid.uuid4(),
            episode_id=episode.id,
            platform=platform,
            content_type="text",
            status=status,
            scheduled_at=datetime.fromisoformat(body.schedule_at)
            if body.schedule_at
            else None,
            sent_at=sent_at,
            error=error_msg,
        )
        db.add(log_entry)
        results[platform] = status

    await db.commit()

    log.info(
        "publish_completed",
        episode_id=body.episode_id,
        results=results,
    )
    return results


@router.get("/{episode_id}")
async def get_publish_logs(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[PublishLogResponse]:
    """List all publish attempts for a given episode.

    Args:
        episode_id: UUID of the episode to retrieve publish history for.
        db: Async database session.
        current_user: Authenticated user from JWT.

    Returns:
        List of publish log entries ordered by most recent first.

    Raises:
        HTTPException: 404 if episode not found or not owned by user.
    """
    episode = await _load_episode_for_user(episode_id, current_user.id, db)

    result = await db.execute(
        select(PublishLog)
        .where(PublishLog.episode_id == episode.id)
        .order_by(PublishLog.sent_at.desc().nulls_last())
    )
    logs = result.scalars().all()

    return [
        PublishLogResponse(
            id=str(entry.id),
            platform=entry.platform,
            content_type=entry.content_type,
            status=entry.status,
            scheduled_at=entry.scheduled_at,
            sent_at=entry.sent_at,
            error=entry.error,
        )
        for entry in logs
    ]
