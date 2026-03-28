"""Voice profile calibration and management routes."""

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import Episode
from api.db.models import VoiceProfile as DBVoiceProfile
from api.db.session import get_db
from api.dependencies import get_current_user
from api.db.models import User
from api.models.voice import (
    CalibrationRequest,
    RefineFeedbackRequest,
    VoiceProfile,
    VoiceProfileUpdate,
)
from api.voice.fingerprint import DEFAULT_VOICE_PROFILE, VoiceFingerprintBuilder

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _db_to_pydantic(db_vp: DBVoiceProfile) -> VoiceProfile:
    """Convert a DB VoiceProfile ORM instance to the Pydantic VoiceProfile model.

    Args:
        db_vp: SQLAlchemy VoiceProfile instance loaded from the database.

    Returns:
        Pydantic VoiceProfile with defaults applied for any null DB fields.
    """
    return VoiceProfile(
        vocabulary_level=db_vp.vocabulary_level or DEFAULT_VOICE_PROFILE.vocabulary_level,
        sentence_style=db_vp.sentence_style or DEFAULT_VOICE_PROFILE.sentence_style,
        humor_level=db_vp.humor_level or DEFAULT_VOICE_PROFILE.humor_level,
        twitter_style=db_vp.twitter_style or DEFAULT_VOICE_PROFILE.twitter_style,
        linkedin_style=db_vp.linkedin_style or DEFAULT_VOICE_PROFILE.linkedin_style,
        signature_phrases=db_vp.signature_phrases or [],
        topics=db_vp.topics or [],
        words_to_avoid=db_vp.words_to_avoid or [],
        tone_adjectives=db_vp.tone_adjectives or [],
        default_cta_style=db_vp.default_cta_style or DEFAULT_VOICE_PROFILE.default_cta_style,
    )


