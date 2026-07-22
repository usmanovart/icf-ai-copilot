"""
Profile service — orchestrates assessment scoring, Granite synthesis,
pgvector embedding, and profile persistence.
"""

import uuid
from datetime import datetime
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.db.models import Profile, Assessment, AssessmentResponse, User
from services import assessment_service, ai_service, vector_service

logger = structlog.get_logger()


async def get_active_profile(user: User, db: AsyncSession) -> Profile | None:
    """Return the user's current active profile, or None."""
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == user.id, Profile.is_active.is_(True))
        .order_by(Profile.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_profile_by_id(
    profile_id: uuid.UUID, user: User, db: AsyncSession
) -> Profile | None:
    result = await db.execute(
        select(Profile).where(
            Profile.id == profile_id,
            Profile.user_id == user.id,
        )
    )
    return result.scalar_one_or_none()


async def build_profile_from_assessment(
    assessment_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> Profile:
    """
    Full profile generation pipeline:
      1. Load assessment responses
      2. Score all modules → domain scores
      3. Call Granite to synthesise the profile JSON
      4. Deactivate previous active profile
      5. Persist new profile with domain data
      6. Generate and store pgvector embedding
      7. Return the new Profile ORM object
    """
    # 1. Load responses
    result = await db.execute(
        select(AssessmentResponse).where(
            AssessmentResponse.assessment_id == assessment_id
        )
    )
    responses = result.scalars().all()
    if not responses:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No responses found for this assessment")

    # 2. Score
    domain_scores = assessment_service.score_assessment(list(responses))
    logger.info("Assessment scored", assessment_id=str(assessment_id))

    # 3. Granite synthesis
    profile_data = await ai_service.generate_profile(domain_scores)
    logger.info("Profile synthesised", assessment_id=str(assessment_id))

    # 4. Deactivate previous active profiles for this user
    prev_result = await db.execute(
        select(Profile).where(
            Profile.user_id == user.id,
            Profile.is_active.is_(True),
        )
    )
    prev_profiles = prev_result.scalars().all()
    for p in prev_profiles:
        p.is_active = False
    await db.flush()

    # Determine next version number
    next_version = len(prev_profiles) + 1

    # 5. Persist new profile
    profile = Profile(
        user_id=user.id,
        assessment_id=assessment_id,
        version=next_version,
        is_active=True,
        mind_data=profile_data.get("mind_data"),
        goal_data=profile_data.get("goal_data"),
        work_capacity_data=profile_data.get("work_capacity_data"),
        summary_text=profile_data.get("summary_text"),
        strengths=profile_data.get("strengths"),
        risks=profile_data.get("risks"),
        opportunities=profile_data.get("opportunities"),
    )
    db.add(profile)
    await db.flush()  # gets profile.id assigned

    # 6. Embed + store in pgvector
    if profile_data.get("summary_text"):
        await vector_service.upsert_profile_embedding(
            profile_id=profile.id,
            summary_text=profile_data["summary_text"],
            db=db,
        )

    logger.info(
        "Profile created",
        profile_id=str(profile.id),
        version=profile.version,
        user_id=str(user.id),
    )
    return profile
