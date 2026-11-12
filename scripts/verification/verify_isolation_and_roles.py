"""Live tenant-isolation, role and authentication checks against an ACEDRA API loaded with the sample
universities (database/seeds/seed_all.py), running in development mode. Takes about 70 seconds.
"""
import base64
import json
import os
import sys
import time

import httpx
import jwt

B = os.environ.get("ACEDRA_API", "http://127.0.0.1:8000/api/v1")
res = []
def check(name, cond, detail=""):
    res.append(bool(cond)); print(("PASS" if cond else "FAIL"), "-", name, detail)
def login(email, pw):
    r = httpx.post(B + "/auth/login", json={"email": email, "password": pw}); r.raise_for_status()
    return {"Authorization": "Bearer " + r.json()["access_token"]}, r.json()
def get(p, h=None, **params): return httpx.get(B + p, headers=h or {}, params=params or None, timeout=30)
def code(r): return f"[{r.status_code}]"
reva, reva_tok = login("anitha.rao@reva.in", "AdminPass123!")
fac, _ = login("kavya.menon@reva.in", "FacultyPass123!")
men, _ = login("suresh.hegde@reva.in", "MentorPass123!")
plc, _ = login("rahul.deshpande@reva.in", "PlacementPass123!")
stu, stu_tok = login("aarav.sharma@reva.in", "StudentPass123!")
nf, _ = login("admin@northfield.example", "AdminPass123!")
dec, _ = login("admin@deccan-tech.example", "AdminPass123!")
sup, _ = login("superadmin@acedra.example", "PlatformPass123!")

# ---- tenant isolation
reva_ids = {s["id"] for skip in (0, 100, 200) for s in get("/students/", reva, limit=100, skip=skip).json()}
nf_students = get("/students/", nf, limit=100).json(); nf_id = nf_students[0]["id"]
check("each tenant lists only its own students", reva_ids and not (reva_ids & {s["id"] for s in nf_students}))
check("REVA total is 240, Northfield 14", get("/students/count", reva).json()["total"] == 240 and get("/students/count", nf).json()["total"] == 14)
for path in (f"/students/{nf_id}", f"/students/{nf_id}/analytics", f"/risk/students/{nf_id}", f"/placement/readiness/{nf_id}"):
    r = get(path, reva); check(f"REVA admin reading another university's student: GET {path.replace(str(nf_id), '{id}')}", r.status_code == 404, code(r))
r = httpx.patch(B + f"/students/{nf_id}", headers=reva, json={"guardian_name": "x"}); check("cross-tenant write refused", r.status_code == 404, code(r))
r = get("/students/", reva, student_id=nf_id); check("cross-tenant id in a query parameter refused", r.status_code == 404, code(r))
users = get("/users/", reva, limit=200).json()["items"]
check("REVA admin sees only REVA accounts", users and all(u["email"].endswith("@reva.in") for u in users), f"{len(users)} accounts")
nf_user = get("/users/", nf, limit=5).json()["items"][0]["id"]
check("cross-tenant user lookup refused", get(f"/users/{nf_user}", reva).status_code == 404)
nf_alert = get("/risk/alerts", nf).json()["items"]
if nf_alert: check("cross-tenant alert lookup refused", get(f"/risk/alerts/{nf_alert[0]['id']}", reva).status_code == 404)
docs_reva = {d["id"] for d in get("/ai/documents", reva).json()}; docs_nf = {d["id"] for d in get("/ai/documents", nf).json()}
check("knowledge-base documents are per tenant", not (docs_reva & docs_nf))
check("audit log is per tenant", all("northfield" not in json.dumps(e).lower() for e in get("/audit-logs/", reva).json()))

# ---- roles
fac_ids = {s["id"] for s in get("/students/", fac, limit=100).json()}; outside = next(iter(reva_ids - fac_ids))
check("faculty scope is a strict subset of the university", fac_ids and fac_ids < reva_ids, f"{len(fac_ids)} of {len(reva_ids)}")
check("faculty cannot open a student outside their sections", get(f"/students/{outside}", fac).status_code == 403)
check("faculty cannot edit a student", httpx.patch(B + f"/students/{next(iter(fac_ids))}", headers=fac, json={"status": "Suspended"}).status_code == 403)
men_ids = [s["id"] for s in get("/students/", men, limit=100).json()]
check("mentor cannot edit a mentee's record", httpx.patch(B + f"/students/{men_ids[0]}", headers=men, json={"status": "Suspended"}).status_code == 403)
sid = stu_tok["user"]["student_id"]; other = next(i for i in reva_ids if i != sid)
check("student sees exactly one student (self)", [s["id"] for s in get("/students/", stu).json()] == [sid])
check("student cannot open another student", get(f"/students/{other}", stu).status_code == 403)
for path in ("/users/", "/audit-logs/", "/imports/jobs", "/students/analytics/admin", "/dashboards/admin", "/tenant/staff-access"):
    check(f"student refused on admin route {path}", get(path, stu).status_code == 403)
