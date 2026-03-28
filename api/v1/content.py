"""Content retrieval and management routes."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import ContentPack, Episode
from api.db.session import get_db
from api.dependencies import get_current_user
from api.models.content import ContentPackResponse

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/{episode_id}", response_model=ContentPackResponse)
async def get_content_pack(
    episode_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ContentPackResponse:
    """Retrieve the full generated content pack for an episode.

    Args:
        episode_id: UUID of the episode whose content to retrieve.
        db: Async database session.
        current_user: Authenticated user from JWT.

    Returns:
        ContentPackResponse with all 8 format outputs.

    Raises:
        HTTPException: 422 if episode_id is not a valid UUID.
        HTTPException: 404 if episode not found or content not yet ready.
        HTTPException: 403 if episode belongs to a different user.
    """
    try:
        ep_uuid = uuid.UUID(episode_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid episode_id format")

    result = await db.execute(
        select(Episode).where(Episode.id == ep_uuid)
    )
    episode = result.scalar_one_or_none()
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")

    if episode.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    pack_result = await db.execute(
        select(ContentPack).where(ContentPack.episode_id == ep_uuid)
    )
    pack = pack_result.scalar_one_or_none()
    if pack is None:
        raise HTTPException(
            status_code=404,
            detail="Content pack not ready yet. Check episode status.",
        )

    return ContentPackResponse(
        episode_id=str(episode.id),
        twitter={
            "main_thread": pack.twitter_thread or [],
            "standalone_hooks": pack.twitter_hooks or [],
            "listen_tweet": pack.twitter_listen_tweet or "",
        },
        linkedin={
            "post": pack.linkedin_post or "",
            "carousel_outline": pack.linkedin_carousel_outline or [],
            "post_hooks": [],
        },
        newsletter={
            "section_title": "",
            "section_body": pack.newsletter_section or "",
            "subject_lines": pack.newsletter_subject_lines or [],
            "preview_text": "",
        },
        short_video={
            "clips": pack.short_video_scripts or [],
        },
        blog_post={
            "title": pack.blog_post_title or "",
            "meta_description": pack.blog_post_meta or "",
            "outline": [],
            "body": pack.blog_post_body or "",
            "internal_link_suggestions": [],
            "target_keywords": [],
        },
        youtube={
            "description": pack.youtube_description or "",
            "chapters": pack.youtube_chapters or [],
            "tags": [],
            "end_screen_script": "",
        },
        quote_cards={
            "quotes": pack.quote_cards or [],
        },
        email_sequence={
            "emails": pack.email_sequence or [],
        },
    )
