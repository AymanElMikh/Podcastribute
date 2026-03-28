"""Quote card generator — self-contained visual quotes for social sharing."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class QuoteCardOutput(BaseModel):
    """Structured output from the quote card generator."""

    quotes: list[dict] = []


_SYSTEM_TEMPLATE = """{voice_context}

You extract the most powerful quotes for visual quote card posts.
Rules:
- Select 5-7 quotes from the transcript
- text: under 140 chars, grammatically correct as standalone
- No context-dependent references (no "as I mentioned", no "like he said")
- attribution: format exactly as '— [Host/Guest Name], [Episode Context]'
- background_suggestion: color or visual mood (e.g. "dark navy, gold text")
- caption: 1-2 sentence social caption to post with the image
- Quotes should be self-contained insights, not setup lines

Return ONLY valid JSON (no markdown fences):
{{
  "quotes": [
    {{
      "text": "the quote under 140 chars",
      "attribution": "— Name, Episode Context",
      "background_suggestion": "color/style description",
      "caption": "social caption for this quote card"
    }}
  ]
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the quote cards now."""


class QuoteCardGenerator:
    """Generates shareable quote cards with captions and design suggestions.

    Output shape:
        quotes: list[dict]  — each with text, attribution,
                              background_suggestion, caption
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
        return "quote_cards"

    async def generate(self, moments: list[dict], transcript: str) -> QuoteCardOutput:
        """Generate visual quote cards from the episode's most quotable moments.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            QuoteCardOutput with quotes list.
            Returns an empty QuoteCardOutput on gateway or parsing failure.
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
            return QuoteCardOutput(**data)
        except Exception as exc:
            log.warning("quote_card_generator_failed", error=str(exc))
            return QuoteCardOutput()
