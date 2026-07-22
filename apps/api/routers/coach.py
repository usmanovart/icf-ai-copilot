"""Coach portal router — stub. Full implementation in Sub-Task 5."""
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user, require_role
from models.db.models import User

router = APIRouter()


@router.get("/coach/cohort")
async def get_cohort(current_user: User = Depends(require_role("coach", "org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}


@router.get("/coach/cohort/{user_id}/summary")
async def member_summary(
    user_id: str,
    current_user: User = Depends(require_role("coach", "org_admin", "super_admin")),
):
    return {"message": "Not yet implemented — Sub-Task 5"}


@router.get("/coach/aggregate-insights")
async def aggregate_insights(current_user: User = Depends(require_role("coach", "org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}


@router.post("/coach/assignments", status_code=201)
async def create_assignment(current_user: User = Depends(require_role("coach", "org_admin", "super_admin"))):
    return {"message": "Not yet implemented — Sub-Task 5"}
