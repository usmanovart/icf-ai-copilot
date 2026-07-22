"""
Consent service — record, verify, and withdraw user consent.

Consent is a hard gate: no AI processing may occur without an active,
non-withdrawn consent record for the current document version.
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from core.config import settings
from models.db.models import ConsentRecord, User

logger = structlog.get_logger()


async def get_active_consent(user: User, db: AsyncSession) -> ConsentRecord | None:
    """Return the user's active consent record, or None if none exists / withdrawn."""
    result = await db.execute(
        select(ConsentRecord)
        .where(
            ConsentRecord.user_id == user.id,
            ConsentRecord.version == settings.CONSENT_DOCUMENT_VERSION,
            ConsentRecord.withdrawn_at.is_(None),
        )
        .order_by(ConsentRecord.consented_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def has_active_consent(user: User, db: AsyncSession) -> bool:
    """Quick boolean check used as a dependency guard."""
    return await get_active_consent(user, db) is not None


async def record_consent(
    user: User,
    db: AsyncSession,
    data_uses: dict,
    ip_hash: str | None = None,
) -> ConsentRecord:
    """
    Record explicit consent for the current document version.
    Idempotent: if consent already exists and is not withdrawn, returns existing record.
    """
    existing = await get_active_consent(user, db)
    if existing:
        logger.info("Consent already active", user_id=str(user.id))
        return existing

    record = ConsentRecord(
        user_id=user.id,
        version=settings.CONSENT_DOCUMENT_VERSION,
        consented_at=datetime.utcnow(),
        ip_hash=ip_hash,
        data_uses=data_uses,
    )
    db.add(record)
    await db.flush()
    logger.info("Consent recorded", user_id=str(user.id), version=record.version)
    return record


async def withdraw_consent(user: User, db: AsyncSession) -> None:
    """
    Mark all active consent records as withdrawn.
    Downstream anonymisation pipeline is triggered externally (future sub-task).
    """
    result = await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == user.id,
            ConsentRecord.withdrawn_at.is_(None),
        )
    )
    records = result.scalars().all()
    now = datetime.utcnow()
    for rec in records:
        rec.withdrawn_at = now
    await db.flush()
    logger.info("Consent withdrawn", user_id=str(user.id), count=len(records))
