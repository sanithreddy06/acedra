"""Regression tests for the production-hardening pass: permission gaps inside a university, sign-in
lockout, single-use refresh tokens, audit addresses, the email outbox and fail-closed configuration."""
import re

import pytest
from conftest import legal_versions

from app.core.database import SessionLocal
from app.core.tenancy import TenantScope, set_session_scope
from app.models.platform import EmailMessage
from app.models.user import User

P = "/api/v1"
TENANT = "deccan-tech.example"  # a tenant the other test modules barely touch
ADMIN = f"admin@{TENANT}"


def _db():
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    return db


def _invitation_token(email):
    db = _db()
    try:
        msg = db.query(EmailMessage).filter(EmailMessage.to_email == email.lower(),
                                            EmailMessage.template == "invitation").order_by(EmailMessage.id.desc()).first()
        return re.search(r"token=([A-Za-z0-9_\-]+)", msg.body_text).group(1)
    finally:
        db.close()


def _new_account(client, auth, local, role="placement_officer", password="Hardening#2026", **extra):
    """Invite and activate a fresh account in the test tenant; returns (email, user_id)."""
    email = f"{local}@{TENANT}"
    dept = client.get(f"{P}/departments/", headers=auth(ADMIN)).json()[0]["id"]
    r = client.post(f"{P}/users/invite", headers=auth(ADMIN),
                    json={"email": email, "full_name": f"Test {local}", "role": role, "department_id": dept, **extra})
    assert r.status_code == 201, r.text
    r2 = client.post(f"{P}/auth/invitations/accept", json={
        "token": _invitation_token(email), "password": password, "accepted_versions": legal_versions(client)})
    assert r2.status_code == 200, r2.text
    return email, r.json()["id"]


# --------------------------------------------------------------------------- reports
def test_staff_only_see_reports_they_generated(client, auth):
    admin, faculty = auth("anitha.rao@reva.in"), auth("kavya.menon@reva.in")
    made = client.post(f"{P}/reports/export", headers=admin, json={"report_type": "RISK_SUMMARY"})
    assert made.status_code == 201, made.text
    admin_report = made.json()["id"]

    listed = client.get(f"{P}/reports", headers=faculty)
    assert listed.status_code == 200
    assert admin_report not in [r["id"] for r in listed.json()]
    assert client.get(f"{P}/reports/{admin_report}/download", headers=faculty).status_code == 404
    assert client.get(f"{P}/reports/{admin_report}/download", headers=admin).status_code == 200


def test_staff_report_contains_only_their_own_students(client, auth):
    admin, faculty = auth("anitha.rao@reva.in"), auth("kavya.menon@reva.in")
    visible = {s["usn"] for s in client.get(f"{P}/students/?limit=1000", headers=faculty).json()}
    everyone = {s["usn"] for s in client.get(f"{P}/students/?limit=1000", headers=admin).json()}
    assert visible and visible < everyone

    made = client.post(f"{P}/reports/export", headers=faculty, json={"report_type": "STUDENT_PROGRESS"})
    assert made.status_code == 201, made.text
    body = client.get(f"{P}/reports/{made.json()['id']}/download", headers=faculty).text
    for usn in everyone - visible:
        assert usn not in body
    assert any(usn in body for usn in visible)


def test_report_types_are_limited_by_role(client, auth):
    placement, faculty = auth("rahul.deshpande@reva.in"), auth("kavya.menon@reva.in")
    assert client.post(f"{P}/reports/export", headers=placement, json={"report_type": "RISK_SUMMARY"}).status_code == 403
    assert client.post(f"{P}/reports/export", headers=placement,
                       json={"report_type": "PLACEMENT_READINESS"}).status_code == 201
    assert client.post(f"{P}/reports/export", headers=faculty,
                       json={"report_type": "DEPARTMENT_SUMMARY"}).status_code == 403


def test_report_cells_cannot_start_a_spreadsheet_formula():
    from app.services.report_service import _safe_cell
    assert _safe_cell("=HYPERLINK(\"http://evil\")") == "'=HYPERLINK(\"http://evil\")"
    assert _safe_cell("+1+1") == "'+1+1"
    assert _safe_cell("@SUM(A1)") == "'@SUM(A1)"
    assert _safe_cell("Asha Rao") == "Asha Rao"
    assert _safe_cell(7.5) == 7.5