async def _upsert_voice_profile(
    db: AsyncSession,
    user: User,
    profile: VoiceProfile,
    samples_count: int = 0,
) -> DBVoiceProfile:
    """Create or update the voice profile record for a user.

    If a VoiceProfile already exists for this user, all scalar fields are
    overwritten. If none exists, a new record is inserted.

    Args:
        db: Async database session.
        user: Authenticated user who owns the profile.
        profile: Pydantic VoiceProfile with the new field values.
        samples_count: Number of calibration samples used (stored for analytics).

    Returns:
        The updated or newly created DBVoiceProfile ORM instance.
    """
    result = await db.execute(
        select(DBVoiceProfile).where(DBVoiceProfile.user_id == user.id)
    )
    db_vp = result.scalar_one_or_none()

    if db_vp is None:
        db_vp = DBVoiceProfile(user_id=user.id, calibration_samples_count=samples_count)
        db.add(db_vp)
    elif samples_count > 0:
        db_vp.calibration_samples_count = samples_count

    db_vp.vocabulary_level = profile.vocabulary_level
    db_vp.sentence_style = profile.sentence_style
    db_vp.humor_level = profile.humor_level
    db_vp.twitter_style = profile.twitter_style
    db_vp.linkedin_style = profile.linkedin_style
    db_vp.signature_phrases = profile.signature_phrases
    db_vp.topics = profile.topics
    db_vp.words_to_avoid = profile.words_to_avoid
    db_vp.tone_adjectives = profile.tone_adjectives
    db_vp.default_cta_style = profile.default_cta_style

    await db.flush()
    await db.refresh(db_vp)
    return db_vp


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/calibrate/transcripts", response_model=VoiceProfile)
async def calibrate_from_transcripts(
    body: CalibrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfile:
    """Build a voice profile from podcast transcript samples.

    Args:
        body: CalibrationRequest with list of transcript strings.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Generated VoiceProfile saved to the database.

    Raises:
        HTTPException: 422 if no transcripts are provided.
    """
    transcripts = body.transcripts or []
    if not transcripts:
        raise HTTPException(
            status_code=422, detail="At least one transcript is required."
        )

    builder = VoiceFingerprintBuilder()
    profile = await builder.build_from_transcripts(transcripts)
    await _upsert_voice_profile(db, current_user, profile, samples_count=len(transcripts))

    log.info(
        "voice_calibrated",
        user_id=str(current_user.id),
        source="transcripts",
        count=len(transcripts),
    )
    return profile


@router.post("/calibrate/posts", response_model=VoiceProfile)
async def calibrate_from_posts(
    body: CalibrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfile:
    """Build a voice profile from social media post samples.

    Args:
        body: CalibrationRequest with list of social post strings.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Generated VoiceProfile saved to the database.

    Raises:
        HTTPException: 422 if no posts are provided.
    """
    posts = body.posts or []
    if not posts:
        raise HTTPException(
            status_code=422, detail="At least one social post is required."
        )

    builder = VoiceFingerprintBuilder()
    profile = await builder.build_from_social_posts(posts)
    await _upsert_voice_profile(db, current_user, profile, samples_count=len(posts))

    log.info(
        "voice_calibrated",
        user_id=str(current_user.id),
        source="social_posts",
        count=len(posts),
    )
    return profile


@router.post("/calibrate/episodes", response_model=VoiceProfile)
async def calibrate_from_episodes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfile:
    """Build a voice profile from the user's previously processed episodes.

    Fetches transcript data from the user's episode history (up to 5 episodes
    with completed transcripts).

    Args:
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Generated VoiceProfile saved to the database.

    Raises:
        HTTPException: 404 if the user has no transcribed episodes yet.
    """
    result = await db.execute(
        select(Episode.transcript)
        .where(
            Episode.user_id == current_user.id,
            Episode.transcript.isnot(None),
            Episode.status == "ready",
        )
        .limit(5)
    )
    transcripts = [row[0] for row in result.fetchall() if row[0]]

    if not transcripts:
        raise HTTPException(
            status_code=404,
            detail=(
                "No transcribed episodes found. "
                "Process at least one episode before calibrating from episodes."
            ),
        )

    builder = VoiceFingerprintBuilder()
    profile = await builder.build_from_transcripts(transcripts)
    await _upsert_voice_profile(db, current_user, profile, samples_count=len(transcripts))

    log.info(
        "voice_calibrated",
        user_id=str(current_user.id),
        source="episodes",
        count=len(transcripts),
    )
    return profile


@router.put("/refine", response_model=VoiceProfile)
async def refine_voice_profile(
    body: RefineFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfile:
    """Refine the voice profile based on natural language feedback.

    Args:
        body: RefineFeedbackRequest with the user's feedback string.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Updated VoiceProfile.
    """
    result = await db.execute(
        select(DBVoiceProfile).where(DBVoiceProfile.user_id == current_user.id)
    )
    db_vp = result.scalar_one_or_none()
    existing = _db_to_pydantic(db_vp) if db_vp else DEFAULT_VOICE_PROFILE

    builder = VoiceFingerprintBuilder()
    refined = await builder.refine(existing, body.feedback)
    await _upsert_voice_profile(db, current_user, refined)

    log.info("voice_refined", user_id=str(current_user.id))
    return refined


@router.get("", response_model=VoiceProfile)
async def get_voice_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfile:
    """Retrieve the current user's voice profile.

    Returns the DEFAULT_VOICE_PROFILE if the user has not yet calibrated.

    Args:
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Current VoiceProfile or the default profile if not yet calibrated.
    """
    result = await db.execute(
        select(DBVoiceProfile).where(DBVoiceProfile.user_id == current_user.id)
    )
    db_vp = result.scalar_one_or_none()
    if db_vp is None:
        return DEFAULT_VOICE_PROFILE
    return _db_to_pydantic(db_vp)


@router.put("", response_model=VoiceProfile)
async def update_voice_profile(
    body: VoiceProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VoiceProfile:
    """Manually override specific voice profile fields.

    Only fields explicitly set in the request body are updated; all others
    retain their existing values.

    Args:
        body: VoiceProfileUpdate with only the fields to change.
        current_user: Authenticated user from JWT.
        db: Async database session.

    Returns:
        Updated VoiceProfile.
    """
    result = await db.execute(
        select(DBVoiceProfile).where(DBVoiceProfile.user_id == current_user.id)
    )
    db_vp = result.scalar_one_or_none()
    existing = _db_to_pydantic(db_vp) if db_vp else DEFAULT_VOICE_PROFILE

    # Apply only the non-None fields from the update request
    updates = body.model_dump(exclude_none=True)
    merged = existing.model_copy(update=updates)

    await _upsert_voice_profile(db, current_user, merged)

    log.info(
        "voice_updated",
        user_id=str(current_user.id),
        fields=list(updates.keys()),
    )
    return merged
