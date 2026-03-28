"""SSE streaming endpoint for real-time episode processing progress."""

import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import Episode
from api.db.session import get_db
from api.dependencies import get_current_user
from api.streaming import event_stream

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/stream", tags=["stream"])


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Provide an async Redis client for the request lifecycle.

    Yields:
        An aioredis.Redis client connected to REDIS_URL.
    """
    client: aioredis.Redis = aioredis.from_url(
        settings.REDIS_URL, decode_responses=False
    )
    try:
        yield client
    finally:
        await client.aclose()


@router.get("/{episode_id}")
async def stream_episode_progress(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
) -> StreamingResponse:
    """Stream real-time processing progress events for an episode via SSE.

    Verifies the episode belongs to the current user, then opens a Redis
    pub/sub subscription and streams events as Server-Sent Events.
    The stream terminates when a "content_ready" or "error" event is received.

    Args:
        episode_id: UUID of the episode to stream progress for.
        db: Async database session.
        current_user: Authenticated user from JWT.
        redis: Async Redis client.

    Returns:
        StreamingResponse with text/event-stream media type.

    Raises:
        HTTPException: 404 if episode not found or not owned by current user.
        HTTPException: 422 if episode_id is not a valid UUID.
    """
    try:
        ep_uuid = uuid.UUID(episode_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid episode_id format")

    result = await db.execute(
        select(Episode).where(
            Episode.id == ep_uuid,
            Episode.user_id == current_user.id,
        )
    )
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")

    log.info(
        "sse_stream_opened",
        episode_id=episode_id,
        user_id=str(current_user.id),
    )

    return StreamingResponse(
        event_stream(redis, episode_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
