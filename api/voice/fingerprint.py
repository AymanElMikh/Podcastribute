"""Voice fingerprint builder — extracts a podcaster's unique style from content samples.

This is the core differentiator of PodcastAI. The voice fingerprint is built from
transcripts or social posts and stored as a VoiceProfile used to personalize
all content generation.
"""

import json
import re

import structlog

from api.generators.base import call_gateway
from api.models.voice import VoiceProfile

log = structlog.get_logger(__name__)

# Maximum combined character length sent to the gateway
_MAX_COMBINED_CHARS: int = 6000
# Maximum number of transcript samples to use
_MAX_SAMPLES: int = 5

FINGERPRINT_PROMPT: str = """You are analyzing content samples from a podcaster to extract their unique voice profile.
Study their vocabulary, sentence rhythm, humor, and topic focus carefully.

Return ONLY valid JSON with no markdown fences or extra text:
{
  "vocabulary_level": "casual|professional|academic|technical",
  "sentence_style": "short_punchy|conversational|detailed|storytelling",
  "humor_level": "none|dry|occasional|frequent",
  "twitter_style": "thread_storyteller|hot_take|educator|question_asker",
  "linkedin_style": "personal_story|industry_insight|contrarian|practical_tips",
  "signature_phrases": ["phrases they use repeatedly"],
  "topics_they_care_about": ["recurring themes"],
  "what_they_never_say": ["jargon and words to avoid"],
  "tone_adjectives": ["three words describing their voice"],
  "default_cta_style": "soft_invite|direct_ask|community_focused|value_first"
}"""

SOCIAL_FINGERPRINT_PROMPT: str = """You are analyzing social media posts from a content creator to extract their unique voice profile.
These are condensed posts — focus on word choice, punctuation style, and how they frame ideas.

Return ONLY valid JSON with no markdown fences or extra text:
{
  "vocabulary_level": "casual|professional|academic|technical",
  "sentence_style": "short_punchy|conversational|detailed|storytelling",
  "humor_level": "none|dry|occasional|frequent",
  "twitter_style": "thread_storyteller|hot_take|educator|question_asker",
  "linkedin_style": "personal_story|industry_insight|contrarian|practical_tips",
  "signature_phrases": ["phrases they use repeatedly"],
  "topics_they_care_about": ["recurring themes"],
  "what_they_never_say": ["jargon and words to avoid"],
  "tone_adjectives": ["three words describing their voice"],
  "default_cta_style": "soft_invite|direct_ask|community_focused|value_first"
}"""

REFINE_PROMPT: str = """You are updating an existing podcaster voice profile based on user feedback.
Read the feedback carefully and update ONLY the fields it addresses.
If a field is not mentioned in the feedback, keep its existing value.

Return the complete updated profile as ONLY valid JSON with no markdown fences."""

