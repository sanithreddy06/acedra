# Deployment guide

## 1. Local development (no Docker)

Requirements: Python 3.10+, Node 18+.

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt          # runtime + pytest + ruff
cp .env.example .env                      # SQLite by default
cd .. && python database/seeds/seed_all.py   # creates acedra.db with synthetic tenants (destructive reset)
cd backend && uvicorn app.main:app --reload --port 8000

# frontend (new terminal)
cd frontend
npm install
npm run dev                                # http://localhost:5173 (proxies /api to :8000)
```

API docs are at http://localhost:8000/docs (disabled in production). In development, emails are not sent. Super
administrators can read invitation and reset links in **Platform → Email outbox**.

## 2. Docker (local stack with PostgreSQL)

```bash
docker compose up --build
# frontend http://localhost:3000 · API http://localhost:8000
```

The backend entrypoint runs `alembic upgrade head`. Then, because `SEED_DEMO_DATA=true`, it loads the
synthetic tenants **only if the database has no universities**. Set `SEED_DEMO_DATA=false` to start empty.

## 3. Production

1. `cp .env.production.example .env.production` and fill in every value. In production the API checks its
   configuration before it touches the database and **refuses to start** with any of the following, so a
   development setting cannot reach a live system:

   | Refused in production | Why |
   |---|---|
   | `SECRET_KEY` missing, shorter than 32 characters, the built-in development value, or trivially repetitive | Tokens could be forged |
   | `DATABASE_URL` pointing at SQLite, or containing a development password | Not a production database |
   | `CORS_ORIGINS` of `*`, or any origin or `PUBLIC_APP_URL` on `localhost` / `127.0.0.1` | Development origins |
   | `PUBLIC_APP_URL` not starting with `https://` | Invitation and reset links would be sent over plain HTTP |
   | `EMAIL_PROVIDER` other than `smtp`, or no `SMTP_HOST` | With `log`, invitations and resets are never delivered |
   | `EMAIL_FROM` left at the built-in `acedra.local` address | Mail would be rejected or misattributed |
   | `SEED_DEMO_DATA=true` | The sample universities use published demonstration passwords |
   | `ALLOW_INSECURE_DEV_SECRET=true` | Development-only switch |

   The seed script itself also refuses to run with `ENVIRONMENT=production`. The API documentation pages
   (`/docs`, `/redoc`) and the OpenAPI schema are not served in production. Use a database password made of
   letters and digits: the compose file places it inside a connection URL.
2. **TLS certificate.** Nginx terminates HTTPS itself and will not start without a certificate. Put
   `fullchain.pem` and `privkey.pem` for your hostname in `TLS_CERT_DIR` (default `./docker/certs`, git-ignored):
   * from your certificate authority, or
   * from Let's Encrypt: port 80 serves `/.well-known/acme-challenge/` from `ACME_WEBROOT` (default
     `./docker/acme`), so `certbot certonly --webroot -w ./docker/acme -d your.host` works once the stack is up
     with a temporary certificate; copy the issued files into `TLS_CERT_DIR` and run
     `docker compose -f docker-compose.prod.yml exec frontend nginx -s reload`. Renew the same way.
   * for a local smoke test only: `./docker/make-selfsigned-cert.sh localhost`.
   If a load balancer already terminates TLS in front of this stack, it must forward to port 443 and you
   should restrict who can reach the stack directly: the API trusts the address Nginx reports.
3. `docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build`
4. Migrations run on start. Demo data is never loaded in production (`SEED_DEMO_DATA=false`). The stack also
   starts Redis, which holds the rate-limit counters shared by the API workers.
5. Create the first ACEDRA super administrator once. There is no sign-up, by design:

