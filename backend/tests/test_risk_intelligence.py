import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Student
from app.models.department import Department
from app.models.academic import SubjectAttendance, StudentAssessment, StudentSemesterRecord, Subject, Semester
from app.models.risk import RiskRule, RiskAlert
from app.services.risk_service import RiskService

client = TestClient(app)


def get_auth_token(email: str, password: str = "AdminPass123!"):
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return get_auth_token("admin@smartcampus.edu", "AdminPass123!")


@pytest.fixture(scope="module")
def student_token():
    return get_auth_token("student@smartcampus.edu", "StudentPass123!")


@pytest.fixture(scope="module")
def faculty_token():
    return get_auth_token("faculty@smartcampus.edu", "FacultyPass123!")


# -----------------------------------------------------------------------------
# 1. TEST RULES RETRIEVAL & ADMIN CONFIGURATION
# -----------------------------------------------------------------------------
def test_rules_retrieval_and_admin_crud(admin_token, student_token):
    # Admin can get rules
    res = client.get("/api/v1/risk/rules", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    rules = res.json()
    assert len(rules) >= 9

    # Student cannot create rule
    uniq_code = f"RULE_CUSTOM_{int(time.time())}"
    create_payload = {
        "name": "Custom Low Lab Marks Warning",
        "code": uniq_code,
        "description": "Custom rule created by administrator",
        "category": "ASSESSMENT",
        "severity": "HIGH",
        "indicator_type": "assessment_percentage",
        "operator": "<",
        "threshold_value": 45.0,
        "suggested_action": "Extra lab session required",
        "is_active": True,
    }
    unauth_res = client.post(
        "/api/v1/risk/rules",
        json=create_payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert unauth_res.status_code == 403

    # Admin creates rule
    auth_res = client.post(
        "/api/v1/risk/rules",
        json=create_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert auth_res.status_code == 201
    created_rule = auth_res.json()
    assert created_rule["code"] == uniq_code

    # Admin updates rule threshold
    update_res = client.put(
        f"/api/v1/risk/rules/{created_rule['id']}",
        json={"threshold_value": 48.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["threshold_value"] == 48.0

    # Clean up test rule
    del_res = client.delete(
        f"/api/v1/risk/rules/{created_rule['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_res.status_code == 204


# -----------------------------------------------------------------------------
# 2. TEST ATTENDANCE BELOW THRESHOLD & EXACTLY AT THRESHOLD (BOUNDARY TEST)
# -----------------------------------------------------------------------------
def test_attendance_boundary_conditions():
    db = SessionLocal()
    try:
        # Create 2 test students:
        # Student A: Attendance 74.0% (< 75.0% -> SHOULD TRIGGER)
        # Student B: Attendance exactly 75.0% (NOT < 75.0% -> SHOULD NOT TRIGGER)
        uniq_id = int(time.time() * 1000) % 1000000

        user_a = User(
            email=f"att_below_{uniq_id}@test.com",
            full_name="Below Threshold Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        user_b = User(
            email=f"att_exact_{uniq_id}@test.com",
            full_name="Exact Threshold Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        db.add_all([user_a, user_b])
        db.flush()

        student_a = Student(
            user_id=user_a.id,
            roll_number=f"ROLL_BELOW_{uniq_id}",
            usn=f"USN_BELOW_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=5,
            section="A",
            status="Active",
            attendance_percentage=74.0,
        )
        student_b = Student(
            user_id=user_b.id,
            roll_number=f"ROLL_EXACT_{uniq_id}",
            usn=f"USN_EXACT_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=5,
            section="A",
            status="Active",
            attendance_percentage=75.0,
        )
        db.add_all([student_a, student_b])
        db.flush()

        # Add attendance records:
        # Student A: 37 attended out of 50 = 74.0%
        att_a = SubjectAttendance(
            student_id=student_a.id,
            subject_id=1,
            semester_id=1,
            total_classes=50,
            attended_classes=37,
        )
        # Student B: 30 attended out of 40 = 75.0%
        att_b = SubjectAttendance(
            student_id=student_b.id,
            subject_id=1,
            semester_id=1,
            total_classes=40,
            attended_classes=30,
        )
        db.add_all([att_a, att_b])
        db.commit()

        # Evaluate student A
        RiskService.evaluate_risk(db, student_id=student_a.id, run_type="TEST")
        # Evaluate student B
        RiskService.evaluate_risk(db, student_id=student_b.id, run_type="TEST")

        # Check attendance warning alert (RULE_ATT_WARNING)
        rule_att_warning = db.query(RiskRule).filter(RiskRule.code == "RULE_ATT_WARNING").first()
        assert rule_att_warning is not None

        alert_a = db.query(RiskAlert).filter(
            RiskAlert.student_id == student_a.id,
            RiskAlert.rule_id == rule_att_warning.id,
            RiskAlert.status == "FLAGGED",
        ).first()
        assert alert_a is not None, "Student with 74.0% attendance must trigger attendance warning alert."
        assert alert_a.observed_value == 74.0

        alert_b = db.query(RiskAlert).filter(
            RiskAlert.student_id == student_b.id,
            RiskAlert.rule_id == rule_att_warning.id,
        ).first()
        assert alert_b is None, "Student with exactly 75.0% attendance must NOT trigger '< 75.0%' alert."

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 3. TEST DECLINING SEMESTER PERFORMANCE (SGPA DROP >= 1.0)
# -----------------------------------------------------------------------------
def test_declining_performance_trigger():
    db = SessionLocal()
    try:
        uniq_id = int(time.time() * 1000) % 1000000
        user = User(
            email=f"sgpa_drop_{uniq_id}@test.com",
            full_name="Downturn Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            roll_number=f"ROLL_DROP_{uniq_id}",
            usn=f"USN_DROP_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=4,
            section="B",
            status="Active",
            attendance_percentage=85.0,
        )
        db.add(student)
        db.flush()

        # Semester 3: SGPA 8.4
        sem3 = StudentSemesterRecord(
            student_id=student.id,
            semester_id=1,
            semester_number=3,
            sgpa=8.4,
            credits_registered=24,
            credits_earned=24,
        )
        # Semester 4: SGPA 7.1 (Drop of 1.3 >= 1.0 threshold)
        sem4 = StudentSemesterRecord(
            student_id=student.id,
            semester_id=2,
            semester_number=4,
            sgpa=7.1,
            credits_registered=24,
            credits_earned=24,
        )
        db.add_all([sem3, sem4])
        db.commit()

        RiskService.evaluate_risk(db, student_id=student.id, run_type="TEST")

        rule_sgpa_drop = db.query(RiskRule).filter(RiskRule.code == "RULE_SGPA_DROP").first()
        assert rule_sgpa_drop is not None

        alert = db.query(RiskAlert).filter(
            RiskAlert.student_id == student.id,
            RiskAlert.rule_id == rule_sgpa_drop.id,
        ).first()
        assert alert is not None, "Student with SGPA drop >= 1.0 must trigger declining performance alert."
        assert alert.observed_value == 1.3
        assert "dropped by 1.30 points" in alert.ai_explanation or "decreased by 1.30" in alert.ai_explanation
        assert alert.severity == "HIGH"

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 4. TEST HEALTHY NO-TRIGGER STUDENT
# -----------------------------------------------------------------------------
def test_healthy_no_trigger_student():
    db = SessionLocal()
    try:
        uniq_id = int(time.time() * 1000) % 1000000
        user = User(
            email=f"healthy_{uniq_id}@test.com",
            full_name="Star Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            roll_number=f"ROLL_STAR_{uniq_id}",
            usn=f"USN_STAR_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=4,
            section="A",
            status="Active",
            attendance_percentage=94.0,
            cgpa=9.2,
        )
        db.add(student)
        db.flush()

        # High attendance
        att = SubjectAttendance(
            student_id=student.id,
            subject_id=1,
            semester_id=1,
            total_classes=40,
            attended_classes=38,  # 95%
        )
        # High assessment
        cia = StudentAssessment(
            student_id=student.id,
            subject_id=1,
            semester_id=1,
            assessment_type="Internal Assessment 1",
            max_marks=30.0,
            marks_obtained=27.0,  # 90%
        )
        # Stable high SGPA
        sem1 = StudentSemesterRecord(
            student_id=student.id,
            semester_id=1,
            semester_number=3,
            sgpa=9.1,
            credits_registered=24,
            credits_earned=24,
            backlogs_count=0,
        )
        sem2 = StudentSemesterRecord(
            student_id=student.id,
            semester_id=2,
            semester_number=4,
            sgpa=9.3,
            credits_registered=24,
            credits_earned=24,
            backlogs_count=0,
        )
        db.add_all([att, cia, sem1, sem2])
        db.commit()

        RiskService.evaluate_risk(db, student_id=student.id, run_type="TEST")

        alerts = db.query(RiskAlert).filter(RiskAlert.student_id == student.id).all()
        assert len(alerts) == 0, "Healthy student meeting all benchmarks must generate zero risk alerts."

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 5. TEST DUPLICATE ALERT PREVENTION
# -----------------------------------------------------------------------------
def test_duplicate_alert_prevention():
    db = SessionLocal()
    try:
        uniq_id = int(time.time() * 1000) % 1000000
        user = User(
            email=f"dup_test_{uniq_id}@test.com",
            full_name="Duplicate Test Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            roll_number=f"ROLL_DUP_{uniq_id}",
            usn=f"USN_DUP_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=3,
            section="A",
            status="Active",
            attendance_percentage=60.0,
        )
        db.add(student)
        db.flush()

        att = SubjectAttendance(
            student_id=student.id,
            subject_id=1,
            semester_id=1,
            total_classes=40,
            attended_classes=24,  # 60%
        )
        db.add(att)
        db.commit()

        # Run evaluation 3 times consecutively
        RiskService.evaluate_risk(db, student_id=student.id, run_type="TEST_1")
        RiskService.evaluate_risk(db, student_id=student_id if (student_id := student.id) else 0, run_type="TEST_2")
        RiskService.evaluate_risk(db, student_id=student.id, run_type="TEST_3")

        # Must have exactly 1 active alert for Critical Attendance Shortfall, not 3
        rule_crit = db.query(RiskRule).filter(RiskRule.code == "RULE_ATT_CRITICAL").first()
        active_alerts = db.query(RiskAlert).filter(
            RiskAlert.student_id == student.id,
            RiskAlert.rule_id == rule_crit.id,
        ).all()

        assert len(active_alerts) == 1, f"Expected exactly 1 alert due to duplicate prevention, found {len(active_alerts)}"

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 6. TEST ALERT WORKFLOW LIFECYCLE (ACKNOWLEDGE, ADD NOTE, RESOLVE, REOPEN)
# -----------------------------------------------------------------------------
def test_alert_lifecycle_workflow(faculty_token, student_token):
    # Fetch active alerts
    res = client.get("/api/v1/risk/alerts", headers={"Authorization": f"Bearer {faculty_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    alert_id = data["items"][0]["id"]

    # Faculty acknowledges alert
    ack_res = client.post(
        f"/api/v1/risk/alerts/{alert_id}/acknowledge",
        json={"notes": "Reviewed by faculty. Assigned supplementary tutorials."},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # Faculty adds review note
    note_res = client.post(
        f"/api/v1/risk/alerts/{alert_id}/notes",
        json={"notes": "Met with student on Tuesday. Progress discussed."},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert note_res.status_code == 200

    # Faculty resolves alert
    resolve_res = client.post(
        f"/api/v1/risk/alerts/{alert_id}/resolve",
        json={
            "resolution_reason": "Remedial Tutorials Completed",
            "review_notes": "Student attendance recovered above 78% following remedial block.",
        },
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # Verify audit history
    detail_res = client.get(
        f"/api/v1/risk/alerts/{alert_id}",
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert detail_res.status_code == 200
    history = detail_res.json()["history"]
    actions = [h["action"] for h in history]
    assert "ACKNOWLEDGED" in actions
    assert "RESOLVED" in actions

    # Student cannot resolve alert
    unauth_resolve = client.post(
        f"/api/v1/risk/alerts/{alert_id}/resolve",
        json={"resolution_reason": "Attempted self-resolution"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert unauth_resolve.status_code == 403


# -----------------------------------------------------------------------------
# 7. TEST STUDENT SECURITY ISOLATION
# -----------------------------------------------------------------------------
def test_student_risk_isolation(student_token, admin_token):
    # Get student profile
    student_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert student_res.status_code == 200
    student_id = student_res.json()["student_id"]

    # Student can access their own profile
    own_res = client.get(
        f"/api/v1/risk/students/{student_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert own_res.status_code == 200
    assert own_res.json()["student_id"] == student_id

    # Student cannot access another student's profile (e.g., student_id + 1)
    other_student_id = student_id + 1
    other_res = client.get(
        f"/api/v1/risk/students/{other_student_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert other_res.status_code == 403
