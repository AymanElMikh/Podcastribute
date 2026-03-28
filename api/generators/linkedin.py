"""LinkedIn content generator — post, carousel outline, and hook variations."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class LinkedInOutput(BaseModel):
    """Structured output from the LinkedIn content generator."""

    post: str = ""
    carousel_outline: list[str] = []
    post_hooks: list[str] = []


_SYSTEM_TEMPLATE = """{voice_context}
LinkedIn style: {linkedin_style}

You write LinkedIn content that earns genuine engagement.
Rules:
- Post: 150-300 words, vulnerability + specificity, no buzzwords
- End with a genuine open-ended question (not rhetorical)
- carousel_outline: 7 slide titles for a Canva carousel — standalone lesson
- post_hooks: 3 alternative opening lines (first sentence only, no full post)
- No corporate language, no "I'm excited to share", no "game-changer"

Return ONLY valid JSON (no markdown fences):
{{
  "post": "full linkedin post text",
  "carousel_outline": ["Slide 1 title", "Slide 2 title", ...],
  "post_hooks": ["hook 1", "hook 2", "hook 3"]
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the LinkedIn content now."""


class LinkedInGenerator:
    """Generates a LinkedIn post, carousel outline, and alternative opening hooks.

    Output shape:
        post: str                    — 150-300 word post
        carousel_outline: list[str]  — 7 slide titles for Canva
        post_hooks: list[str]        — 3 alternative opening lines
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
        return "linkedin"

    async def generate(self, moments: list[dict], transcript: str) -> LinkedInOutput:
        """Generate LinkedIn content from episode moments using the voice profile.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            LinkedInOutput with post, carousel_outline, and post_hooks.
            Returns an empty LinkedInOutput on gateway or parsing failure.
        """
        system = _SYSTEM_TEMPLATE.format(
            voice_context=build_voice_context(self._voice),
            linkedin_style=self._voice.get("linkedin_style", "personal_story"),
        )
        user = _USER_TEMPLATE.format(
            moments=top_moments_block(moments),
            transcript=transcript[:_TRANSCRIPT_CHARS],
        )
        try:
            raw = await call_gateway(system, user, strategy="balanced", max_tokens=2000)
            data = parse_json_response(raw)
            return LinkedInOutput(**data)
        except Exception as exc:
            log.warning("linkedin_generator_failed", error=str(exc))
            return LinkedInOutput()