```bash
docker compose -f docker-compose.prod.yml exec backend python - <<'PY'
from app.core.database import SessionLocal
from app.core.tenancy import TenantScope, set_session_scope
from app.models import EmployeeProfile, Role
from app.services.invitation_service import InvitationService
db = SessionLocal(); set_session_scope(db, TenantScope(bypass=True))
for n, d in [("platform_admin", "ACEDRA Super Administrator"), ("platform_employee", "ACEDRA Employee"),
             ("student", "Student"), ("faculty", "Faculty"), ("mentor", "Mentor"),
             ("admin", "University Administrator"), ("placement_officer", "Placement Officer")]:
    db.query(Role).filter_by(name=n).first() or db.add(Role(name=n, display_name=d, permissions=[]))
db.flush()
u, _, _ = InvitationService(db).create_user_with_invitation(
    email="you@your-company.example", full_name="Your Name", role="platform_admin", university=None, invited_by=None)
db.add(EmployeeProfile(user_id=u.id, employee_code="ACD-0001")); db.commit()
print("Invitation emailed to", u.email)
PY
```

6. Before building the frontend image, create `frontend/.env.production` from `frontend/.env.example` with the
   confirmed operator name, address and contact emails (they are compiled into the public site; unset values show
   as "[To be configured: …]"). Keep `LEGAL_ACCEPTANCE_ENFORCED=true` in `.env.production`.
7. Have the bundled legal drafts reviewed, then publish approved versions from **Platform → Legal documents**
   (draft → approve with a recorded note → publish with an effective date). Users are asked to accept new Terms and
   Privacy versions the next time they use ACEDRA.
8. Set `PUBLIC_APP_URL` to the public HTTPS origin so invitation and reset links are correct.

> **Image build status.** The two production images and the Nginx configuration have **not** been built or run:
> the verification environment could not download base images. Everything the images contain was exercised
> outside Docker instead (the pinned requirements on Python 3.12, the entrypoint as a non-root user, Gunicorn
> with four workers, PostgreSQL 16, Redis, SMTP delivery); see `documentation/RELEASE_VERIFICATION.md`. Before
> going live, run the stack once with a self-signed certificate and confirm that both containers become healthy,
> that `https://<host>/` loads and `http://` redirects, and that `https://<host>/api/health` answers.

### Optional providers

| Setting | Values | Notes |
|---|---|---|
| `LLM_PROVIDER` | `none`, `openai_compatible`, `anthropic`, `ollama` | With `none`, answers are extractive and labelled as offline |
| `EMBEDDING_PROVIDER` | `lexical`, `openai_compatible`, `ollama` | Reindex documents after changing |
| `EMAIL_PROVIDER` | `log`, `smtp` | `log` never sends mail |
| `LEGAL_ACCEPTANCE_ENFORCED` | `false`, `true` | `true`: workspace API requests return 428 until the current Terms and Privacy versions are accepted |
| `CONTACT_RATE_LIMIT` | e.g. `5/hour` | Public contact form, per client address |
| `RATE_LIMIT_STORAGE_URI` | `memory://`, `redis://host:6379/0` | Must be a shared store when more than one worker or instance runs (the production compose file sets Redis) |
| `LOGIN_MAX_FAILED_ATTEMPTS`, `LOGIN_LOCKOUT_MINUTES` | default `5`, `15` | Consecutive failed sign-ins before an account is locked, and for how long. A password reset unlocks it |
| `EMAIL_MAX_ATTEMPTS`, `EMAIL_RETRY_INTERVAL_SECONDS` | default `5`, `60` | Retry policy for queued email |

## 4. Database migrations

```bash
cd backend
alembic upgrade head        # apply
alembic check               # verify models and migrations match
alembic revision --autogenerate -m "describe change"   # after changing models
```

| Revision | Adds |
|---|---|
| `0001_rio_baseline` | The multi-tenant schema |
| `0002_legal_contact` | `legal_documents`, `legal_acceptances`, `contact_messages` (new tables only; no existing data is changed) |
| `0003_lockout_email_queue` | `users.failed_login_count`, `users.locked_until`; `email_messages.attempts`, `last_attempt_at`, `sent_at` (new columns with defaults; no existing data is changed) |

