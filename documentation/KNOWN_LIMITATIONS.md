# Known limitations

ACEDRA in this repository is **version 1.0.0-rc.1, a release candidate**. `RELEASE_VERIFICATION.md` lists what was
executed to verify it. It is not yet institution-ready, and two parts of the production deployment are unverified
(see "Before production").

| Stage | Meaning | Status |
|---|---|---|
| Prototype-complete | All workflows work end to end on synthetic data; isolation and permissions are enforced and tested | **Yes** |
| Release candidate | Application verified in production mode on PostgreSQL 16 with Redis and SMTP delivery; migrations, backup and restore, isolation, permissions, sign-in protection and rate limiting executed and passing; no known dependency vulnerabilities; no secrets in the history | **Yes** |
| Production-ready | The container images and TLS front end built and smoke-tested, monitoring and alerting, an external security review | Not yet; see below |
| Institution-ready | A university has approved the deployment, provided authorised data, validated its policies and rules, and integrations are in place | No. Requires each institution's approval and data |

## Before production

* **No external security review or penetration test** has been performed. Automated tests attack the main
  isolation paths but are not exhaustive.
* **The Docker images and the Nginx TLS configuration have not been built or run.** The verification
  environment could not download base images, so `docker build` and `docker compose up` were not executed, and
  `docker/nginx.conf` has not been loaded by a real Nginx. What the images contain was verified outside Docker:
  the pinned requirements install on Python 3.12, the entrypoint runs as a non-root user, and the API runs under
  Gunicorn with four workers against PostgreSQL 16 and Redis. Both compose files pass `docker compose config`.
  Building the images and smoke-testing the stack (both containers healthy, HTTPS loads, HTTP redirects,
  `/api/health` answers through Nginx) is the first deployment step.
* **Backup and restore were tested on one machine**, from one PostgreSQL 16 database into another, with the
  scripts in `database/`. The commands for the compose stack (`docker compose exec db pg_dump …`) are documented
  but were not executed. Repeat the restore test on the real infrastructure.
* Tokens are stored in `sessionStorage` (cleared when the tab closes). The CSP no longer allows inline scripts
  and refresh tokens are single use, which limits the damage of a stolen token; httpOnly cookies with CSRF
  protection would reduce it further.
* Signing out ends every session of that account on every device (one token version per user).
* Imports, risk evaluation and report exports still run inside the request (in a worker thread, so they no
  longer stall other requests). A very large university needs a job queue with progress reporting.
* Email delivery and retry run inside the API process. That is adequate for invitations and resets; a bulk
  import of thousands of students sends its invitations in batches of 50 per minute per worker.
* Uploaded documents are stored in the database as extracted text. There is no virus scanning, and original files
  are not retained.
* There is no multi-factor authentication or SSO (SAML/OIDC) integration yet.
* Monitoring, alerting and log shipping are not configured. Logs are structured JSON on stdout.

## Functional scope

* **Risk identification is rule-based.** There is no trained predictive model, and the interface says so.
* **The assistant without a language model** returns extractive passages or structured record summaries, labelled
  as offline. Free-form answers need `LLM_PROVIDER` configured.
* **Lexical retrieval** (the default) matches keywords, not meaning. Configure an embedding provider for semantic
  retrieval. Vectors are stored as JSON and ranked in Python; pgvector indexing is not wired up yet, which is fine
  for thousands of passages but not millions.
* **Email provisioning** is recorded (method, counts, indicative estimate, status). ACEDRA does not create mailboxes.
  The cost estimate (₹120 per account per year) is a placeholder for documentation only.
* **No payment, billing or ERP integrations**. Imports are CSV or Excel uploads with column mapping.
* Departments, subjects, terms and teaching assignments are created in the admin UI (Academic structure).
  Editing or deleting subjects and terms is not available in the UI yet; teaching assignments can be removed.
* Imports report rows they cannot use instead of inventing values. A student row needs a known department code and
  a semester; attendance and results need an existing term (the current term for attendance).
* Placement readiness is an internal indicator, not a placement guarantee or employer certification.
* Existing v0.1 databases are not migrated in place (see the deployment guide).

## Product decisions still open

* **One account per email address across all universities.** A person cannot hold accounts at two tenants.
* **Sending student records to an external language model.** With `LLM_PROVIDER` set, personal-mode answers send
  the student's record to that provider. The prompt-injection filter is a short pattern list and is not a
  security boundary. Agree the provider, data-processing terms and consent with each institution first.

## Technical debt

Known, deliberate gaps in code quality, kept small and listed so they can be scheduled:

* **Untyped responses.** Platform, tenant, user and dashboard endpoints still build plain dictionaries without a
  `response_model`. Their shapes are written out in `frontend/src/types/api.ts`; declaring Pydantic schemas for
  them would make OpenAPI (and the generated frontend types) complete.
