"""Tests for authentication endpoints and dependency enforcement.

Covers registration, login, JWT validation, and plan/quota checks.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import User
from api.dependencies import PLAN_LIMITS, check_episode_quota, require_plan
from api.v1.auth import _hash_password, _verify_password


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def test_register_creates_user(client: AsyncClient) -> None:
    """Registration returns 201 and the new user's public data."""
    resp = await client.post(
        "/v1/auth/register",
        json={"email": "alice@example.com", "password": "hunter2"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["plan"] == "free"
    assert data["episodes_this_month"] == 0
    assert "id" in data


async def test_register_hashes_password(client: AsyncClient, db_session: AsyncSession) -> None:
    """Stored password must be a bcrypt hash, not plaintext."""
    await client.post(
        "/v1/auth/register",
        json={"email": "bob@example.com", "password": "secret123"},
    )
    result = await db_session.execute(
        __import__("sqlalchemy").select(User).where(User.email == "bob@example.com")
    )
    user = result.scalar_one()
    assert user.hashed_password != "secret123"
    assert _verify_password("secret123", user.hashed_password)


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    """Registering with the same email twice returns HTTP 409."""
    payload = {"email": "dupe@example.com", "password": "pass"}
    await client.post("/v1/auth/register", json=payload)
    resp = await client.post("/v1/auth/register", json=payload)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_returns_valid_jwt(client: AsyncClient) -> None:
    """Successful login returns a JWT with correct claims."""
    await client.post(
        "/v1/auth/register",
        json={"email": "carol@example.com", "password": "mypassword"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": "carol@example.com", "password": "mypassword"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    token = data["access_token"]

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    assert payload["email"] == "carol@example.com"
    assert payload["plan"] == "free"
    assert "sub" in payload
    assert "exp" in payload


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    """Login with an incorrect password returns HTTP 401."""
    await client.post(
        "/v1/auth/register",
        json={"email": "dave@example.com", "password": "correct"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": "dave@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient) -> None:
    """Login with an email that was never registered returns HTTP 401."""
    resp = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me — JWT validation
# ---------------------------------------------------------------------------


async def test_me_returns_current_user(client: AsyncClient) -> None:
    """GET /v1/auth/me returns the authenticated user's data."""
    await client.post(
        "/v1/auth/register",
        json={"email": "eve@example.com", "password": "pw"},
    )
    login_resp = await client.post(
        "/v1/auth/login",
        json={"email": "eve@example.com", "password": "pw"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "eve@example.com"


async def test_me_expired_token_returns_401(client: AsyncClient) -> None:
    """GET /v1/auth/me with an expired token returns HTTP 401."""
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": "ghost@example.com",
        "plan": "free",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    resp = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


async def test_me_invalid_token_returns_401(client: AsyncClient) -> None:
    """GET /v1/auth/me with a garbage token returns HTTP 401."""
    resp = await client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Plan enforcement
# ---------------------------------------------------------------------------


async def test_require_plan_blocks_insufficient_tier(client: AsyncClient) -> None:
    """require_plan('studio') rejects a free-plan user with HTTP 403."""
    from api.main import app

    await client.post(
        "/v1/auth/register",
        json={"email": "frank@example.com", "password": "pw"},
    )
    login_resp = await client.post(
        "/v1/auth/login",
        json={"email": "frank@example.com", "password": "pw"},
    )
    token = login_resp.json()["access_token"]

    # Build a minimal test route that uses require_plan("studio")
    from fastapi import APIRouter, Depends

    test_router = APIRouter()

    @test_router.get("/_test_plan_check")
    async def _plan_guarded(_: User = Depends(require_plan("studio"))) -> dict:
        return {"ok": True}

    app.include_router(test_router)

    resp = await client.get(
        "/_test_plan_check",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403

    # Cleanup — remove the ephemeral route
    app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_plan_check"]


async def test_require_plan_allows_sufficient_tier(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """require_plan('starter') allows a creator-plan user through."""
    from sqlalchemy import select

    # Register and bump plan to creator
    await client.post(
        "/v1/auth/register",
        json={"email": "grace@example.com", "password": "pw"},
    )
    result = await db_session.execute(select(User).where(User.email == "grace@example.com"))
    grace = result.scalar_one()
    grace.plan = "creator"
    await db_session.flush()

    # Build a token carrying the updated plan (re-login would return old plan from JWT cache)
    from api.v1.auth import _create_access_token

    token = _create_access_token(grace)

    from fastapi import APIRouter, Depends

    from api.main import app

    test_router2 = APIRouter()

    @test_router2.get("/_test_plan_ok")
    async def _plan_ok(_: User = Depends(require_plan("starter"))) -> dict:
        return {"ok": True}

    app.include_router(test_router2)

    resp = await client.get(
        "/_test_plan_ok",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_plan_ok"]


# ---------------------------------------------------------------------------
# Episode quota
# ---------------------------------------------------------------------------


async def test_check_episode_quota_blocks_at_limit(db_session: AsyncSession) -> None:
    """check_episode_quota raises 429 when user is at their plan limit."""
    user = User(
        email="quota@example.com",
        hashed_password=_hash_password("pw"),
        plan="starter",
        episodes_this_month=PLAN_LIMITS["starter"],  # at limit
    )
    db_session.add(user)
    await db_session.flush()

    with pytest.raises(Exception) as exc_info:
        await check_episode_quota(user, db_session)

    assert exc_info.value.status_code == 429


async def test_check_episode_quota_passes_under_limit(db_session: AsyncSession) -> None:
    """check_episode_quota does not raise when user is under their limit."""
    user = User(
        email="underquota@example.com",
        hashed_password=_hash_password("pw"),
        plan="creator",
        episodes_this_month=3,  # under limit of 15
    )
    db_session.add(user)
    await db_session.flush()

    # Should not raise
    await check_episode_quota(user, db_session)


async def test_check_episode_quota_studio_unlimited(db_session: AsyncSession) -> None:
    """Studio plan users are never quota-blocked."""
    user = User(
        email="studio@example.com",
        hashed_password=_hash_password("pw"),
        plan="studio",
        episodes_this_month=9999,
    )
    db_session.add(user)
    await db_session.flush()

    # Should not raise regardless of episode count
    await check_episode_quota(user, db_session)


async def test_check_episode_quota_resets_on_new_period(db_session: AsyncSession) -> None:
    """check_episode_quota resets the counter when plan_reset_at has passed."""
    past_reset = datetime.now(timezone.utc) - timedelta(days=1)
    user = User(
        email="reset@example.com",
        hashed_password=_hash_password("pw"),
        plan="starter",
        episodes_this_month=PLAN_LIMITS["starter"],  # at limit
        plan_reset_at=past_reset,
    )
    db_session.add(user)
    await db_session.flush()

    # Reset should fire and counter drops to 0 — no 429
    await check_episode_quota(user, db_session)
    assert user.episodes_this_month == 0
