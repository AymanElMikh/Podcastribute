"""LangGraph node: detects and scores shareable moments from a podcast transcript.

Chunks the transcript into overlapping 500-word segments, scores each chunk in
parallel using the LLM gateway, deduplicates by start_time, enforces type
diversity, and returns the top-10 most shareable moments.
"""

import asyncio
import json
import re

import structlog

from api.agent.state import PodcastState
from api.generators.base import call_gateway

log = structlog.get_logger(__name__)

MOMENT_TYPES: list[str] = [
    "strong_opinion",
    "surprising_statistic",
    "actionable_advice",
    "personal_story",
    "contrarian_take",
    "quotable_one_liner",
    "debate_moment",
    "prediction",
    "definition",
    "case_study",
]

# Chunking parameters
_CHUNK_WORDS: int = 500
_OVERLAP_WORDS: int = 50
_MIN_SCORE: float = 0.6
_TOP_K: int = 10
_MIN_TYPE_DIVERSITY: int = 3  # at least this many distinct moment types

DETECTOR_PROMPT: str = (
    "You are a podcast content strategist. Analyze this transcript segment and identify "
    "the most shareable moments for social media repurposing.\n\n"
    "Voice profile of this podcaster: {voice_profile_summary}\n\n"
    "Accepted moment types: {moment_types}\n\n"
    "For each strong moment evaluate:\n"
    "- Standalone value (0-1): understood without full episode context?\n"
    "- Emotional resonance (0-1): does it provoke a reaction?\n"
    "- Shareability (0-1): would someone forward this?\n\n"
    "Return ONLY a JSON array of objects with shareability_score >= {min_score}. "
    "Return an empty array [] if no moments meet the threshold.\n"
    'Each object: {{"start_time":"MM:SS","end_time":"MM:SS","text":"exact quote",'
    '"type":"moment_type","shareability_score":0.0,"one_line_hook":"hook text"}}'
)


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------


def _chunk_transcript(transcript: str) -> list[str]:
    """Split a transcript into overlapping 500-word chunks.

    Overlapping by _OVERLAP_WORDS prevents missing moments that span chunk
    boundaries. Each chunk is a plain string — the gateway does not need
    timestamp markers embedded in the text.

    Args:
        transcript: Full episode transcript text.

    Returns:
        List of chunk strings, each at most _CHUNK_WORDS words long.
    """
    words = transcript.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + _CHUNK_WORDS
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - _OVERLAP_WORDS  # slide back for overlap

    return chunks


def _voice_profile_summary(voice_profile: dict) -> str:
    """Produce a short human-readable summary of the voice profile for the prompt.

    Args:
        voice_profile: VoiceProfile as a plain dict.

    Returns:
        One-line summary string.
    """
    if not voice_profile:
        return "conversational podcaster with occasional humor"
    tone = ", ".join(voice_profile.get("tone_adjectives", []) or ["engaging"])
    style = voice_profile.get("sentence_style", "conversational")
    humor = voice_profile.get("humor_level", "occasional")
    return f"{tone} voice, {style} style, {humor} humor"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _extract_json_array(raw: str) -> list:
    """Extract the first JSON array from a gateway response string.

    Handles cases where the model wraps output in prose or code fences.

    Args:
        raw: Raw string from the gateway.

    Returns:
        Parsed list, or empty list if no valid array found.
    """
    raw = raw.strip()
    # Strip markdown code fences
    fence_match = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", raw)
    if fence_match:
        raw = fence_match.group(1).strip()

    # Try direct parse first
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Find first [...] in the string
    bracket_match = re.search(r"\[[\s\S]*\]", raw)
    if bracket_match:
        try:
            return json.loads(bracket_match.group())
        except json.JSONDecodeError:
            pass

    return []


def _is_valid_moment(moment: dict) -> bool:
    """Return True if the moment dict has all required fields and a valid score.

    Args:
        moment: Raw moment dict from gateway output.

    Returns:
        True if the moment is well-formed and meets the minimum score threshold.
    """
    required = {"start_time", "end_time", "text", "type", "shareability_score"}
    if not required.issubset(moment.keys()):
        return False
    try:
        score = float(moment["shareability_score"])
    except (TypeError, ValueError):
        return False
    if score < _MIN_SCORE:
        return False
    if moment.get("type") not in MOMENT_TYPES:
        return False
    return True


# ---------------------------------------------------------------------------
# Deduplication and diversity
# ---------------------------------------------------------------------------


