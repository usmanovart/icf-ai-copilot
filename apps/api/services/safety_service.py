"""
Safety service — crisis detection gate.

Runs BEFORE every LLM call. If a crisis signal is detected, this service
returns a safety response and the LLM call is aborted entirely.

This is a keyword + pattern-based classifier for the MVP.
It is deliberately conservative: false positives (surfacing support
resources unnecessarily) are safer than false negatives.
"""

import re
import structlog

logger = structlog.get_logger()

# ── Crisis signal patterns ─────────────────────────────────────────────────────
# Ordered from highest to lowest severity.
# Patterns are case-insensitive whole-word or phrase matches.
_CRISIS_PATTERNS: list[re.Pattern] = [p for p in [
    re.compile(r"\b(suicide|suicidal|kill myself|end my life|want to die|take my own life)\b", re.I),
    re.compile(r"\b(self.harm|self harm|cut myself|hurt myself|harm myself)\b", re.I),
    re.compile(r"\b(no reason to live|nothing to live for|better off dead|can't go on)\b", re.I),
    re.compile(r"\b(overdose|od on)\b", re.I),
]]

_SUPPORT_RESOURCES = """
I noticed something in what you shared that I want to address directly.

If you are having thoughts of harming yourself or ending your life, please reach out for support right now:

• **International Association for Suicide Prevention**: https://www.iasp.info/resources/Crisis_Centres/
• **Crisis Text Line** (US/UK/CA/IE): Text HOME to 741741
• **Samaritans** (UK & Ireland): 116 123 (free, 24/7)
• **988 Suicide & Crisis Lifeline** (US): Call or text 988

You do not have to face this alone. A trained crisis counsellor can help.

*ICF AI Copilot is a decision-support tool and cannot provide clinical or emergency support.*
"""


class SafetyCheckResult:
    def __init__(self, triggered: bool, response: str | None = None):
        self.triggered = triggered
        self.response = response


def check_safety(text: str) -> SafetyCheckResult:
    """
    Check input text for crisis signals.
    Returns SafetyCheckResult.triggered = True if any pattern matches.
    """
    for pattern in _CRISIS_PATTERNS:
        if pattern.search(text):
            logger.warning(
                "Crisis safety gate triggered",
                pattern=pattern.pattern[:40],
            )
            return SafetyCheckResult(triggered=True, response=_SUPPORT_RESOURCES)

    return SafetyCheckResult(triggered=False)
