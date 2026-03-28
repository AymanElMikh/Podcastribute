"""Email sequence generator — 3-email drip sequence from a single episode."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class EmailSequenceOutput(BaseModel):
    """Structured output from the email sequence generator."""

    emails: list[dict] = []


_SYSTEM_TEMPLATE = """{voice_context}

You write 3-email drip sequences that convert listeners into engaged subscribers.
Rules:
- Email 0 (send_day: 0): episode announcement — make them want to listen NOW
- Email 2 (send_day: 2): best single insight from the episode — delivered as a lesson
- Email 5 (send_day: 5): CTA email — based on the episode topic, what should they do next?
- Each email: 100-200 words, conversational not promotional
- subject: curiosity-driven, under 50 chars
- preview_text: one line shown in email clients, under 90 chars
- body: first-person, feels like an email from a friend
- purpose: "announce" | "insight" | "cta"

Return ONLY valid JSON (no markdown fences):
{{
  "emails": [
    {{
      "subject": "email subject line",
      "preview_text": "preview text under 90 chars",
      "body": "100-200 word email body",
      "send_day": 0,
      "purpose": "announce"
    }},
    {{
      "subject": "subject line",
      "preview_text": "preview text",
      "body": "email body",
      "send_day": 2,
      "purpose": "insight"
    }},
    {{
      "subject": "subject line",
      "preview_text": "preview text",
      "body": "email body",
      "send_day": 5,
      "purpose": "cta"
    }}
  ]
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the 3-email drip sequence now."""


class EmailSequenceGenerator:
    """Generates a 3-email drip sequence timed to the episode release.

    Output shape:
        emails: list[dict]  — each with subject, preview_text, body,
                              send_day, purpose
        Day 0: episode announcement
        Day 2: best insight from episode
        Day 5: CTA based on episode topic
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
        return "email_sequence"

    async def generate(self, moments: list[dict], transcript: str) -> EmailSequenceOutput:
        """Generate a 3-email drip sequence from the episode content.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            EmailSequenceOutput with emails list.
            Returns an empty EmailSequenceOutput on gateway or parsing failure.
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
            return EmailSequenceOutput(**data)
        except Exception as exc:
            log.warning("email_sequence_generator_failed", error=str(exc))
            return EmailSequenceOutput()