# --------------------------------------------------------------------------- student records
def test_only_administrators_can_change_a_student_record(client, auth):
    admin = auth("anitha.rao@reva.in")
    faculty_students = client.get(f"{P}/students/?limit=5", headers=auth("kavya.menon@reva.in")).json()
    sid = faculty_students[0]["id"]
    before = client.get(f"{P}/students/{sid}", headers=admin).json()

    for who in ("kavya.menon@reva.in", "rahul.deshpande@reva.in"):
        r = client.patch(f"{P}/students/{sid}", headers=auth(who), json={"status": "Suspended", "current_semester": 8})
        assert r.status_code == 403, f"{who}: {r.text}"
    mentee = client.get(f"{P}/students/?limit=1", headers=auth("suresh.hegde@reva.in")).json()[0]["id"]
    assert client.patch(f"{P}/students/{mentee}", headers=auth("suresh.hegde@reva.in"),
                        json={"status": "Suspended"}).status_code == 403

    after = client.get(f"{P}/students/{sid}", headers=admin).json()
    assert (after["status"], after["current_semester"]) == (before["status"], before["current_semester"])

    assert client.patch(f"{P}/students/{sid}", headers=admin, json={"assigned_mentor_id": 999999}).status_code == 422
    ok = client.patch(f"{P}/students/{sid}", headers=admin, json={"guardian_name": "Updated Guardian", "status": None})
    assert ok.status_code == 200 and ok.json()["status"] == before["status"]


def test_student_can_only_change_own_contact_details(client, auth):
    student = auth("aarav.sharma@reva.in")
    sid = client.get(f"{P}/auth/me", headers=student).json()["student_id"]
    before = client.get(f"{P}/students/{sid}", headers=student).json()
    r = client.patch(f"{P}/students/{sid}", headers=student,
                     json={"address": "12 Lake Road", "status": "Graduated", "current_semester": 8})
    assert r.status_code == 200
    assert r.json()["address"] == "12 Lake Road"
    assert (r.json()["status"], r.json()["current_semester"]) == (before["status"], before["current_semester"])


# --------------------------------------------------------------------------- placement officer scope
def test_placement_officer_has_no_individual_risk_or_intervention_access(client, auth):
    placement = auth("rahul.deshpande@reva.in")
    sid = client.get(f"{P}/students/?limit=1", headers=placement).json()[0]["id"]
    alert_id = client.get(f"{P}/risk/alerts", headers=auth("anitha.rao@reva.in")).json()["items"][0]["id"]
    assert client.get(f"{P}/risk/alerts", headers=placement).status_code == 403
    assert client.get(f"{P}/risk/alerts/{alert_id}", headers=placement).status_code == 403
    assert client.get(f"{P}/risk/students/{sid}", headers=placement).status_code == 403
    assert client.get(f"{P}/interventions", headers=placement).status_code == 403
    # Their own work is unaffected.
    assert client.get(f"{P}/risk/statistics", headers=placement).status_code == 200
    assert client.get(f"{P}/placement/readiness/{sid}", headers=placement).status_code == 200


# --------------------------------------------------------------------------- user administration
def test_role_change_creates_the_missing_staff_profile(client, auth):
    email, uid = _new_account(client, auth, "rolechange", role="faculty")
    admin = auth(ADMIN)
    mentors_before = {m["user_id"] for m in client.get(f"{P}/tenant/mentors", headers=admin).json()}
    assert uid not in mentors_before
    assert client.patch(f"{P}/users/{uid}", headers=admin, json={"role": "mentor"}).status_code == 200
    mentors_after = {m["user_id"] for m in client.get(f"{P}/tenant/mentors", headers=admin).json()}
    assert uid in mentors_after


def test_conflicts_and_nulls_are_handled_without_a_server_error(client, auth):
    admin = auth(ADMIN)
    students = client.get(f"{P}/students/?limit=1", headers=admin).json()
    dept = client.get(f"{P}/departments/", headers=admin).json()[0]["id"]
    dup = client.post(f"{P}/users/invite", headers=admin, json={
        "email": f"dup.usn@{TENANT}", "full_name": "Duplicate Usn", "role": "student", "department_id": dept,
        "usn": students[0]["usn"]})
    assert dup.status_code == 409, dup.text
    missing = client.post(f"{P}/users/invite", headers=admin, json={
        "email": f"no.usn@{TENANT}", "full_name": "No Usn", "role": "student", "department_id": dept})
    assert missing.status_code == 422
    db = _db()
    try:  # a rejected invitation leaves neither an account nor an email behind
        assert db.query(User).filter(User.email.in_([f"dup.usn@{TENANT}", f"no.usn@{TENANT}"])).count() == 0
        assert db.query(EmailMessage).filter(EmailMessage.to_email.in_(
            [f"dup.usn@{TENANT}", f"no.usn@{TENANT}"])).count() == 0
    finally:
        db.close()

    _, uid = _new_account(client, auth, "nullname")
    r = client.patch(f"{P}/users/{uid}", headers=admin, json={"full_name": None, "title": "Officer"})
    assert r.status_code == 200 and r.json()["full_name"] == "Test nullname"


