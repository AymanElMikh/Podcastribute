"""Authentication routes — register, login, and current user endpoints."""

from datetime import datetime, timedelta, timezone

import bcrypt
import structlog
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import User
from api.db.session import get_db
from api.dependencies import get_current_user
from api.models.user import TokenResponse, UserCreate, UserResponse

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

TOKEN_EXPIRE_DAYS: int = 30


def _hash_password(plaintext: str) -> str:
    """Return a bcrypt hash of the plaintext password."""
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def _verify_password(plaintext: str, hashed: str) -> bool:
    """Return True if the plaintext matches the stored bcrypt hash."""
    return bcrypt.checkpw(plaintext.encode(), hashed.encode())


def _create_access_token(user: User) -> str:
    """Encode a signed JWT for the given user.

    Args:
        user: Authenticated User ORM instance.

    Returns:
        Signed JWT string valid for TOKEN_EXPIRE_DAYS days.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "plan": user.plan,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _user_response(user: User) -> UserResponse:
    """Build a UserResponse from a User ORM instance."""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        plan=user.plan,
        episodes_this_month=user.episodes_this_month,
        created_at=user.created_at,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account.

    Hashes the password with bcrypt and stores the user record.

    Args:
        body: UserCreate with email and plaintext password.
        db: Async database session.

    Returns:
        UserResponse with the new user's public data.

    Raises:
        HTTPException: 409 if email is already registered.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=_hash_password(body.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    log.info("user_registered", user_id=str(user.id), email=user.email)
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user and return a JWT access token.

    Args:
        body: UserCreate with email and plaintext password.
        db: Async database session.

    Returns:
        TokenResponse with signed JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not _verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_access_token(user)
    log.info("user_login", user_id=str(user.id))
    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the currently authenticated user's profile.

    Args:
        current_user: User resolved from the JWT bearer token.

    Returns:
        UserResponse for the authenticated user.
    """
    return _user_response(current_user)
