"""
Unit tests for assessment_service scoring logic.

These tests are pure-Python (no DB, no HTTP) — they exercise the private
scoring helpers and the public score_assessment() function by constructing
lightweight AssessmentResponse-like objects.
"""

import pytest
from unittest.mock import MagicMock


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_response(question_key: str, value, module: str, domain: str = "mind"):
    """Create a minimal AssessmentResponse mock."""
    r = MagicMock()
    r.question_key = question_key
    r.response_value = {"value": value}
    r.module = module
    r.domain = domain
    return r


def _make_question(key: str, reverse_scored: bool = False, q_type: str = "likert5",
                   dimension: str = "dim1"):
    return {
        "key": key,
        "type": q_type,
        "reverse_scored": reverse_scored,
        "dimension": dimension,
    }


# ── Import helpers under test ──────────────────────────────────────────────────

# We import the private helpers directly so tests don't need a DB.
import sys
import os

# Add the api root to sys.path so imports resolve correctly.
API_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if API_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(API_ROOT))

from services.assessment_service import (  # noqa: E402
    _score_sum_normalised,
    _score_mean_per_dimension,
    _aggregate_to_domains,
    score_assessment,
    MODULES,
)


# ══════════════════════════════════════════════════════════════════════════════
# _score_sum_normalised
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreSumNormalised:
    def test_all_zeros_returns_zero(self):
        questions = {
            "q1": _make_question("q1"),
            "q2": _make_question("q2"),
        }
        responses = [
            _make_response("q1", 0, "mind_stress"),
            _make_response("q2", 0, "mind_stress"),
        ]
        result = _score_sum_normalised(responses, questions, [0, 40])
        assert result["raw_score"] == 0
        assert result["normalised"] == 0.0

    def test_all_max_returns_one(self):
        questions = {
            "q1": _make_question("q1"),
            "q2": _make_question("q2"),
        }
        # max per item = 4, 2 items → max_possible = 8; score_range[1] = 8
        responses = [
            _make_response("q1", 4, "mind_stress"),
            _make_response("q2", 4, "mind_stress"),
        ]
        result = _score_sum_normalised(responses, questions, [0, 8])
        assert result["raw_score"] == 8
        assert result["normalised"] == 1.0

    def test_reverse_scored_item(self):
        """A reverse-scored item with value 0 should contribute max (4)."""
        questions = {
            "q1": _make_question("q1", reverse_scored=True),
        }
        responses = [_make_response("q1", 0, "mind_stress")]
        result = _score_sum_normalised(responses, questions, [0, 4])
        assert result["raw_score"] == 4  # 4 - 0 = 4
        assert result["normalised"] == 1.0

    def test_reverse_scored_item_value_4(self):
        """A reverse-scored item with value 4 should contribute 0."""
        questions = {
            "q1": _make_question("q1", reverse_scored=True),
        }
        responses = [_make_response("q1", 4, "mind_stress")]
        result = _score_sum_normalised(responses, questions, [0, 4])
        assert result["raw_score"] == 0
        assert result["normalised"] == 0.0

    def test_unknown_question_key_ignored(self):
        """Responses for unknown question keys must not raise; they are skipped."""
        questions = {"q1": _make_question("q1")}
        responses = [
            _make_response("q1", 2, "mind_stress"),
            _make_response("unknown_key", 4, "mind_stress"),  # should be ignored
        ]
        result = _score_sum_normalised(responses, questions, [0, 4])
        assert result["raw_score"] == 2

    def test_non_integer_value_ignored(self):
        """Non-integer response values should be gracefully skipped."""
        questions = {"q1": _make_question("q1")}
        responses = [
            _make_response("q1", "not_a_number", "mind_stress"),
        ]
        result = _score_sum_normalised(responses, questions, [0, 4])
        assert result["raw_score"] == 0

    def test_zero_max_possible_no_division_error(self):
        """score_range[1] == 0 should return 0.0 without raising."""
        questions = {"q1": _make_question("q1")}
        responses = [_make_response("q1", 2, "mind_stress")]
        result = _score_sum_normalised(responses, questions, [0, 0])
        assert result["normalised"] == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# _score_mean_per_dimension
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreMeanPerDimension:
    def test_single_dimension_mean(self):
        """Two items in same dimension: mean should equal average."""
        questions = {
            "q1": _make_question("q1", dimension="openness"),
            "q2": _make_question("q2", dimension="openness"),
        }
        # 0/4 = 0.0 and 4/4 = 1.0 → mean = 0.5
        responses = [
            _make_response("q1", 0, "mind_big_five"),
            _make_response("q2", 4, "mind_big_five"),
        ]
        result = _score_mean_per_dimension(responses, questions, "dimension")
        assert result["dimensions"]["openness"] == pytest.approx(0.5, abs=1e-3)
        assert result["overall"] == pytest.approx(0.5, abs=1e-3)

    def test_multiple_dimensions(self):
        """Items in separate dimensions are averaged independently."""
        questions = {
            "q1": _make_question("q1", dimension="openness"),
            "q2": _make_question("q2", dimension="conscientiousness"),
        }
        responses = [
            _make_response("q1", 4, "mind_big_five"),   # 1.0
            _make_response("q2", 0, "mind_big_five"),   # 0.0
        ]
        result = _score_mean_per_dimension(responses, questions, "dimension")
        assert result["dimensions"]["openness"] == pytest.approx(1.0, abs=1e-3)
        assert result["dimensions"]["conscientiousness"] == pytest.approx(0.0, abs=1e-3)
        assert result["overall"] == pytest.approx(0.5, abs=1e-3)

    def test_reverse_scored_in_dimension(self):
        """Reverse-scored items flip the normalised value."""
        questions = {
            "q1": _make_question("q1", reverse_scored=True, dimension="neuroticism"),
        }
        responses = [_make_response("q1", 4, "mind_big_five")]  # 4/4=1.0 → reversed = 0.0
        result = _score_mean_per_dimension(responses, questions, "dimension")
        assert result["dimensions"]["neuroticism"] == pytest.approx(0.0, abs=1e-3)

    def test_scale10_type_normalises_to_0_1(self):
        """scale10 questions (0–10) should be divided by 10."""
        questions = {
            "q1": _make_question("q1", q_type="scale10", dimension="goal_clarity"),
        }
        responses = [_make_response("q1", 7, "goal_clarity")]
        result = _score_mean_per_dimension(responses, questions, "dimension")
        assert result["dimensions"]["goal_clarity"] == pytest.approx(0.7, abs=1e-3)

    def test_empty_responses_returns_zero_overall(self):
        questions: dict = {}
        responses: list = []
        result = _score_mean_per_dimension(responses, questions, "dimension")
        assert result["overall"] == 0.0
        assert result["dimensions"] == {}

    def test_unknown_question_key_ignored(self):
        questions = {"q1": _make_question("q1", dimension="openness")}
        responses = [
            _make_response("q1", 2, "mind_big_five"),
            _make_response("ghost_key", 4, "mind_big_five"),
        ]
        result = _score_mean_per_dimension(responses, questions, "dimension")
        assert "openness" in result["dimensions"]
        # ghost_key not producing an extra dimension
        assert len(result["dimensions"]) == 1


