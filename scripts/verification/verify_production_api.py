"""Release verification of a production-mode ACEDRA API on an EMPTY database.

Preconditions: the API runs with ENVIRONMENT=production, LEGAL_ACCEPTANCE_ENFORCED=true, Redis rate-limit storage and
SMTP pointed at scripts/verification/smtp_sink.py; the first super administrator (owner@rc-verify.example.org) has
been invited with the bootstrap snippet from documentation/DEPLOYMENT_GUIDE.md. The API must trust
X-Forwarded-For (as it does behind the bundled Nginx), which this script uses to act as different visitors.
"""
import datetime
import email
import glob
import os
import re
import sys
import time

import httpx
B = os.environ.get("ACEDRA_API", "http://127.0.0.1:8100/api/v1")
MAIL_DIR = os.environ.get("ACEDRA_MAIL_DIR", "/tmp/acedra-mail")
results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond))); print(("PASS" if cond else "FAIL"), "-", name, detail)
def latest_mail(to, kind):
    for path in sorted(glob.glob(os.path.join(MAIL_DIR, "*.eml")), reverse=True):
        msg = email.message_from_bytes(open(path, "rb").read())
        body = msg.get_payload(decode=True).decode("utf-8", "replace") if not msg.is_multipart() else ""
        if msg["To"] == to and kind in body:
            return re.search(r"token=([A-Za-z0-9_\-]+)", body.replace("=\n", "")).group(1)
def post(path, body=None, headers=None, ip="198.51.100.10"):
    h = {"X-Forwarded-For": ip, **(headers or {})}
    return httpx.post(B + path, json=body or {}, headers=h, timeout=30)
def get(path, headers=None, ip="198.51.100.10"):
    return httpx.get(B + path, headers={"X-Forwarded-For": ip, **(headers or {})}, timeout=30)
OWNER, PW = "owner@rc-verify.example.org", "Release#Owner2026"

legal = {d["doc_type"]: d["version"] for d in get("/public/legal").json() if d["doc_type"] in ("terms", "privacy")}
check("public legal documents are published automatically", set(legal) == {"terms", "privacy"}, str(legal))
tok = latest_mail(OWNER, "accept-invitation")
check("invitation email delivered through SMTP with a single-use link", bool(tok))
r = post("/auth/invitations/accept", {"token": tok, "password": PW, "accepted_versions": {}})
check("invitation cannot be accepted without accepting Terms and Privacy", r.status_code in (400, 409, 422), f"[{r.status_code}]")
r = post("/auth/invitations/accept", {"token": tok, "password": "weak", "accepted_versions": legal})
check("weak password rejected", r.status_code == 422, f"[{r.status_code}]")
r = post("/auth/invitations/accept", {"token": tok, "password": PW, "accepted_versions": legal})
check("first super administrator activated", r.status_code == 200 and r.json()["user"]["role"] == "platform_admin", f"[{r.status_code}]")
auth = {"Authorization": "Bearer " + r.json()["access_token"]}; refresh1 = r.json()["refresh_token"]
r = post("/auth/invitations/accept", {"token": tok, "password": PW, "accepted_versions": legal})
check("invitation link is single use", r.status_code == 400, f"[{r.status_code}]")
check("platform workspace reachable after acceptance", get("/platform/meta", auth).status_code == 200)
check("no token -> 401", get("/platform/universities").status_code == 401)
check("forged token -> 401", get("/platform/universities", {"Authorization": "Bearer abc.def.ghi"}).status_code == 401)
check("platform account cannot use university routes", get("/students/", auth).status_code == 403)

# --- legal acceptance enforcement (LEGAL_ACCEPTANCE_ENFORCED=true)
today = datetime.date.today().isoformat()
d = post("/platform/legal-documents", {"doc_type": "terms", "version": "1.0-rc1", "title": "Terms and Conditions",
                                       "body": "# Terms\n\nRelease-candidate verification text."}, auth)
