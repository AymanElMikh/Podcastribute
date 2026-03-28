"""Pydantic models for voice fingerprint profiles and calibration requests."""

from pydantic import BaseModel


class VoiceProfile(BaseModel):
    """Complete voice fingerprint describing a podcaster's unique communication style."""

    vocabulary_level: str = "conversational"
    sentence_style: str = "conversational"
    humor_level: str = "occasional"
    twitter_style: str = "educator"
    linkedin_style: str = "personal_story"
    signature_phrases: list[str] = []
    topics: list[str] = []
    words_to_avoid: list[str] = []
    tone_adjectives: list[str] = []
    default_cta_style: str = "value_first"


class VoiceProfileUpdate(BaseModel):
    """Partial update for a user's voice profile — all fields optional."""

    vocabulary_level: str | None = None
    sentence_style: str | None = None
    humor_level: str | None = None
    twitter_style: str | None = None
    linkedin_style: str | None = None
    signature_phrases: list[str] | None = None
    topics: list[str] | None = None
    words_to_avoid: list[str] | None = None
    tone_adjectives: list[str] | None = None
    default_cta_style: str | None = None


class CalibrationRequest(BaseModel):
    """Request body for voice profile calibration from text samples.

    Either transcripts or posts must be provided.
    """

    transcripts: list[str] | None = None
    posts: list[str] | None = None


class RefineFeedbackRequest(BaseModel):
    """Request body for refining a voice profile via natural language feedback."""

    feedback: str
