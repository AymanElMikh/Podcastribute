"""Short-form video clip generator — hooks and screen notes for TikTok/Reels/Shorts."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class ShortVideoOutput(BaseModel):
    """Structured output from the short video content generator."""

    clips: list[dict] = []


_SYSTEM_TEMPLATE = """{voice_context}

You identify the best moments for short-form video (TikTok, Reels, YouTube Shorts).
Rules:
- Select 3-5 clips, each 45-90 seconds long
- hook: the exact spoken text for the first 3 seconds (must grab attention instantly)
- script_note: what text overlay the editor should add on screen
- platform: best fit — "tiktok", "reels", or "shorts"
- Prioritize the highest-energy, most standalone moments
- The hook must be from the actual transcript, not invented

Return ONLY valid JSON (no markdown fences):
{{
  "clips": [
    {{
      "start_time": "MM:SS",
      "end_time": "MM:SS",
      "hook": "exact opening words from clip",
      "script_note": "text overlay instruction for editor",
      "platform": "tiktok|reels|shorts"
    }}
  ]
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the short video clips now."""


class ShortVideoGenerator:
    """Generates short-form video clip scripts optimized for TikTok, Reels, and Shorts.

    Output shape:
        clips: list[dict]  — each with start_time, end_time, hook,
                             script_note, platform
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
        return "short_video"

    async def generate(self, moments: list[dict], transcript: str) -> ShortVideoOutput:
        """Generate short video clip scripts from episode moments.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            ShortVideoOutput with clips list.
            Returns an empty ShortVideoOutput on gateway or parsing failure.
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
            return ShortVideoOutput(**data)
        except Exception as exc:
            log.warning("short_video_generator_failed", error=str(exc))
            return ShortVideoOutput()
