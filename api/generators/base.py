"""Base protocol and shared utilities for all content generators.

Defines the ContentGenerator Protocol that every generator must satisfy,
plus the shared call_gateway helper and response-parsing utilities used
by all implementations.
"""

import json
import re
from typing import Protocol, runtime_checkable

import httpx
import structlog
from pydantic import BaseModel

from api.config import settings

log = structlog.get_logger(__name__)


@runtime_checkable
class ContentGenerator(Protocol):
    """Protocol defining the interface every content generator must implement.

    The voice profile is injected at construction time so every call to
    generate() already has the voice context baked in.

    Using Protocol (not ABC) so generators can be structurally typed and
    composed freely without inheritance coupling.
    """

    async def generate(self, moments: list[dict], transcript: str) -> BaseModel:
        """Generate content for this format from the given episode data.

        Args:
            moments: List of detected shareable moment dicts.
            transcript: Full episode transcript text.

        Returns:
            A Pydantic model containing all fields for this content format.
        """
        ...

    @property
    def format_name(self) -> str:
        """Return the unique identifier string for this content format."""
        ...


async def call_gateway(
    system: str,
    user: str,
    strategy: str = "balanced",
    max_tokens: int = 2000,
) -> str:
    """Send a chat completion request to OpenAI and return the response text.

    Uses gpt-4o-mini for "balanced"/"fast" strategies and gpt-4o for "quality",
    giving a cost/capability trade-off across content generators.

    Args:
        system: System prompt text.
        user: User prompt text.
        strategy: Routing hint — "quality" uses gpt-4o, everything else uses gpt-4o-mini.
        max_tokens: Maximum tokens to generate.

    Returns:
        The assistant message content string from OpenAI.

    Raises:
        httpx.HTTPStatusError: If OpenAI returns a non-2xx status.
        ValueError: If OPENAI_API_KEY is not configured.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to your .env file."
        )

    model = (
        settings.OPENAI_MODEL_QUALITY
        if strategy == "quality"
        else settings.OPENAI_MODEL_DEFAULT
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def parse_json_response(raw: str) -> dict | list:
    """Parse a JSON object or array from a gateway response string.

    Handles markdown code fences (```json ... ```) and responses where the
    JSON is embedded in surrounding prose.

    Args:
        raw: Raw string from the gateway.

    Returns:
        Parsed Python dict or list.

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    text = raw.strip()

    # Strip ```json ... ``` or ``` ... ```
    fence = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    if fence:
        text = fence.group(1).strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first JSON object {...} or array [...]
    for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    raise ValueError(f"No valid JSON found in gateway response: {text[:200]!r}")


def build_voice_context(voice: dict) -> str:
    """Build a concise voice-context block for system prompts.

    Embeds the key voice profile fields that differentiate one podcaster's
    style from another. Every generator includes this in its system prompt
    so generated content sounds like the specific podcaster.

    Args:
        voice: VoiceProfile serialized as a plain dict.

    Returns:
        Multi-line string describing the podcaster's voice, ready for
        insertion into a system prompt.
    """
    if not voice:
        return "Voice: conversational, engaging, authentic."

    tone = ", ".join(voice.get("tone_adjectives") or ["engaging"])
    vocab = voice.get("vocabulary_level", "conversational")
    style = voice.get("sentence_style", "conversational")
    humor = voice.get("humor_level", "occasional")
    avoid = ", ".join(voice.get("words_to_avoid") or []) or "none"
    phrases = ", ".join(voice.get("signature_phrases") or []) or "none"

    return (
        f"Podcaster voice profile:\n"
        f"- Tone: {tone}\n"
        f"- Vocabulary level: {vocab}\n"
        f"- Sentence style: {style}\n"
        f"- Humor level: {humor}\n"
        f"- Words/phrases to AVOID: {avoid}\n"
        f"- Signature phrases they use: {phrases}"
    )


def top_moments_block(moments: list[dict], limit: int = 5) -> str:
    """Format the top N moments as a compact JSON block for user prompts.

    Args:
        moments: List of moment dicts from the moment detector.
        limit: Maximum number of moments to include.

    Returns:
        JSON-formatted string of the top moments.
    """
    top = moments[:limit]
    lines = []
    for m in top:
        lines.append(
            f'- [{m.get("start_time","??")}] {m.get("text","")[:120]} '
            f'(type: {m.get("type","")}, score: {m.get("shareability_score",0):.2f})'
        )
    return "\n".join(lines) if lines else "(no moments available)"
