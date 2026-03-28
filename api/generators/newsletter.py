"""Newsletter content generator — section body, subject lines, and preview text."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class NewsletterOutput(BaseModel):
    """Structured output from the newsletter content generator."""

    section_title: str = ""
    section_body: str = ""
    subject_lines: list[str] = []
    preview_text: str = ""


_SYSTEM_TEMPLATE = """{voice_context}

You write newsletter sections that feel like a personal letter, not an article.
Rules:
- section_title: punchy heading for this episode's section
- section_body: 200-400 words, conversational not formal, first-person
- subject_lines: 5 options (label A through E), curiosity-driven not clickbait
- preview_text: one line that appears in email clients (under 90 chars)
- No corporate language, no "In this episode we discuss"

Return ONLY valid JSON (no markdown fences):
{{
  "section_title": "section heading",
  "section_body": "200-400 word newsletter section",
  "subject_lines": ["A: subject 1", "B: subject 2", "C: subject 3", "D: subject 4", "E: subject 5"],
  "preview_text": "preview line under 90 chars"
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the newsletter content now."""


class NewsletterGenerator:
    """Generates a newsletter section with subject line options and preview text.

    Output shape:
        section_title: str           — section heading
        section_body: str            — 200-400 word newsletter section
        subject_lines: list[str]     — 5 A/B/C/D/E subject line options
        preview_text: str            — email preview line
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
        return "newsletter"

    async def generate(self, moments: list[dict], transcript: str) -> NewsletterOutput:
        """Generate newsletter content from episode moments using the voice profile.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            NewsletterOutput with section_title, section_body, subject_lines, preview_text.
            Returns an empty NewsletterOutput on gateway or parsing failure.
        """
        system = _SYSTEM_TEMPLATE.format(
            voice_context=build_voice_context(self._voice),
        )
        user = _USER_TEMPLATE.format(
            moments=top_moments_block(moments),
            transcript=transcript[:_TRANSCRIPT_CHARS],
        )
        try:
            raw = await call_gateway(system, user, strategy="balanced", max_tokens=2000)
            data = parse_json_response(raw)
            return NewsletterOutput(**data)
        except Exception as exc:
            log.warning("newsletter_generator_failed", error=str(exc))
            return NewsletterOutput()
