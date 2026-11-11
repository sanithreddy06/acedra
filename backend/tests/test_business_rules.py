"""Unit tests for business rules that were extracted into named, documented functions."""
from types import SimpleNamespace as NS

import pytest

from app.services.placement_service import DEFAULT_CAREER_ROLE_CODE, default_role_code_for_student, role_code_for_goal
from app.services.risk_service import (
    _INDICATOR_OBSERVERS,
    _StudentRiskMetrics,
    compare,
    highest_active_severity,
)


# --- risk rules ---------------------------------------------------------------------------------
@pytest.mark.parametrize("value,op,threshold,expected", [
    (74.9, "<", 75, True), (75, "<", 75, False), (75, "<=", 75, True), (2, ">", 1, True),
    (1, ">=", 1, True), (1.00001, "==", 1, True), (5, "!=", 1, False),  # unknown operators never trigger
])
def test_compare_operators(value, op, threshold, expected):
    assert compare(value, op, threshold) is expected


def _attendance(subject, attended, total):
    return NS(subject_id=subject, subject=NS(name=f"Subject {subject}"), attended_classes=attended,
              total_classes=total, attendance_percentage=round(attended / total * 100, 2))


def _student(attendance=(), assessments=(), semesters=(), results=(), stored_attendance=90.0, semester=5):
    return NS(id=1, user_id=10, usn="U1", roll_number="R1", user=NS(full_name="Test Student"),
              attendance_percentage=stored_attendance, attendance_records=list(attendance),
              assessments=list(assessments), semester_records=list(semesters), subject_results=list(results),
              current_semester=semester, assigned_mentor_id=None)


def _rule(indicator, op="<", threshold=75.0, config=None):
    return NS(indicator_type=indicator, operator=op, threshold_value=threshold, conditions_config=config)


def test_attendance_rule_checks_the_weakest_subject():
    m = _StudentRiskMetrics.from_student(_student(attendance=[_attendance(1, 40, 45), _attendance(2, 30, 45)]))
    assert m.overall_attendance == pytest.approx(77.78)
    obs = _INDICATOR_OBSERVERS["attendance_percentage"](m, _rule("attendance_percentage"))
    assert obs.triggered and obs.subject_id == 2 and obs.value == pytest.approx(66.67)
    assert obs.context["subject_name"] == "Subject 2"


def test_assessment_rule_falls_back_to_average_when_weakest_is_fine():
    asm = [NS(percentage=p, subject_id=1, subject=None, assessment_type="IA", marks_obtained=p, max_marks=100)
           for p in (60.0, 70.0)]
    m = _StudentRiskMetrics.from_student(_student(assessments=asm))
    obs = _INDICATOR_OBSERVERS["assessment_percentage"](m, _rule("assessment_percentage", threshold=50.0))
    assert not obs.triggered and obs.value == 65.0 and obs.display == "65.0% CIA Average"
    assert not _INDICATOR_OBSERVERS["assessment_percentage"](
        _StudentRiskMetrics.from_student(_student()), _rule("assessment_percentage")).triggered


def test_backlogs_use_the_larger_of_semester_count_and_failed_subjects():
    results = [NS(is_backlog=True, subject=NS(name=n)) for n in ("Maths", "Maths", "Physics")]
    m = _StudentRiskMetrics.from_student(_student(semesters=[NS(semester_number=4, sgpa=7.0, backlogs_count=1)],
                                                  results=results))
    assert m.backlog_count == 2 and m.failed_subject_names == ["Maths", "Physics"]
    assert _INDICATOR_OBSERVERS["backlog_count"](m, _rule("backlog_count", ">=", 1)).triggered


def test_sgpa_drop_and_composite_rules():
    semesters = [NS(semester_number=3, sgpa=8.0, backlogs_count=0), NS(semester_number=4, sgpa=7.2, backlogs_count=0)]
    asm = [NS(percentage=40.0, subject_id=1, subject=None, assessment_type="IA", marks_obtained=4, max_marks=10)]
    m = _StudentRiskMetrics.from_student(_student(semesters=semesters, assessments=asm, stored_attendance=60.0))
    assert m.sgpa_drop == 0.8
    assert _INDICATOR_OBSERVERS["sgpa_drop"](m, _rule("sgpa_drop", ">=", 0.5)).triggered
    composite = _INDICATOR_OBSERVERS["composite"](m, _rule("composite", config={"min_attendance": 75,
                                                                               "max_assessment_pct": 50}))
    assert composite.triggered and composite.display == "Att: 60.0%, CIA: 40.0%"


def test_highest_active_severity_ignores_resolved_alerts():
    alerts = [NS(status="RESOLVED", severity="CRITICAL"), NS(status="FLAGGED", severity="MODERATE"),
              NS(status="ACKNOWLEDGED", severity="HIGH")]
    assert highest_active_severity(alerts) == "HIGH"
    assert highest_active_severity([]) == "NORMAL"


# --- placement readiness default role -------------------------------------------------------------
def test_role_code_for_goal():
    assert role_code_for_goal("AI/ML Engineer") == "AI_ML_ENGINEER"
    assert role_code_for_goal("Software Developer") == "SOFTWARE_DEVELOPER"
    assert role_code_for_goal(None) == DEFAULT_CAREER_ROLE_CODE
    assert default_role_code_for_student(NS(career_goals=[])) == DEFAULT_CAREER_ROLE_CODE
    assert default_role_code_for_student(None) == DEFAULT_CAREER_ROLE_CODE


def test_readiness_defaults_to_the_students_goal_including_slashes(client, auth):
    """Regression: "AI/ML Engineer" used to map to an unknown code and silently fall back to Software Developer."""
    headers = auth("admin@northfield.example")
    sid = client.get("/api/v1/students/", headers=headers).json()[-1]["id"]
    r = client.put(f"/api/v1/recommendations/students/{sid}/career-profile",
                   json={"career_goals": ["AI/ML Engineer"], "interests": []}, headers=headers)
    assert r.status_code == 200, r.text
    readiness = client.get(f"/api/v1/placement/readiness/{sid}", headers=headers)
    assert readiness.status_code == 200
    assert readiness.json()["target_role"]["code"] == "AI_ML_ENGINEER"


def test_rule_schema_matches_the_engine():
    """Every indicator the API accepts has an observer, and vice versa."""
    from app.schemas.risk import RISK_INDICATOR_TYPES

    assert set(RISK_INDICATOR_TYPES) == set(_INDICATOR_OBSERVERS)


def test_unsupported_rule_indicator_is_rejected(client, auth):
    headers = auth("admin@reva-demo.example")
    body = {"name": "CGPA watch", "code": "CGPA_WATCH", "category": "ACADEMIC", "indicator_type": "cgpa",
            "operator": "<", "threshold_value": 6}
    r = client.post("/api/v1/risk/rules", json=body, headers=headers)
    assert r.status_code == 422
    assert "indicator_type" in r.text