DEFAULT_VOICE_PROFILE: VoiceProfile = VoiceProfile(
    vocabulary_level="conversational",
    sentence_style="conversational",
    humor_level="occasional",
    twitter_style="educator",
    linkedin_style="personal_story",
    signature_phrases=[],
    topics=[],
    words_to_avoid=[],
    tone_adjectives=["authentic", "engaging", "clear"],
    default_cta_style="value_first",
)


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) from a string.

    Args:
        text: Raw string possibly wrapped in markdown code fences.

    Returns:
        The inner content with fences removed.
    """
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text)
    if match:
        return match.group(1).strip()
    return text


def _parse_profile(raw: str) -> VoiceProfile:
    """Parse a JSON string from the gateway into a VoiceProfile.

    Handles the field name discrepancies between the prompt output
    (topics_they_care_about, what_they_never_say) and the VoiceProfile model
    (topics, words_to_avoid).

    Args:
        raw: Raw JSON string from the gateway.

    Returns:
        Parsed VoiceProfile.

    Raises:
        json.JSONDecodeError: If the string is not valid JSON.
        ValueError: If required fields are missing.
    """
    data = json.loads(_strip_code_fences(raw))

    return VoiceProfile(
        vocabulary_level=data.get(
            "vocabulary_level", DEFAULT_VOICE_PROFILE.vocabulary_level
        ),
        sentence_style=data.get(
            "sentence_style", DEFAULT_VOICE_PROFILE.sentence_style
        ),
        humor_level=data.get("humor_level", DEFAULT_VOICE_PROFILE.humor_level),
        twitter_style=data.get("twitter_style", DEFAULT_VOICE_PROFILE.twitter_style),
        linkedin_style=data.get(
            "linkedin_style", DEFAULT_VOICE_PROFILE.linkedin_style
        ),
        signature_phrases=data.get("signature_phrases", []),
        # Gateway uses "topics_they_care_about"; Pydantic model uses "topics"
        topics=data.get("topics_they_care_about", data.get("topics", [])),
        # Gateway uses "what_they_never_say"; Pydantic model uses "words_to_avoid"
        words_to_avoid=data.get(
            "what_they_never_say", data.get("words_to_avoid", [])
        ),
        tone_adjectives=data.get("tone_adjectives", []),
        default_cta_style=data.get(
            "default_cta_style", DEFAULT_VOICE_PROFILE.default_cta_style
        ),
    )


class VoiceFingerprintBuilder:
    """Builds and refines a VoiceProfile from text samples using the LLM gateway.

    Supports building from podcast transcripts, social media posts,
    or previously uploaded episodes. Can also refine an existing profile
    based on natural language feedback.

    All gateway calls use strategy="quality" because voice extraction requires
    the most capable model for accurate style analysis.
    """

    async def build_from_transcripts(self, transcripts: list[str]) -> VoiceProfile:
        """Extract a VoiceProfile from up to 5 podcast transcript samples.

        Combines up to _MAX_SAMPLES transcripts, truncates the combined text
        to _MAX_COMBINED_CHARS to stay within context limits, then calls the
        gateway with strategy="quality". Falls back to DEFAULT_VOICE_PROFILE
        on any failure.

        Args:
            transcripts: List of transcript text strings.

        Returns:
            Extracted VoiceProfile, or DEFAULT_VOICE_PROFILE on empty input
            or gateway/parsing failure.
        """
        if not transcripts:
            log.info("fingerprint_empty_transcripts")
            return DEFAULT_VOICE_PROFILE

        combined = "\n\n---\n\n".join(transcripts[:_MAX_SAMPLES])
        combined = combined[:_MAX_COMBINED_CHARS]

        user_prompt = f"Here are the podcast transcripts to analyze:\n\n{combined}"

        log.info(
            "fingerprint_build_start",
            source="transcripts",
            samples=min(len(transcripts), _MAX_SAMPLES),
            chars=len(combined),
        )

        try:
            raw = await call_gateway(FINGERPRINT_PROMPT, user_prompt, strategy="quality")
            profile = _parse_profile(raw)
            log.info("fingerprint_build_done", source="transcripts")
            return profile
        except Exception as exc:
            log.warning("fingerprint_build_failed", source="transcripts", error=str(exc))
            return DEFAULT_VOICE_PROFILE

    async def build_from_social_posts(self, posts: list[str]) -> VoiceProfile:
        """Extract a VoiceProfile from social media post samples.

        Uses a variant of the fingerprint prompt that accounts for the
        condensed nature of social media writing.

        Args:
            posts: List of social media post strings.

        Returns:
            Extracted VoiceProfile, or DEFAULT_VOICE_PROFILE on empty input
            or gateway/parsing failure.
        """
        if not posts:
            log.info("fingerprint_empty_posts")
            return DEFAULT_VOICE_PROFILE

        combined = "\n\n---\n\n".join(posts[:_MAX_SAMPLES])
        combined = combined[:_MAX_COMBINED_CHARS]

        user_prompt = f"Here are the social media posts to analyze:\n\n{combined}"

        log.info(
            "fingerprint_build_start",
            source="social_posts",
            samples=min(len(posts), _MAX_SAMPLES),
            chars=len(combined),
        )

        try:
            raw = await call_gateway(
                SOCIAL_FINGERPRINT_PROMPT, user_prompt, strategy="quality"
            )
            profile = _parse_profile(raw)
            log.info("fingerprint_build_done", source="social_posts")
            return profile
        except Exception as exc:
            log.warning("fingerprint_build_failed", source="social_posts", error=str(exc))
            return DEFAULT_VOICE_PROFILE

    async def refine(self, existing: VoiceProfile, feedback: str) -> VoiceProfile:
        """Refine specific fields of an existing VoiceProfile based on user feedback.

        Interprets natural language feedback like "I never use corporate buzzwords"
        and updates only the relevant profile fields. Returns the unchanged existing
        profile on gateway or parsing failure.

        Args:
            existing: The current VoiceProfile to refine.
            feedback: Free-text description of desired changes.

        Returns:
            Updated VoiceProfile with refined fields, or the unchanged existing
            profile on failure.
        """
        if not feedback.strip():
            return existing

        user_prompt = (
            f"Current voice profile:\n{existing.model_dump_json(indent=2)}\n\n"
            f'User feedback: "{feedback}"'
        )

        log.info("fingerprint_refine_start", feedback_length=len(feedback))

        try:
            raw = await call_gateway(REFINE_PROMPT, user_prompt, strategy="quality")
            profile = _parse_profile(raw)
            log.info("fingerprint_refine_done")
            return profile
        except Exception as exc:
            log.warning("fingerprint_refine_failed", error=str(exc))
            return existing
