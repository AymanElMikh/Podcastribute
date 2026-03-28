"""Tests for all 8 content generators."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from api.generators.blog_post import BlogPostGenerator, BlogPostOutput
from api.generators.email_sequence import EmailSequenceGenerator, EmailSequenceOutput
from api.generators.linkedin import LinkedInGenerator, LinkedInOutput
from api.generators.newsletter import NewsletterGenerator, NewsletterOutput
from api.generators.quote_cards import QuoteCardGenerator, QuoteCardOutput
from api.generators.short_video import ShortVideoGenerator, ShortVideoOutput
from api.generators.twitter import TwitterGenerator, TwitterOutput
from api.generators.youtube_description import YouTubeDescriptionGenerator, YouTubeDescriptionOutput

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_VOICE = {
    "tone_adjectives": ["direct", "bold", "curious"],
    "vocabulary_level": "conversational",
    "sentence_style": "short_punchy",
    "humor_level": "dry",
    "twitter_style": "educator",
    "linkedin_style": "personal_story",
    "words_to_avoid": ["synergy", "leverage"],
    "signature_phrases": ["here's the thing", "real talk"],
}

_MOMENTS = [
    {
        "start_time": "05:10",
        "end_time": "05:45",
        "text": "The biggest mistake founders make is hiring too fast.",
        "type": "strong_opinion",
        "shareability_score": 0.92,
        "one_line_hook": "This changes how you think about hiring",
    },
    {
        "start_time": "12:30",
        "end_time": "13:00",
        "text": "We went from 0 to $1M ARR in 11 months without any paid ads.",
        "type": "surprising_statistic",
        "shareability_score": 0.88,
        "one_line_hook": "No paid ads, just this strategy",
    },
]

_TRANSCRIPT = (
    "Today we're talking about startup growth. "
    "The biggest mistake founders make is hiring too fast. "
    "You should only hire when the pain of not hiring outweighs the cost. "
    "We went from 0 to $1M ARR in 11 months without any paid ads. "
    "It was all about content and community. "
) * 10


# ---------------------------------------------------------------------------
# Twitter generator
# ---------------------------------------------------------------------------


_TWITTER_RESPONSE = json.dumps(
    {
        "main_thread": [
            "1/ The biggest mistake founders make is hiring too fast.",
            "2/ You should only hire when the pain outweighs the cost.",
            "3/ We went from $0 to $1M ARR in 11 months with no paid ads.",
            "4/ Here's how we did it.",
            "5/ Content was our #1 channel.",
            "6/ Community came second.",
            "7/ The key insight: distribution before product.",
            "8/ What's your #1 growth channel right now?",
        ],
        "standalone_hooks": [
            "Hiring too fast killed more startups than bad products.",
            "$1M ARR, 11 months, zero paid ads. Here's the breakdown.",
            "The best founders hire slow and fire fast. Here's why.",
        ],
        "listen_tweet": "Just dropped a new episode on startup growth without paid ads. If you're building something, this one's for you.",
    }
)


async def test_twitter_returns_correct_structure() -> None:
    """TwitterGenerator returns a TwitterOutput with all fields."""
    mock_gateway = AsyncMock(return_value=_TWITTER_RESPONSE)
    with patch("api.generators.twitter.call_gateway", mock_gateway):
        result = await TwitterGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, TwitterOutput)
    assert len(result.main_thread) >= 5
    assert len(result.standalone_hooks) == 3
    assert len(result.listen_tweet) > 0


async def test_twitter_voice_in_prompt() -> None:
    """TwitterGenerator includes voice tone and twitter_style in the system prompt."""
    mock_gateway = AsyncMock(return_value=_TWITTER_RESPONSE)
    with patch("api.generators.twitter.call_gateway", mock_gateway) as mock:
        await TwitterGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt
    assert "educator" in system_prompt


async def test_twitter_gateway_failure_returns_empty() -> None:
    """TwitterGenerator returns empty TwitterOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("timeout"))
    with patch("api.generators.twitter.call_gateway", mock_gateway):
        result = await TwitterGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, TwitterOutput)
    assert result.main_thread == []
    assert result.listen_tweet == ""


# ---------------------------------------------------------------------------
# LinkedIn generator
# ---------------------------------------------------------------------------


