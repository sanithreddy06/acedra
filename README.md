# ACEDRA

**University Intelligence. Connected.**

ACEDRA is a configurable university intelligence platform that connects student academic analytics, early-warning
systems, personalised recommendations, skill-gap analysis, AI assistance and intervention tracking into one
institutional workspace.

One shared application serves many universities, and each has its own isolated, configurable workspace. Inside a workspace, five roles (student, faculty, mentor, university
administrator, placement officer) each get a dedicated experience across six connected modules:

1. **Student intelligence & analytics**: records, attendance, assessments, trends, CSV/Excel import with column mapping
2. **Early-warning risk identification**: configurable, explainable rules (no predictive-model claims)
3. **Personalised recommendations**: suggestions that state why, what gap, expected outcome and time, with progress and feedback
4. **Skill gap & placement readiness**: explainable readiness, eligibility-checked opportunities and applications
5. **AI assistant**: university mode (cited documents) and personal mode (authorised records only)
6. **Dashboards & interventions**: mentor cases, follow-ups, notes, outcomes, notifications and reports

The ACEDRA team runs a separate **platform workspace** for enquiries, onboarding, tenants, the dedicated employee
assigned to each university, and audited student-data access grants. A public website introduces ACEDRA and
collects institutional enquiries. There is no public sign-up.

> All bundled data is **generated sample data**. The REVA University workspace is a demonstration client: its people,
> records and policy documents were written for this prototype, are not real REVA data, and imply no partnership.

## Quick start

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && cp .env.example .env
cd .. && python database/seeds/seed_all.py        # resets acedra.db and loads 3 synthetic universities
cd backend && uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend && npm install && npm run dev          # open http://localhost:5173
```

Or with Docker (PostgreSQL included): `docker compose up --build`, then open http://localhost:3000.

## Demo accounts

| Workspace | Email | Password |
|---|---|---|
| ACEDRA super administrator | superadmin@acedra.example | PlatformPass123! |
| ACEDRA employee (assigned to REVA and Deccan Tech) | arjun.rao@acedra.example | PlatformPass123! |
| ACEDRA employee (coordination only) | vikram.nair@acedra.example | PlatformPass123! |
| REVA University · administrator (Dr. Anitha Rao) | anitha.rao@reva.in | AdminPass123! |
| REVA University · faculty (Dr. Kavya Menon) | kavya.menon@reva.in | FacultyPass123! |
| REVA University · mentor (Prof. Suresh Hegde) | suresh.hegde@reva.in | MentorPass123! |
| REVA University · placement officer (Rahul Deshpande) | rahul.deshpande@reva.in | PlacementPass123! |
| REVA University · student (Aarav Sharma) | aarav.sharma@reva.in | StudentPass123! |
| Northfield University (80% attendance rule, terms) | admin@ · faculty@ · mentor@ · placement@ · student@northfield.example | AdminPass123! · FacultyPass123! · MentorPass123! · PlacementPass123! · StudentPass123! |
| Deccan Institute of Technology (3 modules enabled) | same pattern @deccan-tech.example | same passwords |

Every REVA account uses a `firstname.lastname@reva.in` address; other staff and students share the password of
their role. The sign-in page lists these under "Show demo accounts" in development builds only. Email is not sent
in development (`EMAIL_PROVIDER=log`), so nothing is ever delivered to a real `reva.in` mailbox.

## Repository

```
acedra/
├── backend/          FastAPI · SQLAlchemy · Alembic
│   ├── app/          api/ · core/ (tenancy.py, access.py, config.py) · models/ · schemas/ · services/ · repositories/
│   │                 legal_content/ (bundled draft Terms, Privacy and Cookie policies)
│   ├── alembic/      migrations (0001 baseline, 0002 legal documents and contact messages)
│   ├── scripts/      export_openapi.py (feeds the frontend type generator)
│   └── tests/        isolation, roles, workflows, business rules, response privacy, assistant grounding
├── frontend/         React · TypeScript · Vite · Tailwind · Recharts · Lucide
│   ├── public/       favicon, touch icon, share image
│   └── src/          types/ · lib/ (incl. consent, site) · components/ (brand, ui, shell, access, charts, chat, legal) · pages/
├── database/         seeds/ (synthetic tenants, demo-data rebrand), backups/, backup and restore scripts
├── datasets/         sample CSV/JSON files for trying the import centre
├── docker/           Dockerfiles, entrypoint (migrate → optional seed), nginx
├── documentation/    ARCHITECTURE · SECURITY_AND_RBAC · DEPLOYMENT_GUIDE · KNOWN_LIMITATIONS · archive_v0.1/
├── docker-compose.yml · docker-compose.prod.yml
└── .env.example · .env.production.example
```

## Tests and checks

```bash
# backend (from backend/)
python -m pytest -q --ignore=tests/benchmark_performance.py   # tests
ruff check .                                                  # lint (config in backend/ruff.toml)

# frontend (from frontend/)
npm run typecheck      # TypeScript
npm run lint           # ESLint
npm run build          # production build
npm run gen:api        # regenerate src/types/openapi.ts after changing backend schemas (backend venv active)
```

The backend suite covers cross-tenant attacks, role escalation, scope checks for every role, the enquiry →
activation workflow, invitations, password reset, token revocation, assistant grounding, the risk, readiness and
recommendation rules, and checks that no response exposes internal fields. It runs on SQLite and PostgreSQL 16.

See `documentation/ARCHITECTURE.md` for how the code is organised (request layers, module map, conventions).

## Public website and legal pages

Public routes: `/`, `/about`, `/solutions`, `/security`, `/faq`, `/contact`, `/enquire`, `/accessibility` and
`/legal/terms|privacy|cookies` (with version history). There is no public registration and no public chatbot.
Legal links appear in the public footer, on sign-in and invitation pages and at the foot of every workspace.
Users accept the current Terms and Privacy versions when activating an invitation, or when prompted after signing
in; each acceptance stores user, university, document, version, context and time. ACEDRA super administrators
manage versions under **Platform → Legal documents**; the website's contact messages arrive under
**Platform → Contact messages**. The bundled legal text is a draft for legal review.

## Upgrading a database seeded before the rename

Databases seeded while the product was called RIO keep working. To update the synthetic demo logins
(`@rio-platform.example` → `@acedra.example`) and demo codes without touching anything else:

```bash
python database/seeds/rebrand_demo_data.py           # dry run
python database/seeds/rebrand_demo_data.py --apply
```

## Name history

ACEDRA began as the "Smart Campus Intelligence" prototype (v0.1) and was developed as "RIO" before being renamed.
A few internal identifiers keep the old name for compatibility (see `documentation/KNOWN_LIMITATIONS.md`).

## Status

**Prototype-complete. Not production- or institution-ready.** See `documentation/KNOWN_LIMITATIONS.md`.