A local development database created by the app itself (`AUTO_CREATE_SCHEMA=true`, the default outside
production) has no `alembic_version` table. Starting the API adds new tables and any missing nullable or
defaulted columns to it automatically (`core/database.py::add_missing_columns`, development only); to
manage it with Alembic instead, run `alembic stamp 0001_rio_baseline` once and then `alembic upgrade head`. Both
paths were checked on a copy of a seeded development database: existing rows were unchanged and `alembic check`
reported no differences.

`alembic upgrade head` applies `0002` to an existing database without resetting it; `alembic downgrade 0001_rio_baseline`
drops only the three new tables. The first request that needs a legal document publishes the bundled drafts as
version `0.1-draft`.

`0001_rio_baseline` replaces the prototype's migrations, which were incomplete (modules 1 and 6 created no
tables). Existing v0.1 databases are not upgraded in place: re-seed for the prototype, or export and import real
data through the import centre.

## 5. Backup and restore

Both scripts need the PostgreSQL client tools (`pg_dump`, `psql`) of the same major version as the server (16).

**Back up**

```bash
DATABASE_URL=postgresql://user:pass@host:5432/acedra ./database/backup_db.sh /secure/backups
```

This writes `acedra_pg_<timestamp>.sql.gz` (a plain SQL dump without ownership or privilege statements, readable
only by its owner), verifies that the archive can be read back, records its SHA-256 in a `.sha256` file beside
it, and removes ACEDRA backups in that directory older than `BACKUP_RETENTION_DAYS` (default 14). If `pg_dump`
fails, nothing is written and the script exits with an error.

With the production compose stack the database publishes no port, so run the dump inside the database container
and compress it on the host:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T db \
  pg_dump --no-owner --no-privileges -U acedra acedra | gzip -9 > /secure/backups/acedra_pg_$(date +%Y%m%d_%H%M%S).sql.gz
```

Schedule it daily (cron or a systemd timer), copy the files off the server, and keep them encrypted: a backup
contains every student record.

**Restore** (always into a new, empty database first)

```bash
createdb -O acedra acedra_restored
DATABASE_URL=postgresql://user:pass@host:5432/acedra_restored ./database/restore_db.sh /secure/backups/acedra_pg_<timestamp>.sql.gz
```

The restore checks the archive and its checksum, refuses a target that already has tables (unless `--force`),
runs in a single transaction and stops at the first error, so a failed restore leaves the target unchanged.
Check the result (`alembic current` should report the head revision; sign in), then point `DATABASE_URL` at the
restored database and restart the API. Inside the compose stack:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production stop backend
docker compose -f docker-compose.prod.yml --env-file .env.production exec -T db createdb -U acedra acedra_restored
gunzip -c /secure/backups/acedra_pg_<timestamp>.sql.gz | docker compose -f docker-compose.prod.yml --env-file .env.production \
  exec -T db psql -U acedra -d acedra_restored --set ON_ERROR_STOP=1 --single-transaction
# then set POSTGRES_DB=acedra_restored in .env.production and start the backend again
```

`scripts/verification/compare_postgres_databases.py <source-url> <restored-url>` compares two databases table by
table (row counts and content hashes) and their sequences. A restore test with it is part of the release
verification (`documentation/RELEASE_VERIFICATION.md`). **Repeat a restore test on your own infrastructure
before going live, and at least quarterly.**

For SQLite (development only) the scripts copy `acedra.db` (or `$SQLITE_PATH`); a restore first keeps the
existing file as `acedra.db.before-restore-<timestamp>`.

## 6. Health

* `GET /health`: process is up
* `GET /ready`: database reachable; reports the configured AI and email providers

## 7. Tests and security checks

```bash
cd backend && python -m pytest -q --ignore=tests/benchmark_performance.py
# against PostgreSQL:
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/acedra_test python -m pytest -q --ignore=tests/benchmark_performance.py
cd frontend && npm run lint && npm run typecheck && npm run build

# dependency vulnerabilities
pip install pip-audit && pip-audit -r backend/requirements.txt
cd frontend && npm audit

# secrets: working tree against the reviewed baseline, then every commit in the history
pip install detect-secrets==1.5.0
git ls-files -z -- . ':!documentation/archive_v0.1' ':!frontend/package-lock.json' ':!frontend/src/types/openapi.ts' \
  | xargs -0 detect-secrets-hook --baseline .secrets.baseline
python scripts/scan_git_history.py
```

