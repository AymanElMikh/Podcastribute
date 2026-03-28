"""Pydantic models for episode ingestion and processing results."""

from datetime import datetime

from pydantic import BaseModel


class EpisodeCreate(BaseModel):
    """Request body for creating an episode record."""

    title: str
    source_type: str  # upload | youtube | rss
    source_url: str | None = None


class EpisodeResponse(BaseModel):
    """Public-facing episode data returned from API responses."""

    id: str
    title: str
    status: str
    source_type: str
    duration_seconds: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TranscriptResult(BaseModel):
    """Output of the audio transcription process."""

    text: str
    segments: list[dict]
    duration_seconds: int
    language: str


class YouTubeIngestRequest(BaseModel):
    """Request body for YouTube episode ingestion."""

    url: str


class RSSIngestRequest(BaseModel):
    """Request body for RSS feed episode ingestion."""

    feed_url: str
    episode_index: int = 0
