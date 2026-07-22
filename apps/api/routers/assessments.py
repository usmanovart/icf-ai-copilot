"""
Assessments router — full assessment lifecycle with consent gate.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from core.database import get_db
from core.dependencies import get_current_user
from models.db.models import User, Assessment, AssessmentResponse
from models.schemas.schemas import (
    AssessmentStartOut,
    AssessmentResponseIn,
    AssessmentCompleteOut,
)
from services import assessment_service, consent_service, profile_service

router = APIRouter()


def _require_consent(current_user: User, db: AsyncSession):
    """Inline consent dependency (async-safe via separate check)."""
    return current_user, db


@router.get("/assessments/modules")
async def list_modules(current_user: User = Depends(get_current_user)):
    """Return all assessment module configs (ordered)."""
    return {"modules": assessment_service.list_modules()}


@router.get("/assessments/modules/{module_id}")
async def get_module(
    module_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return full module config including questions."""
    return assessment_service.get_module(module_id)


@router.post(
    "/assessments/start",
    response_model=AssessmentStartOut,
    status_code=status.HTTP_201_CREATED,
)
async def start_assessment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Begin a new assessment session.
    Requires active consent — returns 403 if no consent record exists.
    """
    if not await consent_service.has_active_consent(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active consent is required before starting an assessment. "
                   "Please record your consent at POST /consent/record.",
        )
    assessment = await assessment_service.start_assessment(current_user, db)
    return assessment


@router.put("/assessments/{assessment_id}/respond")
async def submit_responses(
    assessment_id: uuid.UUID,
    body: list[AssessmentResponseIn],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit responses for one module.
    Body is a list of {module_id, question_key, response_value} objects.
    All items must belong to the same module.
    """
    if not body:
        raise HTTPException(status_code=400, detail="No responses provided")

    # Validate all items share the same module_id
    module_ids = {r.module_id for r in body}
    if len(module_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail="All responses in one request must belong to the same module_id.",
        )
    module_id = module_ids.pop()
    responses_dicts = [
        {"question_key": r.question_key, "response_value": r.response_value}
        for r in body
    ]
    await assessment_service.store_responses(
        assessment_id=assessment_id,
        module_id=module_id,
        responses=responses_dicts,
        user=current_user,
        db=db,
    )
    return {"assessment_id": str(assessment_id), "module_id": module_id, "stored": len(responses_dicts)}


@router.post("/assessments/{assessment_id}/complete", response_model=AssessmentCompleteOut)
async def complete_assessment(
    assessment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize the assessment session and trigger profile generation.
    Returns the newly created profile_id.
    """
    assessment = await assessment_service.complete_assessment(assessment_id, current_user, db)

    # Trigger profile generation pipeline
    profile = await profile_service.build_profile_from_assessment(
        assessment_id=assessment.id,
        user=current_user,
        db=db,
    )

    return AssessmentCompleteOut(
        assessment_id=assessment.id,
        status="completed",
        profile_id=profile.id,
        message="Assessment complete. Your AI profile has been generated.",
    )


@router.get("/assessments/history")
async def assessment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's assessment history (most recent first)."""
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == current_user.id)
        .order_by(Assessment.started_at.desc())
    )
    assessments = result.scalars().all()
    return {
        "assessments": [
            {
                "id": str(a.id),
                "type": a.type,
                "status": a.status,
                "started_at": a.started_at.isoformat(),
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            }
            for a in assessments
        ]
    }
