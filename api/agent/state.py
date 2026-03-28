"""LangGraph state definition for the podcast processing pipeline.

PodcastState is passed between every node in the graph and accumulates
results as the pipeline progresses from transcription to content generation.
"""

from typing import TypedDict


class PodcastState(TypedDict):
    """Full mutable state object threaded through the LangGraph pipeline.

    Each node reads from and writes to specific keys in this state.
    """

    session_id: str
    user_id: str
    episode_id: str
    source_type: str  # upload | youtube | rss
    audio_path: str
    transcript: str
    speaker_segments: list[dict]  # [{speaker, start, end, text}]
    voice_profile: dict  # VoiceProfile as dict
    moments: list[dict]  # detected moments
    content_pack: dict  # all generated content
    status: str
    error: str | None