`.secrets.baseline` lists the known development placeholders (the built-in development secret, the published
demonstration passwords, example connection strings); each entry has been reviewed. A new finding fails the
check: remove the secret (and rotate it if it was ever real), or, for a new placeholder, regenerate the baseline
with `detect-secrets scan` using the same exclusions and review the difference.

`.github/workflows/ci.yml` runs all of this on every push and pull request: Ruff, `alembic check`, the tests on
SQLite and on PostgreSQL 16, the frontend lint, typecheck and build, `pip-audit`, `npm audit`, detect-secrets,
the history scanner, gitleaks, and a build of both production images.

## 8. Building a release

```bash
./scripts/make_release.sh            # version from backend/app/core/config.py
```

The script builds `release/acedra-<version>/` and `release/acedra-<version>.tar.gz` from the current commit. Only
tracked files are included, so no Git metadata, database, backup, recovery archive, cache, `.env` file or TLS
material can be in it; the v0.1 documentation archive is left out too. It refuses to run with uncommitted
changes, re-checks the output for forbidden files, and writes `MANIFEST.txt` with the SHA-256 of every file.

## 9. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Backend container exits at once with `Invalid ACEDRA configuration: …` | The message lists every refused setting (see the table in section 3). Fix `.env.production` and start again; nothing was changed in the database |
| `required variable … is missing a value` from `docker compose` | A mandatory value in `.env.production` is empty (`SECRET_KEY`, `POSTGRES_PASSWORD`, `CORS_ORIGINS`, `PUBLIC_APP_URL`, `EMAIL_FROM`, `SMTP_HOST`), or `--env-file .env.production` was left off the command |
| Frontend container restarts; log shows `cannot load certificate "/etc/nginx/certs/fullchain.pem"` | No certificate in `TLS_CERT_DIR`. Add `fullchain.pem` and `privkey.pem`, or run `./docker/make-selfsigned-cert.sh` for a smoke test |
| Backend unhealthy; log shows a database authentication or connection error | `POSTGRES_PASSWORD` differs from the one the database volume was first created with, or it contains characters that break the URL (`@ : / ? #`). Use letters and digits |
| Invitation or reset email never arrives | Platform → Email outbox shows each message as `queued`, `sent` or `failed` with the relay's error and the number of attempts. Failed messages are retried up to `EMAIL_MAX_ATTEMPTS`; fix the SMTP settings and they go out on the next pass |
| Sign-in answers 429 "Too many failed sign-in attempts" | The account is locked for `LOGIN_LOCKOUT_MINUTES` after `LOGIN_MAX_FAILED_ATTEMPTS` wrong passwords. Wait, or use "Forgot password": a reset unlocks it |
| Any request answers 429 with a rate-limit message | More than the allowed requests from one address (sign-in 20/minute, everything else 240/minute). If every user shares one limit, the API is not seeing real visitor addresses: it must be reached only through the bundled Nginx |
| API answers 428 after signing in | A newer Terms or Privacy version has been published and `LEGAL_ACCEPTANCE_ENFORCED=true`. The web app shows the acceptance screen; API clients call `GET /auth/legal-status` then `POST /auth/legal-acceptances` with the current version of **both** documents |
| 409 "This conflicts with an existing record" | A unique value is already in use (USN, employee ID, department or subject code, email) |
| `alembic check` reports differences after an upgrade | Run `alembic upgrade head`. A development database created by the app itself has no `alembic_version`; see section 4 |
| Sample data does not load in Docker | It loads only when `SEED_DEMO_DATA=true`, the environment is not production, and the database has no universities yet |
| Sign-in page shows no demo accounts | They are listed only in development builds (`npm run dev`) |
| Restore refuses with "the target database already has N table(s)" | By design. Restore into a new, empty database, or pass `--force` |

Each run creates and seeds its own isolated database.
