"""
Pydantic schemas — shared request/response models for the API.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, field_validator


# ─── Users ────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: uuid.UUID
    clerk_user_id: str
    email: str
    role: str
    org_id: Optional[uuid.UUID]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateIn(BaseModel):
    role: Optional[str] = None


# ─── Consent ──────────────────────────────────────────────────────────────────

class ConsentRecordIn(BaseModel):
    version: str
    data_uses: dict  # e.g. {"ai_processing": true, "org_sharing": false}
    ip_hash: Optional[str] = None


class ConsentRecordOut(BaseModel):
    id: uuid.UUID
    version: str
    consented_at: datetime
    data_uses: dict
    withdrawn_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ─── Assessments ──────────────────────────────────────────────────────────────

class AssessmentStartOut(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    started_at: datetime

    model_config = {"from_attributes": True}


class AssessmentResponseIn(BaseModel):
    module_id: str
    question_key: str
    response_value: Any


class AssessmentCompleteOut(BaseModel):
    assessment_id: uuid.UUID
    status: str
    profile_id: Optional[uuid.UUID] = None
    message: str


# ─── Profiles ─────────────────────────────────────────────────────────────────

class ProfileOut(BaseModel):
    id: uuid.UUID
    version: int
    is_active: bool
    mind_data: Optional[dict]
    goal_data: Optional[dict]
    work_capacity_data: Optional[dict]
    summary_text: Optional[str]
    strengths: Optional[list]
    risks: Optional[list]
    opportunities: Optional[list]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Copilot ──────────────────────────────────────────────────────────────────

# ─── Copilot ──────────────────────────────────────────────────────────────────

class ChatMessageIn(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    context_type: str = "general"
    content: str


class QuickActionIn(BaseModel):
    """Request body for quick-action endpoints (briefing, burnout, etc.)"""
    context: Optional[dict] = None


# ─── Action Plans ─────────────────────────────────────────────────────────────

class ActionItemOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    domain: str
    priority: str
    due_date: Optional[str]
    status: str
    ai_rationale: Optional[str]
    framework_refs: Optional[list]

    model_config = {"from_attributes": True}


class ActionPlanOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    items: List[ActionItemOut] = []

    model_config = {"from_attributes": True}


class ActionItemStatusIn(BaseModel):
    status: str  # todo | in_progress | done | skipped


# ─── Governance ───────────────────────────────────────────────────────────────

class AuditLogEntryOut(BaseModel):
    id: uuid.UUID
    model_id: str
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    confidence_score: Optional[float]
    safety_triggered: bool
    latency_ms: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthOut(BaseModel):
    status: str
    version: str
    env: str