# --------------------------------------------------------------------------- sign-in hardening
def test_account_locks_after_repeated_failures_and_reset_unlocks(client, auth):
    from app.core.config import settings
    email, _ = _new_account(client, auth, "lockout")
    for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS):
        assert client.post(f"{P}/auth/login", json={"email": email, "password": "Wrong#Password1"}).status_code == 401
    locked = client.post(f"{P}/auth/login", json={"email": email, "password": "Hardening#2026"})
    assert locked.status_code == 429, locked.text

    assert client.post(f"{P}/auth/password-reset-request", json={"email": email}).status_code == 200
    db = _db()
    try:
        msg = db.query(EmailMessage).filter(EmailMessage.to_email == email, EmailMessage.template == "password_reset") \
            .order_by(EmailMessage.id.desc()).first()
        token = re.search(r"token=([A-Za-z0-9_\-]+)", msg.body_text).group(1)
    finally:
        db.close()
    assert client.post(f"{P}/auth/password-reset-confirm",
                       json={"token": token, "new_password": "Recovered#2026"}).status_code == 200
    assert client.post(f"{P}/auth/login", json={"email": email, "password": "Recovered#2026"}).status_code == 200


def test_a_successful_sign_in_resets_the_failure_count(client, auth):
    from app.core.config import settings
    email, _ = _new_account(client, auth, "counter")
    for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
        client.post(f"{P}/auth/login", json={"email": email, "password": "Wrong#Password1"})
    assert client.post(f"{P}/auth/login", json={"email": email, "password": "Hardening#2026"}).status_code == 200
    for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
        client.post(f"{P}/auth/login", json={"email": email, "password": "Wrong#Password1"})
    assert client.post(f"{P}/auth/login", json={"email": email, "password": "Hardening#2026"}).status_code == 200


def test_only_the_newest_password_reset_link_works(client, auth):
    email, _ = _new_account(client, auth, "resetlinks")
    tokens = []
    for _ in range(2):
        client.post(f"{P}/auth/password-reset-request", json={"email": email})
        db = _db()
        try:
            msg = db.query(EmailMessage).filter(EmailMessage.to_email == email,
                                                EmailMessage.template == "password_reset").order_by(EmailMessage.id.desc()).first()
            tokens.append(re.search(r"token=([A-Za-z0-9_\-]+)", msg.body_text).group(1))
        finally:
            db.close()
    old, new = tokens
    assert client.post(f"{P}/auth/password-reset-confirm", json={"token": old, "new_password": "Another#2026x"}).status_code == 400
    assert client.post(f"{P}/auth/password-reset-confirm", json={"token": new, "new_password": "Another#2026x"}).status_code == 200


def test_unknown_accounts_cost_the_same_password_check(client, monkeypatch):
    from app.services import auth_service
    calls = []
    monkeypatch.setattr(auth_service, "burn_password_check", lambda pw: calls.append(pw))
    r = client.post(f"{P}/auth/login", json={"email": "nobody@nowhere.example", "password": "Whatever#12345"})
    assert r.status_code == 401 and calls == ["Whatever#12345"]


