"""End-to-end institutional workflow: enquiry → agreement → tenant → employee → admin → activation → users."""
import re
from datetime import timedelta

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.core.tenancy import TenantScope, set_session_scope
from app.models import AuditLog, User
from app.models.platform import EmailMessage
from tests.conftest import legal_versions

SUPER = "superadmin@acedra.example"
EMP_ARJUN = "arjun.rao@acedra.example"
EMP_FATIMA = "fatima.sheikh@acedra.example"
EMP_VIKRAM = "vikram.nair@acedra.example"


def latest_token(to_email: str, template: str) -> str:
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    msg = db.query(EmailMessage).filter(EmailMessage.to_email == to_email.lower(), EmailMessage.template == template) \
        .order_by(EmailMessage.id.desc()).first()
    db.close()
    assert msg, f"no {template} email for {to_email}"
    return re.search(r"token=([A-Za-z0-9_\-]+)", msg.body_text).group(1)


ENQUIRY = {
    "university_name": "Greenfield University", "official_website": "https://greenfield.example",
    "institution_type": "Private university", "location": "Mysuru, Karnataka", "student_population": "2,000 – 5,000",
    "department_count": 6, "campus_count": 1, "contact_name": "Dr. Asha Rao", "contact_designation": "Registrar",
    "contact_email": "registrar@greenfield.example", "contact_phone": "+91 821 000 0000",
    "preferred_contact_method": "email", "requested_modules": ["student_intelligence", "risk_identification",
                                                               "ai_assistant"],
    "existing_sis": "Spreadsheets", "has_student_emails": False, "email_provisioning": "rio_assisted",
    "accounts_required": 800, "institutional_requirements": "Early warning for first-years.",
    "expected_outcomes": "Reduce attendance shortfall.", "consent_to_contact": True,
}


def _ids_by_email(*emails):
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    out = [db.query(User).filter(User.email == e).first().id for e in emails]
    db.close()
    return out


def test_public_enquiry_validation(client):
    bad = dict(ENQUIRY, requested_modules=["chatbot_for_everyone"])
    assert client.post("/api/v1/public/enquiries", json=bad).status_code == 422
    no_consent = dict(ENQUIRY, consent_to_contact=False)
    assert client.post("/api/v1/public/enquiries", json=no_consent).status_code == 422


