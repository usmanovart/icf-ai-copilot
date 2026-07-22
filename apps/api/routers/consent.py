"""
Consent router — record, verify, and withdraw user consent.
Consent is a hard gate required before any assessment or AI processing.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib

from core.database import get_db
from core.dependencies import get_current_user
from core.config import settings
from models.db.models import User
from models.schemas.schemas import ConsentRecordIn, ConsentRecordOut
from services import consent_service

router = APIRouter()


@router.get("/consent/current", response_model=ConsentRecordOut | None)
async def get_consent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the user's active consent record, or null if none exists."""
    return await consent_service.get_active_consent(current_user, db)


@router.post("/consent/record", response_model=ConsentRecordOut, status_code=status.HTTP_201_CREATED)
async def record_consent(
    body: ConsentRecordIn,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Record explicit informed consent for the current document version.
    The client IP is hashed (SHA-256) before storage — raw IPs are never persisted.
    """
    client_ip = request.client.host if request.client else None
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest() if client_ip else None

    record = await consent_service.record_consent(
        user=current_user,
        db=db,
        data_uses=body.data_uses,
        ip_hash=ip_hash,
    )
    return record


@router.delete("/consent/withdraw", status_code=status.HTTP_204_NO_CONTENT)
async def withdraw_consent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Withdraw all active consent records for this user.
    Triggers anonymisation pipeline (implemented in Sub-Task 5).
    """
    await consent_service.withdraw_consent(current_user, db)
    return None
