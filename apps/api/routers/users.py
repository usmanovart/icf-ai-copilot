from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models.db.models import User
from models.schemas.schemas import UserOut

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return current_user


@router.patch("/users/me", response_model=UserOut)
async def update_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences (stub — expanded in later sub-tasks)."""
    return current_user
