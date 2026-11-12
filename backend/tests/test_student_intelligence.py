import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_token(email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]


def test_student_list_admin_and_student_isolation():
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")
    student_token = get_token("aarav.sharma@reva.in", "StudentPass123!")

    # 1. Admin lists all students (should see 36 students)
    res_admin = client.get("/api/v1/students/", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    admin_students = res_admin.json()
    assert len(admin_students) >= 30

    # 2. Student lists students (must only see their own 1 profile)
    res_student = client.get("/api/v1/students/", headers={"Authorization": f"Bearer {student_token}"})
    assert res_student.status_code == 200
    student_list = res_student.json()
    assert len(student_list) == 1
    assert student_list[0]["email"] == "aarav.sharma@reva.in"


def test_student_profile_security_isolation():
    student_token = get_token("aarav.sharma@reva.in", "StudentPass123!")
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")

    # Primary student (Alex Mercer) has student_id = 1
    # Another student in the synthetic cohort has student_id = 2
    # Student 1 attempts to access Student 2's analytics -> must return 403 Forbidden!
    res_unauth = client.get(
        "/api/v1/students/2/analytics",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_unauth.status_code == 403
    assert "Access denied" in res_unauth.json()["message"] or "forbidden" in str(res_unauth.json()).lower()

    # Admin accesses Student 2's analytics -> must return 200 OK
    res_admin = client.get(
        "/api/v1/students/2/analytics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "student_profile" in data
    assert "sgpa_trend" in data
    assert "attendance_breakdown" in data
    assert "skills_by_category" in data


import time


def test_admin_create_and_edit_student():
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")

    uniq_id = int(time.time() * 1000) % 100000
    new_student_data = {
        "full_name": f"Test Student Acceptance {uniq_id}",
        "email": f"test.acc{uniq_id}@reva.in",
        "roll_number": f"ACC-{uniq_id}",
        "usn": f"1RV22ACC{uniq_id:04d}",
        "srn": f"SRN-2022-ACC{uniq_id:04d}",
        "department_id": 1,
        "program": "B.Tech Computer Science & Engineering",
        "current_semester": 5,
        "batch_year": 2024,
        "admission_year": 2022,
        "section": "A",
        "status": "Active",
        "placement_status": "Eligible"
    }

    # Create student
    res_create = client.post(
        "/api/v1/students/",
        json=new_student_data,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_create.status_code == 201
    created_student = res_create.json()
    assert created_student["usn"] == new_student_data["usn"]
    st_id = created_student["id"]

    # Edit student
    res_update = client.patch(
        f"/api/v1/students/{st_id}",
        json={"section": "B", "status": "Active", "guardian_name": "Dr. Acceptance Guardian"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["section"] == "B"
    assert updated["guardian_name"] == "Dr. Acceptance Guardian"


def test_calculated_attendance_and_analytics_integrity():
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")

    # Student 2 Analytics
    res = client.get("/api/v1/students/2/analytics", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    analytics = res.json()

    # Check attendance is calculated from raw counts
    for att in analytics["attendance_breakdown"]:
        assert "total_classes" in att
        assert "attended_classes" in att
        assert "attendance_percentage" in att
        expected_pct = round((att["attended_classes"] / att["total_classes"]) * 100.0, 1)
        assert abs(att["attendance_percentage"] - expected_pct) <= 0.1

    # Check SGPA trend has valid semesters
    assert len(analytics["sgpa_trend"]) >= 1
    for sem in analytics["sgpa_trend"]:
        assert sem["sgpa"] >= 0.0 and sem["sgpa"] <= 10.0


def test_student_skill_persistence():
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")

    skill_payload = {
        "skill_name": "GraphQL API Architecture",
        "category": "framework",
        "proficiency_level": "Advanced"
    }

    res_add = client.post(
        "/api/v1/students/1/skills",
        json=skill_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_add.status_code == 201
    skill_res = res_add.json()
    assert skill_res["skill_name"] == "GraphQL API Architecture"
    assert skill_res["proficiency_level"] == "Advanced"

    # Verify skill persisted in analytics endpoint
    res_analytics = client.get(
        "/api/v1/students/1/analytics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_analytics.status_code == 200
    frameworks = res_analytics.json()["skills_by_category"]["framework"]
    assert any(s["skill_name"] == "GraphQL API Architecture" for s in frameworks)


def test_csv_import_preview_and_validation():
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")

    uniq = int(time.time() * 1000) % 100000
    # Valid CSV
    valid_csv = (
        "usn,email,name,department,semester,section,roll_number,cgpa,attendance\n"
        f"1RV22CSV{uniq}1,csv.student{uniq}1@reva.in,CSV Student 1,CSE,5,A,CSV-{uniq}1,8.5,90.0\n"
        f"1RV22CSV{uniq}2,csv.student{uniq}2@reva.in,CSV Student 2,CSE,5,A,CSV-{uniq}2,7.8,85.0\n"
    )

    res_preview = client.post(
        "/api/v1/imports/preview",
        data={"import_type": "students"},
        files={"file": ("valid.csv", io.BytesIO(valid_csv.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_preview.status_code == 200
    preview_data = res_preview.json()
    assert preview_data["total_rows"] == 2
    assert preview_data["valid_rows_count"] == 2
    assert preview_data["invalid_rows_count"] == 0

    # Invalid CSV (missing USN, duplicate email)
    invalid_csv = (
        "usn,email,name,department,semester,section,roll_number\n"
        ",no.usn@reva.in,Missing USN,CSE,5,A,CSV-003\n"
        "1RV22SYN001,aarav.sharma@reva.in,Duplicate User,CSE,5,A,CSV-004\n"
    )

    res_invalid_preview = client.post(
        "/api/v1/imports/preview",
        data={"import_type": "students"},
        files={"file": ("invalid.csv", io.BytesIO(invalid_csv.encode("utf-8")), "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_invalid_preview.status_code == 200
    invalid_data = res_invalid_preview.json()
    assert invalid_data["invalid_rows_count"] >= 1
    assert len(invalid_data["errors"]) >= 1


def test_faculty_and_admin_analytics_endpoints():
    admin_token = get_token("anitha.rao@reva.in", "AdminPass123!")
    faculty_token = get_token("kavya.menon@reva.in", "FacultyPass123!")

    # Faculty Analytics
    res_faculty = client.get(
        "/api/v1/students/analytics/faculty",
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res_faculty.status_code == 200
    fac_data = res_faculty.json()
    assert "assigned_courses" in fac_data
    assert "total_assigned_students" in fac_data
    assert fac_data["total_assigned_students"] >= 1

    # Admin Analytics
    res_admin = client.get(
        "/api/v1/students/analytics/admin",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert "institutional_stats" in admin_data
    assert "department_wise_stats" in admin_data
    assert "attendance_distribution" in admin_data
    assert "cgpa_distribution" in admin_data
    assert admin_data["institutional_stats"]["total_students"] >= 30


def test_student_update_survives_failed_risk_reevaluation(client, auth, monkeypatch):
    """A profile update is committed before risk re-evaluation; a failure there must not become a 500."""
    from app.services.risk_service import RiskService

    def boom(*args, **kwargs):
        raise RuntimeError("simulated evaluation failure")

    monkeypatch.setattr(RiskService, "evaluate_risk", boom)
    headers = auth("anitha.rao@reva.in")
    r = client.patch("/api/v1/students/2", json={"phone": "+91-90000-00002"}, headers=headers)
    assert r.status_code == 200, r.text