def test_full_onboarding_workflow(client, auth):
    # 1–3. University submits an enquiry from the public website; it is persisted
    r = client.post("/api/v1/public/enquiries", json=ENQUIRY)
    assert r.status_code == 201, r.text
    ref = r.json()["reference"]
    assert r.json()["email_service_estimate"]["accounts"] == 800

    sa = auth(SUPER)
    # 4. Platform super administrator sees it
    found = client.get(f"/api/v1/platform/enquiries?search={ref}", headers=sa).json()["items"]
    assert len(found) == 1 and found[0]["status"] == "new"
    eid = found[0]["id"]

    # 5–7. Review, contact, meeting, requirements
    for st in ("under_review", "contacted"):
        assert client.post(f"/api/v1/platform/enquiries/{eid}/status", json={"status": st}, headers=sa).status_code == 200
    client.post(f"/api/v1/platform/enquiries/{eid}/activities",
                json={"kind": "meeting", "body": "Discovery call with registrar", "meeting_at": "2026-11-20T10:00:00"},
                headers=sa)
    detail = client.post(f"/api/v1/platform/enquiries/{eid}/activities",
                         json={"kind": "requirements", "body": "Pilot with 2 departments."}, headers=sa).json()
    assert detail["status"] == "meeting_scheduled"
    assert detail["finalized_requirements"] == "Pilot with 2 departments."

    # Approval requires a recorded agreement
    assert client.post(f"/api/v1/platform/enquiries/{eid}/status", json={"status": "approved"},
                       headers=sa).status_code == 422
    # 8–9. Requirements finalised, agreement recorded
    client.post(f"/api/v1/platform/enquiries/{eid}/agreement",
                json={"reference": "ACD-SA-TEST-01", "agreed_modules": ["student_intelligence", "risk_identification"]},
                headers=sa)
    r = client.post(f"/api/v1/platform/enquiries/{eid}/status", json={"status": "approved"}, headers=sa)
    assert r.status_code == 200 and r.json()["status"] == "approved"

    # Employees cannot create tenants
    arjun_id, fatima_id, vikram_id = _ids_by_email(EMP_ARJUN, EMP_FATIMA, EMP_VIKRAM)
    body = {"short_name": "Greenfield", "slug": "greenfield", "domains": ["greenfield.example"],
            "primary_employee_id": fatima_id}
    assert client.post(f"/api/v1/platform/enquiries/{eid}/create-tenant", json=body,
                       headers=auth(EMP_ARJUN)).status_code == 403
    # 10–11. Tenant created with a dedicated employee
    r = client.post(f"/api/v1/platform/enquiries/{eid}/create-tenant", json=body, headers=sa)
    assert r.status_code == 201, r.text
    uni = r.json()
    uid = uni["id"]
    assert uni["status"] == "onboarding"
    assert uni["primary_employee"]["id"] == fatima_id
    assert uni["enabled_modules"] == ["student_intelligence", "risk_identification"]
    assert client.get(f"/api/v1/platform/enquiries/{eid}", headers=sa).json()["status"] == "onboarding"
    prov = client.get(f"/api/v1/platform/universities/{uid}/provisioning", headers=sa).json()
    assert prov and prov[0]["is_chargeable"] and prov[0]["method"] == "rio_assisted"

    # Configuration permissions: unassigned employee cannot configure; assigned employee can
    assert client.patch(f"/api/v1/platform/universities/{uid}", json={"tagline": "x"},
                        headers=auth(EMP_ARJUN)).status_code == 403
    fat = auth(EMP_FATIMA)
    r = client.patch(f"/api/v1/platform/universities/{uid}",
                     json={"tagline": "Learning, measured kindly", "academic_structure": {"minimum_attendance_percent": 85}},
                     headers=fat)
    assert r.status_code == 200 and r.json()["academic_structure"]["minimum_attendance_percent"] == 85
    # ...but cannot change the primary employee
    assert client.post(f"/api/v1/platform/universities/{uid}/primary-employee", json={"employee_id": arjun_id},
                       headers=fat).status_code == 403
    # coordination-only employee cannot configure even if assigned later
    assert client.patch(f"/api/v1/platform/universities/{uid}", json={"tagline": "y"},
                        headers=auth(EMP_VIKRAM)).status_code == 403

    # Activation is blocked until the checklist is complete
    assert client.post(f"/api/v1/platform/universities/{uid}/status", json={"status": "active"},
                       headers=sa).status_code == 422

    # 12–13. Initial administrator is provisioned by invitation (domain enforced)
    assert client.post(f"/api/v1/platform/universities/{uid}/admins",
                       json={"email": "head@gmail.com", "full_name": "Wrong Domain"}, headers=fat).status_code == 422
    r = client.post(f"/api/v1/platform/universities/{uid}/admins",
                    json={"email": "registrar.office@greenfield.example", "full_name": "Asha Rao", "title": "Registrar"},
                    headers=fat)
    assert r.status_code == 201, r.text
    # Uninvited/unverified admin cannot log in yet
    assert client.post("/api/v1/auth/login", json={"email": "registrar.office@greenfield.example",
                                                   "password": "whatever-123A"}).status_code in (401, 403)
    token = latest_token("registrar.office@greenfield.example", "invitation")
    info = client.get(f"/api/v1/auth/invitations/{token}").json()
    assert info["university_name"] == "Greenfield University" and info["role"] == "admin"
    assert (
        client.post(
            "/api/v1/auth/invitations/accept",
            json={"token": token, "password": "weak", "accepted_versions": legal_versions(client)},
        ).status_code
        == 422
    )
    r = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": token, "password": "Greenfield#2026", "accepted_versions": legal_versions(client)},
    )
    assert r.status_code == 200
    admin_h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    # token is single-use
    assert (
        client.post(
            "/api/v1/auth/invitations/accept",
            json={"token": token, "password": "Greenfield#2026", "accepted_versions": legal_versions(client)},
        ).status_code
        == 400
    )

    # Admin can configure during onboarding; other roles cannot sign in until activation
    client.post("/api/v1/tenant/departments", json={"code": "CSE", "name": "Computer Science"}, headers=admin_h)
    dept_id = client.get("/api/v1/tenant/departments", headers=admin_h).json()[0]["id"]
    r = client.post(
        "/api/v1/users/invite",
        json={
            "email": "first.student@greenfield.example",
            "full_name": "First Student",
            "role": "student",
            "department_id": dept_id,
            "usn": "GF24CS001",
            "current_semester": 1,
        },
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    # domain matching alone grants nothing — and non-matching domains are refused
    assert (
        client.post(
            "/api/v1/users/invite",
            json={"email": "someone@yahoo.com", "full_name": "Outsider", "role": "faculty", "department_id": dept_id},
            headers=admin_h,
        ).status_code
        == 422
    )
    assert client.post(
        "/api/v1/auth/login", json={"email": "first.student@greenfield.example", "password": "Anything#2026"}
    ).status_code in (401, 403)

    # 14. Activate
    r = client.post(f"/api/v1/platform/universities/{uid}/status", json={"status": "active"}, headers=sa)
    assert r.status_code == 200 and r.json()["status"] == "active"
    assert client.get(f"/api/v1/platform/enquiries/{eid}", headers=sa).json()["status"] == "active"

    stoken = latest_token("first.student@greenfield.example", "invitation")
    r = client.post(
        "/api/v1/auth/invitations/accept",
        json={"token": stoken, "password": "Student#Green1", "accepted_versions": legal_versions(client)},
    )
    assert r.status_code == 200
    sh = {"Authorization": f"Bearer {r.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=sh).json()
    assert me["role"] == "student" and me["university"]["name"] == "Greenfield University"
    assert len(client.get("/api/v1/students/", headers=sh).json()) == 1
    # Module agreed set is enforced
    assert client.get("/api/v1/placement/skills", headers=sh).status_code == 403

    # University admin sees their ACEDRA contact but cannot see other tenants
    prof = client.get("/api/v1/tenant/profile", headers=admin_h).json()
    assert prof["acedra_contact"]["email"] == EMP_FATIMA
    assert client.get("/api/v1/platform/universities", headers=admin_h).status_code == 404

    # Deactivation locks the workspace immediately
    client.post(f"/api/v1/platform/universities/{uid}/status", json={"status": "suspended"}, headers=sa)
    assert client.get("/api/v1/students/", headers=sh).status_code == 403


def test_student_data_grant_is_explicit_and_audited(client, auth):
    sa = auth(SUPER)
    (arjun_id,) = _ids_by_email(EMP_ARJUN)
    unis = client.get("/api/v1/platform/universities", headers=sa).json()
    nf = next(u for u in unis if u["slug"] == "northfield")
    emp = auth(EMP_ARJUN)
    assert client.get(f"/api/v1/platform/universities/{nf['id']}/student-directory", headers=emp).status_code == 403
    # employees cannot grant themselves access
    assert (
        client.post(
            f"/api/v1/platform/universities/{nf['id']}/grants",
            json={
                "employee_id": arjun_id,
                "reason": "Investigating an import error",
                "university_authorised_by": "Registrar",
            },
            headers=emp,
        ).status_code
        == 403
    )
    r = client.post(
        f"/api/v1/platform/universities/{nf['id']}/grants",
        json={
            "employee_id": arjun_id,
            "reason": "Investigating import discrepancy reported by registrar",
            "university_authorised_by": "Dr. Helen D'Souza (Registrar)",
            "days": 2,
        },
        headers=sa,
    )
    assert r.status_code == 201
    gid = r.json()["id"]
    r = client.get(f"/api/v1/platform/universities/{nf['id']}/student-directory", headers=emp)
    assert r.status_code == 200 and len(r.json()["students"]) == 14
    assert set(r.json()["students"][0]) == {"id", "full_name", "usn", "department", "semester", "status"}
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    assert db.query(AuditLog).filter(AuditLog.action == "STUDENT_DATA_ACCESSED").count() >= 1
    db.close()
    client.post(f"/api/v1/platform/grants/{gid}/revoke", headers=sa)
    assert client.get(f"/api/v1/platform/universities/{nf['id']}/student-directory", headers=emp).status_code == 403


def test_password_reset_logout_and_expiry(client, auth):
    email = "placement@northfield.example"
    r = client.post("/api/v1/auth/password-reset-request", json={"email": email})
    assert r.status_code == 200 and "reset_token" not in r.json()  # token is never returned over HTTP
    # unknown accounts get the same response
    assert (
        client.post("/api/v1/auth/password-reset-request", json={"email": "nobody@northfield.example"}).json()
        == r.json()
    )
    token = latest_token(email, "password_reset")
    assert (
        client.post("/api/v1/auth/password-reset-confirm", json={"token": token, "new_password": "short"}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/auth/password-reset-confirm", json={"token": token, "new_password": "Placement#2027x"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/password-reset-confirm", json={"token": token, "new_password": "Placement#2028x"}
        ).status_code
        == 400
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "Placement#2027x"})
    assert login.status_code == 200
    h = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=h).status_code == 200
    client.post("/api/v1/auth/logout", headers=h)
    assert client.get("/api/v1/auth/me", headers=h).status_code == 401  # revoked server-side
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": login.json()["refresh_token"]}).status_code == 401

    (uid,) = _ids_by_email(email)
    expired = create_access_token(subject=uid, expires_delta=timedelta(seconds=-5), role="placement_officer")
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    # a token minted for another tenant id is rejected
    forged = create_access_token(subject=uid, role="admin", tenant_id=1, token_version=2)
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_role_change_ends_sessions_and_blocks_escalation(client, auth):
    admin = auth("admin@deccan-tech.example")
    users = client.get("/api/v1/users/?role=placement_officer", headers=admin).json()["items"]
    po = users[0]
    r = client.patch(f"/api/v1/users/{po['id']}", json={"role": "student"}, headers=admin)
    assert r.status_code == 422
    me = client.get("/api/v1/auth/me", headers=admin).json()
    assert client.patch(f"/api/v1/users/{me['id']}", json={"role": "faculty"}, headers=admin).status_code == 422
    assert client.patch(f"/api/v1/users/{me['id']}", json={"is_active": False}, headers=admin).status_code == 422
