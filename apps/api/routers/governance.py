"""Governance router — stub. Full implementation in Sub-Task 4."""
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from models.db.models import User

router = APIRouter()


@router.get("/governance/audit-log")
async def audit_log(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}


@router.get("/governance/explain/{message_id}")
async def explain_message(message_id: str, current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}


@router.get("/governance/bias-report")
async def bias_report(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}
