from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STUDENT_EMAIL = "aarav.sharma@reva.in"
STUDENT_PASS = "StudentPass123!"

ADMIN_EMAIL = "anitha.rao@reva.in"
ADMIN_PASS = "AdminPass123!"

FACULTY_EMAIL = "kavya.menon@reva.in"
FACULTY_PASS = "FacultyPass123!"

MENTOR_EMAIL = "suresh.hegde@reva.in"
MENTOR_PASS = "MentorPass123!"

PLACEMENT_EMAIL = "rahul.deshpande@reva.in"
PLACEMENT_PASS = "PlacementPass123!"


def get_token(email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]


# =============================================================================
# 1. Role Dashboard Tests (All 5 Roles)
# =============================================================================

def test_student_dashboard_integration():
    token = get_token(STUDENT_EMAIL, STUDENT_PASS)
    res = client.get("/api/v1/dashboards/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "student"
    assert len(data["summary_cards"]) >= 4
    assert "Cumulative CGPA" in [c["title"] for c in data["summary_cards"]]
    assert "Overall Attendance" in [c["title"] for c in data["summary_cards"]]
    assert "Placement Readiness" in [c["title"] for c in data["summary_cards"]]
    assert "Faculty Mentor" in [c["title"] for c in data["summary_cards"]]
    assert "sgpa_trends" in data["quick_stats"]
    assert "readiness_score" in data["quick_stats"]
    assert "alerts" in data["details"]
    assert "recommendations" in data["details"]


def test_faculty_cohort_dashboard_integration():
    token = get_token(FACULTY_EMAIL, FACULTY_PASS)
    res = client.get("/api/v1/dashboards/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "faculty"
    assert len(data["summary_cards"]) >= 4
    titles = [c["title"] for c in data["summary_cards"]]
    assert "Allocated Courses" in titles
    assert "Department Cohort" in titles
    assert "Cohort Avg Attendance" in titles
    assert "performance_distribution" in data["quick_stats"]
    assert "assigned_courses" in data["details"]


def test_mentor_dashboard_integration():
    token = get_token(MENTOR_EMAIL, MENTOR_PASS)
    res = client.get("/api/v1/dashboards/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "mentor"
    titles = [c["title"] for c in data["summary_cards"]]
    assert "Assigned Mentees" in titles
    assert "Mentees At Risk" in titles
    assert "Active Interventions" in titles
    assert "Upcoming Follow-ups" in titles
    assert "mentee_roster" in data["details"]
    assert "active_interventions" in data["details"]
    assert "pending_followups" in data["details"]


def test_admin_executive_dashboard_integration():
    token = get_token(ADMIN_EMAIL, ADMIN_PASS)
    res = client.get("/api/v1/dashboards/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "admin"
    titles = [c["title"] for c in data["summary_cards"]]
    assert "Total Enrolled Students" in titles
    assert "Faculty & Mentors" in titles
    assert "Active Risk Alerts" in titles
    assert "Active Interventions" in titles
    assert "departments" in data["details"]
    assert "performance_stats" in data["quick_stats"]
    assert "intervention_stats" in data["quick_stats"]


def test_placement_officer_dashboard_integration():
    token = get_token(PLACEMENT_EMAIL, PLACEMENT_PASS)
    res = client.get("/api/v1/dashboards/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "placement_officer"
    titles = [c["title"] for c in data["summary_cards"]]
    assert "Placement Eligible Cohort" in titles
    assert "Students Placed" in titles
    assert "Campus Avg CGPA" in titles
    assert "Active Recruitment Drives" in titles
    assert "pipeline" in data["quick_stats"]
    assert "opportunities" in data["details"]
    assert "eligible_roster" in data["details"]


# =============================================================================
# 2. Intervention Management & RBAC Permissions
# =============================================================================

def test_student_forbidden_from_creating_intervention():
    token = get_token(STUDENT_EMAIL, STUDENT_PASS)
    res = client.post(
        "/api/v1/interventions",
        json={
            "student_id": 1,
            "title": "Unauthorized student intervention",
            "intervention_type": "ACADEMIC_REMEDIAL",
            "priority": "HIGH",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code in [401, 403]


def test_mentor_creates_and_tracks_intervention():
    token = get_token(MENTOR_EMAIL, MENTOR_PASS)

    # 1. Create intervention
    target_date = (date.today() + timedelta(days=14)).isoformat()
    create_res = client.post(
        "/api/v1/interventions",
        json={
            "student_id": 1,
            "title": "Automated Test Remedial Coaching Case",
            "intervention_type": "ACADEMIC_REMEDIAL",
            "priority": "HIGH",
            "initial_notes": "Identified weakness in algorithms lab and midterm assessment 1.",
            "target_resolution_date": target_date,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    it_data = create_res.json()
    it_id = it_data["id"]
    assert it_data["title"] == "Automated Test Remedial Coaching Case"
    assert it_data["status"] in ["OPEN", "ASSIGNED"]

    # 2. Add case note
    note_res = client.post(
        f"/api/v1/interventions/{it_id}/notes",
        json={
            "note_text": "Met with student for 30 minutes. Discussed recursion and dynamic programming practice.",
            "note_type": "COUNSELING",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert note_res.status_code == 201
    note_data = note_res.json()
    assert note_data["note_type"] == "COUNSELING"

    # 3. Schedule follow-up
    sched_date = (date.today() + timedelta(days=5)).isoformat()
    follow_res = client.post(
        f"/api/v1/interventions/{it_id}/followups",
        json={
            "scheduled_date": sched_date,
            "outcome_notes": "Initial follow-up checkpoint on lab exercises",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert follow_res.status_code == 201
    f_data = follow_res.json()
    f_id = f_data["id"]
    assert f_data["followup_status"] == "SCHEDULED"

    # 4. Record follow-up outcome
    outcome_res = client.put(
        f"/api/v1/interventions/followups/{f_id}",
        json={
            "followup_status": "COMPLETED",
            "outcome_notes": "Student submitted 5 completed exercises on dynamic programming.",
            "student_feedback": "Feel much more confident about time complexity analysis.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert outcome_res.status_code == 200
    assert outcome_res.json()["followup_status"] == "COMPLETED"

    # 5. Transition status to IN_PROGRESS and then RESOLVED
    prog_res = client.put(
        f"/api/v1/interventions/{it_id}/status",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prog_res.status_code == 200
    assert prog_res.json()["status"] == "IN_PROGRESS"

    res_res = client.put(
        f"/api/v1/interventions/{it_id}/status",
        json={
            "status": "RESOLVED",
            "resolution_summary": "Student passed makeup lab examination with 88% score. Case successfully resolved.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    assert res_res.json()["resolution_summary"] is not None

    # 6. Fetch full dossier
    detail_res = client.get(
        f"/api/v1/interventions/{it_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["notes"]) >= 2
    assert len(detail["followups"]) >= 1


# =============================================================================
# 3. In-App Notifications & Preferences
# =============================================================================

def test_notifications_workflow():
    token = get_token(STUDENT_EMAIL, STUDENT_PASS)

    # 1. Fetch notifications
    res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "notifications" in data
    assert "unread_count" in data
    assert isinstance(data["notifications"], list)

    if len(data["notifications"]) > 0:
        first_notif_id = data["notifications"][0]["id"]

        # 2. Mark single notification read
        read_res = client.put(
            f"/api/v1/notifications/{first_notif_id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert read_res.status_code == 200

    # 3. Mark all notifications read
    read_all_res = client.put(
        "/api/v1/notifications/read-all",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert read_all_res.status_code == 200

    # 4. Verify unread count is now 0
    after_res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert after_res.status_code == 200
    assert after_res.json()["unread_count"] == 0

    # 5. Manage Preferences
    pref_res = client.get("/api/v1/notifications/preferences", headers={"Authorization": f"Bearer {token}"})
    assert pref_res.status_code == 200
    assert "email_alerts_enabled" in pref_res.json()

    update_pref = client.put(
        "/api/v1/notifications/preferences",
        json={"email_alerts_enabled": False, "risk_notifications": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_pref.status_code == 200
    assert update_pref.json()["email_alerts_enabled"] is False


# =============================================================================
# 4. Institutional Compliance & Progress Reports
# =============================================================================

def test_reports_export_and_download():
    token = get_token(ADMIN_EMAIL, ADMIN_PASS)

    # 1. Export Student Progress Report
    exp_res = client.post(
        "/api/v1/reports/export",
        json={"report_type": "STUDENT_PROGRESS", "file_format": "CSV"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exp_res.status_code == 201
    exp_data = exp_res.json()
    report_id = exp_data["id"]
    assert exp_data["report_type"] == "STUDENT_PROGRESS"
    assert exp_data["file_name"].endswith(".csv")

    # 2. List reports
    list_res = client.get("/api/v1/reports", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Download CSV report
    dl_res = client.get(
        f"/api/v1/reports/{report_id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dl_res.status_code == 200
    assert "text/csv" in dl_res.headers["content-type"]
    csv_text = dl_res.text
    assert "Student ID" in csv_text
    assert "USN" in csv_text
    assert "CGPA" in csv_text