check("student cannot create a risk rule", httpx.post(B + "/risk/rules", headers=stu, json={}).status_code == 403)
check("student cannot invite users", httpx.post(B + "/users/invite", headers=stu, json={"email": "x@reva.in", "full_name": "X Y", "role": "admin"}).status_code == 403)
for path in ("/risk/alerts", f"/risk/students/{other}", "/interventions"):
    check(f"placement officer refused on {path.replace(str(other), '{id}')}", get(path, plc).status_code == 403)
check("placement officer keeps placement data", get("/placement/applications/count", plc).status_code == 200)
admin_reports = get("/reports", reva).json()
if admin_reports: check("faculty cannot download an administrator's report", get(f"/reports/{admin_reports[0]['id']}/download", fac).status_code == 404)
r = httpx.patch(B + f"/users/{reva_tok['user']['id']}", headers=reva, json={"role": "platform_admin"}); check("university admin cannot grant a platform role", r.status_code == 422, code(r))
check("module not enabled for a university is refused (Deccan: placement)", get("/placement/roles", dec).status_code == 403)

# ---- platform boundary
check("university admin gets 404 on platform routes", get("/platform/universities", reva).status_code == 404)
check("platform admin refused on university routes", get("/students/", sup).status_code == 403)
unis = get("/platform/universities", sup).json(); uid = (unis.get("items") if isinstance(unis, dict) else unis)[0]["id"]
r = get(f"/platform/universities/{uid}/student-directory", sup); check("platform staff cannot read students without a grant", r.status_code == 403, code(r))
conv = httpx.post(B + "/ai/conversations", headers=stu, json={"mode": "PERSONAL_MODE_B", "title": "private"}).json()["id"]
check("another user's assistant conversation is invisible (404)", get(f"/ai/conversations/{conv}", reva).status_code == 404)

# ---- authentication
tok = stu_tok["access_token"]; claims = jwt.decode(tok, options={"verify_signature": False})
h, p, s = tok.split(".")
def b64(d): return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
forged_role = f"{h}.{b64({**claims, 'role': 'admin', 'sub': str(reva_tok['user']['id'])})}.{s}"
none_alg = f"{b64({'alg': 'none', 'typ': 'JWT'})}.{b64({**claims, 'sub': str(reva_tok['user']['id'])})}."
wrong_key = jwt.encode({**claims, "sub": str(reva_tok["user"]["id"])}, "dev-only-insecure-secret-change-me-not", algorithm="HS256")
for name, t in (("payload edited, signature kept", forged_role), ("alg=none token", none_alg), ("token signed with another key", wrong_key)):
    check(f"rejected: {name}", get("/auth/me", {"Authorization": "Bearer " + t}).status_code == 401)
check("refresh token cannot be used as an access token", get("/auth/me", {"Authorization": "Bearer " + stu_tok["refresh_token"]}).status_code == 401)
check("no token -> 401 on a university route", get("/students/").status_code == 401)
time.sleep(61)  # start a fresh rate-limit window so every response below is a real credential check
r = httpx.post(B + "/auth/login", json={"email": "aarav.sharma@reva.in", "password": "wrong"}); r2 = httpx.post(B + "/auth/login", json={"email": "nobody@reva.in", "password": "wrong"})
check("same error for wrong password and unknown account", r.status_code == r2.status_code == 401 and r.json()["detail"] == r2.json()["detail"])
t = []; codes = []
for email in ("aarav.sharma@reva.in", "nobody@reva.in"):
    s0 = time.perf_counter()
    codes += [httpx.post(B + "/auth/login", json={"email": email, "password": "wrong-pass"}).status_code for _ in range(3)]
    t.append((time.perf_counter() - s0) / 3 * 1000)
check("similar response time for known and unknown accounts", codes == [401] * 6 and 0.5 < t[0] / t[1] < 2.0, f"{t[0]:.0f} ms vs {t[1]:.0f} ms {codes}")
check("a correct sign-in still works and clears the failure count", httpx.post(B + "/auth/login", json={"email": "aarav.sharma@reva.in", "password": "StudentPass123!"}).status_code == 200)
print(f"\n{sum(res)}/{len(res)} checks passed"); sys.exit(0 if all(res) else 1)
