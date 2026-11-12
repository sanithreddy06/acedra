# ACEDRA 1.0.0-rc.1 — release verification record

Date: 12 November 2026. Everything in the "Result" columns below is the actual output of a command that was
run for this release candidate. Anything that was **not** executed is listed under
[Not executed](#not-executed) and is not claimed as passing.

## Summary

| Area | Result |
|---|---|
| Docker image builds and `docker compose up` | **Not executed** — base images could not be downloaded in the verification environment |
| Compose files | Both pass `docker compose config` |
| What the backend image contains, run outside Docker | Pass — pinned requirements on Python 3.12, entrypoint as a non-root user, Gunicorn × 4, PostgreSQL 16, Redis, SMTP |
| Migrations | Pass — empty PostgreSQL database to head (`0003_lockout_email_queue`); `alembic check` clean on PostgreSQL and SQLite |
| Health checks | Pass — `/health` and `/ready` 200; `/docs`, `/redoc`, OpenAPI schema 404 in production |
| First super administrator bootstrap | Pass — documented snippet, invitation delivered over SMTP, accepted |
| Legal acceptance enforcement | Pass — 428 until the current Terms and Privacy versions are accepted |
| Backend tests | Pass — 165 on SQLite, 165 on PostgreSQL 16 |
| Frontend | Pass — `npm ci`, ESLint, TypeScript, production build |
| Dependency vulnerabilities | 11 npm advisories found and fixed; `npm audit` 0, `pip-audit` 0 |
| Secrets | No credentials in the working tree or in any commit |
| Backup and restore | Pass — restored into a separate database; 69 tables, 14,655 rows, content identical |
| Tenant isolation, roles, authentication | Pass — 46 of 46 live checks, plus the test suite |
| Rate limiting | Pass — enforced across four workers through Redis, per visitor address |
| Production configuration guards | Pass — eight development settings each refused before the database is touched |
| User interface | Pass — 57 pages across six roles from the production build, no errors |

## Environment

| Component | Version |
|---|---|
| Python (application and tests) | 3.12.3, packages from `backend/requirements.txt` / `requirements-dev.txt` |
| PostgreSQL | 16.15 |
| Redis | 7.0.15 |
| Node / npm | 22.23.4 / 10.9.9 |
| Docker / Compose (for `config` only) | 29.9.3 / 5.7.0 |

The stack was run on one Linux machine without containers. To stay as close to `docker/Dockerfile.backend.prod`
as possible: a virtual environment at `/opt/venv` was built with `pip install -r backend/requirements.txt`; the
application was copied to `/app` in the image's layout (`app/`, `alembic/`, `alembic.ini`, `database/seeds/`);
`docker/entrypoint.sh` was installed as `/entrypoint.sh`; and everything ran as an unprivileged user `appuser`
(uid 10001), started with the image's own command.

## 1. Dockerfiles and compose files

| Command | Result |
|---|---|
| `docker pull python:3.12-slim` (also `node:20-alpine`, `nginx:1.27-alpine`, `pgvector/pgvector:pg16`, `redis:7-alpine`) | `failed to do request: Head "https://registry-1.docker.io/…": Forbidden` — the registry is blocked from the verification environment, so **no image could be built or started** |
| `docker compose -f docker-compose.prod.yml --env-file <values> config -q` | exit 0; services `db redis backend frontend`; published ports: 80 and 443 only (the database, Redis and the API publish none) |
| `docker compose -f docker-compose.prod.yml config -q` (no values) | fails with 6 "required variable … is missing a value" messages, as intended |
| `docker compose -f docker-compose.yml config -q` | exit 0 |
| `crossplane parse --single-file docker/nginx.conf` (syntax parse without Nginx) | `status: ok`, no errors; 2 servers, 8 locations. A deliberately broken file is reported as failed |
| `pip install -r backend/requirements.txt` on Python 3.12, then `pip check` | installs; `No broken requirements found.` |
| Non-root user can run the application | `appuser` executes `/opt/venv/bin/gunicorn` and owns `/app` |

Reviewing the files found and fixed one real defect: the sample-data seed could not import the application in
the container layout (`ModuleNotFoundError: No module named 'app'`), so the development Docker stack would have
failed on first start. After the fix the entrypoint migrates an empty PostgreSQL database and loads the sample
universities (`Students per tenant: {'REVA': 240, 'Northfield': 14, 'Deccan Tech': 10}`), and a second start
reports `Database already contains universities — skipping demo seed.`

## 2. Migrations, health, bootstrap, legal acceptance (production mode)

Started with `ENVIRONMENT=production`, a random 64-character secret, PostgreSQL 16, `RATE_LIMIT_STORAGE_URI=redis://…`,
`EMAIL_PROVIDER=smtp` pointing at a local SMTP server that stores what it receives, `LEGAL_ACCEPTANCE_ENFORCED=true`:

```
/entrypoint.sh gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8100 \
    --forwarded-allow-ips '*' --timeout 120
```

| Check | Result |
|---|---|
| Entrypoint on an empty database | `Running upgrade -> 0001_rio_baseline`, `-> 0002_legal_contact`, `-> 0003_lockout_email_queue`; four workers booted; all five processes owned by `appuser` |
| `alembic current` / `alembic check` | `0003_lockout_email_queue (head)` / `No new upgrade operations detected.` |
| `GET /health` | `{"status":"healthy","service":"ACEDRA","version":"1.0.0-rc.1"}` [200] |
| `GET /ready` | `{"status":"ready","database":"connected",…,"email":"smtp"}` [200] |
| `GET /docs`, `/redoc`, `/api/v1/openapi.json` | 404, 404, 404 |
| Bootstrap snippet from the deployment guide | `Invitation emailed to owner@rc-verify.example.org`; the outbox row is `sent` after 1 attempt; the message arrived at the SMTP server with an `https://` link |
| `python scripts/verification/verify_production_api.py` | **37/37 checks passed**, exit 0 |
| Errors in the API log during the run | 0 |

The 37 checks, all passing:

* Legal documents are published automatically; an invitation cannot be accepted without accepting Terms and
  Privacy (422); a weak password is refused (422); the first super administrator is activated; the invitation
  link works once (400 on re-use).
* No token → 401; forged token → 401; a platform account is refused on university routes (403).
* A new Terms version cannot be published without a recorded approval (409). After approval and publication the
  API answers **428** on workspace calls; `legal-status` lists the pending version; accepting a superseded
  version is refused (409); accepting the current versions restores access.
* Email bodies are hidden in the production outbox.
* A refresh token exchanges once; re-use is rejected (401) and ends every session of the account; logout
  revokes the access token.
* Five wrong passwords → the account is locked even for the right password (429); the reset email is
  delivered over SMTP; the reset link works once; a reset unlocks the account; a reset request for an unknown
  address gets the same answer.
* Sign-in is limited to 20 per minute per visitor across the four workers (requests 21–24 → 429) while another
  visitor is unaffected; the public contact form is limited to 5 per hour (requests 6–7 → 429).

## 3. Tests, type-check, lint, build

| Command | Result |
|---|---|
| `ruff check .` (backend) | `All checks passed!` |
| `alembic upgrade head && alembic check` (SQLite) | `No new upgrade operations detected.` |
| `python -m pytest -q` (SQLite) | `165 passed, 8 warnings in 61.28s` |
| `TEST_DATABASE_URL=postgresql+psycopg://… python -m pytest -q` (PostgreSQL 16) | `165 passed, 8 warnings in 73.61s` |
| `npm ci` | `found 0 vulnerabilities` |
| `npm run lint` | exit 0 |
| `npm run typecheck` | exit 0 |
| `npm run build` | `✓ built in 4.20s`; no inline scripts in `dist/index.html` |

The 8 warnings are deprecation notices from libraries (Pydantic class-based config in `schemas/placement.py`,
Starlette's test client); none is a failure.

## 4. Dependency vulnerabilities

| Scanner | Before | After |
|---|---|---|
| `pip-audit -r backend/requirements.txt` | No known vulnerabilities | `No known vulnerabilities found` |
| `npm audit` | 11 (1 high, 10 moderate) | `found 0 vulnerabilities` |
| `npm audit --omit=dev` (what ships to browsers) | 2 moderate | `found 0 vulnerabilities` |

| Package | Severity | Advisory | Affects | Status |
|---|---|---|---|---|
| `react-router`, `react-router-dom` 6.x | moderate | GHSA-wrjc-x8rr-h8h6 (open redirect via backslash in links), GHSA-337j-9hxr-rhxg (constructor injection in SSR hydration) | the shipped site | **Fixed** — upgraded to 7.18.5 |
| `vite` 5.x | high | GHSA-4w7w-66w2-5vf9, GHSA-9jrq-w75r-8gcw, GHSA-rq7h-c2jc-7f22, GHSA-fx2h-pf6j-xcff and four `launch-editor` advisories | development server only | **Fixed** — upgraded to 7.3.8 (`@vitejs/plugin-react` to 5.2) |
| `esbuild` ≤ 0.24.2 | moderate | GHSA-67mh-4wv8-2f99 | development server only | **Fixed** — newer version comes with Vite 7 |
| `minimatch` 10.x under `typescript-eslint` (6 packages reported) | moderate | GHSA-g3hv-75wg-m249 (denial of service) | the linter only | **Fixed** — npm override to 11.0.8; `typescript-eslint` itself is already at its latest version |

After the upgrades the lint, type-check and build pass, and the built site was exercised page by page (section 7).
Vite 7 needs Node 20.19 or newer; the images use `node:20-alpine`.

## 5. Secret scanning

| Command | Result |
|---|---|
| `detect-secrets scan` (working tree) | 38 findings in 19 files, each reviewed: the built-in development secret, the published demonstration and test passwords, and example connection strings. Recorded in `.secrets.baseline` |
| `detect-secrets-hook --baseline .secrets.baseline <all tracked files>` | exit 0 (nothing outside the reviewed baseline) |
| Control: a file containing an AWS-style access key | detected, exit 1 |
| `python scripts/scan_git_history.py` (added lines of every commit, and every file name ever committed) | `0 finding(s).` Four placeholder strings in early commits (`REPLACE_WITH_…`, `change-this-in-production-…`) were reviewed and allow-listed |
| Sensitive file names ever committed (`.env`, `*.pem`, `*.key`, `*.db`) | none; only the `.env*.example` templates |

Gitleaks is configured in CI for the full history but its binary could not be run in the verification
environment; the dependency-free history scanner above was used instead. Both, together with `pip-audit`,
`npm audit` and detect-secrets, run on every push (`.github/workflows/ci.yml`, job `security`). **The CI
workflow itself has not run yet** — the repository has no remote.

## 6. Backup and restore

Source: a PostgreSQL 16 database created by the entrypoint (migrations plus the sample universities). Target: a
separate, empty database.

| Command | Result |
|---|---|
| `DATABASE_URL=…/acedra_devstack ./database/backup_db.sh <dir>` | `Backup written: acedra_pg_20261112_144744.sql.gz (288K)`; file and `.sha256` created with owner-only permissions |
| `DATABASE_URL=…/acedra_restore_test ./database/restore_db.sh <file>` | `Checksum verified.` … `Restore complete: 69 tables.` exit 0 |
| `python scripts/verification/compare_postgres_databases.py <source> <restored>` | `tables: source=69 restored=69; rows: source=14655 restored=14655`; `tables whose row count or content hash differ: none; sequences identical: True (68 sequences)` |
| `alembic current` / `alembic check` on the restored database | `0003_lockout_email_queue (head)` / no differences |
| API started on the restored database | sign-in succeeds; `{"total":240}` students |
| Restore again into the now non-empty database | refused, exit 1 |
| Restore a truncated archive | refused, exit 1 |
| Restore an archive whose checksum does not match | refused: `checksum mismatch` |
| SQLite: back up a **copy** of `acedra.db`, delete all students in the copy, restore | 0 students after the damage, 264 after the restore; restored file is byte-identical to the original |

The original `acedra.db` was not modified: its SHA-256 began `76ca21438b1fbb52` before and after.

## 7. Tenant isolation, permissions, authentication

`python scripts/verification/verify_isolation_and_roles.py` against the API on the seeded PostgreSQL database:
**46/46 checks passed**, exit 0.

* **Tenants.** Each university lists only its own students (REVA 240, Northfield 14). A REVA administrator gets
  404 for another university's student on four read routes, on a write, and when the id is passed as a query
  parameter; sees only `@reva.in` accounts; gets 404 for another university's user and alert. Knowledge-base
  documents and the audit log are per university.
* **Roles.** Faculty see 16 of 240 students, get 403 outside their sections and cannot edit a student; a mentor
  cannot edit a mentee; a student sees only themselves and is refused on six administrator routes, on creating
  rules and on inviting users; a placement officer is refused on individual risk records and interventions but
  keeps placement data; faculty cannot download an administrator's report (404); a university administrator
  cannot grant a platform role (422); a module that is not enabled is refused (403).
* **Platform boundary.** University administrators get 404 on platform routes; platform administrators get 403
  on university routes and cannot read students without a grant (403); another user's assistant conversation
  is invisible (404).
* **Authentication.** Rejected with 401: an edited payload with the original signature, an `alg=none` token, a
  token signed with another key, a refresh token used as an access token, and no token. Wrong password and
  unknown account give the same error and take the same time (257 ms and 258 ms).

The test suite covers the same ground with 165 tests on both databases.

**User interface.** The production build was served and every page was opened as administrator, faculty,
mentor, placement officer, student and platform staff with a scripted browser: 57 pages, no console errors, no
failed requests, no placeholder text; no errors in the API log.

## 8. Production environment review

Each of these was set on an otherwise valid production configuration and the entrypoint was run; every one
exited with status 1 **before** any migration ran (the database still had 0 tables):

| Setting | Message |
|---|---|
| no `SECRET_KEY` | `SECRET_KEY must be set to a random value of at least 32 characters.` |
| `EMAIL_PROVIDER=log` | `EMAIL_PROVIDER must be smtp in production: with 'log', invitations and password resets are stored on the server and never delivered.` |
| `SEED_DEMO_DATA=true` | `SEED_DEMO_DATA must be false in production: the sample universities use published demonstration passwords.` |
| `PUBLIC_APP_URL=http://localhost:5173` | `CORS_ORIGINS and PUBLIC_APP_URL must not point at localhost in production.` |
| `EMAIL_FROM` at the built-in `acedra.local` address | `EMAIL_FROM must be a real sender address on your own domain.` |
| `DATABASE_URL` with the development password | `DATABASE_URL still uses a development password.` |
| `CORS_ORIGINS=*` | `CORS_ORIGINS must list explicit origins in production.` |
| `ALLOW_INSECURE_DEV_SECRET=true` | `ALLOW_INSECURE_DEV_SECRET must not be set in production.` |

Running the seed directly in production prints `Refusing to load sample data: ENVIRONMENT=production.` The
production image sets `ENVIRONMENT=production` by default. `docker-compose.prod.yml` fixes `EMAIL_PROVIDER=smtp`
and `SEED_DEMO_DATA=false` and requires `SECRET_KEY`, `POSTGRES_PASSWORD`, `CORS_ORIGINS`, `PUBLIC_APP_URL`,
`EMAIL_FROM` and `SMTP_HOST`. The demonstration accounts are listed on the sign-in page only in development
builds. `backend/.env` (development values) is git-ignored, excluded by `.dockerignore`, and not in the release.

## Not executed

* `docker build` of either image, `docker compose up` of the production or development stack, and the container
  health checks. Reason: the base images could not be downloaded.
* Nginx itself: TLS termination, the HTTP → HTTPS redirect, the security headers and the reverse proxy.
  `docker/nginx.conf` passed a syntax parse only.
* The backup and restore commands for the compose stack (`docker compose exec db pg_dump …`). The scripts were
  tested directly against PostgreSQL instead.
* The GitHub Actions workflow and gitleaks. Nothing was pushed.
* Delivery to a real mail provider (a local SMTP server was used), a real language-model or embedding provider
  (`LLM_PROVIDER=none`, `EMBEDDING_PROVIDER=lexical`), and any load test.

## Remaining security limitations

* No external security review or penetration test.
* No multi-factor authentication or single sign-on.
* Access and refresh tokens are held in `sessionStorage`, not httpOnly cookies.
* Signing out ends every session of the account on every device.
* Account lockout can be used to keep a known account locked for 15 minutes at a time; a password reset unlocks it.
* The prompt-injection filter for the assistant is a short pattern list, not a security boundary; with a
  language model configured, student records are sent to that provider.
* Uploaded documents are not virus-scanned.
* No monitoring, alerting or log shipping; no automatic retention or deletion of personal data.
* Backups are not encrypted by the script; encrypt them where they are stored.
* The legal documents are drafts awaiting legal review.
* No automated dependency updates; the audits run in CI but someone has to act on them.

See `KNOWN_LIMITATIONS.md` for functional scope and technical debt.

## Re-running the verification

```bash
# production-mode API on an empty database (see the script's header for the preconditions)
pip install aiosmtpd && python scripts/verification/smtp_sink.py &
ACEDRA_MAIL_DIR=/tmp/acedra-mail python scripts/verification/verify_production_api.py

# isolation, roles and authentication against a seeded development-mode API on port 8000
python scripts/verification/verify_isolation_and_roles.py

# backup and restore
DATABASE_URL=postgresql://…/source ./database/backup_db.sh /tmp/backups
DATABASE_URL=postgresql://…/empty_target ./database/restore_db.sh /tmp/backups/acedra_pg_<timestamp>.sql.gz
python scripts/verification/compare_postgres_databases.py postgresql://…/source postgresql://…/empty_target
```

## Release contents

`./scripts/make_release.sh` builds `release/acedra-1.0.0-rc.1/` from the release commit. The script was
run and its output unpacked into an empty directory, where the backend tests passed (`165 passed`), `npm ci`
reported 0 vulnerabilities, the frontend built, and every file matched its checksum in the manifest. A second run
is refused because the release already exists, and a run with uncommitted changes is refused. Its `MANIFEST.txt`
lists every file with its SHA-256. Excluded: `.git`, databases, backups, recovery archives, caches,
`node_modules`, build output, `.env` files, TLS material, `.DS_Store`, and the v0.1 documentation archive.
