"""FastAPI dependency functions for auth, DB, and plan enforcement."""

import uuid
from collections.abc import Callable
from datetime import datetime, timezone

import structlog
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import User
from api.db.session import get_db

log = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

# Plan hierarchy — index = rank (higher is better)
PLAN_ORDER: list[str] = ["free", "starter", "creator", "studio"]

# Monthly episode limits per plan (None = unlimited)
PLAN_LIMITS: dict[str, int | None] = {
    "free": 1,
    "starter": 4,
    "creator": 15,
    "studio": None,
}

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate the JWT bearer token and return the current user.

    Decodes and verifies the JWT, then loads the user from the database.

    Args:
        token: JWT access token from the Authorization header.
        db: Async database session.

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException: 401 if token is invalid or expired.
        HTTPException: 404 if the user no longer exists.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise _CREDENTIALS_EXCEPTION
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def require_plan(min_plan: str) -> Callable:
    """Return a FastAPI dependency that enforces a minimum subscription plan.

    Plan hierarchy: free < starter < creator < studio

    Usage::

        @router.post("/feature")
        async def feature(user: User = Depends(require_plan("creator"))):
            ...

    Args:
        min_plan: Minimum plan name required to access the endpoint.

    Returns:
        An async dependency callable that resolves to the authenticated User.

    Raises:
        HTTPException: 403 with upgrade message if the user's plan is too low.
    """

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        """Enforce plan tier."""
        try:
            user_rank = PLAN_ORDER.index(current_user.plan)
            required_rank = PLAN_ORDER.index(min_plan)
        except ValueError:
            raise HTTPException(status_code=403, detail="Unknown plan tier")

        if user_rank < required_rank:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Your current plan ({current_user.plan!r}) does not include this feature. "
                    f"Upgrade to {min_plan!r} or higher."
                ),
            )
        return current_user

    return _check


async def check_episode_quota(user: User, db: AsyncSession) -> None:
    """Verify the user has not exceeded their monthly episode processing quota.

    Resets the episode counter when plan_reset_at has passed.
    Enforces plan limits: free=1 trial, starter=4, creator=15, studio=unlimited.

    Args:
        user: The authenticated User ORM object.
        db: Async database session.

    Raises:
        HTTPException: 429 with quota message if limit is reached.
    """
    now = datetime.now(timezone.utc)

    # Reset monthly counter if the reset date has passed
    if user.plan_reset_at is not None:
        from datetime import timedelta

        reset_at = user.plan_reset_at
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if now >= reset_at:
            user.episodes_this_month = 0
            user.plan_reset_at = now + timedelta(days=30)
            await db.flush()
            log.info("quota_reset", user_id=str(user.id), plan=user.plan)

    limit = PLAN_LIMITS.get(user.plan)
    if limit is not None and user.episodes_this_month >= limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Monthly episode limit reached ({limit} episodes on the {user.plan!r} plan). "
                "Upgrade your plan to process more episodes."
            ),
        )