def test_refresh_tokens_are_single_use_and_reuse_ends_the_session(client, auth):
    email, _ = _new_account(client, auth, "refresher")
    first = client.post(f"{P}/auth/login", json={"email": email, "password": "Hardening#2026"}).json()
    second = client.post(f"{P}/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert second.status_code == 200
    assert second.json()["refresh_token"] != first["refresh_token"]
    new_access = {"Authorization": f"Bearer {second.json()['access_token']}"}
    assert client.get(f"{P}/auth/me", headers=new_access).status_code == 200

    # Presenting the first token again means it was copied: every session for the account ends.
    assert client.post(f"{P}/auth/refresh", json={"refresh_token": first["refresh_token"]}).status_code == 401
    assert client.get(f"{P}/auth/me", headers=new_access).status_code == 401
    assert client.post(f"{P}/auth/refresh", json={"refresh_token": second.json()["refresh_token"]}).status_code == 401


def test_audit_address_ignores_a_forged_forwarded_header(client):
    from app.models.audit import AuditLog
    client.post(f"{P}/auth/login", headers={"X-Forwarded-For": "203.0.113.77"},
                json={"email": "forged-header@nowhere.example", "password": "Whatever#12345"})
    db = _db()
    try:
        entry = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILED").order_by(AuditLog.id.desc()).first()
        assert entry.ip_address != "203.0.113.77"
    finally:
        db.close()


# --------------------------------------------------------------------------- email outbox
class _FakeSmtp:
    sent, fail = [], False

    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, *a): pass

    def send_message(self, msg):
        if _FakeSmtp.fail:
            raise ConnectionError("relay unavailable")
        _FakeSmtp.sent.append(msg["To"])


@pytest.fixture
def smtp(monkeypatch):
    from app.core.config import settings
    from app.services import email_service
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test.invalid")
    monkeypatch.setattr(settings, "EMAIL_RETRY_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(email_service.smtplib, "SMTP", _FakeSmtp)
    monkeypatch.setattr(email_service._executor, "submit", lambda fn: None)  # deliver explicitly in tests
    _FakeSmtp.sent, _FakeSmtp.fail = [], False
    return email_service


def test_email_is_sent_only_after_commit_and_never_after_rollback(smtp):
    db = _db()
    try:
        smtp.EmailService(db).send("rolled.back@example.org", "s", "b", template="test")
        db.rollback()
        smtp.deliver_queued()
        assert _FakeSmtp.sent == []

        row = smtp.EmailService(db).send("committed@example.org", "s", "b", template="test")
        assert row.status == "queued"
        smtp.deliver_queued()
        assert _FakeSmtp.sent == []  # still uncommitted: nothing leaves the server
        db.commit()
        assert smtp.deliver_queued() == 1
        assert _FakeSmtp.sent == ["committed@example.org"]
        db.refresh(row)
        assert row.status == "sent" and row.attempts == 1 and row.sent_at is not None
        assert smtp.deliver_queued() == 0  # not sent twice
    finally:
        db.close()


def test_failed_email_is_retried_then_given_up(smtp):
    from app.core.config import settings
    db = _db()
    try:
        row = smtp.EmailService(db).send("flaky@example.org", "s", "b", template="test")
        db.commit()
        _FakeSmtp.fail = True
        smtp.deliver_queued()
        db.refresh(row)
        assert row.status == "failed" and row.attempts == 1 and "relay unavailable" in row.error
        _FakeSmtp.fail = False
        assert smtp.deliver_queued() == 1
        db.refresh(row)
        assert row.status == "sent" and row.attempts == 2

        dead = smtp.EmailService(db).send("dead@example.org", "s", "b", template="test")
        db.commit()
        _FakeSmtp.fail = True
        for _ in range(settings.EMAIL_MAX_ATTEMPTS + 3):
            smtp.deliver_queued()
        db.refresh(dead)
        assert dead.status == "failed" and dead.attempts == settings.EMAIL_MAX_ATTEMPTS
    finally:
        db.close()


# --------------------------------------------------------------------------- configuration
def test_configuration_fails_closed():
    from app.core.config import Settings
    good = dict(ENVIRONMENT="production", SECRET_KEY="x" * 40, DATABASE_URL="postgresql+psycopg://u:p@db/acedra",
                CORS_ORIGINS="https://acedra.example.org", PUBLIC_APP_URL="https://acedra.example.org")
    Settings(_env_file=None, **good)
    with pytest.raises(ValueError):
        Settings(_env_file=None, **{**good, "PUBLIC_APP_URL": "http://acedra.example.org"})
    with pytest.raises(ValueError):
        Settings(_env_file=None, **{**good, "ENVIRONMENT": "prod"})  # a typo must not silently mean "development"
    with pytest.raises(ValueError):  # built-in secret with a real database server, whatever the environment
        Settings(_env_file=None, ENVIRONMENT="development", DATABASE_URL="postgresql+psycopg://u:p@db/acedra")
    Settings(_env_file=None, ENVIRONMENT="development", DATABASE_URL="sqlite:///./dev.db")
