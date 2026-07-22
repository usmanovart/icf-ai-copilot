"""
Clerk webhook handler.

Verifies the svix signature and syncs user/org events to PostgreSQL.
Events handled:
  - user.created
  - user.updated
  - organizationMembership.created
  - organization.created
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from core.config import settings
from core.database import get_db
from models.db.models import User, Organization

router = APIRouter()
logger = structlog.get_logger()


async def _verify_svix_signature(request: Request) -> dict:
    """Verify the webhook came from Clerk using svix signature headers."""
    try:
        from svix.webhooks import Webhook
        payload = await request.body()
        headers = dict(request.headers)
        wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
        return wh.verify(payload, headers)  # type: ignore
    except Exception as exc:
        logger.warning("Webhook signature verification failed", error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")


@router.post("/auth/webhook")
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives Clerk webhook events and keeps the local user/org tables in sync.
    This is the only endpoint that does NOT require a Bearer token.
    """
    event = await _verify_svix_signature(request)
    event_type = event.get("type", "")
    data = event.get("data", {})

    logger.info("Clerk webhook received", event_type=event_type)

    if event_type == "user.created":
        await _upsert_user(db, data)

    elif event_type == "user.updated":
        await _upsert_user(db, data)

    elif event_type == "organization.created":
        await _upsert_organization(db, data)

    elif event_type == "organizationMembership.created":
        await _handle_membership(db, data)

    return Response(status_code=200)


async def _upsert_user(db: AsyncSession, data: dict) -> None:
    clerk_user_id = data.get("id", "")
    email = ""
    if data.get("email_addresses"):
        email = data["email_addresses"][0].get("email_address", "")

    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            clerk_user_id=clerk_user_id,
            email=email,
            role="individual",
        )
        db.add(user)
        logger.info("User created from webhook", clerk_user_id=clerk_user_id)
    else:
        user.email = email
        logger.info("User updated from webhook", clerk_user_id=clerk_user_id)

    await db.flush()


async def _upsert_organization(db: AsyncSession, data: dict) -> None:
    clerk_org_id = data.get("id", "")
    name = data.get("name", "Unnamed Organization")

    result = await db.execute(select(Organization).where(Organization.clerk_org_id == clerk_org_id))
    org = result.scalar_one_or_none()

    if org is None:
        org = Organization(clerk_org_id=clerk_org_id, name=name)
        db.add(org)
        logger.info("Organization created from webhook", clerk_org_id=clerk_org_id)

    await db.flush()


async def _handle_membership(db: AsyncSession, data: dict) -> None:
    """Link a user to an org when they join."""
    clerk_user_id = data.get("public_user_data", {}).get("user_id", "")
    clerk_org_id = data.get("organization", {}).get("id", "")
    role = data.get("role", "org:member")

    if not clerk_user_id or not clerk_org_id:
        return

    user_result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = user_result.scalar_one_or_none()

    org_result = await db.execute(select(Organization).where(Organization.clerk_org_id == clerk_org_id))
    org = org_result.scalar_one_or_none()

    if user and org:
        user.org_id = org.id
        # Map Clerk org roles to our internal roles
        if role == "org:admin":
            user.role = "org_admin"
        elif role in ("org:coach", "org:tutor"):
            user.role = "coach"
        logger.info("Membership linked", clerk_user_id=clerk_user_id, org=clerk_org_id, role=role)

    await db.flush()
