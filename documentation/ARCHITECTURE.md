# ACEDRA architecture

ACEDRA is one application serving many universities. Each university is a **tenant** with its own configuration,
users and records. The ACEDRA team (the company operating the platform) works in a separate **platform** workspace.

```
                       ┌──────────────────────────── React + Vite (TypeScript, Tailwind) ────────────────────────────┐
 Public website  ───▶  │  /  /enquire  /login  /accept-invitation  /reset-password                                    │
 University users ───▶ │  /app/*       role workspaces: student · faculty · mentor · admin · placement officer        │
 ACEDRA staff ───────▶ │  /platform/*  enquiries · universities · team · grants · audit · email outbox                 │
                       └───────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                               │ /api/v1 (JWT bearer)
                       ┌───────────────────────────────────────▼────────────────────────────────────────────────────┐
                       │ FastAPI                                                                                    │
                       │  public/*  auth/*          → unauthenticated (rate limited)                                │
                       │  platform/*                → platform accounts only (others get 404)                       │
                       │  tenant/* users/* students/* risk/* recommendations/* placement/* ai/* interventions/* …   │
                       │       └─ get_university_user guard: rejects platform accounts, enforces enabled modules,   │
                       │          checks every student_id against the caller's authorised scope                     │
                       │  Services: business rules, queries and response serialisers, one file per module           │
                       │  SQLAlchemy session ── tenancy events: tenant filter · student scope · write guard           │
                       └───────────────────────────────────────┬────────────────────────────────────────────────────┘
                                                               │
                                           PostgreSQL 16 (production) / SQLite (local)
```

## Multi-tenancy

* `universities` is the tenant table. Every university-owned table has `university_id` via `TenantMixin`
  (`backend/app/core/tenancy.py`) — 54 tables in total.
* **Read isolation** is automatic. On every authenticated request `deps.get_current_user` places a `TenantScope`
  on the database session. A `do_orm_execute` hook adds `university_id = :tenant` to every SELECT, UPDATE and
  DELETE on tenant-owned entities, including relationship loads. The existing services were not rewritten; they
  inherit isolation.
* **Student scope**: for students, faculty and mentors the same hook also limits `Student` and every
  student-owned table to the students that user may see (`core/access.py`):
  * student → their own record
  * faculty → students in the department, semester and section of their teaching assignments, plus students an
    administrator explicitly shared with them (`staff_student_access`)
  * mentor → assigned mentees
  * administrator and placement officer → the whole university
* **Write isolation**: a `before_flush` hook stamps new rows with the session's tenant and raises
  `CrossTenantWriteError` (HTTP 403) on any attempt to create, change or delete a row in another tenant.
* **Platform sessions** cannot read confidential academic tables at all (the hook adds `WHERE false`). The one
  exception is `GET /platform/universities/{id}/student-directory`, which checks for an active
  `StudentDataAccessGrant`, reads a minimal set of fields and writes a `STUDENT_DATA_ACCESSED` audit record.
* Per-tenant uniqueness: department codes, subject codes, USNs, employee IDs, rule codes, skill names and similar
  keys are unique per university.

## Two administration levels

| | Platform (ACEDRA team) | University administrator |
|---|---|---|
| Routes | `/platform/*` | `/tenant/*`, `/users/*`, module admin endpoints |
| Accounts | `platform_admin`, `platform_employee` (`university_id` is NULL) | `admin` in one university |
| Can | manage enquiries, create tenants, configure identity, domains, modules and academic structure, assign the primary ACEDRA employee, provision the first administrator, activate or suspend, record data grants | invite users, assign roles, manage departments, mentors, shared access, rules, catalogue, documents, imports, reports, and settings within their authority |
| Cannot | read student records without a grant | see other universities, use platform routes, change the ACEDRA contact, assign platform roles, change identity, domains or modules |

ACEDRA employee permissions are split into **configure** (`tenant.configure`, only for universities they are
assigned to) and **coordinate** (`tenant.coordinate`: enquiries, notes, provisioning). Student-data access is
never a standing permission. Each university's primary employee is stored in `universities.primary_employee_id`,
with full history in `employee_assignments`.

## Accounts and authentication

* No public registration. Users are created by an administrator (or by the platform for a university's first
  administrator) as **inactive and unverified**, with an unusable password. An invitation email carries a
  single-use token (only its SHA-256 hash is stored). Accepting it verifies the address, sets the password and
  activates the account.
* Invitations require an email on one of the university's approved domains. A matching domain alone grants
  nothing.
* Access tokens (60 min) carry `tid` (tenant) and `ver` (token version). Logout, password change, password
  reset, role change and deactivation increment `users.token_version`, which revokes every issued token
  server-side.
