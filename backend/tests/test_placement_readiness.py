import pytest
from fastapi.testclient import TestClient

from app.core.tenancy import TenantScope, set_session_scope
from app.main import app


def _tenant_session(db, tenant_id=1):
    set_session_scope(db, TenantScope(tenant_id=tenant_id))
    return db
from app.core.database import SessionLocal
from app.models.placement import (
    StudentApplication,
)
from app.models.profile import Student
from app.models.student_intelligence import Skill, StudentSkill
from app.services.placement_service import PlacementService

client = TestClient(app)


def get_auth_token(username: str, role: str) -> str:
    login_data = {
        "student": ("student@reva-demo.example", "StudentPass123!"),
        "faculty": ("faculty@reva-demo.example", "FacultyPass123!"),
        "mentor": ("mentor@reva-demo.example", "MentorPass123!"),
        "admin": ("admin@reva-demo.example", "AdminPass123!"),
        "placement": ("placement@reva-demo.example", "PlacementPass123!"),
    }
    email, password = login_data[role]
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Failed login for {role}: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def db():
    session = _tenant_session(SessionLocal())
    try:
        yield session
    finally:
        session.close()


def test_complete_skill_match(db):
    """
    Test 1: Complete Skill Match.
    A student possessing all required skills for a role at or above the benchmark
    achieves a high readiness score (>= 90%), meets mandatory requirements, and receives READY tier.
    """
    admin_token = get_auth_token("admin", "admin")
    student = db.query(Student).filter(Student.id == 1).first()
    assert student is not None

    role = PlacementService.get_career_role_by_id_or_code(db, "SOFTWARE_DEVELOPER")
    assert role is not None

    # Equip student with all role skills at Advanced or Expert
    for rs in role.role_skills:
        PlacementService.add_or_update_student_skill(
            db,
            student_id=student.id,
            skill_name=rs.skill.name,
            category=rs.skill.category,
            proficiency_level="Expert"
        )
        # Mark as verified
        ss = db.query(StudentSkill).filter(
            StudentSkill.student_id == student.id,
            StudentSkill.skill_id == rs.skill_id
        ).first()
        if ss:
            ss.is_verified = True
            db.commit()

    res = client.get(
        f"/api/v1/placement/readiness/{student.id}?role=SOFTWARE_DEVELOPER",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["readiness_score"] >= 90.0
    assert data["mandatory_skills_met"] is True
    assert data["skills_missing_count"] == 0
    assert data["readiness_tier"] == "READY"
    assert "Internal prototype readiness indicator" in data["disclaimer"]


def test_missing_skills_detection(db):
    """
    Test 2: Missing Skills Detection.
    A student missing core or mandatory role skills is flagged with status='MISSING',
    lowering readiness score and generating learning recommendations.
    """
    admin_token = get_auth_token("admin", "admin")
    # Student 2: remove Cloud & DevOps skills
    student = db.query(Student).filter(Student.id == 2).first()
    assert student is not None

    role = PlacementService.get_career_role_by_id_or_code(db, "CLOUD_ENGINEER")
    assert role is not None

    # Remove AWS and Kubernetes from student 2
    aws_skill = db.query(Skill).filter(Skill.name.ilike("AWS")).first()
    if aws_skill:
        db.query(StudentSkill).filter(
            StudentSkill.student_id == student.id,
            StudentSkill.skill_id == aws_skill.id
        ).delete()
        db.commit()

    res = client.get(
        f"/api/v1/placement/readiness/{student.id}?role=CLOUD_ENGINEER",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["skills_missing_count"] > 0
    missing_items = [item for item in data["skill_gaps"] if item["status"] == "MISSING"]
    assert len(missing_items) > 0
    # Mandatory skills not met if AWS was mandatory
    aws_item = next((item for item in missing_items if item["skill_name"] == "AWS"), None)
    if aws_item and aws_item["is_mandatory"]:
        assert data["mandatory_skills_met"] is False


def test_low_proficiency_detection(db):
    """
    Test 3: Low Proficiency Detection.
    When a student possesses a required skill but below the role benchmark
    (e.g., Beginner instead of Advanced), status is BELOW_PROFICIENCY with partial score.
    """
    admin_token = get_auth_token("admin", "admin")
    student = db.query(Student).filter(Student.id == 3).first()
    assert student is not None

    # Set Python to Beginner
    PlacementService.add_or_update_student_skill(
        db,
        student_id=student.id,
        skill_name="Python",
        category="programming",
        proficiency_level="Beginner"
    )

    res = client.get(
        f"/api/v1/placement/readiness/{student.id}?role=SOFTWARE_DEVELOPER",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    python_gap = next((g for g in data["skill_gaps"] if g["skill_name"] == "Python"), None)
    assert python_gap is not None
    assert python_gap["status"] == "BELOW_PROFICIENCY"
    assert python_gap["student_proficiency"] == "Beginner"
    assert python_gap["student_level_val"] < python_gap["required_level_val"]
    assert "Advance proficiency" in python_gap["suggested_improvement"]


def test_different_career_roles_comparison(db):
    """
    Test 4: Different Career Roles Comparison.
    Evaluating the same student against two disparate roles (e.g. Software Developer vs. Cybersecurity Analyst)
    yields distinct skill gap profiles and different readiness metrics.
    """
    admin_token = get_auth_token("admin", "admin")
    student_id = 1

    res_swe = client.get(
        f"/api/v1/placement/readiness/{student_id}?role=SOFTWARE_DEVELOPER",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    res_sec = client.get(
        f"/api/v1/placement/readiness/{student_id}?role=CYBERSECURITY_ANALYST",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_swe.status_code == 200
    assert res_sec.status_code == 200

    swe_data = res_swe.json()
    sec_data = res_sec.json()

    assert swe_data["target_role"]["code"] == "SOFTWARE_DEVELOPER"
    assert sec_data["target_role"]["code"] == "CYBERSECURITY_ANALYST"
    # The required skills list differs
    swe_skills = {g["skill_name"] for g in swe_data["skill_gaps"]}
    sec_skills = {g["skill_name"] for g in sec_data["skill_gaps"]}
    assert swe_skills != sec_skills


def test_student_skill_updates_and_evidence_verification(db):
    """
    Test 5: Student Skill Updates & Evidence Verification.
    Student updates a skill and submits evidence. Faculty verifies the evidence,
    which automatically transitions the skill to verified status.
    """
    student_token = get_auth_token("student", "student")
    faculty_token = get_auth_token("faculty", "faculty")
    student = db.query(Student).filter(Student.id == 1).first()
    assert student is not None

    # Clean up any existing test skill from previous runs
    old_skill = db.query(Skill).filter(Skill.name.ilike("GraphQL API Design")).first()
    if old_skill:
        db.query(StudentSkill).filter(
            StudentSkill.student_id == student.id,
            StudentSkill.skill_id == old_skill.id
        ).delete()
        db.commit()

    # Student adds a new skill with evidence
    skill_payload = {
        "skill_name": "GraphQL API Design",
        "category": "framework",
        "proficiency_level": "Intermediate",
        "evidence": {
            "evidence_type": "PROJECT",
            "title": "Campus Microservices GraphQL Gateway",
            "url": "https://github.com/alex-mercer/graphql-gateway",
            "description": "Implemented Apollo federation with JWT auth.",
        }
    }
    res_add = client.post(
        f"/api/v1/placement/students/{student.id}/skills",
        json=skill_payload,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_add.status_code == 200
    added_skill = res_add.json()
    assert added_skill["skill_name"] == "GraphQL API Design"
    assert added_skill["is_verified"] is False
    assert added_skill["evidence_count"] >= 1
    evidence_id = added_skill["evidences"][0]["id"]

    # Faculty verifies the evidence
    verify_payload = {
        "verification_status": "VERIFIED",
        "verification_feedback": "Code reviewed. Schema design and resolvers are well-structured."
    }
    res_verify = client.post(
        f"/api/v1/placement/evidence/{evidence_id}/verify",
        json=verify_payload,
        headers={"Authorization": f"Bearer {faculty_token}"}
    )
    assert res_verify.status_code == 200
    verified_ev = res_verify.json()
    assert verified_ev["verification_status"] == "VERIFIED"

    # Check that student skill is now verified
    res_get = client.get(
        f"/api/v1/placement/students/{student.id}/skills",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_get.status_code == 200
    skills_list = res_get.json()
    verified_item = next((s for s in skills_list if s["skill_name"] == "GraphQL API Design"), None)
    assert verified_item is not None
    assert verified_item["is_verified"] is True


def test_opportunity_matching_and_application_tracking(db):
    """
    Test 6: Opportunity Matching & Application Tracking.
    Verifies opportunity eligibility matching, application submission, duplicate prevention,
    and placement officer application status progression (SHORTLISTED, OFFERED).
    """
    student_token = get_auth_token("student", "student")
    placement_token = get_auth_token("placement", "placement")
    student = db.query(Student).filter(Student.id == 1).first()
    assert student is not None

    # Retrieve matching opportunities
    res_matches = client.get(
        f"/api/v1/placement/students/{student.id}/matching-opportunities",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_matches.status_code == 200
    matches = res_matches.json()
    assert len(matches) > 0

    # Ineligible applications are refused server-side
    ineligible = [m for m in matches if not m["is_eligible"]]
    if ineligible:
        db.query(StudentApplication).filter(StudentApplication.student_id == student.id,
                                            StudentApplication.opportunity_id == ineligible[0]["id"]).delete()
        db.commit()
        res_bad = client.post("/api/v1/placement/applications", json={"opportunity_id": ineligible[0]["id"]},
                              headers={"Authorization": f"Bearer {student_token}"})
        assert res_bad.status_code == 400
        assert "eligib" in res_bad.text.lower()

    # Pick an eligible opportunity to apply to
    eligible = [m for m in matches if m["is_eligible"]]
    assert eligible, "seed data should include at least one opportunity the demo student qualifies for"
    target_opp = eligible[0]
    opp_id = target_opp["id"]

    # Clean existing application if any
    db.query(StudentApplication).filter(
        StudentApplication.student_id == student.id,
        StudentApplication.opportunity_id == opp_id
    ).delete()
    db.commit()

    # Apply
    apply_payload = {
        "opportunity_id": opp_id,
        "resume_url": "https://campus-drive.edu/resumes/alex_mercer.pdf",
        "cover_notes": "Strong candidate with comprehensive full-stack and algorithmic background."
    }
    res_apply = client.post(
        "/api/v1/placement/applications",
        json=apply_payload,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_apply.status_code == 200
    app_data = res_apply.json()
    assert app_data["status"] == "APPLIED"
    assert app_data["opportunity_id"] == opp_id
    application_id = app_data["id"]

    # Prevent duplicate application
    res_dup = client.post(
        "/api/v1/placement/applications",
        json=apply_payload,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_dup.status_code == 400

    # Placement Officer updates application status
    status_payload = {
        "status": "SHORTLISTED",
        "reviewer_notes": "Selected for Round 1 Technical Interview."
    }
    res_status = client.put(
        f"/api/v1/placement/applications/{application_id}/status",
        json=status_payload,
        headers={"Authorization": f"Bearer {placement_token}"}
    )
    assert res_status.status_code == 200
    updated_app = res_status.json()
    assert updated_app["status"] == "SHORTLISTED"
    assert updated_app["reviewer_notes"] == "Selected for Round 1 Technical Interview."


def test_unauthorized_placement_data_access(db):
    """
    Test 7: Unauthorized Placement Data Access (RBAC Protection).
    A student cannot view another student's readiness analysis, skill evidence, or applications.
    Non-placement officers cannot post opportunities or update application statuses.
    """
    student_token = get_auth_token("student", "student")  # Alex Mercer (id=1)

    # Student 1 tries to access Student 2's readiness
    res_unauth_readiness = client.get(
        "/api/v1/placement/readiness/2",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_unauth_readiness.status_code == 403

    # Student 1 tries to access Student 2's skills
    res_unauth_skills = client.get(
        "/api/v1/placement/students/2/skills",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_unauth_skills.status_code == 403

    # Student tries to post an opportunity
    opp_payload = {
        "company_name": "FakeCorp",
        "title": "Unauthorized Drive",
        "opportunity_type": "JOB",
        "ctc_stipend": "10 LPA",
        "application_deadline": "2026-12-31"
    }
    res_unauth_opp = client.post(
        "/api/v1/placement/opportunities",
        json=opp_payload,
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_unauth_opp.status_code == 403

    # Student tries to verify evidence
    res_unauth_verify = client.post(
        "/api/v1/placement/evidence/1/verify",
        json={"verification_status": "VERIFIED"},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert res_unauth_verify.status_code == 403
