"""Pydantic models for generated content packs."""

from pydantic import BaseModel


class ContentPackResponse(BaseModel):
    """All 8 generated content formats for a single episode."""

    episode_id: str
    twitter: dict
    linkedin: dict
    newsletter: dict
    short_video: dict
    blog_post: dict
    youtube: dict
    quote_cards: dict
    email_sequence: dict
