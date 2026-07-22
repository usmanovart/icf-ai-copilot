"""
AI service — IBM Granite LangChain integration.

MVP: LangChain LCEL chains per use-case.
Phase 2: Migrates to LangGraph ICFAgentState multi-agent graph.

All LLM calls are wrapped by the governance_service (Sub-Task 4).
Credentials not set → raises a clear error pointing to .env.
"""

import json
import structlog
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from core.config import settings

logger = structlog.get_logger()


def _get_llm():
    """Lazily build the watsonx.ai Granite LLM client."""
    if not settings.WATSONX_API_KEY or not settings.WATSONX_PROJECT_ID:
        raise RuntimeError(
            "IBM watsonx credentials not configured. "
            "Set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file."
        )
    from langchain_ibm import WatsonxLLM
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames

    return WatsonxLLM(
        model_id=settings.WATSONX_LLM_MODEL_ID,
        url=settings.WATSONX_URL,
        apikey=settings.WATSONX_API_KEY,
        project_id=settings.WATSONX_PROJECT_ID,
        params={
            GenTextParamsMetaNames.MAX_NEW_TOKENS: 1024,
            GenTextParamsMetaNames.TEMPERATURE: 0.3,
            GenTextParamsMetaNames.REPETITION_PENALTY: 1.1,
        },
    )


# ── Profile generation ─────────────────────────────────────────────────────────

PROFILE_SYSTEM_PROMPT = """\
You are the ICF AI Copilot profile synthesis engine.

Your task is to analyse assessment scores and generate a structured, evidence-informed
multidimensional profile for this user.

HARD CONSTRAINTS:
1. You must NEVER diagnose, suggest, or imply any medical or mental health diagnosis.
2. Frame all observations as reflections and patterns, not clinical findings.
3. Use evidence-informed frameworks as lenses: Big Five personality, Self-Determination Theory,
   Maslach burnout dimensions, cognitive load theory, Goal-Setting Theory.
4. Be specific, actionable, and grounded in the score data provided.
5. Return ONLY valid JSON matching the schema below. No markdown, no prose, only JSON.

OUTPUT SCHEMA:
{{
  "summary_text": "2-3 sentence narrative overview of the user's profile",
  "mind_data": {{
    "stress_level": "low|moderate|high",
    "stress_score_normalised": 0.0,
    "cognitive_load": "low|moderate|high",
    "big_five": {{
      "openness": 0.0,
      "conscientiousness": 0.0,
      "extraversion": 0.0,
      "agreeableness": 0.0,
      "neuroticism": 0.0
    }},
    "key_observations": ["observation 1", "observation 2"]
  }},
  "goal_data": {{
    "clarity_score": 0.0,
    "sdt_autonomy": 0.0,
    "sdt_competence": 0.0,
    "sdt_relatedness": 0.0,
    "goal_commitment": 0.0,
    "values_alignment": "low|moderate|high",
    "key_observations": ["observation 1", "observation 2"]
  }},
  "work_capacity_data": {{
    "burnout_risk": "low|moderate|high",
    "exhaustion_score": 0.0,
    "depersonalisation_score": 0.0,
    "efficacy_score": 0.0,
    "energy_level": 0.0,
    "focus_capacity": 0.0,
    "key_observations": ["observation 1", "observation 2"]
  }},
  "strengths": [
    {{"label": "strength label", "domain": "mind|goal|work_capacity", "rationale": "why this is a strength", "framework_ref": "e.g. Big Five:conscientiousness"}}
  ],
  "risks": [
    {{"label": "risk label", "domain": "mind|goal|work_capacity", "severity": "low|moderate|high", "rationale": "why this is a risk", "framework_ref": "e.g. Maslach:exhaustion"}}
  ],
  "opportunities": [
    {{"label": "opportunity label", "domain": "mind|goal|work_capacity", "rationale": "how to leverage this", "framework_ref": "e.g. SDT:autonomy"}}
  ]
}}
"""

PROFILE_USER_PROMPT = """\
Assessment domain scores:

{domain_scores_json}

Generate the profile JSON. Remember: observations only, never diagnoses.
"""


