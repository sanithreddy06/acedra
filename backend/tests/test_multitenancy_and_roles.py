"""Cross-tenant isolation and role enforcement, attacked through the public API."""
from app.core.database import SessionLocal
from app.core.tenancy import TenantScope, set_session_scope
from app.models import Document, RiskAlert, Student, User
from app.models.platform import University

REVA_ADMIN = "anitha.rao@reva.in"
NF_ADMIN = "admin@northfield.example"
REVA_STUDENT = "aarav.sharma@reva.in"
NF_STUDENT = "student@northfield.example"
DT_STUDENT = "student@deccan-tech.example"
SUPER = "superadmin@acedra.example"


def _ids():
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    unis = {u.slug: u.id for u in db.query(University).all()}
    reva_student = db.query(Student).filter(Student.university_id == unis["reva"]).order_by(Student.id).first().id
    nf_students = [s.id for s in db.query(Student).filter(Student.university_id == unis["northfield"]).all()]
    reva_alert = db.query(RiskAlert).filter(RiskAlert.university_id == unis["reva"]).first().id
    reva_doc = db.query(Document).filter(Document.university_id == unis["reva"]).first().id
    reva_user = db.query(User).filter(User.email == REVA_STUDENT).first().id
    db.close()
    return unis, reva_student, nf_students, reva_alert, reva_doc, reva_user


def test_university_admin_sees_only_own_students(client, auth):
    unis, reva_student, nf_students, *_ = _ids()
    r = client.get("/api/v1/students/?limit=1000", headers=auth(NF_ADMIN))
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()}
    assert ids and ids <= set(nf_students)
    assert reva_student not in ids


def test_cross_tenant_record_access_is_not_found(client, auth):
    _, reva_student, _, reva_alert, reva_doc, reva_user = _ids()
    h = auth(NF_ADMIN)
    for path in (f"/api/v1/students/{reva_student}", f"/api/v1/students/{reva_student}/analytics",
                 f"/api/v1/risk/students/{reva_student}", f"/api/v1/risk/alerts/{reva_alert}",
                 f"/api/v1/ai/documents/{reva_doc}", f"/api/v1/users/{reva_user}",
                 f"/api/v1/placement/readiness/{reva_student}"):
        r = client.get(path, headers=h)
        assert r.status_code == 404, (path, r.status_code, r.text)


def test_cross_tenant_writes_are_blocked(client, auth):
    _, reva_student, _, reva_alert, _, reva_user = _ids()
    h = auth(NF_ADMIN)
    assert client.patch(f"/api/v1/users/{reva_user}", json={"is_active": False}, headers=h).status_code == 404
    assert client.post(f"/api/v1/risk/alerts/{reva_alert}/acknowledge", json={"notes": "x"}, headers=h).status_code == 404
    assert client.patch(f"/api/v1/students/{reva_student}", json={"section": "Z"}, headers=h).status_code == 404


def test_rag_retrieval_is_tenant_isolated(client, auth):
    r = client.get("/api/v1/ai/rag/search?q=attendance condonation policy", headers=auth(NF_STUDENT))
    assert r.status_code == 200
    titles = [p["document_title"] for p in r.json()["results"]]
    assert titles and all("REVA" not in t for t in titles)
    assert any("Northfield" in t for t in titles)


def test_tenant_configuration_differs(client, auth):
    reva = client.get("/api/v1/tenant/profile", headers=auth(REVA_ADMIN)).json()
    nf = client.get("/api/v1/tenant/profile", headers=auth(NF_ADMIN)).json()
    assert reva["name"] != nf["name"]
    assert nf["academic_structure"]["minimum_attendance_percent"] == 80
    assert reva["academic_structure"]["minimum_attendance_percent"] == 75
    assert reva["acedra_contact"]["email"] != nf["acedra_contact"]["email"]
    rules = client.get("/api/v1/risk/rules", headers=auth(NF_ADMIN)).json()
    att = [r for r in rules if r["indicator_type"] == "attendance_percentage" and r["operator"] in ("<", "<=")]
    assert att and att[0]["threshold_value"] == 80.0


def test_disabled_module_is_blocked(client, auth):
    r = client.get("/api/v1/recommendations/", headers=auth(DT_STUDENT))
    assert r.status_code == 403
    assert "not enabled" in r.json()["detail"]
    assert client.get("/api/v1/risk/alerts", headers=auth(DT_STUDENT)).status_code == 200


def test_student_cannot_reach_admin_or_platform_endpoints(client, auth):
    h = auth(REVA_STUDENT)
    assert client.get("/api/v1/users/", headers=h).status_code == 403
    assert client.post("/api/v1/users/invite", json={"email": "x@reva.in", "full_name": "X Y",
                                                     "role": "admin"}, headers=h).status_code == 403
    assert client.patch("/api/v1/tenant/settings", json={"tagline": "pwned"}, headers=h).status_code == 403
    assert client.post("/api/v1/risk/rules", json={}, headers=h).status_code in (403, 422)
    assert client.get("/api/v1/platform/universities", headers=h).status_code == 404
    assert client.get("/api/v1/audit-logs/", headers=h).status_code == 403
    profile = client.get("/api/v1/tenant/profile", headers=h).json()
    assert "acedra_contact" not in profile and "domains" not in profile