* **HTTP errors inside services.** Services raise `HTTPException` directly. That is consistent but couples
  business logic to HTTP; a small set of domain exceptions mapped in `main.py` would decouple them.
* **Large files.** `student_service.py` (profiles, analytics and the import pipeline) and `dashboard_service.py`
  are each several hundred lines; the frontend groups several pages per file (`admin.tsx` is the largest).
  Splitting them is mechanical but was left for a focused change.
* **Type checking.** The backend is linted with Ruff but not type-checked (annotations are partial; mypy would
  report many existing issues). The frontend is strict TypeScript with ESLint; Prettier is not used, to avoid a
  repository-wide reformat.
* **Transactions.** Services commit their own work, so an operation that spans several services is not
  atomic. Moving commits to the route (one unit of work per request) is the next structural change.
* **Tenancy scope is session state.** `AuthService` and the public routes switch the request's session to
  bypass mode and leave it there. It is safe where they are used today (authentication and public endpoints),
  but any new caller inside a university route would silently lose tenant filtering; wrap such uses in
  `unscoped(db)` instead.
* **Dependencies.** Python packages are pinned exactly in `backend/requirements.txt` and audited in CI; there
  is no automated update tool (Dependabot or Renovate) yet. `npm audit` and `pip-audit`
  report no known vulnerabilities at this release: React Router was upgraded from 6 to 7 and Vite from 5 to 7,
  and `minimatch` (used only by the linter) is pinned to a fixed version through an npm override.

## Public website and legal documents

* **Legal text is a draft.** The Terms and Conditions, Privacy Policy and Cookie Policy bundled in
  `backend/app/legal_content/` are published automatically as version `0.1-draft` so the site is never without
  them. They describe what the software does, are marked "Draft for legal review", and contain "To be confirmed"
  items (operating entity, registered address, governing law, liability, DPDP roles, retention periods, hosting
  and AI providers, grievance officer, guardian consent for under-18 students). They must be reviewed by a lawyer
  and agreed with each institution before being relied on.
* **Organisation details are placeholders.** Operator name, address, support, security and accessibility contacts
  render as "[To be configured: …]" until the `VITE_*` variables in `frontend/.env.example` are set at build time.
* **Approval is a recorded step, not a second person.** Publishing requires a super administrator to record an
  approval note first, and approver, publisher and times are stored, but the same super administrator can draft,
  approve and publish. A two-person rule would need at least two super administrators.
* **Server-side enforcement of acceptance is optional.** The web app always asks for acceptance of new Terms and
  Privacy versions after sign-in. The API refuses workspace requests until then only when
  `LEGAL_ACCEPTANCE_ENFORCED=true` (recommended in production, off by default for local development and API
  clients).
* **Cookie policy** is accurate for the current code: no cookies and no third-party requests; `sessionStorage`
  tokens and `localStorage` consent are essential; the saved appearance is the only optional item. Any new storage
  or third-party service needs the policy updated first.
* **Contact form** messages are stored and acknowledged by email (logged, not sent, with `EMAIL_PROVIDER=log`).
  Replies are sent from staff mailboxes; the platform inbox only tracks status. There is no automatic retention or
  deletion of contact messages, enquiries, audit logs or email copies.
* **Accessibility** was checked with keyboard navigation, a 375 px mobile viewport and axe-core (WCAG 2.0/2.1 A and
  AA rules, public pages only: no violations after raising the contrast of the muted, faint and bronze colours).
  No formal audit or systematic screen-reader testing has been done, and workspace charts lack full table
  alternatives. Full WCAG conformance is not claimed.

## Data

All bundled data is **generated sample data**. "REVA University" is the demonstration client workspace (240
students, four departments, `@reva.in` addresses): its people, records and policy documents were written for this
prototype, are not real REVA data and imply no partnership. Keep `EMAIL_PROVIDER=log` while it is loaded so that
no message is ever sent to a real `reva.in` address. Northfield University and Deccan Institute of Technology are
fictional and labelled as sample workspaces in the interface. Real integrations with any institution are future work that needs
that institution's authorisation.

## Identifiers kept from earlier names

The product was renamed from RIO to ACEDRA. These internal values keep the old name on purpose, because changing
them would break existing databases or stored records:

| Identifier | Where | Why it stays |
|---|---|---|
| `0001_rio_baseline` | Alembic revision ID (`backend/alembic/versions/0001_baseline_multitenant.py`) | Recorded in `alembic_version` of every migrated database |
| `rio_assisted` | Stored value of `student_email_mode`, enquiry `email_provisioning` and provisioning `method` | Persisted in existing rows; the interface shows it as "ACEDRA-assisted" |
| Historical text | Audit logs, email outbox and enquiry notes created before the rename | Records are kept exactly as written |