_LINKEDIN_RESPONSE = json.dumps(
    {
        "post": (
            "I almost destroyed my company by hiring too fast.\n\n"
            "In year one, I thought growth meant headcount. I was wrong.\n\n"
            "We went from $0 to $1M ARR in 11 months with zero paid ads.\n\n"
            "The secret? We hired slow and let content do the heavy lifting.\n\n"
            "What's your take — hire fast or hire slow?"
        ),
        "carousel_outline": [
            "The hiring mistake that almost killed us",
            "What $1M ARR really looks like",
            "The no-ads growth strategy",
            "Content > Paid for early-stage",
            "When to hire your first salesperson",
            "The rule we use for every hire",
            "One question to ask before any hire",
        ],
        "post_hooks": [
            "I almost destroyed my company by hiring too fast.",
            "Zero paid ads. $1M ARR. 11 months. Here's what actually worked.",
            "Most founders hire their way into bankruptcy. Here's how to avoid it.",
        ],
    }
)


async def test_linkedin_returns_correct_structure() -> None:
    """LinkedInGenerator returns a LinkedInOutput with all fields."""
    mock_gateway = AsyncMock(return_value=_LINKEDIN_RESPONSE)
    with patch("api.generators.linkedin.call_gateway", mock_gateway):
        result = await LinkedInGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, LinkedInOutput)
    assert len(result.post) > 100
    assert len(result.carousel_outline) == 7
    assert len(result.post_hooks) == 3


async def test_linkedin_voice_in_prompt() -> None:
    """LinkedInGenerator includes voice context and linkedin_style in system prompt."""
    mock_gateway = AsyncMock(return_value=_LINKEDIN_RESPONSE)
    with patch("api.generators.linkedin.call_gateway", mock_gateway) as mock:
        await LinkedInGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt
    assert "personal_story" in system_prompt


async def test_linkedin_gateway_failure_returns_empty() -> None:
    """LinkedInGenerator returns empty LinkedInOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("network error"))
    with patch("api.generators.linkedin.call_gateway", mock_gateway):
        result = await LinkedInGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, LinkedInOutput)
    assert result.post == ""
    assert result.carousel_outline == []


# ---------------------------------------------------------------------------
# Newsletter generator
# ---------------------------------------------------------------------------


_NEWSLETTER_RESPONSE = json.dumps(
    {
        "section_title": "The Hiring Trap (And How to Avoid It)",
        "section_body": (
            "Here's the thing — every founder I know has made the same mistake.\n\n"
            "They hire too fast, burn runway, and then wonder why growth stalled.\n\n"
            "This week's episode digs into why slow hiring is actually a growth strategy. "
            "My guest went from $0 to $1M ARR in 11 months without a single paid ad. "
            "Their secret was brutal prioritization on who gets a seat at the table.\n\n"
            "The rule they use: only hire when the pain of NOT hiring is greater than the cost of hiring."
        ),
        "subject_lines": [
            "A: The hiring mistake that cost founders millions",
            "B: $1M ARR, zero paid ads — the full breakdown",
            "C: Why slow hiring is a growth strategy",
            "D: The rule every founder needs before their next hire",
            "E: Stop hiring your way into bankruptcy",
        ],
        "preview_text": "The counterintuitive growth playbook that actually works.",
    }
)


async def test_newsletter_returns_correct_structure() -> None:
    """NewsletterGenerator returns a NewsletterOutput with all fields."""
    mock_gateway = AsyncMock(return_value=_NEWSLETTER_RESPONSE)
    with patch("api.generators.newsletter.call_gateway", mock_gateway):
        result = await NewsletterGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, NewsletterOutput)
    assert len(result.section_title) > 0
    assert len(result.section_body) > 100
    assert len(result.subject_lines) == 5
    assert len(result.preview_text) > 0


async def test_newsletter_voice_in_prompt() -> None:
    """NewsletterGenerator includes voice context in the system prompt."""
    mock_gateway = AsyncMock(return_value=_NEWSLETTER_RESPONSE)
    with patch("api.generators.newsletter.call_gateway", mock_gateway) as mock:
        await NewsletterGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt


async def test_newsletter_gateway_failure_returns_empty() -> None:
    """NewsletterGenerator returns empty NewsletterOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("timeout"))
    with patch("api.generators.newsletter.call_gateway", mock_gateway):
        result = await NewsletterGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, NewsletterOutput)
    assert result.section_title == ""
    assert result.subject_lines == []


# ---------------------------------------------------------------------------
# Short video generator
# ---------------------------------------------------------------------------


