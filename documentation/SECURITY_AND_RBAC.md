# Security, privacy and access control

## Roles

| Role | Workspace | Sees |
|---|---|---|
| Student | `/app` | Only their own profile, academics, alerts, plan, readiness, applications, notifications and conversations |
| Faculty | `/app` | Students in sections they teach, plus students an administrator explicitly shared with them (the same set in lists, direct access and analytics, across departments) |
| Mentor | `/app` | Assigned mentees, and interventions for them |
| University administrator / HOD | `/app` | Everything in their own university |
| Placement officer | `/app` | Placement data for their university; no intervention notes |
| ACEDRA super administrator | `/platform` | Enquiries, tenants, team, audit. No student records without a grant |
| ACEDRA employee | `/platform` | As above, with configuration limited to assigned universities and only the permissions granted |

Navigation only reflects these rules. **They are enforced on the server**: role dependencies on every route,
the university guard on every tenant router, ORM-level tenant and student scoping, and resource ownership checks
(conversations, messages, interventions).

## Fixes made in this release (relative to v0.1)

| Issue in v0.1 | Fix |
|---|---|
| No tenant model; all data global | `TenantMixin` on 54 tables, ORM read scoping, write guard, per-tenant unique keys |
| Faculty and mentors could open any student by ID | Student scope enforced in the ORM and checked on every `student_id` path or query parameter (403 inside the tenant, 404 across tenants) |
| Password reset returned the reset token in the HTTP response | Emailed single-use hashed tokens; uniform responses |
| Default shared password (`StudentPass123!`) for created and imported students | Invitation-only activation; imports send invitations |
| Anonymous chatbot; conversations readable by session ID or by any admin | Auth required; strict per-user ownership; client session IDs ignored |
| Staff "personal mode" silently picked an arbitrary student | Staff must choose a student inside their scope |
| Hard-coded insecure JWT secret accepted in production | Production refuses to start with a default or short secret, wildcard CORS or SQLite |
| Tokens could not be revoked | `token_version` claim; logout, password, role and status changes revoke tokens |
| Upload type trusted the file extension | Magic-byte and UTF-8 checks, size limit, category and access validation |
| Tracebacks printed for every error | Structured JSON logging; generic 500 bodies; paths only (no query strings or bodies) in logs |
| Retrieval described as "semantic embeddings" | Labelled lexical retrieval; real embeddings only when configured |
| Deterministic fallback presented as AI output | `generation_mode` stored and shown; fallback is extractive or record-based only |
| `ACTIVE` alert filter matched nothing (assistant always reported zero alerts) | `ACTIVE` now means "not resolved or closed" |
| Personal assistant read a non-existent metric (0% attendance, "critical deficit") | Uses calculated attendance and the university's configured threshold |
| Students could apply to opportunities they weren't eligible for | Eligibility enforced server-side |
| Students saw staff intervention notes | Intervention detail is staff-only; the student list hides notes |

## Other controls

* bcrypt (12 rounds) password hashing; password policy of at least 10 characters mixing three character classes.
* Rate limits: login, invitation and reset 20/min, public enquiries and contact messages 5/hour, everything else
  240/min (slowapi; disabled in tests). The enquiry and contact forms have honeypot fields; the contact form also
  rejects free-mail addresses and link-heavy messages.
* Legal documents: only ACEDRA super administrators can create, edit, approve and publish versions; ACEDRA
  employees can read them; university accounts get 404. Publishing requires a recorded approval, published
  versions are immutable, and all actions are audited. Acceptances are recorded per user, university, document and
  version; signing in is never treated as acceptance. `LEGAL_ACCEPTANCE_ENFORCED=true` makes the API refuse
  workspace requests (428) until the current versions are accepted.
* The frontend loads no third-party scripts, fonts or trackers and sets no cookies; the Nginx CSP allows only
  `'self'` origins.
* CORS restricted to configured origins and methods. Security headers set by both the API and Nginx; the Nginx
  CSP restricts `connect-src` to self.
* Prompt-injection patterns are blocked in questions and neutralised inside retrieved documents. The system
  prompt forbids following instructions found in documents or discussing other students.
* Audit log entries are tenant-scoped for university administrators and platform-wide for ACEDRA staff, covering
  sign-in success and failure, invitations, configuration, grants, every student-data access and enquiry changes.

## Tests that attack these controls

`backend/tests/test_multitenancy_and_roles.py` and `test_platform_workflow.py` cover:
cross-tenant reads and writes by ID, tenant-isolated retrieval, disabled modules, students calling admin and
platform endpoints, university admins calling platform endpoints and assigning platform roles, faculty and mentor
scope, platform accounts reading student data, conversation ownership, the explicit grant flow with audit and
revocation, the password reset and logout revocation, expired and forged tokens, role-change escalation and the
whole enquiry → activation workflow.