def _deduplicate(moments: list[dict]) -> list[dict]:
    """Remove duplicate moments that share the same start_time.

    When the same start_time appears multiple times (from overlapping chunks),
    keep the one with the highest shareability_score.

    Args:
        moments: Flat list of moment dicts, possibly with duplicates.

    Returns:
        Deduplicated list with the best-scoring entry per start_time.
    """
    best: dict[str, dict] = {}
    for m in moments:
        key = m.get("start_time", "")
        existing = best.get(key)
        if existing is None or float(m["shareability_score"]) > float(
            existing["shareability_score"]
        ):
            best[key] = m
    return list(best.values())


def _ensure_diversity(moments: list[dict], min_types: int) -> list[dict]:
    """Ensure the final list contains at least min_types distinct moment types.

    If diversity is already satisfied, the list is returned as-is. Otherwise
    moments are reordered so that the first min_types entries are all different
    types, then the rest follow by score.

    Args:
        moments: Score-sorted list of moment dicts.
        min_types: Minimum number of distinct types required.

    Returns:
        Reordered list with diversity guarantee.
    """
    types_seen: set[str] = set()
    diverse: list[dict] = []
    remainder: list[dict] = []

    for m in moments:
        t = m.get("type", "")
        if t not in types_seen and len(types_seen) < min_types:
            diverse.append(m)
            types_seen.add(t)
        else:
            remainder.append(m)

    return diverse + remainder


# ---------------------------------------------------------------------------
# Per-chunk scorer
# ---------------------------------------------------------------------------


async def _score_chunk(chunk: str, prompt: str) -> list[dict]:
    """Score a single transcript chunk and return valid moments.

    Args:
        chunk: Transcript text chunk.
        prompt: Fully-formatted detector prompt.

    Returns:
        List of valid moment dicts from this chunk, or empty list on failure.
    """
    user_prompt = f"Transcript segment:\n\n{chunk}"
    try:
        raw = await call_gateway(prompt, user_prompt, strategy="balanced")
        moments = _extract_json_array(raw)
        return [m for m in moments if _is_valid_moment(m)]
    except Exception as exc:
        log.warning("moment_chunk_failed", error=str(exc))
        return []


# ---------------------------------------------------------------------------
# Main node function
# ---------------------------------------------------------------------------


async def moment_detector(state: PodcastState) -> dict:
    """Detect and rank the top-10 shareable moments from the episode transcript.

    Pipeline:
    1. Chunk the transcript into overlapping 500-word segments
    2. Score every chunk in parallel (asyncio.gather)
    3. Flatten, validate, and deduplicate results
    4. Sort by shareability_score descending
    5. Enforce type diversity (≥3 distinct types)
    6. Return the top 10

    Handles transcripts with no strong moments gracefully (returns empty list).

    Args:
        state: Current pipeline state containing transcript and voice_profile.

    Returns:
        Dict with key "moments" containing list of ranked moment dicts (max 10).
    """
    transcript = state.get("transcript", "") or ""
    voice_profile = state.get("voice_profile", {}) or {}

    if not transcript.strip():
        log.warning("moment_detector_empty_transcript", episode_id=state.get("episode_id"))
        return {"moments": []}

    # Build the prompt (filled once, reused per chunk)
    prompt = DETECTOR_PROMPT.format(
        voice_profile_summary=_voice_profile_summary(voice_profile),
        moment_types=", ".join(MOMENT_TYPES),
        min_score=_MIN_SCORE,
    )

    chunks = _chunk_transcript(transcript)
    log.info(
        "moment_detection_start",
        episode_id=state.get("episode_id"),
        chunks=len(chunks),
    )

    # Score all chunks in parallel
    chunk_results = await asyncio.gather(
        *[_score_chunk(chunk, prompt) for chunk in chunks],
        return_exceptions=False,
    )

    # Flatten
    all_moments: list[dict] = [m for chunk in chunk_results for m in chunk]

    if not all_moments:
        log.info("moment_detector_no_moments", episode_id=state.get("episode_id"))
        return {"moments": []}

    # Deduplicate by start_time, keeping highest score
    unique = _deduplicate(all_moments)

    # Sort by shareability_score descending
    ranked = sorted(unique, key=lambda m: float(m["shareability_score"]), reverse=True)

    # Enforce diversity then take top _TOP_K
    diverse = _ensure_diversity(ranked, _MIN_TYPE_DIVERSITY)
    top = diverse[:_TOP_K]

    log.info(
        "moment_detector_done",
        episode_id=state.get("episode_id"),
        total_found=len(unique),
        returned=len(top),
    )

    return {"moments": top}