_SHORT_VIDEO_RESPONSE = json.dumps(
    {
        "clips": [
            {
                "start_time": "05:10",
                "end_time": "05:55",
                "hook": "The biggest mistake founders make is hiring too fast.",
                "script_note": "Show text overlay: 'Hiring mistake #1' with red background",
                "platform": "reels",
            },
            {
                "start_time": "12:30",
                "end_time": "13:15",
                "hook": "We went from 0 to $1M ARR in 11 months without any paid ads.",
                "script_note": "Show '$1M ARR' counter graphic, then revenue chart",
                "platform": "tiktok",
            },
        ]
    }
)


async def test_short_video_returns_correct_structure() -> None:
    """ShortVideoGenerator returns a ShortVideoOutput with clips."""
    mock_gateway = AsyncMock(return_value=_SHORT_VIDEO_RESPONSE)
    with patch("api.generators.short_video.call_gateway", mock_gateway):
        result = await ShortVideoGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, ShortVideoOutput)
    assert len(result.clips) == 2
    assert "hook" in result.clips[0]
    assert "platform" in result.clips[0]
    assert result.clips[0]["platform"] in ("tiktok", "reels", "shorts")


async def test_short_video_voice_in_prompt() -> None:
    """ShortVideoGenerator includes voice context in the system prompt."""
    mock_gateway = AsyncMock(return_value=_SHORT_VIDEO_RESPONSE)
    with patch("api.generators.short_video.call_gateway", mock_gateway) as mock:
        await ShortVideoGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt


async def test_short_video_gateway_failure_returns_empty() -> None:
    """ShortVideoGenerator returns empty ShortVideoOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("gateway down"))
    with patch("api.generators.short_video.call_gateway", mock_gateway):
        result = await ShortVideoGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, ShortVideoOutput)
    assert result.clips == []


# ---------------------------------------------------------------------------
# Blog post generator
# ---------------------------------------------------------------------------


_BLOG_POST_RESPONSE = json.dumps(
    {
        "title": "How to Grow from $0 to $1M ARR Without Paid Ads",
        "meta_description": "One founder's playbook for reaching $1M ARR in 11 months using content and community — no paid ads required.",
        "outline": [
            "Why Most Founders Hire Too Fast",
            "The No-Ads Growth Strategy That Works",
            "Content as Your Primary Distribution Channel",
            "Building Community Before Product",
            "The Hiring Rule That Changes Everything",
        ],
        "body": "# How to Grow from $0 to $1M ARR Without Paid Ads\n\nMost founders believe growth requires budget. But the best founders know that distribution is the real moat. In this post we break down the exact playbook that took one founder from zero to a million in ARR without spending a dollar on ads.",
        "internal_link_suggestions": [
            "founder hiring mistakes",
            "content-led growth strategies",
            "early-stage startup metrics",
        ],
        "target_keywords": [
            "startup growth without paid ads",
            "founder hiring mistakes",
            "$1M ARR",
            "content-led growth",
            "early stage startup",
        ],
    }
)


async def test_blog_post_returns_correct_structure() -> None:
    """BlogPostGenerator returns a BlogPostOutput with all fields."""
    mock_gateway = AsyncMock(return_value=_BLOG_POST_RESPONSE)
    with patch("api.generators.blog_post.call_gateway", mock_gateway):
        result = await BlogPostGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, BlogPostOutput)
    assert len(result.title) > 0
    assert len(result.meta_description) <= 155
    assert len(result.outline) >= 4
    assert len(result.body) > 200
    assert len(result.target_keywords) >= 3


async def test_blog_post_voice_in_prompt() -> None:
    """BlogPostGenerator includes voice context in the system prompt."""
    mock_gateway = AsyncMock(return_value=_BLOG_POST_RESPONSE)
    with patch("api.generators.blog_post.call_gateway", mock_gateway) as mock:
        await BlogPostGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt


async def test_blog_post_uses_quality_strategy() -> None:
    """BlogPostGenerator uses the 'quality' gateway strategy."""
    mock_gateway = AsyncMock(return_value=_BLOG_POST_RESPONSE)
    with patch("api.generators.blog_post.call_gateway", mock_gateway) as mock:
        await BlogPostGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert mock.call_args[1]["strategy"] == "quality"


async def test_blog_post_gateway_failure_returns_empty() -> None:
    """BlogPostGenerator returns empty BlogPostOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("timeout"))
    with patch("api.generators.blog_post.call_gateway", mock_gateway):
        result = await BlogPostGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, BlogPostOutput)
    assert result.title == ""
    assert result.body == ""


