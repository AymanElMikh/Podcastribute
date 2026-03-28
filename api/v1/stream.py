"""SSE streaming endpoint for real-time episode processing progress."""

import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import Episode, User
from api.db.session import get_db
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


async def _resolve_user(
    request: Request,
    token: str | None,
    db: AsyncSession,
) -> User:
    """Resolve the authenticated user from either header or query param token.

    The browser EventSource API cannot set custom headers, so the JWT must be
    passed as a ``?token=`` query parameter for SSE connections. Regular API
    calls may still use the Authorization header.

    Args:
        request: FastAPI Request (used to read the Authorization header).
        token: Optional JWT passed as a query parameter.
        db: Async database session.

    Returns:
        Authenticated User ORM object.

    Raises:
        HTTPException: 401 if no token provided or token is invalid.
    """
    # Prefer query param (EventSource), fall back to Authorization header
    raw_token = token
    if not raw_token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[len("Bearer "):]

    if not raw_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    credentials_exc = HTTPException(status_code=401, detail="Invalid token")
    try:
        payload = jwt.decode(
            raw_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc
    return user


@router.get("/{episode_id}")
async def stream_episode_progress(
    episode_id: str,
    request: Request,
    token: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> StreamingResponse:
    """Stream real-time processing progress events for an episode via SSE.

    Accepts authentication via Authorization header OR ``?token=`` query param
    (required because the browser EventSource API cannot set custom headers).

    Verifies the episode belongs to the current user, then opens a Redis
    pub/sub subscription and streams events as Server-Sent Events.
    The stream terminates when a "content_ready" or "error" event is received.

    Args:
        episode_id: UUID of the episode to stream progress for.
        request: FastAPI request (for header-based auth fallback).
        token: Optional JWT passed as a query parameter.
        db: Async database session.
        redis: Async Redis client.

    Returns:
        StreamingResponse with text/event-stream media type.

    Raises:
        HTTPException: 401 if not authenticated.
        HTTPException: 404 if episode not found or not owned by current user.
        HTTPException: 422 if episode_id is not a valid UUID.
    """
    current_user = await _resolve_user(request, token, db)

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