* Password reset uses emailed single-use tokens (30 min). The token is never returned over HTTP. Responses are
  identical whether or not the account exists.
* Suspended or inactive universities lock out all their users immediately. During onboarding only the
  university's administrators can sign in.

## Enquiry → onboarding workflow

`public/enquiries` → `new` → under review → contacted → meeting scheduled → requirements gathering →
proposal/agreement (agreement reference and modules recorded) → approved → **create tenant** (sets onboarding,
seeds default rules and catalogue, assigns the ACEDRA employee, records any ACEDRA-assisted email request as a
chargeable provisioning request) → configure → **invite administrator** → **activate** (blocked until the
checklist is complete; sets the enquiry to active). Rejected and closed are terminal, with reopening to under
review. Every step writes an `enquiry_activities` row and an audit record.

## Legal documents, acceptance and the contact form

* `models/legal.py`: `LegalDocument` (type `terms` | `privacy` | `cookies`, version, body, status
  `draft` → `approved` → `published`, effective date, approver/publisher and note), `LegalAcceptance` (user,
  university, document, type, version, context `invitation` | `sign_in`, time) and `ContactMessage`. These are
  global, not tenant-scoped; acceptances carry the user's university for reporting. Migration `0002_legal_contact`.
* `services/legal_service.py`: the version in force is the newest published one whose effective date has arrived.
  If a type has never been published, the bundled text in `app/legal_content/` is published as `0.1-draft` (in its
  own session, tolerant of concurrent first requests). `record_acceptance` accepts only the versions in force
  (409 for stale versions) and is idempotent. `LegalDocumentAdmin` drafts, edits drafts, approves with a note,
  returns to draft and publishes; every action is audited.
* Routes: `GET /public/legal[/{type}[/history]]`, `POST /public/contact`; `GET /auth/legal-status`,
  `POST /auth/legal-acceptances`, `accepted_versions` on `POST /auth/invitations/accept`;
  `/platform/legal-documents` (read: ACEDRA team; write: super administrators) and `/platform/contact-messages`.
* `api/deps.py::_require_legal_acceptance` returns 428 from the university and platform guards when
  `LEGAL_ACCEPTANCE_ENFORCED` is on and documents are pending.
* Frontend: `components/legal.tsx` (legal links, cookie banner and preferences dialog, Markdown renderer, the
  post-sign-in `LegalAcceptanceGate` inside `RequireAuth`), `lib/consent.ts` (stored choice; the theme is saved only
  with preference consent), `lib/site.ts` (organisation details from `VITE_*`, placeholders otherwise),
  `pages/site.tsx` (public information and legal pages), `pages/legalAdmin.tsx` (platform legal administration
  and contact inbox).

## AI assistant

* Authenticated only; there is no chatbot on the public site. Conversations belong to one user; others get 404.
* **University mode** retrieves passages from the tenant's documents, filtered by the document's access level
  and the caller's role, then drops passages that do not cover the question's content terms.
* **Personal mode** grounds answers in `StudentContextService`. Students get only themselves; staff must name a
  student inside their scope.
* `LLM_PROVIDER` = `openai_compatible` | `anthropic` | `ollama` generates answers from sanitised passages. With
  `none` (the default), ACEDRA returns extractive passages or a structured summary of verified records, flagged
  `generation_mode = "offline_fallback"`. The interface labels it "Offline answer · no language model used".
* `EMBEDDING_PROVIDER=lexical` is a hashed term-frequency vector: **keyword retrieval, not semantic**. Real
  embeddings are used when an embedding provider is configured; reindex documents after switching provider.

## Backend layout and conventions

A request passes through four layers:

1. **Authentication** (`api/deps.py`): `get_current_user` validates the JWT (type, token version, tenant claim),
   checks the university is active, and places the caller's `TenantScope` on the session.
2. **Route guard**: every university router is mounted with `get_university_user` (`api/v1/__init__.py`), which
   rejects platform accounts, blocks disabled modules and checks any `student_id` in the path or query against
   the caller's scope. Role checks use `require_role(...)`, `require_university_admin` or `require_platform_*`.
3. **Route handler** (`api/v1/<module>.py`): parses input, applies the remaining per-endpoint rules (for example
   "students may only act on their own records"), calls a service and returns its result.
4. **Service** (`services/<module>_service.py`): business rules, queries and the serialisers that turn ORM rows
   into response schemas (`alert_summary`, `recommendation_to_out`, `application_to_response`,
   `intervention_summary`, …). Every endpoint that returns the same kind of record uses the same serialiser.

Conventions:

* Responses are declared with Pydantic schemas (`schemas/<module>.py`) wherever practical, so FastAPI filters
  out anything not listed and the frontend types can be generated from OpenAPI. Never return ORM objects from an
  endpoint without a `response_model`.