# ---------------------------------------------------------------------------
# YouTube description generator
# ---------------------------------------------------------------------------


_YOUTUBE_RESPONSE = json.dumps(
    {
        "description": (
            "$1M ARR in 11 months with zero paid ads — here's exactly how they did it.\n\n"
            "In this episode we break down the hiring mistakes killing startups and the "
            "content-led growth strategy that actually works.\n\n"
            "📌 Chapters below\n🔔 Subscribe for weekly founder interviews"
        ),
        "chapters": [
            {"time": "0:00", "title": "Introduction"},
            {"time": "5:10", "title": "The hiring mistake founders make"},
            {"time": "12:30", "title": "$1M ARR with zero paid ads"},
            {"time": "20:00", "title": "Content as a growth channel"},
        ],
        "tags": [
            "startup growth",
            "founder interview",
            "startup podcast",
            "$1M ARR",
            "content led growth",
            "hiring mistakes",
            "entrepreneurship",
            "business podcast",
            "saas growth",
            "startup advice",
            "no paid ads",
            "content marketing",
            "founder tips",
            "scaling startup",
            "bootstrapped startup",
        ],
        "end_screen_script": (
            "If this episode gave you something to think about, hit subscribe — "
            "we drop new founder interviews every week. And check out last week's episode "
            "on product-market fit, link's right there."
        ),
    }
)


async def test_youtube_returns_correct_structure() -> None:
    """YouTubeDescriptionGenerator returns a YouTubeDescriptionOutput with all fields."""
    mock_gateway = AsyncMock(return_value=_YOUTUBE_RESPONSE)
    with patch("api.generators.youtube_description.call_gateway", mock_gateway):
        result = await YouTubeDescriptionGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, YouTubeDescriptionOutput)
    assert len(result.description) > 0
    assert len(result.chapters) >= 3
    assert len(result.tags) == 15
    assert len(result.end_screen_script) > 0


async def test_youtube_voice_in_prompt() -> None:
    """YouTubeDescriptionGenerator includes voice context in the system prompt."""
    mock_gateway = AsyncMock(return_value=_YOUTUBE_RESPONSE)
    with patch("api.generators.youtube_description.call_gateway", mock_gateway) as mock:
        await YouTubeDescriptionGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt


async def test_youtube_gateway_failure_returns_empty() -> None:
    """YouTubeDescriptionGenerator returns empty output when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("gateway error"))
    with patch("api.generators.youtube_description.call_gateway", mock_gateway):
        result = await YouTubeDescriptionGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, YouTubeDescriptionOutput)
    assert result.description == ""
    assert result.chapters == []


# ---------------------------------------------------------------------------
# Quote card generator
# ---------------------------------------------------------------------------


_QUOTE_CARDS_RESPONSE = json.dumps(
    {
        "quotes": [
            {
                "text": "Only hire when the pain of not hiring outweighs the cost.",
                "attribution": "— Episode Guest, Startup Growth Podcast",
                "background_suggestion": "dark navy with white text, minimal design",
                "caption": "This one rule changed how we build teams. Save this.",
            },
            {
                "text": "$1M ARR in 11 months. Zero paid ads. Just content and community.",
                "attribution": "— Episode Guest, Startup Growth Podcast",
                "background_suggestion": "bold green gradient with dark text",
                "caption": "Proof that distribution > budget at early stage.",
            },
        ]
    }
)


async def test_quote_cards_returns_correct_structure() -> None:
    """QuoteCardGenerator returns a QuoteCardOutput with quotes."""
    mock_gateway = AsyncMock(return_value=_QUOTE_CARDS_RESPONSE)
    with patch("api.generators.quote_cards.call_gateway", mock_gateway):
        result = await QuoteCardGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, QuoteCardOutput)
    assert len(result.quotes) == 2
    assert "text" in result.quotes[0]
    assert "attribution" in result.quotes[0]
    assert "caption" in result.quotes[0]
    assert len(result.quotes[0]["text"]) <= 140


async def test_quote_cards_voice_in_prompt() -> None:
    """QuoteCardGenerator includes voice context in the system prompt."""
    mock_gateway = AsyncMock(return_value=_QUOTE_CARDS_RESPONSE)
    with patch("api.generators.quote_cards.call_gateway", mock_gateway) as mock:
        await QuoteCardGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt


async def test_quote_cards_gateway_failure_returns_empty() -> None:
    """QuoteCardGenerator returns empty QuoteCardOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("timeout"))
    with patch("api.generators.quote_cards.call_gateway", mock_gateway):
        result = await QuoteCardGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, QuoteCardOutput)
    assert result.quotes == []


