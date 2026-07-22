"""Plans router — stub. Full implementation in Sub-Task 4."""
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from models.db.models import User

router = APIRouter()


@router.get("/plans")
async def list_plans(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}


@router.post("/plans/generate", status_code=201)
async def generate_plan(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}


@router.patch("/plans/{plan_id}/items/{item_id}")
async def update_item(plan_id: str, item_id: str, current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 4"}


@router.delete("/plans/{plan_id}", status_code=204)
async def archive_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    return None