async def generate_profile(domain_scores: dict) -> dict:
    """
    Call IBM Granite to synthesise a multidimensional profile from domain scores.
    Returns a parsed dict matching the profile schema above.
    Falls back to a stub profile if credentials are not configured.
    """
    try:
        llm = _get_llm()
    except RuntimeError as exc:
        logger.warning("LLM not configured — returning stub profile", error=str(exc))
        return _stub_profile(domain_scores)

    prompt = ChatPromptTemplate.from_messages([
        ("system", PROFILE_SYSTEM_PROMPT),
        ("human", PROFILE_USER_PROMPT),
    ])
    chain = prompt | llm | StrOutputParser()

    try:
        raw = await chain.ainvoke({
            "domain_scores_json": json.dumps(domain_scores, indent=2),
        })
        # Strip markdown fences if Granite adds them
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as exc:
        logger.error("Profile generation failed", error=str(exc))
        return _stub_profile(domain_scores)


def _stub_profile(domain_scores: dict) -> dict:
    """
    Minimal stub profile used when IBM credentials are not set.
    Keeps the application runnable during local development.
    """
    mind = domain_scores.get("mind", {})
    goal = domain_scores.get("goal", {})
    work = domain_scores.get("work_capacity", {})

    stress_norm = mind.get("modules", {}).get("mind_stress", {}).get("normalised", 0.5)
    stress_level = "high" if stress_norm > 0.65 else "moderate" if stress_norm > 0.35 else "low"
    big_five = mind.get("modules", {}).get("mind_big_five", {}).get("dimensions", {})
    goal_dims = goal.get("modules", {}).get("goal_clarity", {}).get("dimensions", {})
    work_dims = work.get("modules", {}).get("work_capacity_burnout", {}).get("dimensions", {})
    burnout_ex = work_dims.get("exhaustion", 0.5)
    burnout_level = "high" if burnout_ex > 0.65 else "moderate" if burnout_ex > 0.35 else "low"

    return {
        "summary_text": (
            f"Your profile shows {stress_level} stress levels with "
            f"{burnout_level} burnout risk indicators. "
            "Your goal clarity and values alignment are core areas to build on."
        ),
        "mind_data": {
            "stress_level": stress_level,
            "stress_score_normalised": stress_norm,
            "cognitive_load": stress_level,
            "big_five": {
                "openness": big_five.get("openness", 0.6),
                "conscientiousness": big_five.get("conscientiousness", 0.6),
                "extraversion": big_five.get("extraversion", 0.5),
                "agreeableness": big_five.get("agreeableness", 0.6),
                "neuroticism": big_five.get("neuroticism", 0.4),
            },
            "key_observations": [
                "Moderate cognitive demands are present based on your responses.",
                "Attention management may benefit from structured focus time.",
            ],
        },
        "goal_data": {
            "clarity_score": goal_dims.get("clarity", 0.6),
            "sdt_autonomy": goal_dims.get("autonomy", 0.65),
            "sdt_competence": goal_dims.get("competence", 0.6),
            "sdt_relatedness": goal_dims.get("relatedness", 0.55),
            "goal_commitment": goal_dims.get("commitment", 0.65),
            "values_alignment": "moderate",
            "key_observations": [
                "Your goals reflect a moderate level of clarity.",
                "Autonomy is a strength — you are self-directed in your pursuits.",
            ],
        },
        "work_capacity_data": {
            "burnout_risk": burnout_level,
            "exhaustion_score": burnout_ex,
            "depersonalisation_score": work_dims.get("depersonalisation", 0.3),
            "efficacy_score": work_dims.get("efficacy", 0.6),
            "energy_level": work_dims.get("energy", 0.6),
            "focus_capacity": work_dims.get("focus", 0.55),
            "key_observations": [
                f"Exhaustion indicators are {burnout_level}.",
                "Personal efficacy remains a relative strength.",
            ],
        },
        "strengths": [
            {
                "label": "Self-directed goal pursuit",
                "domain": "goal",
                "rationale": "High autonomy score reflects genuine ownership of your goals.",
                "framework_ref": "SDT:autonomy",
            },
        ],
        "risks": [
            {
                "label": "Elevated stress load",
                "domain": "mind",
                "severity": stress_level,
                "rationale": "Stress indicators suggest current demands may be stretching capacity.",
                "framework_ref": "PSS-10:perceived_stress",
            },
        ],
        "opportunities": [
            {
                "label": "Strengthen goal clarity",
                "domain": "goal",
                "rationale": "Building clearer 90-day priorities would improve daily decision quality.",
                "framework_ref": "Goal-Setting Theory:specificity",
            },
        ],
    }
