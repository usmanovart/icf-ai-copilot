"""
Profiles router — serve multidimensional profile data and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from core.database import get_db
from core.dependencies import get_current_user
from models.db.models import User
from models.schemas.schemas import ProfileOut
from services import profile_service, consent_service

router = APIRouter()


@router.get("/profiles/me", response_model=ProfileOut)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's current active profile."""
    profile = await profile_service.get_active_profile(current_user, db)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active profile found. Complete an assessment to generate your profile.",
        )
    return profile


@router.get("/profiles/{profile_id}", response_model=ProfileOut)
async def get_profile_by_id(
    profile_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a specific profile version."""
    profile = await profile_service.get_profile_by_id(profile_id, current_user, db)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.get("/profiles/me/insights")
async def get_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a structured insights summary: strengths, risks, opportunities,
    and framework references from the active profile.
    """
    profile = await profile_service.get_active_profile(current_user, db)
    if not profile:
        raise HTTPException(status_code=404, detail="No active profile found")

    return {
        "profile_id": str(profile.id),
        "version": profile.version,
        "summary": profile.summary_text,
        "strengths": profile.strengths or [],
        "risks": profile.risks or [],
        "opportunities": profile.opportunities or [],
        "domains": {
            "mind": profile.mind_data,
            "goal": profile.goal_data,
            "work_capacity": profile.work_capacity_data,
        },
    }


@router.post("/profiles/me/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger profile re-generation from the most recent completed assessment.
    Returns 202 — generation runs synchronously but may be moved to a background
    task in production.
    """
    from sqlalchemy import select
    from models.db.models import Assessment

    # Find most recent completed assessment
    result = await db.execute(
        select(Assessment)
        .where(
            Assessment.user_id == current_user.id,
            Assessment.status == "completed",
        )
        .order_by(Assessment.completed_at.desc())
        .limit(1)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(
            status_code=404,
            detail="No completed assessment found. Complete an assessment first.",
        )

    profile = await profile_service.build_profile_from_assessment(
        assessment_id=assessment.id,
        user=current_user,
        db=db,
    )
    return {
        "message": "Profile regenerated",
        "profile_id": str(profile.id),
        "version": profile.version,
    }
