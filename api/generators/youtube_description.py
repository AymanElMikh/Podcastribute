"""YouTube description generator — optimized description, chapters, and tags."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class YouTubeDescriptionOutput(BaseModel):
    """Structured output from the YouTube description generator."""

    description: str = ""
    chapters: list[dict] = []
    tags: list[str] = []
    end_screen_script: str = ""


_SYSTEM_TEMPLATE = """{voice_context}

You write YouTube descriptions that maximize click-through and watch time.
Rules:
- description: first 150 chars must hook the viewer (shown before "more")
  then expand with key insights, links section, and subscribe CTA
- chapters: timestamp list [{{"time": "0:00", "title": "Intro"}}, ...]
  improves watch time — use moment timestamps where possible
- tags: 15 tags mixing specific (guest name, exact topic) and broad (podcast, interview)
- end_screen_script: exactly what the host says in the last 20 seconds
  — subscribe ask + next video tease, conversational not scripted-sounding

Return ONLY valid JSON (no markdown fences):
{{
  "description": "full youtube description",
  "chapters": [{{"time": "0:00", "title": "chapter title"}}, ...],
  "tags": ["tag1", "tag2", ...],
  "end_screen_script": "spoken text for last 20 seconds"
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the YouTube description assets now."""


class YouTubeDescriptionGenerator:
    """Generates a YouTube video description with chapters, tags, and end screen script.

    Output shape:
        description: str             — first 150 chars are critical
        chapters: list[dict]         — [{time, title}] for timestamps
        tags: list[str]              — 15 mixed broad/specific tags
        end_screen_script: str       — spoken text for last 20 seconds
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
        return "youtube"

    async def generate(self, moments: list[dict], transcript: str) -> YouTubeDescriptionOutput:
        """Generate YouTube description assets from episode content.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            YouTubeDescriptionOutput with description, chapters, tags, end_screen_script.
            Returns an empty YouTubeDescriptionOutput on gateway or parsing failure.
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
            return YouTubeDescriptionOutput(**data)
        except Exception as exc:
            log.warning("youtube_description_generator_failed", error=str(exc))
            return YouTubeDescriptionOutput()
