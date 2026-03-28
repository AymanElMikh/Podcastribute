"""Tests for the LangGraph podcast processing pipeline."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.agent.graph import build_podcast_graph
from api.agent.nodes.content_factory import content_factory
from api.agent.nodes.quality_checker import quality_checker
from api.agent.state import PodcastState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_state(
    transcript: str = "word " * 200,
    moments: list[dict] | None = None,
    content_pack: dict | None = None,
    voice_profile: dict | None = None,
) -> PodcastState:
    return PodcastState(
        session_id="sess-test",
        user_id="user-1",
        episode_id="ep-1",
        source_type="upload",
        audio_path="/tmp/ep.wav",
        transcript=transcript,
        speaker_segments=[],
        voice_profile=voice_profile or {"tone_adjectives": ["direct"]},
        moments=moments or [],
        content_pack=content_pack or {},
        status="generating",
        error=None,
    )


def _make_moment(i: int = 0) -> dict:
    return {
        "start_time": f"{i:02d}:00",
        "end_time": f"{i:02d}:30",
        "text": f"Insight number {i}",
        "type": "strong_opinion",
        "shareability_score": 0.9,
        "one_line_hook": f"Hook {i}",
    }


def _mock_generator_output(format_name: str) -> MagicMock:
    """Return a MagicMock whose model_dump() returns a minimal valid dict."""
    out = MagicMock()
    out.model_dump.return_value = {"format": format_name, "content": "generated"}
    return out


# ---------------------------------------------------------------------------
# content_factory node
# ---------------------------------------------------------------------------


async def test_content_factory_returns_all_8_format_keys() -> None:
    """content_factory populates content_pack with all 8 format keys."""
    mock_output = _mock_generator_output("any")

    with patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate",
        new=AsyncMock(return_value=mock_output),
    ):
        result = await content_factory(_make_state(moments=[_make_moment()]))

    assert "content_pack" in result
    pack = result["content_pack"]
    expected_keys = {
        "twitter", "linkedin", "newsletter", "short_video",
        "blog_post", "youtube", "quote_cards", "email_sequence",
    }
    assert set(pack.keys()) == expected_keys


async def test_content_factory_failed_generator_does_not_crash() -> None:
    """A generator that raises does not stop other generators from completing."""
    good_output = _mock_generator_output("good")

    with patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate",
        new=AsyncMock(side_effect=Exception("twitter gateway timeout")),
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate",
        new=AsyncMock(return_value=good_output),
    ):
        result = await content_factory(_make_state(moments=[_make_moment()]))

    pack = result["content_pack"]
    # Twitter should have an error entry
    assert pack["twitter"]["error"] == "twitter gateway timeout"
    assert pack["twitter"]["content"] is None
    # All other formats should have succeeded
    for key in ("linkedin", "newsletter", "short_video", "blog_post", "youtube", "quote_cards", "email_sequence"):
        assert "error" not in pack[key]


async def test_content_factory_status_is_ready() -> None:
    """content_factory sets status to 'ready'."""
    good_output = _mock_generator_output("any")

    with patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate", new=AsyncMock(return_value=good_output)
    ):
        result = await content_factory(_make_state(moments=[_make_moment()]))

    assert result["status"] == "ready"


async def test_content_factory_emits_content_ready_event() -> None:
    """content_factory calls _emit with 'content_ready' on success."""
    good_output = _mock_generator_output("any")

    with patch(
        "api.agent.nodes.content_factory._emit", new=AsyncMock()
    ) as mock_emit, patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate", new=AsyncMock(return_value=good_output)
    ):
        await content_factory(_make_state(moments=[_make_moment()]))

    emitted_types = [call.args[1] for call in mock_emit.call_args_list]
    assert "content_ready" in emitted_types


# ---------------------------------------------------------------------------
# quality_checker node
# ---------------------------------------------------------------------------


async def test_quality_checker_passes_good_content() -> None:
    """quality_checker returns status 'ready' when all checks pass."""
    pack = {
        "twitter": {"main_thread": [f"tweet {i}" for i in range(8)]},
        "blog_post": {"body": "word " * 500},
        "linkedin": {"post": "great post"},
        "newsletter": {},
        "short_video": {},
        "youtube": {},
        "quote_cards": {},
        "email_sequence": {},
    }
    result = await quality_checker(_make_state(content_pack=pack))
    assert result["status"] == "ready"


async def test_quality_checker_still_ready_on_low_quality() -> None:
    """quality_checker returns 'ready' even when quality checks fail (non-blocking)."""
    pack = {
        "twitter": {"main_thread": ["only one tweet"]},  # below min
        "blog_post": {"body": "too short"},  # below min words
        "linkedin": {},
        "newsletter": {"error": "failed", "content": None},
        "short_video": {"error": "failed", "content": None},
        "youtube": {"error": "failed", "content": None},
        "quote_cards": {},
        "email_sequence": {},
    }
    result = await quality_checker(_make_state(content_pack=pack))
    assert result["status"] == "ready"


async def test_quality_checker_empty_pack_still_returns_ready() -> None:
    """quality_checker handles an empty content_pack without crashing."""
    result = await quality_checker(_make_state(content_pack={}))
    assert result["status"] == "ready"


# ---------------------------------------------------------------------------
# Full graph integration
# ---------------------------------------------------------------------------


async def test_full_graph_runs_end_to_end() -> None:
    """Full graph: START → moment_detector → content_factory → quality_checker → END."""
    moment = _make_moment()
    good_output = _mock_generator_output("any")

    mock_gateway = AsyncMock(return_value=json.dumps([moment]))

    with patch(
        "api.agent.nodes.moment_detector.call_gateway", mock_gateway
    ), patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate", new=AsyncMock(return_value=good_output)
    ):
        graph = build_podcast_graph()
        final_state = await graph.ainvoke(_make_state())

    assert final_state["status"] == "ready"
    assert "content_pack" in final_state
    assert set(final_state["content_pack"].keys()) == {
        "twitter", "linkedin", "newsletter", "short_video",
        "blog_post", "youtube", "quote_cards", "email_sequence",
    }


async def test_full_graph_failed_generator_does_not_stop_pipeline() -> None:
    """Graph completes even when one generator raises an exception."""
    moment = _make_moment()
    good_output = _mock_generator_output("any")

    mock_gateway = AsyncMock(return_value=json.dumps([moment]))

    with patch(
        "api.agent.nodes.moment_detector.call_gateway", mock_gateway
    ), patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate",
        new=AsyncMock(side_effect=Exception("boom")),
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate", new=AsyncMock(return_value=good_output)
    ):
        graph = build_podcast_graph()
        final_state = await graph.ainvoke(_make_state())

    assert final_state["status"] == "ready"
    assert final_state["content_pack"]["twitter"]["error"] == "boom"
    # All other formats succeeded
    for key in ("linkedin", "newsletter", "short_video", "blog_post", "youtube", "quote_cards", "email_sequence"):
        assert "error" not in final_state["content_pack"][key]


async def test_full_graph_content_ready_event_emitted() -> None:
    """Graph emits content_ready event via _emit on successful completion."""
    moment = _make_moment()
    good_output = _mock_generator_output("any")

    mock_gateway = AsyncMock(return_value=json.dumps([moment]))

    with patch(
        "api.agent.nodes.content_factory._emit", new=AsyncMock()
    ) as mock_emit, patch(
        "api.agent.nodes.moment_detector.call_gateway", mock_gateway
    ), patch(
        "api.agent.nodes.content_factory.TwitterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.LinkedInGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.NewsletterGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.ShortVideoGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.BlogPostGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.YouTubeDescriptionGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.QuoteCardGenerator.generate", new=AsyncMock(return_value=good_output)
    ), patch(
        "api.agent.nodes.content_factory.EmailSequenceGenerator.generate", new=AsyncMock(return_value=good_output)
    ):
        graph = build_podcast_graph()
        await graph.ainvoke(_make_state())

    emitted_types = [call.args[1] for call in mock_emit.call_args_list]
    assert "content_ready" in emitted_types
