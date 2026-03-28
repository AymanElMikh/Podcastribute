"""Tests for the voice fingerprint builder and voice calibration API."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import User
from api.dependencies import get_current_user
from api.main import app
from api.models.voice import VoiceProfile
from api.v1.auth import _hash_password
from api.voice.fingerprint import (
    DEFAULT_VOICE_PROFILE,
    VoiceFingerprintBuilder,
    _parse_profile,
    _strip_code_fences,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_user() -> User:
    """Unauthenticated-but-identified User for dependency overrides."""
    return User(
        id=uuid.uuid4(),
        email="voicetester@example.com",
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


# Gateway response that maps to a fully-populated VoiceProfile
_GOOD_GATEWAY_JSON = json.dumps(
    {
        "vocabulary_level": "casual",
        "sentence_style": "short_punchy",
        "humor_level": "dry",
        "twitter_style": "hot_take",
        "linkedin_style": "contrarian",
        "signature_phrases": ["here's the thing", "look"],
        "topics_they_care_about": ["startups", "AI"],
        "what_they_never_say": ["synergy", "leverage"],
        "tone_adjectives": ["direct", "witty", "bold"],
        "default_cta_style": "direct_ask",
    }
)


# ---------------------------------------------------------------------------
# _strip_code_fences
# ---------------------------------------------------------------------------


def test_strip_code_fences_removes_json_fence() -> None:
    """_strip_code_fences removes ```json ... ``` wrapping."""
    raw = "```json\n{}\n```"
    assert _strip_code_fences(raw) == "{}"


def test_strip_code_fences_removes_plain_fence() -> None:
    """_strip_code_fences removes ``` ... ``` wrapping."""
    raw = "```\n{\"a\": 1}\n```"
    assert _strip_code_fences(raw) == '{"a": 1}'


def test_strip_code_fences_noop_on_plain_json() -> None:
    """_strip_code_fences leaves plain JSON untouched."""
    raw = '{"key": "value"}'
    assert _strip_code_fences(raw) == raw


# ---------------------------------------------------------------------------
# _parse_profile
# ---------------------------------------------------------------------------


def test_parse_profile_maps_gateway_field_names() -> None:
    """_parse_profile translates topics_they_care_about → topics and what_they_never_say → words_to_avoid."""
    profile = _parse_profile(_GOOD_GATEWAY_JSON)
    assert profile.topics == ["startups", "AI"]
    assert profile.words_to_avoid == ["synergy", "leverage"]
    assert profile.vocabulary_level == "casual"
    assert profile.humor_level == "dry"


def test_parse_profile_fallback_for_missing_fields() -> None:
    """_parse_profile uses DEFAULT_VOICE_PROFILE values for missing fields."""
    minimal = json.dumps({"vocabulary_level": "technical"})
    profile = _parse_profile(minimal)
    assert profile.vocabulary_level == "technical"
    assert profile.sentence_style == DEFAULT_VOICE_PROFILE.sentence_style
    assert profile.signature_phrases == []


# ---------------------------------------------------------------------------
# VoiceFingerprintBuilder.build_from_transcripts
# ---------------------------------------------------------------------------


async def test_build_from_transcripts_returns_valid_profile() -> None:
    """build_from_transcripts() returns a VoiceProfile when gateway succeeds."""
    mock_response = AsyncMock(return_value=_GOOD_GATEWAY_JSON)

    with patch("api.voice.fingerprint.call_gateway", mock_response):
        builder = VoiceFingerprintBuilder()
        profile = await builder.build_from_transcripts(
            ["This is a test transcript with some content."]
        )

    assert isinstance(profile, VoiceProfile)
    assert profile.vocabulary_level == "casual"
    assert profile.topics == ["startups", "AI"]
    mock_response.assert_called_once()
    # strategy="quality" is required for voice extraction
    assert mock_response.call_args.kwargs.get("strategy") == "quality"


async def test_build_from_transcripts_empty_list_returns_default() -> None:
    """build_from_transcripts() with empty list returns DEFAULT_VOICE_PROFILE without calling gateway."""
    mock_gateway = AsyncMock()

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        profile = await VoiceFingerprintBuilder().build_from_transcripts([])

    assert profile == DEFAULT_VOICE_PROFILE
    mock_gateway.assert_not_called()


async def test_build_from_transcripts_gateway_failure_returns_default() -> None:
    """build_from_transcripts() falls back to DEFAULT_VOICE_PROFILE on gateway error."""
    mock_gateway = AsyncMock(side_effect=Exception("gateway unreachable"))

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        profile = await VoiceFingerprintBuilder().build_from_transcripts(["some transcript"])

    assert profile == DEFAULT_VOICE_PROFILE


async def test_build_from_transcripts_limits_to_5_samples() -> None:
    """build_from_transcripts() uses at most 5 transcripts regardless of input length."""
    samples = [f"Transcript number {i}." for i in range(10)]
    captured_args: list = []

    async def capture_gateway(system: str, user: str, **kwargs) -> str:
        captured_args.append(user)
        return _GOOD_GATEWAY_JSON

    with patch("api.voice.fingerprint.call_gateway", capture_gateway):
        await VoiceFingerprintBuilder().build_from_transcripts(samples)

    assert len(captured_args) == 1
    # Only the first 5 should appear
    user_prompt = captured_args[0]
    assert "Transcript number 5" not in user_prompt  # 6th+ excluded
    assert "Transcript number 0" in user_prompt


async def test_build_from_transcripts_truncates_to_6000_chars() -> None:
    """build_from_transcripts() truncates combined input to 6000 chars."""
    long_transcript = "word " * 2000  # ~10000 chars
    captured_args: list = []

    async def capture_gateway(system: str, user: str, **kwargs) -> str:
        captured_args.append(user)
        return _GOOD_GATEWAY_JSON

    with patch("api.voice.fingerprint.call_gateway", capture_gateway):
        await VoiceFingerprintBuilder().build_from_transcripts([long_transcript])

    # The user prompt includes a preamble + the truncated content
    # The content portion itself is ≤ 6000 chars
    user_prompt = captured_args[0]
    preamble = "Here are the podcast transcripts to analyze:\n\n"
    content = user_prompt[len(preamble):]
    assert len(content) <= 6000


# ---------------------------------------------------------------------------
# VoiceFingerprintBuilder.build_from_social_posts
# ---------------------------------------------------------------------------


async def test_build_from_social_posts_returns_valid_profile() -> None:
    """build_from_social_posts() returns a VoiceProfile when gateway succeeds."""
    mock_gateway = AsyncMock(return_value=_GOOD_GATEWAY_JSON)

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        profile = await VoiceFingerprintBuilder().build_from_social_posts(
            ["Short punchy tweet here.", "Another hot take."]
        )

    assert isinstance(profile, VoiceProfile)
    assert profile.twitter_style == "hot_take"


async def test_build_from_social_posts_empty_list_returns_default() -> None:
    """build_from_social_posts() with empty list returns DEFAULT_VOICE_PROFILE."""
    profile = await VoiceFingerprintBuilder().build_from_social_posts([])
    assert profile == DEFAULT_VOICE_PROFILE


# ---------------------------------------------------------------------------
# VoiceFingerprintBuilder.refine
# ---------------------------------------------------------------------------


async def test_refine_updates_relevant_fields() -> None:
    """refine() returns an updated VoiceProfile based on feedback."""
    refined_json = json.dumps(
        {
            **json.loads(_GOOD_GATEWAY_JSON),
            # Gateway field name is what_they_never_say, not words_to_avoid
            "what_they_never_say": ["synergy", "leverage", "circle back"],
            "humor_level": "none",
        }
    )
    mock_gateway = AsyncMock(return_value=refined_json)

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        refined = await VoiceFingerprintBuilder().refine(
            DEFAULT_VOICE_PROFILE,
            feedback="I never use corporate buzzwords and I'm not funny at all",
        )

    assert "circle back" in refined.words_to_avoid
    assert refined.humor_level == "none"
    mock_gateway.assert_called_once()


async def test_refine_gateway_failure_returns_existing() -> None:
    """refine() returns the existing profile unchanged on gateway failure."""
    mock_gateway = AsyncMock(side_effect=Exception("timeout"))

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        result = await VoiceFingerprintBuilder().refine(
            DEFAULT_VOICE_PROFILE, feedback="make it more casual"
        )

    assert result == DEFAULT_VOICE_PROFILE


async def test_refine_empty_feedback_returns_existing() -> None:
    """refine() returns the existing profile unchanged when feedback is empty."""
    mock_gateway = AsyncMock()

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        result = await VoiceFingerprintBuilder().refine(DEFAULT_VOICE_PROFILE, feedback="  ")

    assert result == DEFAULT_VOICE_PROFILE
    mock_gateway.assert_not_called()


# ---------------------------------------------------------------------------
# Voice API endpoints
# ---------------------------------------------------------------------------


async def test_get_voice_profile_returns_default_when_uncalibrated(
    authed_client: AsyncClient,
) -> None:
    """GET /v1/voice returns the default profile for a new user."""
    resp = await authed_client.get("/v1/voice")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vocabulary_level"] == DEFAULT_VOICE_PROFILE.vocabulary_level


async def test_calibrate_from_transcripts_saves_profile(
    authed_client: AsyncClient,
) -> None:
    """POST /v1/voice/calibrate/transcripts saves and returns a VoiceProfile."""
    mock_gateway = AsyncMock(return_value=_GOOD_GATEWAY_JSON)

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        resp = await authed_client.post(
            "/v1/voice/calibrate/transcripts",
            json={"transcripts": ["Hello world this is a podcast transcript."]},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["vocabulary_level"] == "casual"
    assert data["twitter_style"] == "hot_take"


async def test_calibrate_from_transcripts_empty_returns_422(
    authed_client: AsyncClient,
) -> None:
    """POST /v1/voice/calibrate/transcripts with empty list returns 422."""
    resp = await authed_client.post(
        "/v1/voice/calibrate/transcripts",
        json={"transcripts": []},
    )
    assert resp.status_code == 422


async def test_calibrate_from_posts_saves_profile(authed_client: AsyncClient) -> None:
    """POST /v1/voice/calibrate/posts saves and returns a VoiceProfile."""
    mock_gateway = AsyncMock(return_value=_GOOD_GATEWAY_JSON)

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        resp = await authed_client.post(
            "/v1/voice/calibrate/posts",
            json={"posts": ["Hot take: most productivity advice is wrong."]},
        )

    assert resp.status_code == 200
    assert resp.json()["humor_level"] == "dry"


async def test_update_voice_profile_partial_update(authed_client: AsyncClient) -> None:
    """PUT /v1/voice updates only the specified fields."""
    resp = await authed_client.put(
        "/v1/voice",
        json={"vocabulary_level": "technical", "humor_level": "none"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["vocabulary_level"] == "technical"
    assert data["humor_level"] == "none"
    # Unspecified fields retain defaults
    assert data["sentence_style"] == DEFAULT_VOICE_PROFILE.sentence_style


async def test_refine_voice_profile_endpoint(authed_client: AsyncClient) -> None:
    """PUT /v1/voice/refine calls the builder and returns the updated profile."""
    mock_gateway = AsyncMock(return_value=_GOOD_GATEWAY_JSON)

    with patch("api.voice.fingerprint.call_gateway", mock_gateway):
        resp = await authed_client.put(
            "/v1/voice/refine",
            json={"feedback": "I never use corporate buzzwords"},
        )

    assert resp.status_code == 200
    mock_gateway.assert_called_once()