# ══════════════════════════════════════════════════════════════════════════════
# _aggregate_to_domains
# ══════════════════════════════════════════════════════════════════════════════

class TestAggregateToDomains:
    def test_empty_input_returns_zero_overalls(self):
        result = _aggregate_to_domains({})
        assert result["mind"]["overall"] == 0.0
        assert result["goal"]["overall"] == 0.0
        assert result["work_capacity"]["overall"] == 0.0

    def test_single_mind_module(self):
        module_scores = {"mind_stress": {"raw_score": 20, "normalised": 0.5}}
        result = _aggregate_to_domains(module_scores)
        assert result["mind"]["overall"] == pytest.approx(0.5, abs=1e-3)

    def test_two_mind_modules_averaged(self):
        module_scores = {
            "mind_stress": {"normalised": 0.4},
            "mind_big_five": {"overall": 0.8},
        }
        result = _aggregate_to_domains(module_scores)
        expected = (0.4 + 0.8) / 2
        assert result["mind"]["overall"] == pytest.approx(expected, abs=1e-3)

    def test_goal_and_work_capacity_isolated(self):
        module_scores = {
            "goal_clarity": {"overall": 0.7},
            "work_capacity_burnout": {"overall": 0.3},
        }
        result = _aggregate_to_domains(module_scores)
        assert result["goal"]["overall"] == pytest.approx(0.7, abs=1e-3)
        assert result["work_capacity"]["overall"] == pytest.approx(0.3, abs=1e-3)
        assert result["mind"]["overall"] == 0.0

    def test_unknown_module_id_ignored(self):
        """Module IDs not in any known bucket should be silently ignored."""
        module_scores = {
            "future_module_x": {"overall": 0.9},
            "goal_clarity": {"overall": 0.6},
        }
        result = _aggregate_to_domains(module_scores)
        assert result["goal"]["overall"] == pytest.approx(0.6, abs=1e-3)


# ══════════════════════════════════════════════════════════════════════════════
# score_assessment (integration of the above)
# ══════════════════════════════════════════════════════════════════════════════

class TestScoreAssessment:
    """Integration test — calls score_assessment() with mock responses.

    Requires MODULES to be loaded (JSON files on disk).
    Only runs when module files are present (skipped otherwise).
    """

    @pytest.fixture(autouse=True)
    def require_modules(self):
        if not MODULES:
            pytest.skip("Assessment module JSON files not found — skipping integration test")

    def _build_responses_for_module(self, module_id: str, value: int):
        """Create one response per question with a fixed value."""
        module = MODULES[module_id]
        return [
            _make_response(q["key"], value, module_id, module["domain"])
            for q in module["questions"]
        ]

    def test_score_assessment_returns_three_domains(self):
        all_responses = []
        for mid in MODULES:
            all_responses.extend(self._build_responses_for_module(mid, 2))

        result = score_assessment(all_responses)
        assert "mind" in result
        assert "goal" in result
        assert "work_capacity" in result

    def test_score_assessment_normalised_range(self):
        """All domain overall scores must be between 0.0 and 1.0."""
        all_responses = []
        for mid in MODULES:
            all_responses.extend(self._build_responses_for_module(mid, 3))

        result = score_assessment(all_responses)
        for domain_name, domain_data in result.items():
            overall = domain_data.get("overall", 0.0)
            assert 0.0 <= overall <= 1.0, (
                f"Domain '{domain_name}' overall {overall} out of [0, 1]"
            )

    def test_score_assessment_empty_returns_zero_domains(self):
        result = score_assessment([])
        for domain_data in result.values():
            assert domain_data["overall"] == 0.0

    def test_mind_stress_module_high_stress(self):
        """All max-value responses on mind_stress should yield a high normalised score."""
        if "mind_stress" not in MODULES:
            pytest.skip("mind_stress module not found")
        module = MODULES["mind_stress"]
        max_per_likert = 4
        # Use max value for non-reverse items, 0 for reverse items
        responses = []
        for q in module["questions"]:
            val = 0 if q.get("reverse_scored") else max_per_likert
            responses.append(_make_response(q["key"], val, "mind_stress", "mind"))
        result = score_assessment(responses)
        stress_normalised = result["mind"]["modules"]["mind_stress"]["normalised"]
        assert stress_normalised == pytest.approx(1.0, abs=0.01)
