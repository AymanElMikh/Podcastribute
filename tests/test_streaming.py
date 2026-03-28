"""Tests for SSE streaming utilities and the /v1/stream/{episode_id} endpoint."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from api.db.models import User
from api.dependencies import get_current_user
from api.main import app
from api.streaming import TERMINAL_EVENTS, emit_event, event_stream
from api.v1.auth import _hash_password


# ---------------------------------------------------------------------------
# Auth fixtures (same pattern as test_ingestion.py / test_voice.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_user() -> User:
    """A minimal User with a pre-set UUID for dependency overrides."""
    return User(
        id=uuid.uuid4(),
        email="streamer@example.com",
        hashed_password=_hash_password("pw"),
        plan="creator",
        episodes_this_month=0,
    )


@pytest.fixture
def authed_client(client: AsyncClient, fake_user: User):
    """AsyncClient with get_current_user overridden to return fake_user."""
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_redis_message(event_type: str, data: dict | None = None) -> dict:
    """Build a fake Redis pub/sub message dict."""
    payload = json.dumps(
        {"type": event_type, "data": data or {}, "label": event_type, "timestamp": "2026-01-01T00:00:00+00:00"}
    )
    return {"type": "message", "data": payload.encode()}


def _make_subscribe_message() -> dict:
    """Build a fake Redis subscribe confirmation message (should be skipped)."""
    return {"type": "subscribe", "data": 1}


# ---------------------------------------------------------------------------
# emit_event
# ---------------------------------------------------------------------------


async def test_emit_event_publishes_to_correct_channel() -> None:
    """emit_event publishes to podcast:{session_id}."""
    mock_redis = AsyncMock()
    await emit_event(mock_redis, "sess-123", "upload_received")

    mock_redis.publish.assert_awaited_once()
    channel, payload = mock_redis.publish.call_args.args
    assert channel == "podcast:sess-123"


async def test_emit_event_payload_contains_required_fields() -> None:
    """emit_event payload has type, data, label, and timestamp."""
    mock_redis = AsyncMock()
    await emit_event(mock_redis, "sess-abc", "content_ready", {"episode_id": "ep-1"})

    _, payload = mock_redis.publish.call_args.args
    event = json.loads(payload)
    assert event["type"] == "content_ready"
    assert event["data"] == {"episode_id": "ep-1"}
    assert "label" in event
    assert "timestamp" in event


async def test_emit_event_none_redis_is_noop() -> None:
    """emit_event with redis=None does not raise and does not publish."""
    # Should not raise
    await emit_event(None, "sess-1", "upload_received")


async def test_emit_event_unknown_type_uses_type_as_label() -> None:
    """emit_event falls back to the event_type string for unknown types."""
    mock_redis = AsyncMock()
    await emit_event(mock_redis, "sess-1", "custom_event_xyz")

    _, payload = mock_redis.publish.call_args.args
    event = json.loads(payload)
    assert event["label"] == "custom_event_xyz"


# ---------------------------------------------------------------------------
# event_stream
# ---------------------------------------------------------------------------


async def test_event_stream_yields_sse_formatted_strings() -> None:
    """event_stream yields 'data: {...}\\n\\n' for each message."""
    messages = [
        _make_subscribe_message(),  # should be skipped
        _make_redis_message("moments_detected", {"count": 5}),
        _make_redis_message("content_ready"),
    ]

    mock_pubsub = AsyncMock()
    mock_pubsub.listen = MagicMock(return_value=_async_iter(messages))
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.aclose = AsyncMock()

    mock_redis = MagicMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    collected = []
    async for chunk in event_stream(mock_redis, "sess-1"):
        collected.append(chunk)

    assert len(collected) == 2  # subscribe message skipped
    assert collected[0].startswith("data: ")
    assert collected[0].endswith("\n\n")
    assert "moments_detected" in collected[0]


async def test_event_stream_stops_on_content_ready() -> None:
    """event_stream terminates after yielding the content_ready event."""
    messages = [
        _make_redis_message("generating_content"),
        _make_redis_message("content_ready"),
        _make_redis_message("should_not_appear"),  # after terminal event
    ]

    mock_pubsub = _make_pubsub(messages)
    mock_redis = MagicMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    collected = []
    async for chunk in event_stream(mock_redis, "sess-2"):
        collected.append(chunk)

    types = [json.loads(c[len("data: "):].strip())["type"] for c in collected]
    assert "content_ready" in types
    assert "should_not_appear" not in types


async def test_event_stream_stops_on_error_event() -> None:
    """event_stream terminates after yielding an error terminal event."""
    messages = [
        _make_redis_message("transcription_start"),
        _make_redis_message("error", {"message": "out of memory"}),
    ]

    mock_pubsub = _make_pubsub(messages)
    mock_redis = MagicMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    collected = []
    async for chunk in event_stream(mock_redis, "sess-3"):
        collected.append(chunk)

    types = [json.loads(c[len("data: "):].strip())["type"] for c in collected]
    assert types[-1] == "error"


async def test_event_stream_subscribes_and_unsubscribes() -> None:
    """event_stream subscribes to the correct channel and always unsubscribes."""
    messages = [_make_redis_message("content_ready")]

    mock_pubsub = _make_pubsub(messages)
    mock_redis = MagicMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    async for _ in event_stream(mock_redis, "sess-ep-42"):
        pass

    mock_pubsub.subscribe.assert_awaited_once_with("podcast:sess-ep-42")
    mock_pubsub.unsubscribe.assert_awaited_once()
    mock_pubsub.aclose.assert_awaited_once()


async def test_event_stream_skips_non_message_type() -> None:
    """event_stream ignores subscribe/unsubscribe confirmation messages."""
    messages = [
        {"type": "subscribe", "data": 1},
        {"type": "psubscribe", "data": 1},
        _make_redis_message("content_ready"),
    ]

    mock_pubsub = _make_pubsub(messages)
    mock_redis = MagicMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    collected = []
    async for chunk in event_stream(mock_redis, "sess-4"):
        collected.append(chunk)

    assert len(collected) == 1
    assert "content_ready" in collected[0]


# ---------------------------------------------------------------------------
# /v1/stream/{episode_id} endpoint
# ---------------------------------------------------------------------------


async def test_stream_endpoint_returns_404_for_unknown_episode(authed_client) -> None:
    """GET /v1/stream/{id} returns 404 when episode does not exist."""
    from api.v1.stream import get_redis

    fake_id = str(uuid.uuid4())
    app.dependency_overrides[get_redis] = _fake_redis_dep
    try:
        response = await authed_client.get(f"/v1/stream/{fake_id}")
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 404


async def test_stream_endpoint_returns_422_for_invalid_uuid(authed_client) -> None:
    """GET /v1/stream/not-a-uuid returns 422."""
    from api.v1.stream import get_redis

    app.dependency_overrides[get_redis] = _fake_redis_dep
    try:
        response = await authed_client.get("/v1/stream/not-a-uuid")
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 422


async def test_stream_endpoint_returns_event_stream(authed_client, db_session, fake_user) -> None:
    """GET /v1/stream/{id} returns text/event-stream for a valid episode."""
    from api.db.models import Episode
    from api.v1.stream import get_redis

    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="Test Episode",
        source_type="upload",
        status="generating",
    )
    db_session.add(episode)
    await db_session.commit()

    events = [_make_redis_message("content_ready")]
    mock_pubsub = _make_pubsub(events)
    mock_redis = MagicMock()
    mock_redis.pubsub = MagicMock(return_value=mock_pubsub)

    async def _redis_with_events():
        yield mock_redis

    app.dependency_overrides[get_redis] = _redis_with_events
    try:
        response = await authed_client.get(f"/v1/stream/{episode.id}")
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "content_ready" in response.text


async def test_stream_endpoint_rejects_other_users_episode(authed_client, db_session) -> None:
    """GET /v1/stream/{id} returns 404 for an episode owned by another user."""
    from api.db.models import Episode
    from api.v1.stream import get_redis

    other_user_id = uuid.uuid4()
    episode = Episode(
        id=uuid.uuid4(),
        user_id=other_user_id,
        title="Someone Else's Episode",
        source_type="upload",
        status="generating",
    )
    db_session.add(episode)
    await db_session.commit()

    app.dependency_overrides[get_redis] = _fake_redis_dep
    try:
        response = await authed_client.get(f"/v1/stream/{episode.id}")
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------


async def _async_iter(items):
    """Yield items as an async iterable."""
    for item in items:
        yield item


def _make_pubsub(messages: list[dict]) -> AsyncMock:
    """Build a mock pubsub object that returns the given messages from listen()."""
    mock_pubsub = AsyncMock()
    mock_pubsub.listen = MagicMock(return_value=_async_iter(messages))
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.aclose = AsyncMock()
    return mock_pubsub


async def _fake_redis_dep():
    """Dependency override that yields a do-nothing Redis mock."""
    yield AsyncMock()
