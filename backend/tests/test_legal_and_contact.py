"""Phase 2A: public legal documents, versioned acceptance, legal administration and the contact form."""
from datetime import timedelta

import pytest

from app.core.clock import utcnow
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.tenancy import TenantScope, set_session_scope
from app.models import ContactMessage, LegalAcceptance, User
from app.models.platform import EmailMessage
from tests.conftest import legal_versions
from tests.test_platform_workflow import latest_token

SUPER = "superadmin@acedra.example"
EMPLOYEE = "arjun.rao@acedra.example"


def _db():
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    return db


def _user(email):
    db = _db()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def _acceptances(user_id):
    db = _db()
    try:
        return [(a.doc_type, a.version, a.university_id, a.context)
                for a in db.query(LegalAcceptance).filter(LegalAcceptance.user_id == user_id).all()]
    finally:
        db.close()


# --- public documents ---------------------------------------------------------------------------
def test_public_legal_documents_are_published_and_marked_as_drafts(client):
    docs = {d["doc_type"]: d for d in client.get("/api/v1/public/legal").json()}
    assert set(docs) == {"terms", "privacy", "cookies"}
    for doc_type in docs:
        full = client.get(f"/api/v1/public/legal/{doc_type}").json()
        assert full["status"] == "published" and full["effective_date"]
        assert "Draft for legal review" in full["body"]
        history = client.get(f"/api/v1/public/legal/{doc_type}/history").json()
        assert history and history[0]["version"]
    assert client.get("/api/v1/public/legal/refund-policy").status_code == 404


# --- contact form ---------------------------------------------------------------------------------
CONTACT = {"name": "Dr. Kiran Desai", "email": "kiran.desai@hillview.example", "institution": "Hillview College",
           "subject": "Pilot for first-year students", "message": "We would like to understand how onboarding works."}


def test_contact_form_persists_acknowledges_and_reaches_the_platform_inbox(client, auth):
    r = client.post("/api/v1/public/contact", json=CONTACT)
    assert r.status_code == 201
    db = _db()
    try:
        stored = db.query(ContactMessage).filter(ContactMessage.email == CONTACT["email"]).one()
        assert stored.status == "new" and stored.institution == "Hillview College"
        assert db.query(EmailMessage).filter(EmailMessage.to_email == CONTACT["email"],
                                             EmailMessage.template == "contact_acknowledgement").count() == 1
    finally:
        db.close()

    inbox = client.get("/api/v1/platform/contact-messages", headers=auth(EMPLOYEE)).json()
    msg = next(m for m in inbox if m["email"] == CONTACT["email"])
    r = client.patch(f"/api/v1/platform/contact-messages/{msg['id']}", json={"status": "in_progress"},
                     headers=auth(EMPLOYEE))
    assert r.status_code == 200 and r.json()["status"] == "in_progress"
    # University accounts cannot see the ACEDRA inbox.
    assert client.get("/api/v1/platform/contact-messages", headers=auth("admin@reva-demo.example")).status_code == 404


@pytest.mark.parametrize("change,field", [
    ({"email": "someone@gmail.com"}, "institution"),
    ({"message": "too short"}, "message"),
    ({"message": "see https://a.example https://b.example https://c.example https://d.example now please"}, "links"),
    ({"name": ""}, "name"),
])
def test_contact_form_validation(client, change, field):
    r = client.post("/api/v1/public/contact", json={**CONTACT, **change})
    assert r.status_code == 422


def test_contact_honeypot_is_accepted_silently_and_not_stored(client):
    bot = {**CONTACT, "email": "bot@spam.example", "website": "http://spam.example"}
    assert client.post("/api/v1/public/contact", json=bot).status_code == 201
    db = _db()
    try:
        assert db.query(ContactMessage).filter(ContactMessage.email == "bot@spam.example").count() == 0
    finally:
        db.close()


# --- acceptance on invitation ---------------------------------------------------------------------
def test_invitation_acceptance_records_the_reviewed_versions(client, auth):
    email = "new.faculty.legal@reva-demo.example"
    dept = client.get("/api/v1/tenant/departments", headers=auth("admin@reva-demo.example")).json()[0]["id"]
    r = client.post("/api/v1/users/invite", headers=auth("admin@reva-demo.example"),
                    json={"email": email, "full_name": "Legal Test Faculty", "role": "faculty", "department_id": dept})
    assert r.status_code == 201, r.text
    token = latest_token(email, "invitation")
    body = {"token": token, "password": "Faculty#Legal1"}

    assert client.post("/api/v1/auth/invitations/accept", json={**body, "accepted_versions": {}}).status_code == 422
    stale = {k: "0.0-old" for k in legal_versions(client)}
    assert client.post("/api/v1/auth/invitations/accept", json={**body, "accepted_versions": stale}).status_code == 409
    user = _user(email)
    assert _acceptances(user.id) == [] and not user.is_verified  # nothing recorded, invitation still open

    r = client.post("/api/v1/auth/invitations/accept", json={**body, "accepted_versions": legal_versions(client)})
    assert r.status_code == 200, r.text
    rows = _acceptances(user.id)
    versions = legal_versions(client)
    assert sorted(rows) == sorted([(t, versions[t], user.university_id, "invitation") for t in ("terms", "privacy")])
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/v1/auth/legal-status", headers=headers).json()["pending"] == []