# ---------------------------------------------------------------------------
# Email sequence generator
# ---------------------------------------------------------------------------


_EMAIL_SEQUENCE_RESPONSE = json.dumps(
    {
        "emails": [
            {
                "subject": "New episode: $1M with no paid ads",
                "preview_text": "The hiring rule that changed everything.",
                "body": (
                    "Hey,\n\nJust dropped a new episode and this one's worth your time.\n\n"
                    "My guest went from $0 to $1M ARR in 11 months — no paid ads, no VC money. "
                    "Just content, community, and one counterintuitive rule about hiring.\n\n"
                    "Worth 45 minutes of your time. Link below.\n\n— Host"
                ),
                "send_day": 0,
                "purpose": "announce",
            },
            {
                "subject": "The hiring rule I wish I'd known earlier",
                "preview_text": "Only hire when the pain outweighs the cost.",
                "body": (
                    "Hey,\n\nOne thing from this week's episode stuck with me.\n\n"
                    "The rule: only hire when the pain of not hiring outweighs the cost of hiring.\n\n"
                    "Simple. But most founders ignore it. They hire for growth they haven't earned yet.\n\n"
                    "What's your current hiring rule?\n\n— Host"
                ),
                "send_day": 2,
                "purpose": "insight",
            },
            {
                "subject": "One action to take this week",
                "preview_text": "Based on what we covered in this episode.",
                "body": (
                    "Hey,\n\nIf you listened to this week's episode, here's your one action:\n\n"
                    "Audit your last 3 hires. Were they hired because the pain was real, or because growth felt exciting?\n\n"
                    "Reply and tell me what you find.\n\n— Host"
                ),
                "send_day": 5,
                "purpose": "cta",
            },
        ]
    }
)


async def test_email_sequence_returns_correct_structure() -> None:
    """EmailSequenceGenerator returns an EmailSequenceOutput with 3 emails."""
    mock_gateway = AsyncMock(return_value=_EMAIL_SEQUENCE_RESPONSE)
    with patch("api.generators.email_sequence.call_gateway", mock_gateway):
        result = await EmailSequenceGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, EmailSequenceOutput)
    assert len(result.emails) == 3
    send_days = [e["send_day"] for e in result.emails]
    assert 0 in send_days
    assert 2 in send_days
    assert 5 in send_days
    purposes = {e["purpose"] for e in result.emails}
    assert purposes == {"announce", "insight", "cta"}


async def test_email_sequence_voice_in_prompt() -> None:
    """EmailSequenceGenerator includes voice context in the system prompt."""
    mock_gateway = AsyncMock(return_value=_EMAIL_SEQUENCE_RESPONSE)
    with patch("api.generators.email_sequence.call_gateway", mock_gateway) as mock:
        await EmailSequenceGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    system_prompt = mock.call_args[0][0]
    assert "direct" in system_prompt


async def test_email_sequence_gateway_failure_returns_empty() -> None:
    """EmailSequenceGenerator returns empty EmailSequenceOutput when gateway fails."""
    mock_gateway = AsyncMock(side_effect=Exception("timeout"))
    with patch("api.generators.email_sequence.call_gateway", mock_gateway):
        result = await EmailSequenceGenerator(_VOICE).generate(_MOMENTS, _TRANSCRIPT)

    assert isinstance(result, EmailSequenceOutput)
    assert result.emails == []


# ---------------------------------------------------------------------------
# format_name property for all generators
# ---------------------------------------------------------------------------


def test_all_generators_have_unique_format_names() -> None:
    """Every generator has a unique format_name."""
    generators = [
        TwitterGenerator(_VOICE),
        LinkedInGenerator(_VOICE),
        NewsletterGenerator(_VOICE),
        ShortVideoGenerator(_VOICE),
        BlogPostGenerator(_VOICE),
        YouTubeDescriptionGenerator(_VOICE),
        QuoteCardGenerator(_VOICE),
        EmailSequenceGenerator(_VOICE),
    ]
    names = [g.format_name for g in generators]
    assert len(names) == len(set(names)), "Duplicate format_name found"
    assert set(names) == {
        "twitter",
        "linkedin",
        "newsletter",
        "short_video",
        "blog_post",
        "youtube",
        "quote_cards",
        "email_sequence",
    }
