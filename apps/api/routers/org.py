"""Org workspace router — stub. Full implementation in Sub-Task 5."""
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user, require_role
from models.db.models import User

router = APIRouter()


@router.get("/org/members")
async def list_members(current_user: User = Depends(require_role("org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}


@router.post("/org/invite", status_code=201)
async def invite_member(current_user: User = Depends(require_role("org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}


@router.delete("/org/members/{user_id}", status_code=204)
async def remove_member(user_id: str, current_user: User = Depends(require_role("org_admin", "super_admin"))):
    return None


@router.get("/org/insights")
async def org_insights(current_user: User = Depends(require_role("org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}


@router.get("/org/analytics")
async def org_analytics(current_user: User = Depends(require_role("org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}