* Timestamps are naive UTC: use `app.core.clock.utcnow()`.
* Services raise `HTTPException` (or `ValueError`, translated by the route) with a user-facing message; unexpected
  errors reach the global handler in `main.py`, which logs them and returns a generic 500.
* A broad `except Exception` is allowed only around third-party calls with an explicit, logged fallback, and
  carries a `# noqa: BLE001 — reason` comment.
* Configuration lives in `core/config.py` (`Settings`); invalid production settings stop the API at start-up.

### Module map

| Module | API routes | Service | Models | Frontend pages |
|---|---|---|---|---|
| 1. Student intelligence | `students.py`, `academics.py`, `imports.py`, `departments.py` | `student_service.py` | `profile`, `academic`, `student_intelligence` | `student.tsx` (academics), `staff.tsx`, `admin.tsx` (import, structure) |
| 2. Early warning | `risk.py` | `risk_service.py` | `risk` | `staff.tsx` (alerts), `student.tsx` (support), `admin.tsx` (rules) |
| 3. Recommendations | `recommendations.py` | `recommendation_service.py` | `recommendation` | `student.tsx` (plan), `admin.tsx` (catalogue) |
| 4. Placement readiness | `placement.py` | `placement_service.py` | `placement` | `student.tsx` (career), `roles.tsx` (placement pages) |
| 5. AI assistant | `ai_assistant.py` | `ai_assistant_service.py`, `llm_service.py`, `embedding_service.py`, `student_context_service.py` | `ai_assistant` | `components/chat.tsx`, `admin.tsx` (documents) |
| 6. Dashboards & interventions | `dashboards.py`, `interventions.py` | `dashboard_service.py`, `intervention_service.py`, `notification_service.py`, `report_service.py` | `intervention` | `roles.tsx` (role homes), `staff.tsx` (interventions), `admin.tsx` (reports) |
| Tenancy & users | `tenant.py`, `users.py`, `auth.py`, `audit_logs.py`, `system_settings.py` | `auth_service.py`, `invitation_service.py`, `email_service.py` | `user`, `platform`, `audit`, `system` | `admin.tsx` (people, settings, audit), `public.tsx` (sign-in, invitations) |
| Platform | `platform.py`, `public.py` | `platform_service.py` | `platform` | `platform.tsx`, `public.tsx` (website, enquiry) |
| Legal & contact | `public.py`, `auth.py`, `platform.py` | `legal_service.py` | `legal` | `site.tsx`, `legalAdmin.tsx`, `components/legal.tsx` |

Business rules are documented where they are implemented: risk evaluation on `risk_service`
(`_StudentRiskMetrics` and the per-indicator observers), recommendation generation on
`RecommendationService.generate_recommendations_for_student`, readiness scoring on
`PlacementService.calculate_placement_readiness`, and the student access policy in `core/access.py`.

## Frontend structure

```
frontend/src/
  types/        api.ts (domain types) · openapi.ts (generated from the backend, do not edit)
  lib/          api client (typed verbs, refresh-on-401, errorMessage), auth context, useApi hook, formatting, theme,
                consent (browser-storage choice), site (configurable organisation details)
  components/   ui.tsx (design system), shell.tsx (app shell, nav, menus), access.tsx (module and role gates),
                brand.tsx, charts.tsx, chat.tsx (assistant workspace), legal.tsx (legal links, consent, acceptance gate)
  pages/        public.tsx, student.tsx, staff.tsx (directory, student detail, alerts, interventions),
                roles.tsx (faculty, mentor, admin, placement homes + placement pages), admin.tsx, platform.tsx, common.tsx,
                site.tsx (about, platform, security, FAQ, contact, accessibility, legal documents), legalAdmin.tsx
```

* **Types.** Where the backend declares a response schema, `types/api.ts` aliases the generated OpenAPI type, so
  a backend change that breaks the UI fails `npm run typecheck`. Regenerate after changing backend schemas with
  `npm run gen:api` with the backend's virtual environment active (it imports the app; no server or database
  needed). The few endpoints that still return plain
  dictionaries have hand-written interfaces in the same file, each naming the backend function it mirrors.
* **Data loading.** `useApi<T>(path, params)` handles loading, errors, reloads and stale responses; mutations
  call `api.post<T>()` etc. and report failures with `errorMessage(e)`.
* **Code splitting.** `App.tsx` lazy-loads each page module, so the public site and sign-in page do not download
  the workspaces or the charting library.

Design tokens live in `src/index.css` as CSS variables, with a light theme (primary) and a dark theme, and are
mapped into Tailwind in `tailwind.config.js`.
