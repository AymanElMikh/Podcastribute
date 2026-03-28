"""Twitter/X content generator — produces threads, hooks, and listen tweets."""

import structlog
from pydantic import BaseModel

from api.generators.base import build_voice_context, call_gateway, parse_json_response, top_moments_block

log = structlog.get_logger(__name__)

_TRANSCRIPT_CHARS = 2000


class TwitterOutput(BaseModel):
    """Structured output from the Twitter content generator."""

    main_thread: list[str] = []
    standalone_hooks: list[str] = []
    listen_tweet: str = ""


_SYSTEM_TEMPLATE = """{voice_context}
Twitter style: {twitter_style}

You write Twitter threads that tell a story, not just list bullet points.
Rules:
- Thread: 8-12 tweets, numbered (1/, 2/, etc.)
- First tweet is the hook — no "🧵 Thread:" prefix, no emoji unless natural
- Each tweet ≤ 280 characters
- No corporate language, no buzzwords
- standalone_hooks: 3 single viral tweets (not numbered, not threaded)
- listen_tweet: one tweet that makes people want to play the episode

Return ONLY valid JSON (no markdown fences):
{{
  "main_thread": ["tweet 1", "tweet 2", ...],
  "standalone_hooks": ["hook 1", "hook 2", "hook 3"],
  "listen_tweet": "tweet driving plays"
}}"""

_USER_TEMPLATE = """Top moments from this episode:
{moments}

Transcript excerpt:
{transcript}

Generate the Twitter content now."""


class TwitterGenerator:
    """Generates a Twitter thread, standalone hooks, and a listen tweet for an episode.

    Output shape:
        main_thread: list[str]       — 8-12 tweets, numbered
        standalone_hooks: list[str]  — 3 single viral tweets
        listen_tweet: str            — drives episode plays
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
        return "twitter"

    async def generate(self, moments: list[dict], transcript: str) -> TwitterOutput:
        """Generate Twitter content from episode moments using the voice profile.

        Args:
            moments: Ranked shareable moments from the episode.
            transcript: Full episode transcript.

        Returns:
            TwitterOutput with main_thread, standalone_hooks, and listen_tweet.
            Returns an empty TwitterOutput on gateway or parsing failure.
        """
        system = _SYSTEM_TEMPLATE.format(
            voice_context=build_voice_context(self._voice),
            twitter_style=self._voice.get("twitter_style", "educator"),
        )
        user = _USER_TEMPLATE.format(
            moments=top_moments_block(moments),
            transcript=transcript[:_TRANSCRIPT_CHARS],
        )
        try:
            raw = await call_gateway(system, user, strategy="balanced", max_tokens=2000)
            data = parse_json_response(raw)
            return TwitterOutput(**data)
        except Exception as exc:
            log.warning("twitter_generator_failed", error=str(exc))
            return TwitterOutput()
