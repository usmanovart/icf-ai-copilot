"""
Assessment service — module loading, response scoring, and domain mapping.

Scoring rules per module type:
  - likert5 / sum_normalised : sum all non-reverse items; reverse-scored items are
                                subtracted from max_value (4) before summing
  - likert5 / mean_per_dimension: mean of items within each named dimension
  - scale10 : value stored as-is (0–10), normalised to 0.0–1.0
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from models.db.models import Assessment, AssessmentResponse, User

logger = structlog.get_logger()

# ── Module configs loaded once at import time ──────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data" / "assessment_modules"
_MODULE_ORDER = [
    "mind_stress",
    "mind_big_five",
    "goal_clarity",
    "work_capacity_burnout",
]

def _load_modules() -> dict[str, dict]:
    modules: dict[str, dict] = {}
    for mid in _MODULE_ORDER:
        path = _DATA_DIR / f"{mid}.json"
        if path.exists():
            modules[mid] = json.loads(path.read_text(encoding="utf-8"))
    return modules

MODULES: dict[str, dict] = _load_modules()


# ── Module API ─────────────────────────────────────────────────────────────────

def list_modules() -> list[dict]:
    """Return ordered module configs (questions omitted for brevity in list view)."""
    return [
        {
            "module_id": m["module_id"],
            "domain": m["domain"],
            "title": m["title"],
            "description": m["description"],
            "estimated_minutes": m["estimated_minutes"],
            "question_count": len(m["questions"]),
            "disclaimer": m.get("disclaimer"),
        }
        for m in MODULES.values()
    ]


def get_module(module_id: str) -> dict:
    if module_id not in MODULES:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")
    return MODULES[module_id]


# ── Assessment lifecycle ───────────────────────────────────────────────────────

async def start_assessment(user: User, db: AsyncSession) -> Assessment:
    """Create a new in-progress assessment session."""
    assessment = Assessment(user_id=user.id, type="full", status="in_progress")
    db.add(assessment)
    await db.flush()
    logger.info("Assessment started", assessment_id=str(assessment.id), user_id=str(user.id))
    return assessment


async def get_assessment(
    assessment_id: uuid.UUID, user: User, db: AsyncSession
) -> Assessment:
    result = await db.execute(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.user_id == user.id,
        )
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


async def store_responses(
    assessment_id: uuid.UUID,
    module_id: str,
    responses: list[dict],  # [{question_key, response_value}]
    user: User,
    db: AsyncSession,
) -> list[AssessmentResponse]:
    """Persist a batch of responses for one module."""
    assessment = await get_assessment(assessment_id, user, db)
    if assessment.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment is not in progress",
        )

    module = get_module(module_id)
    domain = module["domain"]
    stored: list[AssessmentResponse] = []

    for resp in responses:
        ar = AssessmentResponse(
            assessment_id=assessment.id,
            domain=domain,
            module=module_id,
            question_key=resp["question_key"],
            response_value={"value": resp["response_value"]},
        )
        db.add(ar)
        stored.append(ar)

    await db.flush()
    logger.info(
        "Responses stored",
        assessment_id=str(assessment_id),
        module=module_id,
        count=len(stored),
    )
    return stored


async def complete_assessment(
    assessment_id: uuid.UUID, user: User, db: AsyncSession
) -> Assessment:
    """Mark assessment as completed."""
    assessment = await get_assessment(assessment_id, user, db)
    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()
    await db.flush()
    logger.info("Assessment completed", assessment_id=str(assessment_id))
    return assessment


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_assessment(responses: list[AssessmentResponse]) -> dict[str, Any]:
    """
    Compute domain scores from raw responses.
    Returns a dict keyed by domain, each containing dimension/facet sub-scores
    and a normalised overall score (0.0–1.0).
    """
    # Group responses by module
    by_module: dict[str, list[AssessmentResponse]] = {}
    for r in responses:
        by_module.setdefault(r.module, []).append(r)

    domain_scores: dict[str, Any] = {}

    for module_id, module_responses in by_module.items():
        if module_id not in MODULES:
            continue
        module = MODULES[module_id]
        scoring_type = module["scoring"]
        questions = {q["key"]: q for q in module["questions"]}

        if scoring_type == "sum_normalised":
            domain_scores[module_id] = _score_sum_normalised(
                module_responses, questions, module["score_range"]
            )
        elif scoring_type in ("mean_per_dimension", "likert_mean_per_facet"):
            dim_key = "dimension" if "dimension" in module["questions"][0] else "facet"
            domain_scores[module_id] = _score_mean_per_dimension(
                module_responses, questions, dim_key
            )

    # Aggregate into top-level domain buckets
    return _aggregate_to_domains(domain_scores)


def _score_sum_normalised(
    responses: list[AssessmentResponse],
    questions: dict,
    score_range: list[int],
) -> dict:
    raw_sum = 0
    for r in responses:
        q = questions.get(r.question_key)
        if not q:
            continue
        val = r.response_value.get("value", 0)
        if isinstance(val, int):
            if q.get("reverse_scored"):
                val = 4 - val  # Likert 5-point reverse: 0-4 scale
            raw_sum += val

    max_possible = score_range[1]
    normalised = round(raw_sum / max_possible, 3) if max_possible else 0.0
    return {"raw_score": raw_sum, "normalised": normalised}


def _score_mean_per_dimension(
    responses: list[AssessmentResponse],
    questions: dict,
    dim_key: str,
) -> dict:
    dim_totals: dict[str, list[float]] = {}
    for r in responses:
        q = questions.get(r.question_key)
        if not q:
            continue
        dim = q.get(dim_key, "unknown")
        val = r.response_value.get("value", 0)
        if isinstance(val, (int, float)):
            # Likert 5-point: map 1-5 input to 0.0-1.0
            if q.get("type") == "scale10":
                normalised_val = val / 10.0
            else:
                # 0-indexed likert (0=Never, 4=Always) → 0.0–1.0
                normalised_val = val / 4.0
            if q.get("reverse_scored"):
                normalised_val = 1.0 - normalised_val
            dim_totals.setdefault(dim, []).append(normalised_val)

    dim_means = {
        dim: round(sum(vals) / len(vals), 3)
        for dim, vals in dim_totals.items()
        if vals
    }
    overall = round(sum(dim_means.values()) / len(dim_means), 3) if dim_means else 0.0
    return {"dimensions": dim_means, "overall": overall}


def _aggregate_to_domains(module_scores: dict) -> dict:
    """Roll up module scores into the three top-level domains."""
    mind_modules = ["mind_stress", "mind_big_five"]
    goal_modules = ["goal_clarity"]
    work_modules = ["work_capacity_burnout"]

    def _domain_summary(module_ids: list[str]) -> dict:
        relevant = {k: v for k, v in module_scores.items() if k in module_ids}
        if not relevant:
            return {"modules": {}, "overall": 0.0}
        overalls = []
        for v in relevant.values():
            if "normalised" in v:
                overalls.append(v["normalised"])
            elif "overall" in v:
                overalls.append(v["overall"])
        overall = round(sum(overalls) / len(overalls), 3) if overalls else 0.0
        return {"modules": relevant, "overall": overall}

    return {
        "mind": _domain_summary(mind_modules),
        "goal": _domain_summary(goal_modules),
        "work_capacity": _domain_summary(work_modules),
    }
