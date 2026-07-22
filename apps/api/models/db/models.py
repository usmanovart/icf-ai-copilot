"""
SQLAlchemy ORM models — all tables defined in the architecture plan.
pgvector VECTOR columns are declared using pgvector's SQLAlchemy type.
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Boolean, Integer, Float, Text, Date,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from core.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ──────────────────────────────────────────────────────────────────────────────
# ORGANIZATIONS
# ──────────────────────────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    clerk_org_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    settings_data: Mapped[Optional[dict]] = mapped_column("settings", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization")


# ──────────────────────────────────────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="individual")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization: Mapped[Optional["Organization"]] = relationship(back_populates="users")
    consent_records: Mapped[list["ConsentRecord"]] = relationship(back_populates="user")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="user")
    profiles: Mapped[list["Profile"]] = relationship(back_populates="user")
    action_plans: Mapped[list["ActionPlan"]] = relationship(back_populates="user")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")


# ──────────────────────────────────────────────────────────────────────────────
# CONSENT
# ──────────────────────────────────────────────────────────────────────────────

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, nullable=False, default=datetime.utcnow)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    data_uses: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMPTZ, nullable=True)

    user: Mapped["User"] = relationship(back_populates="consent_records")


# ──────────────────────────────────────────────────────────────────────────────
# ASSESSMENTS
# ──────────────────────────────────────────────────────────────────────────────

class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="full")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress")
    started_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMPTZ, nullable=True)

    user: Mapped["User"] = relationship(back_populates="assessments")
    responses: Mapped[list["AssessmentResponse"]] = relationship(back_populates="assessment")
    profiles: Mapped[list["Profile"]] = relationship(back_populates="assessment")


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    question_key: Mapped[str] = mapped_column(String(200), nullable=False)
    response_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    responded_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    assessment: Mapped["Assessment"] = relationship(back_populates="responses")


# ──────────────────────────────────────────────────────────────────────────────
# PROFILES
# ──────────────────────────────────────────────────────────────────────────────

class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Domain data (MVP: 3 domains; future: 6)
    mind_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    goal_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    work_capacity_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    language_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    body_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    scenario_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    global_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Synthesized outputs
    summary_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    risks: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    opportunities: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # pgvector embedding (1536 dims — Granite slate-125m)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="profiles")
    assessment: Mapped[Optional["Assessment"]] = relationship(back_populates="profiles")
    action_plans: Mapped[list["ActionPlan"]] = relationship(back_populates="profile")

    __table_args__ = (
        Index("ix_profiles_user_active", "user_id", "is_active"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# ACTION PLANS & ITEMS
# ──────────────────────────────────────────────────────────────────────────────

class ActionPlan(Base):
    __tablename__ = "action_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="action_plans")
    profile: Mapped[Optional["Profile"]] = relationship(back_populates="action_plans")
    items: Mapped[list["ActionItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("action_plans.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="todo")
    ai_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    framework_refs: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan: Mapped["ActionPlan"] = relationship(back_populates="items")


# ──────────────────────────────────────────────────────────────────────────────
# CONVERSATIONS & MESSAGES
# ──────────────────────────────────────────────────────────────────────────────

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    reasoning: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    has_disclaimer: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


# ──────────────────────────────────────────────────────────────────────────────
# GOVERNANCE & AUDIT
# ──────────────────────────────────────────────────────────────────────────────

class AiAuditLog(Base):
    """Append-only audit log for every LLM call. Never updated or deleted."""
    __tablename__ = "ai_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    model_id: Mapped[str] = mapped_column(String(200), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bias_flags: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    safety_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_user_created", "user_id", "created_at"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# COACH ASSIGNMENTS
# ──────────────────────────────────────────────────────────────────────────────

class CoachAssignment(Base):
    __tablename__ = "coach_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    coach_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("coach_id", "member_id", name="uq_coach_member"),
    )
