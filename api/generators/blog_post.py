"""Blog post generator — SEO-optimized long-form article from episode content."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 3000


class BlogPostOutput(BaseModel):
    """Structured output from the blog post generator."""

    title: str = ""
    meta_description: str = ""
    outline: list[str] = []
    body: str = ""
    internal_link_suggestions: list[str] = []
    target_keywords: list[str] = []


_SYSTEM_TEMPLATE = """{voice_context}

You write SEO-optimized blog posts that add context beyond the episode transcript.
Rules:
- title: compelling H1, optimized for search intent (not "Ep 42: ...")
- meta_description: exactly under 155 chars, includes primary keyword
- outline: 4-6 H2 section headings that are skimmable
- body: 800-1200 words in markdown, adds context not just transcription
- internal_link_suggestions: 3 topic areas this post could link to
- target_keywords: 5-8 keywords (mix of head terms and long-tail)
- Every section must be skimmable with clear value
- Write in the podcaster's voice, not generic blog voice

Return ONLY valid JSON (no markdown fences):
{{
  "title": "SEO blog post title",
  "meta_description": "155 char meta description",
  "outline": ["H2 heading 1", "H2 heading 2", ...],
  "body": "full 800-1200 word markdown blog post",
  "internal_link_suggestions": ["topic area 1", "topic area 2", "topic area 3"],
  "target_keywords": ["keyword 1", "keyword 2", ...]
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the blog post now."""


class BlogPostGenerator:
    """Generates a full SEO-optimized blog post from an episode.

    Output shape:
        title: str                             — SEO-optimized H1
        meta_description: str                  — 155 char meta tag
        outline: list[str]                     — H2 section headings
        body: str                              — 800-1200 words markdown
        internal_link_suggestions: list[str]
        target_keywords: list[str]
    """

    def __init__(self, voice: dict) -> None:
        """Initialise with the podcaster's voice profile.

        Args:
            voice: VoiceProfile serialised as a plain dict.
        """
        self._voice = voice

    @property
    def format_name(self) -> str:
        """Return the unique format identifier for this generator."""
        return "blog_post"

    async def generate(self, moments: list[dict], transcript: str) -> BlogPostOutput:
        """Generate an SEO blog post from episode moments and transcript.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            BlogPostOutput with title, meta_description, outline, body,
            internal_link_suggestions, and target_keywords.
            Returns an empty BlogPostOutput on gateway or parsing failure.
        """
        system = _SYSTEM_TEMPLATE.format(
            voice_context=build_voice_context(self._voice),
        )
        user = _USER_TEMPLATE.format(
            moments=top_moments_block(moments),
            transcript=transcript[:_TRANSCRIPT_CHARS],
        )
        try:
            raw = await call_gateway(system, user, strategy="quality", max_tokens=3000)
            data = parse_json_response(raw)
            return BlogPostOutput(**data)
        except Exception as exc:
            log.warning("blog_post_generator_failed", error=str(exc))
            return BlogPostOutput()
