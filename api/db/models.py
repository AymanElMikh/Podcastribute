"""SQLAlchemy ORM models for all database tables.

Uses SQLAlchemy 2.x declarative style with mapped_column and type annotations.
All primary keys are UUIDs generated server-side.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Use JSONB on PostgreSQL (better indexing), fall back to JSON on SQLite (tests).
_JsonB = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class User(Base):
    """Represents a registered SaaS user with subscription plan details."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    plan: Mapped[str] = mapped_column(
        String, nullable=False, default="free"
    )  # free | starter | creator | studio
    episodes_this_month: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    plan_reset_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    episodes: Mapped[list["Episode"]] = relationship("Episode", back_populates="user")
    voice_profile: Mapped["VoiceProfile | None"] = relationship(
        "VoiceProfile", back_populates="user", uselist=False
    )


class VoiceProfile(Base):
    """Stores the extracted voice fingerprint for a user's content generation style."""

    __tablename__ = "voice_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    vocabulary_level: Mapped[str | None] = mapped_column(String, nullable=True)
    sentence_style: Mapped[str | None] = mapped_column(String, nullable=True)
    humor_level: Mapped[str | None] = mapped_column(String, nullable=True)
    twitter_style: Mapped[str | None] = mapped_column(String, nullable=True)
    linkedin_style: Mapped[str | None] = mapped_column(String, nullable=True)
    signature_phrases: Mapped[list[str] | None] = mapped_column(_JsonB, nullable=True)
    topics: Mapped[list[str] | None] = mapped_column(_JsonB, nullable=True)
    words_to_avoid: Mapped[list[str] | None] = mapped_column(_JsonB, nullable=True)
    tone_adjectives: Mapped[list[str] | None] = mapped_column(_JsonB, nullable=True)
    default_cta_style: Mapped[str | None] = mapped_column(String, nullable=True)
    calibration_samples_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="voice_profile")


class Episode(Base):
    """Represents a podcast episode submitted for processing."""

    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # upload | youtube | rss
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="queued"
    )  # queued|transcribing|detecting|generating|ready|error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    processing_completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="episodes")
    moments: Mapped[list["Moment"]] = relationship("Moment", back_populates="episode")
    content_pack: Mapped["ContentPack | None"] = relationship(
        "ContentPack", back_populates="episode", uselist=False
    )
    publish_logs: Mapped[list["PublishLog"]] = relationship(
        "PublishLog", back_populates="episode"
    )


class Moment(Base):
    """A key moment detected in a podcast episode, scored for shareability."""

    __tablename__ = "moments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False
    )
    start_time: Mapped[str | None] = mapped_column(String, nullable=True)
    end_time: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    moment_type: Mapped[str | None] = mapped_column(String, nullable=True)
    shareability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    one_line_hook: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    episode: Mapped["Episode"] = relationship("Episode", back_populates="moments")


class ContentPack(Base):
    """All generated content formats for a single episode."""

    __tablename__ = "content_packs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False
    )

    # Twitter
    twitter_thread: Mapped[list[Any] | None] = mapped_column(_JsonB, nullable=True)
    twitter_hooks: Mapped[list[Any] | None] = mapped_column(_JsonB, nullable=True)
    twitter_listen_tweet: Mapped[str | None] = mapped_column(Text, nullable=True)

    # LinkedIn
    linkedin_post: Mapped[str | None] = mapped_column(Text, nullable=True)
    linkedin_carousel_outline: Mapped[list[Any] | None] = mapped_column(
        _JsonB, nullable=True
    )

    # Newsletter
    newsletter_section: Mapped[str | None] = mapped_column(Text, nullable=True)
    newsletter_subject_lines: Mapped[list[Any] | None] = mapped_column(
        _JsonB, nullable=True
    )

    # Short video
    short_video_scripts: Mapped[list[Any] | None] = mapped_column(_JsonB, nullable=True)

    # Blog post
    blog_post_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    blog_post_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    blog_post_meta: Mapped[str | None] = mapped_column(Text, nullable=True)

    # YouTube
    youtube_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    youtube_chapters: Mapped[list[Any] | None] = mapped_column(_JsonB, nullable=True)

    # Quote cards
    quote_cards: Mapped[list[Any] | None] = mapped_column(_JsonB, nullable=True)

    # Email sequence
    email_sequence: Mapped[list[Any] | None] = mapped_column(_JsonB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    episode: Mapped["Episode"] = relationship("Episode", back_populates="content_pack")


class PublishLog(Base):
    """Audit log of all content publish attempts to external platforms."""

    __tablename__ = "publish_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id"), nullable=False
    )
    platform: Mapped[str | None] = mapped_column(String, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # sent | failed | scheduled
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    episode: Mapped["Episode"] = relationship("Episode", back_populates="publish_logs")