check("draft legal version created", d.status_code == 201, f"[{d.status_code}] {d.text[:80]}")
doc_id = d.json()["id"]
r = post(f"/platform/legal-documents/{doc_id}/publish", {"effective_date": today}, auth)
check("publishing without recorded approval is refused", r.status_code in (400, 409, 422), f"[{r.status_code}]")
check("approval recorded", post(f"/platform/legal-documents/{doc_id}/approve", {"approval_note": "RC verification approval"}, auth).status_code == 200)
check("version published", post(f"/platform/legal-documents/{doc_id}/publish", {"effective_date": today}, auth).status_code == 200)
r = get("/platform/meta", auth)
check("API refuses workspace calls until new Terms are accepted (428)", r.status_code == 428, f"[{r.status_code}]")
pend = get("/auth/legal-status", auth).json()["pending"]
check("legal-status lists the pending version", [p["version"] for p in pend] == ["1.0-rc1"], str([p["version"] for p in pend]))
r = post("/auth/legal-acceptances", {"accepted_versions": {"terms": "0.1-draft", "privacy": legal["privacy"]}}, auth)
check("accepting a superseded version is refused", r.status_code == 409, f"[{r.status_code}]")
check("accepting the current version", post("/auth/legal-acceptances", {"accepted_versions": {"terms": "1.0-rc1", "privacy": legal["privacy"]}}, auth).status_code == 200)
check("workspace reachable again", get("/platform/meta", auth).status_code == 200)

# --- production data exposure
out = get("/platform/email-outbox", auth).json()
check("email bodies (single-use links) hidden in production outbox", out["bodies_visible"] is False and all(i["body_text"] is None for i in out["items"]))

# --- tokens
r2 = post("/auth/refresh", {"refresh_token": refresh1})
check("refresh token exchanges once", r2.status_code == 200)
new_auth = {"Authorization": "Bearer " + r2.json()["access_token"]}
check("re-used refresh token is rejected", post("/auth/refresh", {"refresh_token": refresh1}).status_code == 401)
check("re-use ends every session for the account", get("/auth/me", new_auth).status_code == 401)
r = post("/auth/login", {"email": OWNER, "password": PW}); auth = {"Authorization": "Bearer " + r.json()["access_token"]}
check("sign in again", r.status_code == 200)
check("logout", post("/auth/logout", None, auth).status_code == 200)
check("token revoked by logout", get("/auth/me", auth).status_code == 401)

# --- lockout (each attempt from a different address, so this is the account lock, not the rate limit)
codes = [post("/auth/login", {"email": OWNER, "password": "Wrong#Password1"}, ip=f"203.0.113.{i}").status_code for i in range(1, 6)]
check("five wrong passwords -> 401 each", codes == [401] * 5, str(codes))
r = post("/auth/login", {"email": OWNER, "password": PW}, ip="203.0.113.50")
check("account locked even with the right password (429)", r.status_code == 429, f"[{r.status_code}]")
check("reset request accepted", post("/auth/password-reset-request", {"email": OWNER}).status_code == 200)
time.sleep(7)
rt = latest_mail(OWNER, "reset-password")
check("password reset email delivered through SMTP", bool(rt))
check("password reset", post("/auth/password-reset-confirm", {"token": rt, "new_password": "Release#Owner2027"}).status_code == 200)
check("reset link is single use", post("/auth/password-reset-confirm", {"token": rt, "new_password": "Release#Owner2028"}).status_code == 400)
check("reset unlocks the account", post("/auth/login", {"email": OWNER, "password": "Release#Owner2027"}, ip="203.0.113.51").status_code == 200)
r = post("/auth/password-reset-request", {"email": "nobody@rc-verify.example.org"})
check("reset for unknown email gives the same answer", r.status_code == 200 and "If an active account exists" in r.text)

# --- rate limiting through Redis across the four workers
codes = [post("/auth/login", {"email": "nobody@rc-verify.example.org", "password": "Wrong#Password1"}, ip="192.0.2.77").status_code for _ in range(24)]
check("sign-in limited to 20/minute per visitor across 4 workers", codes[:20] == [401] * 20 and codes[20:] == [429] * 4, str(codes[18:]))
check("another visitor is not affected", post("/auth/login", {"email": "nobody@rc-verify.example.org", "password": "Wrong#Password1"}, ip="192.0.2.78").status_code == 401)
codes = [httpx.post(B + "/public/contact", json={"name": "Asha Rao", "email": "asha@uni.example.org", "institution": "Example University", "subject": "Verification", "message": "Release candidate rate limit verification message.", "website": ""}, headers={"X-Forwarded-For": "192.0.2.90"}).status_code for _ in range(7)]
check("public contact form limited to 5/hour per visitor", codes.count(429) == 2 and codes[5:] == [429, 429], str(codes))

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed"); sys.exit(1 if failed else 0)
