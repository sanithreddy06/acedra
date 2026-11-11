import time

import pytest
from fastapi.testclient import TestClient

from app.core.tenancy import TenantScope, set_session_scope
from app.main import app


def _tenant_session(db, tenant_id=1):
    set_session_scope(db, TenantScope(tenant_id=tenant_id))
    return db
from app.core.database import SessionLocal
from app.models.academic import Subject, SubjectResult
from app.models.profile import Student
from app.models.student_intelligence import Skill, StudentSkill
from app.models.user import User
from app.services.recommendation_service import RecommendationService

client = TestClient(app)


def get_token(email: str, password: str = "AdminPass123!") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    return get_token("admin@reva-demo.example", "AdminPass123!")


@pytest.fixture(scope="module")
def student_token():
    return get_token("student@reva-demo.example", "StudentPass123!")


@pytest.fixture(scope="module")
def faculty_token():
    return get_token("faculty@reva-demo.example", "FacultyPass123!")


# -----------------------------------------------------------------------------
# 1. TEST CATALOGUE RETRIEVAL & ADMIN CRUD
# -----------------------------------------------------------------------------
def test_catalogue_management(admin_token, student_token):
    # Retrieve catalogue
    res = client.get("/api/v1/recommendations/catalogue", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 11

    # Student cannot create catalogue item
    payload = {
        "title": "Custom Cloud Security Bootcamp",
        "category": "TECHNICAL_CERTIFICATIONS",
        "description": "Intensive hands-on lab series for cloud security engineers.",
        "difficulty_level": "Advanced",
        "provider": "AWS / Linux Foundation",
        "resource_url": "https://aws.amazon.com/security",
        "estimated_duration": "4 Weeks",
        "status": "Active",
    }
    unauth = client.post(
        "/api/v1/recommendations/catalogue",
        json=payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert unauth.status_code == 403

    # Admin creates catalogue item
    auth_res = client.post(
        "/api/v1/recommendations/catalogue",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert auth_res.status_code == 201
    created = auth_res.json()
    assert created["title"] == payload["title"]

    # Admin updates catalogue item
    update_res = client.put(
        f"/api/v1/recommendations/catalogue/{created['id']}",
        json={"estimated_duration": "6 Weeks"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["estimated_duration"] == "6 Weeks"

    # Admin deletes catalogue item
    del_res = client.delete(
        f"/api/v1/recommendations/catalogue/{created['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_res.status_code == 204


# -----------------------------------------------------------------------------
# 2. TEST WEAK SUBJECT PERFORMANCE RECOMMENDATION
# -----------------------------------------------------------------------------
def test_weak_subject_performance_recommendation():
    db = _tenant_session(SessionLocal())
    try:
        uniq_id = int(time.time() * 1000) % 1000000
        user = User(
            email=f"weak_subj_{uniq_id}@test.com",
            full_name="Weak Subject Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            roll_number=f"ROLL_WEAK_{uniq_id}",
            usn=f"USN_WEAK_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=5,
            section="A",
            status="Active",
            career_goals=["Full Stack Developer"],
        )
        db.add(student)
        db.flush()

        # Subject: Database Management Systems (CS501) with poor score (38/100)
        subject = db.query(Subject).first()
        subj_id = subject.id if subject else 1

        res_db = SubjectResult(
            student_id=student.id,
            subject_id=subj_id,
            semester_id=1,
            internal_marks=14.0,
            external_marks=24.0,
            total_marks=38.0,
            letter_grade="F",
            grade_point=0.0,
            is_backlog=True,
        )
        db.add(res_db)
        db.commit()

        # Generate recommendations
        recs = RecommendationService.generate_recommendations_for_student(db, student_id=student.id)
        assert len(recs) > 0

        # Verify a subject improvement recommendation was created for this weak subject
        weak_rec = next((r for r in recs if r.category == "SUBJECT_IMPROVEMENT"), None)
        assert weak_rec is not None, "Student with weak subject score must receive SUBJECT_IMPROVEMENT recommendation."
        assert weak_rec.gap_type == "ACADEMIC_WEAKNESS"
        assert "vulnerability" in weak_rec.reason.lower() or "score" in weak_rec.reason.lower()
        assert weak_rec.priority in ["HIGH", "CRITICAL"]

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 3. TEST MISSING TECHNICAL SKILLS RECOMMENDATION
# -----------------------------------------------------------------------------
def test_missing_technical_skills_recommendation():
    db = _tenant_session(SessionLocal())
    try:
        uniq_id = int(time.time() * 1000) % 1000000
        user = User(
            email=f"skill_gap_{uniq_id}@test.com",
            full_name="Skill Gap Student",
            hashed_password="hash",
            role="student",
            is_active=True,
            department_id=1,
        )
        db.add(user)
        db.flush()

        # Career Goal: AI/ML Engineer (requires Python, Machine Learning, PyTorch, Pandas)
        student = Student(
            user_id=user.id,
            roll_number=f"ROLL_GAP_{uniq_id}",
            usn=f"USN_GAP_{uniq_id}",
            department_id=1,
            batch_year=2024,
            current_semester=4,
            section="A",
            status="Active",
            career_goals=["AI/ML Engineer"],
            interests=["Deep Learning"],
        )
        db.add(student)
        db.flush()

        # Student only knows C and HTML (missing Python, PyTorch, Machine Learning)
        c_skill = db.query(Skill).filter(Skill.name == "C").first()
        if c_skill:
            st_skill = StudentSkill(student_id=student.id, skill_id=c_skill.id, proficiency_level="Intermediate")
            db.add(st_skill)
        db.commit()

        recs = RecommendationService.generate_recommendations_for_student(db, student_id=student.id)
        assert len(recs) > 0

        # Should recommend learning courses for missing AI/ML skills
        skill_rec = next((r for r in recs if r.gap_type == "SKILL_DEFICIT"), None)
        assert skill_rec is not None, "Student with missing skills for career goal must receive SKILL_DEFICIT recommendation."
        assert "AI/ML Engineer" in skill_rec.reason
        assert skill_rec.status == "SUGGESTED"

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 4. TEST HEALTHY NO-GAP STUDENT
# -----------------------------------------------------------------------------
def test_healthy_no_gap_student():
    db = _tenant_session(SessionLocal())
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
            current_semester=2,
            section="A",
            status="Active",
            cgpa=9.5,
            attendance_percentage=96.0,
            career_goals=[],
            interests=[],
        )
        db.add(student)
        db.commit()

        # Engine should generate advanced competitive challenge recommendations without crashing
        recs = RecommendationService.generate_recommendations_for_student(db, student_id=student.id)
        assert len(recs) >= 1
        assert any("outstanding" in r.reason.lower() or "advanced" in r.reason.lower() for r in recs)

    finally:
        db.close()


# -----------------------------------------------------------------------------
# 5. TEST ACCEPTED & COMPLETED RECOMMENDATIONS WORKFLOW
# -----------------------------------------------------------------------------
def test_recommendation_lifecycle_and_feedback(student_token):
    # Get student's recommendations
    res = client.get("/api/v1/recommendations/", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) > 0
    rec = recs[0]
    rec_id = rec["id"]

    # Student accepts recommendation
    accept_res = client.post(
        f"/api/v1/recommendations/{rec_id}/accept",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"

    # Student logs progress: In Progress 50%
    prog_res = client.post(
        f"/api/v1/recommendations/{rec_id}/progress",
        json={"status": "IN_PROGRESS", "percent_complete": 50, "notes": "Halfway through module lectures.", "hours_spent": 6.5},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert prog_res.status_code == 200
    assert prog_res.json()["status"] == "IN_PROGRESS"

    # Student completes recommendation: 100%
    comp_res = client.post(
        f"/api/v1/recommendations/{rec_id}/progress",
        json={"status": "COMPLETED", "percent_complete": 100, "notes": "Completed and passed certification quiz.", "hours_spent": 14.0},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"

    # Student submits 5-star feedback
    fb_res = client.post(
        f"/api/v1/recommendations/{rec_id}/feedback",
        json={"rating": 5, "helpful": True, "relevance_score": 5, "comments": "Very relevant and practical course.", "outcome_achieved": True},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["rating"] == 5
    assert fb_res.json()["outcome_achieved"] is True


# -----------------------------------------------------------------------------
# 6. TEST UNAUTHORIZED CROSS-STUDENT ACCESS
# -----------------------------------------------------------------------------
def test_unauthorized_student_access(student_token):
    # Fetch own profile to get own ID
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    student_id = me_res.json()["student_id"]

    other_student_id = student_id + 1

    # Student cannot view another student's learning roadmap
    unauth_roadmap = client.get(
        f"/api/v1/recommendations/students/{other_student_id}/learning-path",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert unauth_roadmap.status_code == 403

    # Student cannot update another student's career profile
    unauth_update = client.put(
        f"/api/v1/recommendations/students/{other_student_id}/career-profile",
        json={"career_goals": ["Hacker"], "interests": ["Gaming"]},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert unauth_update.status_code == 403


# -----------------------------------------------------------------------------
# 7. TEST MENTOR SUGGESTION WORKFLOW
# -----------------------------------------------------------------------------
def test_mentor_suggest_and_guidance(faculty_token, admin_token):
    # Faculty suggests custom resource for student 1
    suggest_res = client.post(
        "/api/v1/recommendations/suggest",
        json={
            "student_id": 1,
            "title": "Faculty Directed Graph Algorithms Intensive",
            "category": "PROGRAMMING_PRACTICE",
            "reason": "Faculty identified graph traversal weakness in Semester 3 data structures.",
            "gap_type": "ACADEMIC_WEAKNESS",
            "gap_detail": "Graph BFS/DFS & Dijkstra shortest path",
            "expected_outcome": "Implement Dijkstra and A* pathfinding with adjacency lists.",
            "priority": "HIGH",
            "resource_url": "https://leetcode.com/tag/graph/",
            "suggested_completion_time": "2 Weeks",
            "mentor_guidance_notes": "Focus on cycle detection in directed graphs first.",
        },
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert suggest_res.status_code == 201
    rec_id = suggest_res.json()["recommendation_id"]

    # Faculty adds further coaching notes
    guidance_res = client.post(
        f"/api/v1/recommendations/{rec_id}/guidance",
        json={"guidance_notes": "Reviewed in office hours. Ready for topological sort."},
        headers={"Authorization": f"Bearer {faculty_token}"},
    )
    assert guidance_res.status_code == 200
    assert "topological sort" in guidance_res.json()["guidance_notes"]
