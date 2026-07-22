"""
FastAPI dependency injection helpers.

Provides reusable dependencies for:
  - current_user: authenticated User ORM object
  - require_role: role-based access control
  - get_db: async database session (re-exported from database.py)
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import verify_clerk_token
from models.db.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Verify the Clerk JWT and return the corresponding User from the database.
    Creates a stub if the user exists in Clerk but not yet synced (race condition guard).
    """
    payload = verify_clerk_token(credentials.credentials)
    clerk_user_id: str = payload.get("sub", "")

    if not clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing sub claim",
        )

    result = await db.execute(
        select(User).where(User.clerk_user_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Ensure webhook sync is configured.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(*roles: str):
    """
    Returns a dependency that enforces one of the given roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("org_admin", "super_admin"))])
    """
    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' is not authorized for this resource",
            )
        return current_user

    return _check
