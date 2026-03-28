"""Tests for the moment detector LangGraph node."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from api.agent.nodes.moment_detector import (
    MOMENT_TYPES,
    _TOP_K,
    _chunk_transcript,
    _deduplicate,
    _ensure_diversity,
    _extract_json_array,
    _is_valid_moment,
    _voice_profile_summary,
    moment_detector,
)
from api.agent.state import PodcastState


# ---------------------------------------------------------------------------
# Helpers to build test fixtures
# ---------------------------------------------------------------------------


def _make_moment(
    start: str = "00:10",
    end: str = "00:40",
    text: str = "Great insight here.",
    moment_type: str = "strong_opinion",
    score: float = 0.85,
    hook: str = "Worth sharing",
) -> dict:
    return {
        "start_time": start,
        "end_time": end,
        "text": text,
        "type": moment_type,
        "shareability_score": score,
        "one_line_hook": hook,
    }


def _make_state(transcript: str = "", voice_profile: dict | None = None) -> PodcastState:
    return PodcastState(
        session_id="sess-1",
        user_id="user-1",
        episode_id="ep-1",
        source_type="upload",
        audio_path="/tmp/ep.wav",
        transcript=transcript,
        speaker_segments=[],
        voice_profile=voice_profile or {},
        moments=[],
        content_pack={},
        status="detecting",
        error=None,
    )


# ---------------------------------------------------------------------------
# _chunk_transcript
# ---------------------------------------------------------------------------


def test_chunk_transcript_empty_returns_empty() -> None:
    assert _chunk_transcript("") == []


def test_chunk_transcript_short_transcript_single_chunk() -> None:
    transcript = "word " * 100
    chunks = _chunk_transcript(transcript)
    assert len(chunks) == 1


def test_chunk_transcript_long_transcript_produces_multiple_chunks() -> None:
    # 1200 words → should need 3 chunks (500, 500 with 50-word overlap, remainder)
    transcript = " ".join(f"word{i}" for i in range(1200))
    chunks = _chunk_transcript(transcript)
    assert len(chunks) >= 3


def test_chunk_transcript_overlap_means_boundary_words_appear_twice() -> None:
    """The last 50 words of chunk N should appear at the start of chunk N+1."""
    transcript = " ".join(f"w{i}" for i in range(600))
    chunks = _chunk_transcript(transcript)
    assert len(chunks) >= 2

    last_50_of_first = chunks[0].split()[-50:]
    first_50_of_second = chunks[1].split()[:50]
    assert last_50_of_first == first_50_of_second


def test_chunk_transcript_each_chunk_at_most_500_words() -> None:
    transcript = " ".join(f"w{i}" for i in range(2000))
    for chunk in _chunk_transcript(transcript):
        assert len(chunk.split()) <= 500


# ---------------------------------------------------------------------------
# _extract_json_array
# ---------------------------------------------------------------------------


def test_extract_json_array_plain_json() -> None:
    raw = json.dumps([_make_moment()])
    result = _extract_json_array(raw)
    assert len(result) == 1


def test_extract_json_array_with_code_fence() -> None:
    raw = f"```json\n{json.dumps([_make_moment()])}\n```"
    result = _extract_json_array(raw)
    assert len(result) == 1


def test_extract_json_array_embedded_in_prose() -> None:
    moment = _make_moment()
    raw = f"Here are the moments I found:\n{json.dumps([moment])}\nEnd."
    result = _extract_json_array(raw)
    assert len(result) == 1


def test_extract_json_array_returns_empty_on_garbage() -> None:
    assert _extract_json_array("no json here at all") == []


def test_extract_json_array_returns_empty_on_empty_array() -> None:
    assert _extract_json_array("[]") == []


# ---------------------------------------------------------------------------
# _is_valid_moment
# ---------------------------------------------------------------------------


def test_is_valid_moment_accepts_good_moment() -> None:
    assert _is_valid_moment(_make_moment()) is True


def test_is_valid_moment_rejects_low_score() -> None:
    assert _is_valid_moment(_make_moment(score=0.3)) is False


def test_is_valid_moment_rejects_unknown_type() -> None:
    m = _make_moment()
    m["type"] = "fake_type_that_does_not_exist"
    assert _is_valid_moment(m) is False


def test_is_valid_moment_rejects_missing_fields() -> None:
    assert _is_valid_moment({"start_time": "00:10", "text": "hi"}) is False


# ---------------------------------------------------------------------------
# _deduplicate
# ---------------------------------------------------------------------------


def test_deduplicate_keeps_highest_score_for_same_start_time() -> None:
    low = _make_moment(start="00:10", score=0.7)
    high = _make_moment(start="00:10", score=0.92)
    result = _deduplicate([low, high])
    assert len(result) == 1
    assert result[0]["shareability_score"] == 0.92


def test_deduplicate_keeps_different_start_times() -> None:
    a = _make_moment(start="00:10", score=0.8)
    b = _make_moment(start="01:30", score=0.75)
    result = _deduplicate([a, b])
    assert len(result) == 2


# ---------------------------------------------------------------------------
# _ensure_diversity
# ---------------------------------------------------------------------------


def test_ensure_diversity_reorders_for_min_types() -> None:
    # All strong_opinion — diversity not possible
    moments = [_make_moment(moment_type="strong_opinion", score=0.9 - i * 0.05) for i in range(5)]
    result = _ensure_diversity(moments, min_types=3)
    # Can only get 1 type, but list should still be returned intact
    assert len(result) == 5


def test_ensure_diversity_promotes_varied_types_to_front() -> None:
    m1 = _make_moment(moment_type="strong_opinion", score=0.9, start="00:10")
    m2 = _make_moment(moment_type="strong_opinion", score=0.85, start="01:00")
    m3 = _make_moment(moment_type="personal_story", score=0.7, start="02:00")
    m4 = _make_moment(moment_type="prediction", score=0.65, start="03:00")

    # Input is score-sorted
    result = _ensure_diversity([m1, m2, m3, m4], min_types=3)
    types_in_first_three = {r["type"] for r in result[:3]}
    assert len(types_in_first_three) == 3


# ---------------------------------------------------------------------------
# _voice_profile_summary
# ---------------------------------------------------------------------------


def test_voice_profile_summary_with_full_profile() -> None:
    profile = {
        "tone_adjectives": ["direct", "bold"],
        "sentence_style": "short_punchy",
        "humor_level": "dry",
    }
    summary = _voice_profile_summary(profile)
    assert "direct" in summary
    assert "short_punchy" in summary
    assert "dry" in summary


def test_voice_profile_summary_with_empty_profile() -> None:
    summary = _voice_profile_summary({})
    assert len(summary) > 0  # fallback string, not empty


# ---------------------------------------------------------------------------
# moment_detector (full node)
# ---------------------------------------------------------------------------


async def test_moment_detector_returns_moments_from_transcript() -> None:
    """moment_detector() returns detected moments from a real transcript."""
    moments = [
        _make_moment(start=f"0{i}:00", moment_type=MOMENT_TYPES[i % len(MOMENT_TYPES)], score=0.9 - i * 0.02)
        for i in range(5)
    ]
    mock_gateway = AsyncMock(return_value=json.dumps(moments))

    transcript = " ".join(["word"] * 600)  # > 500 words → 2 chunks
    state = _make_state(transcript=transcript, voice_profile={"tone_adjectives": ["bold"]})

    with patch("api.agent.nodes.moment_detector.call_gateway", mock_gateway):
        result = await moment_detector(state)

    assert "moments" in result
    assert len(result["moments"]) > 0


async def test_moment_detector_returns_max_10_moments() -> None:
    """moment_detector() never returns more than 10 moments."""
    # Gateway returns 15 valid moments per chunk
    many_moments = [
        _make_moment(
            start=f"{i:02d}:00",
            moment_type=MOMENT_TYPES[i % len(MOMENT_TYPES)],
            score=0.95,
        )
        for i in range(15)
    ]
    mock_gateway = AsyncMock(return_value=json.dumps(many_moments))

    # Short transcript → 1 chunk
    state = _make_state(transcript=" ".join(["word"] * 100))

    with patch("api.agent.nodes.moment_detector.call_gateway", mock_gateway):
        result = await moment_detector(state)

    assert len(result["moments"]) <= _TOP_K


async def test_moment_detector_ensures_type_diversity() -> None:
    """moment_detector() includes at least 3 different moment types."""
    # Build 12 moments with varied types
    moments = [
        _make_moment(
            start=f"{i:02d}:00",
            moment_type=MOMENT_TYPES[i % len(MOMENT_TYPES)],
            score=0.9,
        )
        for i in range(12)
    ]
    mock_gateway = AsyncMock(return_value=json.dumps(moments))

    state = _make_state(transcript=" ".join(["word"] * 100))

    with patch("api.agent.nodes.moment_detector.call_gateway", mock_gateway):
        result = await moment_detector(state)

    types = {m["type"] for m in result["moments"]}
    assert len(types) >= 3


async def test_moment_detector_empty_transcript_returns_empty() -> None:
    """moment_detector() returns [] for an empty transcript without calling gateway."""
    mock_gateway = AsyncMock()
    state = _make_state(transcript="")

    with patch("api.agent.nodes.moment_detector.call_gateway", mock_gateway):
        result = await moment_detector(state)

    assert result == {"moments": []}
    mock_gateway.assert_not_called()


async def test_moment_detector_no_strong_moments_returns_empty() -> None:
    """moment_detector() returns [] when gateway finds no moments above threshold."""
    mock_gateway = AsyncMock(return_value="[]")
    state = _make_state(transcript=" ".join(["word"] * 100))

    with patch("api.agent.nodes.moment_detector.call_gateway", mock_gateway):
        result = await moment_detector(state)

    assert result == {"moments": []}


async def test_moment_detector_chunk_failure_does_not_crash() -> None:
    """moment_detector() handles a gateway error on one chunk without crashing."""
    call_count = 0

    async def flaky_gateway(system: str, user: str, **kwargs) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("gateway timeout")
        return json.dumps([_make_moment(start=f"{call_count:02d}:00")])

    # 600 words → 2 chunks; first fails, second succeeds
    state = _make_state(transcript=" ".join(["word"] * 600))

    with patch("api.agent.nodes.moment_detector.call_gateway", flaky_gateway):
        result = await moment_detector(state)

    # Should still return moments from the successful chunk
    assert "moments" in result


async def test_moment_detector_deduplicates_across_chunks() -> None:
    """moment_detector() deduplicates moments with the same start_time across chunks."""
    # Both chunks return a moment at the same timestamp
    duplicate_moment = _make_moment(start="05:00", score=0.8)
    better_duplicate = _make_moment(start="05:00", score=0.95)

    call_count = 0

    async def gateway_with_duplicates(system: str, user: str, **kwargs) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return json.dumps([duplicate_moment])
        return json.dumps([better_duplicate])

    state = _make_state(transcript=" ".join(["word"] * 600))

    with patch("api.agent.nodes.moment_detector.call_gateway", gateway_with_duplicates):
        result = await moment_detector(state)

    starts = [m["start_time"] for m in result["moments"]]
    # No duplicate start times
    assert len(starts) == len(set(starts))
    # The higher-scored one is kept
    assert result["moments"][0]["shareability_score"] == 0.95
