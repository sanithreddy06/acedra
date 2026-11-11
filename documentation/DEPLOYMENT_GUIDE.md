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

1. `cp .env.production.example .env.production` and fill in every value. The API refuses to start with a
   default or short `SECRET_KEY`, wildcard CORS, a SQLite URL or a `PUBLIC_APP_URL` that is not `https://`.
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

> The production images have been reviewed but **not yet built or run** in this repository's history (no Docker
> was available where the changes were made). The CI workflow builds both images on every push; treat its first
> green run, followed by a smoke test of the stack with a self-signed certificate, as the real verification.

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

```bash
DATABASE_URL=postgresql://user:pass@host:5432/acedra ./database/backup_db.sh ./database/backups
DATABASE_URL=postgresql://user:pass@host:5432/acedra ./database/restore_db.sh ./database/backups/<file>.sql.gz
```

For SQLite the scripts copy `acedra.db`. Schedule backups daily and test a restore before going live.

## 6. Health

* `GET /health`: process is up
* `GET /ready`: database reachable; reports the configured AI and email providers

## 7. Tests

```bash
cd backend && python -m pytest -q --ignore=tests/benchmark_performance.py
# against PostgreSQL:
TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/acedra_test python -m pytest -q --ignore=tests/benchmark_performance.py
cd frontend && npm run lint && npm run typecheck && npm run build
```

`.github/workflows/ci.yml` runs all of this on every push and pull request: Ruff, `alembic check`, the tests on
SQLite and on PostgreSQL 16, the frontend lint, typecheck and build, and a build of both production images.

Each run creates and seeds its own isolated database.
