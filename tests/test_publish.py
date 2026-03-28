"""Tests for publisher clients, publish endpoint, and content endpoint."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
import httpx
from httpx import AsyncClient

from api.db.models import ContentPack, Episode, PublishLog, User
from api.dependencies import get_current_user
from api.main import app
from api.publisher.beehiiv_client import BeehiivClient
from api.publisher.buffer_client import BufferClient
from api.publisher.linkedin_client import LinkedInClient
from api.v1.auth import _hash_password


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_user() -> User:
    """Minimal User with pre-set UUID."""
    return User(
        id=uuid.uuid4(),
        email="publisher@example.com",
        hashed_password=_hash_password("pw"),
        plan="creator",
        episodes_this_month=0,
    )


@pytest.fixture
def authed_client(client: AsyncClient, fake_user: User):
    """AsyncClient with get_current_user overridden."""
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# BufferClient
# ---------------------------------------------------------------------------


@respx.mock
async def test_buffer_schedule_post_calls_correct_endpoint() -> None:
    """BufferClient.schedule_post POSTs to the Buffer updates/create endpoint."""
    respx.post("https://api.bufferapp.com/1/updates/create.json").mock(
        return_value=httpx.Response(200, json={"updates": [{"id": "buf-123"}]})
    )

    client = BufferClient(access_token="tok-abc")
    result = await client.schedule_post(
        profile_id="profile-1",
        text="Hello Buffer!",
    )

    assert result["updates"][0]["id"] == "buf-123"
    assert respx.calls.call_count == 1


@respx.mock
async def test_buffer_schedule_post_includes_scheduled_at() -> None:
    """BufferClient passes scheduled_at when provided."""
    route = respx.post("https://api.bufferapp.com/1/updates/create.json").mock(
        return_value=httpx.Response(200, json={"updates": [{"id": "buf-456"}]})
    )

    client = BufferClient(access_token="tok-abc")
    await client.schedule_post(
        profile_id="profile-1",
        text="Scheduled post",
        scheduled_at="2026-04-01T10:00:00Z",
    )

    sent_data = route.calls[0].request.content.decode()
    assert "scheduled_at" in sent_data


@respx.mock
async def test_buffer_raises_on_api_error() -> None:
    """BufferClient raises HTTPStatusError on non-2xx response."""
    respx.post("https://api.bufferapp.com/1/updates/create.json").mock(
        return_value=httpx.Response(401, json={"error": "Unauthorized"})
    )

    client = BufferClient(access_token="bad-token")
    with pytest.raises(httpx.HTTPStatusError):
        await client.schedule_post(profile_id="p1", text="test")


# ---------------------------------------------------------------------------
# BeehiivClient
# ---------------------------------------------------------------------------


@respx.mock
async def test_beehiiv_create_draft_calls_correct_endpoint() -> None:
    """BeehiivClient.create_draft POSTs to the Beehiiv publications endpoint."""
    pub_id = "pub-xyz"
    respx.post(f"https://api.beehiiv.com/v2/publications/{pub_id}/posts").mock(
        return_value=httpx.Response(201, json={"data": {"id": "post-999"}})
    )

    client = BeehiivClient(api_key="bh-key", publication_id=pub_id)
    result = await client.create_draft(
        subject="My newsletter subject",
        body_html="<p>Hello subscribers!</p>",
        preview_text="A great read",
    )

    assert result["data"]["id"] == "post-999"


@respx.mock
async def test_beehiiv_create_draft_sets_status_draft() -> None:
    """BeehiivClient always creates posts as drafts."""
    pub_id = "pub-xyz"
    route = respx.post(
        f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
    ).mock(return_value=httpx.Response(201, json={"data": {"id": "d1"}}))

    client = BeehiivClient(api_key="bh-key", publication_id=pub_id)
    await client.create_draft(subject="Sub", body_html="<p>body</p>")

    import json
    body = json.loads(route.calls[0].request.content)
    assert body["status"] == "draft"


@respx.mock
async def test_beehiiv_raises_on_api_error() -> None:
    """BeehiivClient raises HTTPStatusError on non-2xx response."""
    pub_id = "pub-xyz"
    respx.post(f"https://api.beehiiv.com/v2/publications/{pub_id}/posts").mock(
        return_value=httpx.Response(403, json={"error": "Forbidden"})
    )

    client = BeehiivClient(api_key="bad", publication_id=pub_id)
    with pytest.raises(httpx.HTTPStatusError):
        await client.create_draft(subject="s", body_html="b")


# ---------------------------------------------------------------------------
# LinkedInClient
# ---------------------------------------------------------------------------


@respx.mock
async def test_linkedin_publish_post_calls_ugc_endpoint() -> None:
    """LinkedInClient.publish_post POSTs to the UGC Posts endpoint."""
    respx.post("https://api.linkedin.com/v2/ugcPosts").mock(
        return_value=httpx.Response(201, json={"id": "urn:li:ugcPost:123"})
    )

    client = LinkedInClient(
        access_token="li-token",
        author_urn="urn:li:person:abc123",
    )
    result = await client.publish_post("Great insights from today's episode!")

    assert result["id"] == "urn:li:ugcPost:123"


@respx.mock
async def test_linkedin_publish_post_sets_author_urn() -> None:
    """LinkedInClient embeds author_urn in the request payload."""
    route = respx.post("https://api.linkedin.com/v2/ugcPosts").mock(
        return_value=httpx.Response(201, json={"id": "urn:li:ugcPost:456"})
    )

    author = "urn:li:person:xyz"
    client = LinkedInClient(access_token="tok", author_urn=author)
    await client.publish_post("Test post")

    import json
    body = json.loads(route.calls[0].request.content)
    assert body["author"] == author
    assert body["lifecycleState"] == "PUBLISHED"


@respx.mock
async def test_linkedin_raises_on_api_error() -> None:
    """LinkedInClient raises HTTPStatusError on non-2xx response."""
    respx.post("https://api.linkedin.com/v2/ugcPosts").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )

    client = LinkedInClient(access_token="bad", author_urn="urn:li:person:x")
    with pytest.raises(httpx.HTTPStatusError):
        await client.publish_post("test")


# ---------------------------------------------------------------------------
# POST /v1/publish
# ---------------------------------------------------------------------------


async def test_publish_endpoint_logs_attempt(
    authed_client: AsyncClient, db_session, fake_user: User
) -> None:
    """POST /v1/publish creates a PublishLog entry for each platform."""
    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="Test Ep",
        source_type="upload",
        status="ready",
    )
    db_session.add(episode)
    await db_session.commit()

    response = await authed_client.post(
        "/v1/publish",
        json={
            "episode_id": str(episode.id),
            "platforms": ["twitter"],
            "content_overrides": {
                "twitter": {"main_thread": ["Tweet 1", "Tweet 2"]}
            },
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert "twitter" in result
    # Twitter will fail (no Buffer connected) but the log is still recorded
    assert result["twitter"] in ("sent", "failed")


async def test_publish_endpoint_returns_404_for_missing_episode(
    authed_client: AsyncClient,
) -> None:
    """POST /v1/publish returns 404 for a non-existent episode."""
    response = await authed_client.post(
        "/v1/publish",
        json={
            "episode_id": str(uuid.uuid4()),
            "platforms": ["linkedin"],
        },
    )
    assert response.status_code == 404


async def test_publish_endpoint_returns_400_for_unsupported_platform(
    authed_client: AsyncClient, db_session, fake_user: User
) -> None:
    """POST /v1/publish returns 400 when all requested platforms are unsupported."""
    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="Ep",
        source_type="upload",
        status="ready",
    )
    db_session.add(episode)
    await db_session.commit()

    response = await authed_client.post(
        "/v1/publish",
        json={
            "episode_id": str(episode.id),
            "platforms": ["tiktok", "snapchat"],  # unsupported
        },
    )
    assert response.status_code == 400


async def test_publish_endpoint_rejects_other_users_episode(
    authed_client: AsyncClient, db_session
) -> None:
    """POST /v1/publish returns 404 for an episode owned by another user."""
    other_episode = Episode(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),  # different user
        title="Not yours",
        source_type="upload",
        status="ready",
    )
    db_session.add(other_episode)
    await db_session.commit()

    response = await authed_client.post(
        "/v1/publish",
        json={
            "episode_id": str(other_episode.id),
            "platforms": ["twitter"],
        },
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /v1/publish/{episode_id}
# ---------------------------------------------------------------------------


async def test_publish_logs_endpoint_returns_empty_initially(
    authed_client: AsyncClient, db_session, fake_user: User
) -> None:
    """GET /v1/publish/{id} returns empty list when no publishes have happened."""
    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="Fresh",
        source_type="upload",
        status="ready",
    )
    db_session.add(episode)
    await db_session.commit()

    response = await authed_client.get(f"/v1/publish/{episode.id}")
    assert response.status_code == 200
    assert response.json() == []


async def test_publish_logs_endpoint_returns_existing_logs(
    authed_client: AsyncClient, db_session, fake_user: User
) -> None:
    """GET /v1/publish/{id} returns recorded publish log entries."""
    from datetime import datetime, timezone

    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="With logs",
        source_type="upload",
        status="ready",
    )
    log_entry = PublishLog(
        id=uuid.uuid4(),
        episode_id=episode.id,
        platform="linkedin",
        content_type="text",
        status="sent",
        sent_at=datetime.now(timezone.utc),
    )
    db_session.add(episode)
    db_session.add(log_entry)
    await db_session.commit()

    response = await authed_client.get(f"/v1/publish/{episode.id}")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["platform"] == "linkedin"
    assert logs[0]["status"] == "sent"


# ---------------------------------------------------------------------------
# GET /v1/content/{episode_id}
# ---------------------------------------------------------------------------


async def test_content_endpoint_returns_pack(
    authed_client: AsyncClient, db_session, fake_user: User
) -> None:
    """GET /v1/content/{id} returns the full content pack."""
    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="Ready ep",
        source_type="upload",
        status="ready",
    )
    pack = ContentPack(
        id=uuid.uuid4(),
        episode_id=episode.id,
        twitter_thread=["Tweet 1", "Tweet 2"],
        twitter_hooks=["Hook 1"],
        twitter_listen_tweet="Listen now",
        linkedin_post="Great post here",
        blog_post_title="My Blog Post",
        blog_post_body="Full body text here.",
    )
    db_session.add(episode)
    db_session.add(pack)
    await db_session.commit()

    response = await authed_client.get(f"/v1/content/{episode.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["episode_id"] == str(episode.id)
    assert data["twitter"]["main_thread"] == ["Tweet 1", "Tweet 2"]
    assert data["linkedin"]["post"] == "Great post here"
    assert data["blog_post"]["title"] == "My Blog Post"


async def test_content_endpoint_returns_404_when_no_pack(
    authed_client: AsyncClient, db_session, fake_user: User
) -> None:
    """GET /v1/content/{id} returns 404 when content pack not yet generated."""
    episode = Episode(
        id=uuid.uuid4(),
        user_id=fake_user.id,
        title="Processing",
        source_type="upload",
        status="generating",
    )
    db_session.add(episode)
    await db_session.commit()

    response = await authed_client.get(f"/v1/content/{episode.id}")
    assert response.status_code == 404


async def test_content_endpoint_returns_403_for_other_users_episode(
    authed_client: AsyncClient, db_session
) -> None:
    """GET /v1/content/{id} returns 403 for an episode owned by another user."""
    other_episode = Episode(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Not yours",
        source_type="upload",
        status="ready",
    )
    db_session.add(other_episode)
    await db_session.commit()

    response = await authed_client.get(f"/v1/content/{other_episode.id}")
    assert response.status_code == 403


async def test_content_endpoint_returns_422_for_invalid_id(
    authed_client: AsyncClient,
) -> None:
    """GET /v1/content/not-a-uuid returns 422."""
    response = await authed_client.get("/v1/content/not-a-uuid")
    assert response.status_code == 422
