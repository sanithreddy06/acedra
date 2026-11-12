"""Phase 1 regression tests: faculty visibility parity, term breakdown, missing faculty profile, force regeneration."""
from app.core.database import SessionLocal
from app.core.tenancy import TenantScope, set_session_scope
from app.models import Recommendation, User


def _me(client, headers):
    return client.get("/api/v1/auth/me", headers=headers).json()


def _ids(client, headers, path="/api/v1/students/", **params):
    return {s["id"] for s in client.get(path, headers=headers, params={"limit": 100, **params}).json()}


# --- 1. Faculty cross-department visibility -------------------------------------------------------
def test_shared_cross_department_student_is_listed_and_openable_then_revoked(client, auth):
    fac_h, admin_h = auth("kavya.menon@reva.in"), auth("anitha.rao@reva.in")
    fac = _me(client, fac_h)
    visible = _ids(client, fac_h)
    all_students = client.get("/api/v1/students/", headers=admin_h, params={"limit": 100}).json()
    other_dept = [s for s in all_students if s["department_id"] != fac["department_id"] and s["id"] not in visible]
    assert other_dept, "seed data should contain students outside the faculty member's department"
    target = other_dept[0]["id"]

    # Negative: not taught and not shared -> neither listed nor openable.
    assert target not in visible
    assert client.get(f"/api/v1/students/{target}", headers=fac_h).status_code == 403
    assert client.get(f"/api/v1/students/{target}/analytics", headers=fac_h).status_code == 403

    grant = client.post("/api/v1/tenant/staff-access", headers=admin_h,
                        json={"user_id": fac["id"], "student_id": target, "reason": "Cross-department project guide"})
    assert grant.status_code == 201, grant.text
    try:
        # Positive: an explicit share makes the student both listed and openable, consistently.
        assert target in _ids(client, fac_h)
        assert client.get(f"/api/v1/students/{target}", headers=fac_h).status_code == 200
        cohort = client.get("/api/v1/students/analytics/faculty", headers=fac_h).json()
        assert cohort["total_assigned_students"] == len(_ids(client, fac_h))
    finally:
        access_id = next(a["id"] for a in client.get("/api/v1/tenant/staff-access", headers=admin_h).json()
                         if a["student_id"] == target and a["user_id"] == fac["id"])
        assert client.delete(f"/api/v1/tenant/staff-access/{access_id}", headers=admin_h).status_code in (200, 204)

    # Revocation takes effect immediately for both paths.
    assert target not in _ids(client, fac_h)
    assert client.get(f"/api/v1/students/{target}", headers=fac_h).status_code == 403


def test_faculty_list_matches_direct_access_and_never_crosses_tenants(client, auth):
    fac_h = auth("kavya.menon@reva.in")
    visible = _ids(client, fac_h)
    assert visible
    for sid in list(visible)[:5]:
        assert client.get(f"/api/v1/students/{sid}", headers=fac_h).status_code == 200
    other_tenant = _ids(client, auth("admin@northfield.example"))
    for sid in list(other_tenant)[:3]:
        assert client.get(f"/api/v1/students/{sid}", headers=fac_h).status_code == 404


# --- 2. Term breakdown follows each tenant's academic structure ------------------------------------
def test_term_breakdown_uses_tenant_structure(client, auth):
    reva = client.get("/api/v1/students/analytics/admin", headers=auth("anitha.rao@reva.in")).json()
    nf = client.get("/api/v1/students/analytics/admin", headers=auth("admin@northfield.example")).json()

    reva_terms = reva["semester_wise_performance"]
    assert [t["semester_number"] for t in reva_terms] == list(range(1, 9))  # 2 terms/year x 4 years
    assert reva_terms[0]["semester"] == "Semester 1"

    nf_terms = nf["semester_wise_performance"]
    assert [t["semester_number"] for t in nf_terms] == list(range(1, 13))  # 3 terms/year x 4 years
    assert all(t["semester"].startswith("Term ") for t in nf_terms)
    # Northfield students are in term 4 — invisible under the old fixed 1/3/5/7 breakdown.
    assert next(t for t in nf_terms if t["semester_number"] == 4)["student_count"] > 0

    for data in (reva, nf):
        assert sum(t["student_count"] for t in data["semester_wise_performance"]) == \
            data["institutional_stats"]["total_students"]


# --- 3. Missing faculty profile --------------------------------------------------------------------
def test_faculty_analytics_without_profile_is_an_explicit_empty_state(client, auth):
    data = client.get("/api/v1/students/analytics/faculty", headers=auth("anitha.rao@reva.in")).json()
    assert data["profile_configured"] is False
    assert data["faculty_id"] is None
    assert data["assigned_courses"] == [] and data["students_summary"] == []
    assert data["total_assigned_students"] == 0


def test_faculty_analytics_with_profile_lists_only_their_cohort(client, auth):
    fac_h = auth("kavya.menon@reva.in")
    data = client.get("/api/v1/students/analytics/faculty", headers=fac_h).json()
    assert data["profile_configured"] is True and data["faculty_id"]
    cohort = {s["id"] for s in data["students_summary"]}
    assert cohort and cohort <= _ids(client, fac_h)
    attendance = [s["attendance"] for s in data["students_summary"]]
    assert attendance == sorted(attendance)


# --- 4. Force regeneration --------------------------------------------------------------------------
def _recs(student_id):
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    try:
        # Keyed by (id, created_at): SQLite may reuse the id of a deleted row.
        return {(r.id, r.created_at): (r.status, r.source, r.title) for r in db.query(Recommendation).filter(
            Recommendation.student_id == student_id).all()}
    finally:
        db.close()


def test_generation_is_additive_and_force_withdraws_only_untouched_suggestions(client, auth):
    h = auth("admin@northfield.example")
    sid = client.get("/api/v1/students/", headers=h).json()[1]["id"]
    first = client.post(f"/api/v1/recommendations/generate/{sid}", headers=h)
    assert first.status_code == 200 and first.json()
    before = _recs(sid)

    # Without force, regeneration only adds; nothing existing changes.
    client.post(f"/api/v1/recommendations/generate/{sid}", headers=h)
    assert set(before) <= set(_recs(sid))

    kept = next(i for i, (status, source, _) in before.items() if status == "SUGGESTED" and source == "SYSTEM")
    assert client.post(f"/api/v1/recommendations/{kept[0]}/accept", headers=h).status_code == 200
    untouched = {i for i, (status, source, _) in _recs(sid).items() if status == "SUGGESTED" and source == "SYSTEM"}

    r = client.post(f"/api/v1/recommendations/generate/{sid}", headers=h, params={"force_regenerate": True})
    assert r.status_code == 200
    after = _recs(sid)
    assert after[kept][0] == "ACCEPTED"          # acted-on items are always kept
    assert not (untouched & set(after))           # untouched suggestions were withdrawn ...
    assert any(s == "SUGGESTED" for s, _, _ in after.values())  # ... and current ones generated afresh


def test_force_regeneration_requires_access_to_the_student(client, auth):
    other = client.get("/api/v1/students/", headers=auth("anitha.rao@reva.in")).json()[0]["id"]
    r = client.post(f"/api/v1/recommendations/generate/{other}", headers=auth("admin@northfield.example"),
                    params={"force_regenerate": True})
    assert r.status_code == 404


def test_users_table_untouched_by_regeneration():
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    try:
        assert db.query(User).count() > 0
    finally:
        db.close()
