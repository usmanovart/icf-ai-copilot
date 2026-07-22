"""Copilot router — stub. Full implementation in Sub-Task 3."""
from fastapi import APIRouter, Depends
from core.dependencies import get_current_user
from models.db.models import User

router = APIRouter()


@router.post("/copilot/chat")
async def chat(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.post("/copilot/daily-briefing")
async def daily_briefing(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.post("/copilot/priority-engine")
async def priority_engine(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.post("/copilot/burnout-check")
async def burnout_check(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.post("/copilot/goal-clarity")
async def goal_clarity(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.post("/copilot/habit-builder")
async def habit_builder(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.get("/copilot/conversations")
async def list_conversations(current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}


@router.get("/copilot/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: User = Depends(get_current_user)):
    return {"message": "Not yet implemented — Sub-Task 3"}