def test_university_admin_cannot_use_platform_or_assign_platform_roles(client, auth):
    h = auth(REVA_ADMIN)
    assert client.get("/api/v1/platform/overview", headers=h).status_code == 404
    assert client.post("/api/v1/platform/universities/1/primary-employee", json={"employee_id": 1},
                       headers=h).status_code == 404
    r = client.post("/api/v1/users/invite", json={"email": "evil@reva.in", "full_name": "Evil",
                                                  "role": "platform_admin"}, headers=h)
    assert r.status_code == 422
    r = client.patch("/api/v1/tenant/settings", json={"academic_structure": {"cgpa_max": 4}}, headers=h)
    assert r.status_code == 403


def test_faculty_limited_to_assigned_sections(client, auth):
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    from app.core.access import accessible_student_ids
    fac = db.query(User).filter(User.email == "faculty@northfield.example").first()
    allowed = accessible_student_ids(db, fac)
    nf = db.query(University).filter(University.slug == "northfield").first()
    others = [s.id for s in db.query(Student).filter(Student.university_id == nf.id).all() if s.id not in allowed]
    db.close()
    h = auth("faculty@northfield.example")
    assert allowed and others
    assert client.get(f"/api/v1/students/{next(iter(allowed))}", headers=h).status_code == 200
    assert client.get(f"/api/v1/students/{others[0]}", headers=h).status_code == 403
    listed = {s["id"] for s in client.get("/api/v1/students/?limit=1000", headers=h).json()}
    assert listed <= allowed


def test_mentor_limited_to_mentees(client, auth):
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    nf = db.query(University).filter(University.slug == "northfield").first()
    from app.models import Mentor
    mentor = db.query(Mentor).filter(Mentor.university_id == nf.id).first()
    mentee = db.query(Student).filter(Student.assigned_mentor_id == mentor.id).first().id
    other = db.query(Student).filter(Student.university_id == nf.id, Student.assigned_mentor_id.is_(None)).first().id
    db.close()
    h = auth("mentor@northfield.example")
    assert client.get(f"/api/v1/risk/students/{mentee}", headers=h).status_code == 200
    assert client.get(f"/api/v1/risk/students/{other}", headers=h).status_code == 403
    alerts = client.get("/api/v1/risk/alerts?limit=100", headers=h).json()
    items = alerts["alerts"] if isinstance(alerts, dict) and "alerts" in alerts else alerts.get("items", alerts)
    assert all(a["student_id"] != other for a in items)


def test_student_sees_only_self_everywhere(client, auth):
    h = auth(NF_STUDENT)
    me = client.get("/api/v1/auth/me", headers=h).json()
    students = client.get("/api/v1/students/", headers=h).json()
    assert [s["id"] for s in students] == [me["student_id"]]
    recs = client.get("/api/v1/recommendations/", headers=h).json()
    recs = recs.get("items", recs) if isinstance(recs, dict) else recs
    assert all(r["student_id"] == me["student_id"] for r in recs)


def test_platform_accounts_cannot_read_student_records(client, auth):
    h = auth(SUPER)
    assert client.get("/api/v1/students/", headers=h).status_code == 403
    assert client.get("/api/v1/risk/alerts", headers=h).status_code == 403
    uni = client.get("/api/v1/platform/universities", headers=h).json()[0]
    r = client.get(f"/api/v1/platform/universities/{uni['id']}/student-directory", headers=h)
    assert r.status_code == 403  # configuration authority never implies student-data access


def test_conversations_are_private_to_their_owner(client, auth):
    a = auth(REVA_STUDENT)
    conv = client.post("/api/v1/ai/conversations", json={"mode": "PERSONAL_MODE_B", "title": "mine"}, headers=a).json()
    other = auth("rohan.iyer@reva.in")
    assert client.get(f"/api/v1/ai/conversations/{conv['id']}", headers=other).status_code == 404
    assert client.post(f"/api/v1/ai/conversations/{conv['id']}/messages", json={"content": "my cgpa?"},
                       headers=other).status_code == 404
    assert client.delete(f"/api/v1/ai/conversations/{conv['id']}", headers=auth(REVA_ADMIN)).status_code == 404
    assert client.get(f"/api/v1/ai/conversations/{conv['id']}", headers=a).status_code == 200


def test_staff_personal_mode_requires_authorised_student(client, auth):
    h = auth("mentor@northfield.example")
    conv = client.post("/api/v1/ai/conversations", json={"mode": "PERSONAL_MODE_B"}, headers=h).json()
    r = client.post(f"/api/v1/ai/conversations/{conv['id']}/messages", json={"content": "summary"}, headers=h)
    assert r.status_code == 422
    _, reva_student, *_ = _ids()
    r = client.post(f"/api/v1/ai/conversations/{conv['id']}/messages",
                    json={"content": "summary", "student_id": reva_student}, headers=h)
    assert r.status_code in (403, 404)


def test_personal_assistant_uses_real_record_and_tenant_threshold(client, auth):
    h = auth(NF_STUDENT)
    me = client.get("/api/v1/auth/me", headers=h).json()
    analytics = client.get(f"/api/v1/students/{me['student_id']}/analytics", headers=h).json()
    expected = analytics["metrics"]["calculated_attendance_percentage"]
    conv = client.post("/api/v1/ai/conversations", json={"mode": "PERSONAL_MODE_B"}, headers=h).json()
    reply = client.post(f"/api/v1/ai/conversations/{conv['id']}/messages",
                        json={"content": "What is my attendance?"}, headers=h).json()
    assert f"{expected}%" in reply["content"]
    assert "requirement 80%" in reply["content"]  # Northfield's configured threshold, not a hard-coded 75
    assert reply["generation_mode"] == "offline_fallback"