# --- acceptance after sign-in, and re-acceptance after a new version -----------------------------
def test_sign_in_never_counts_as_acceptance_and_new_versions_require_review(client, auth):
    h = auth("mentor@northfield.example")
    user = _user("mentor@northfield.example")
    status = client.get("/api/v1/auth/legal-status", headers=h).json()
    assert {d["doc_type"] for d in status["pending"]} == {"terms", "privacy"}
    assert _acceptances(user.id) == []

    r = client.post("/api/v1/auth/legal-acceptances", headers=h, json={"accepted_versions": legal_versions(client)})
    assert r.status_code == 200 and r.json()["pending"] == []
    assert client.post("/api/v1/auth/legal-acceptances", headers=h,
                       json={"accepted_versions": legal_versions(client)}).status_code == 200  # idempotent
    assert len(_acceptances(user.id)) == 2

    # The ACEDRA super administrator publishes a new privacy policy version.
    sa = auth(SUPER)
    draft = client.post("/api/v1/platform/legal-documents", headers=sa,
                        json={"doc_type": "privacy", "version": "0.2-test", "change_summary": "Clarify retention"})
    assert draft.status_code == 201, draft.text
    did = draft.json()["id"]
    assert client.patch(f"/api/v1/platform/legal-documents/{did}", headers=sa,
                        json={"body": draft.json()["body"] + "\n\n## Retention update\n\nClarified."}).status_code == 200
    assert client.post(f"/api/v1/platform/legal-documents/{did}/publish", headers=sa,
                       json={"effective_date": str(utcnow().date())}).status_code == 409  # not approved yet
    assert client.post(f"/api/v1/platform/legal-documents/{did}/approve", headers=sa,
                       json={"approval_note": "short"}).status_code == 422
    assert client.post(f"/api/v1/platform/legal-documents/{did}/approve", headers=sa,
                       json={"approval_note": "Reviewed by counsel (test fixture)."}).status_code == 200
    assert client.patch(f"/api/v1/platform/legal-documents/{did}", headers=sa,
                        json={"title": "Changed after approval"}).status_code == 409
    r = client.post(f"/api/v1/platform/legal-documents/{did}/publish", headers=sa,
                    json={"effective_date": str(utcnow().date())})
    assert r.status_code == 200 and r.json()["is_current"] is True
    assert client.get("/api/v1/public/legal/privacy").json()["version"] == "0.2-test"

    # The mentor must now review the new privacy policy (only); the old acceptance remains on record.
    pending = client.get("/api/v1/auth/legal-status", headers=h).json()["pending"]
    assert [d["doc_type"] for d in pending] == ["privacy"]
    old_privacy = client.get("/api/v1/public/legal/privacy/history").json()[-1]["version"]
    assert ("privacy", old_privacy, user.university_id, "sign_in") in _acceptances(user.id)


def test_future_effective_dates_do_not_take_effect_early(client, auth):
    sa = auth(SUPER)
    before = client.get("/api/v1/public/legal/cookies").json()["version"]
    did = client.post("/api/v1/platform/legal-documents", headers=sa,
                      json={"doc_type": "cookies", "version": "9.9-future"}).json()["id"]
    client.post(f"/api/v1/platform/legal-documents/{did}/approve", headers=sa,
                json={"approval_note": "Approved for next quarter (test fixture)."})
    tomorrow = str(utcnow().date() + timedelta(days=30))
    assert client.post(f"/api/v1/platform/legal-documents/{did}/publish", headers=sa,
                       json={"effective_date": tomorrow}).status_code == 200
    assert client.get("/api/v1/public/legal/cookies").json()["version"] == before


def test_only_super_admins_can_change_legal_documents(client, auth):
    emp = auth(EMPLOYEE)
    assert client.get("/api/v1/platform/legal-documents", headers=emp).status_code == 200
    assert client.post("/api/v1/platform/legal-documents", headers=emp,
                       json={"doc_type": "terms", "version": "0.3-emp"}).status_code == 403
    docs = client.get("/api/v1/platform/legal-documents", headers=emp).json()
    assert client.post(f"/api/v1/platform/legal-documents/{docs[0]['id']}/approve", headers=emp,
                       json={"approval_note": "Employee trying to approve"}).status_code == 403
    for account in ("admin@reva-demo.example", "student@reva-demo.example"):
        assert client.get("/api/v1/platform/legal-documents", headers=auth(account)).status_code == 404
        assert client.post("/api/v1/platform/legal-documents", headers=auth(account),
                           json={"doc_type": "terms", "version": "0.3-uni"}).status_code == 404


def test_optional_server_side_enforcement(client, auth, monkeypatch):
    h = auth("placement@deccan-tech.example")
    monkeypatch.setattr(settings, "LEGAL_ACCEPTANCE_ENFORCED", True)
    assert client.get("/api/v1/students/", headers=h).status_code == 428
    assert client.get("/api/v1/auth/legal-status", headers=h).status_code == 200  # can still review and accept
    client.post("/api/v1/auth/legal-acceptances", headers=h, json={"accepted_versions": legal_versions(client)})
    assert client.get("/api/v1/students/", headers=h).status_code == 200


def test_baseline_seeding_tolerates_a_concurrent_first_request(client, monkeypatch):
    """Two first requests can both see "no published version"; the second insert must not fail the request."""
    from app.models import LegalDocument
    from app.services import legal_service

    client.get("/api/v1/public/legal")  # baseline exists now
    monkeypatch.setattr(legal_service, "_published_types", lambda db: set())  # simulate the stale check
    for path in ("/api/v1/public/legal", "/api/v1/public/legal/terms/history", "/api/v1/public/legal/privacy"):
        assert client.get(path).status_code == 200
    db = _db()
    try:
        assert db.query(LegalDocument).filter(LegalDocument.version == legal_service.BASELINE_VERSION).count() == 3
    finally:
        db.close()
