# Smart Campus Intelligence (RIO Prototype v0.1)
## AI-Powered Student Success & Institutional Intelligence Platform

![Build Status](https://img.shields.io/badge/status-active_development-emerald)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal)
![React](https://img.shields.io/badge/React-18-cyan)
![Tailwind](https://img.shields.io/badge/TailwindCSS-v3-indigo)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791)

---

## 1. Overview
Smart Campus Intelligence is an institutional platform designed to unify student academic tracking, faculty workload management, mentorship interventions, placement readiness, and executive governance into a single intelligence dashboard.

This repository contains **MODULE 0 — PROJECT FOUNDATION**: the complete monorepo, persistent relational database architecture, role-based access control (RBAC), and enterprise UI foundation.

---

## 2. Five Platform Roles & Demo Credentials

Pre-seeded accounts are provided for immediate evaluation. You can log in using these credentials or click the **1-Click Demo Login** preset buttons on the login screen.

| Role | Name & Title | Email | Password |
| :--- | :--- | :--- | :--- |
| **Student** | Alex Mercer (5th Sem CSE) | `student@smartcampus.edu` | `StudentPass123!` |
| **Faculty** | Dr. Elena Rostova (Professor) | `faculty@smartcampus.edu` | `FacultyPass123!` |
| **Mentor** | Prof. David K. Sterling (Lead Mentor) | `mentor@smartcampus.edu` | `MentorPass123!` |
| **Administrator / HOD**| Dr. Sarah Jenkins (HOD CSE) | `admin@smartcampus.edu` | `AdminPass123!` |
| **Placement Officer** | Marcus Vance (Corporate Relations) | `placement@smartcampus.edu` | `PlacementPass123!` |

---

## 3. Monorepo Directory Structure

```
RIO Prototype v0.1/
├── backend/                  # FastAPI Application, Services, Repositories, Alembic
│   ├── app/
│   │   ├── api/              # REST Endpoints (Auth, Users, Academics, Dashboards)
│   │   ├── core/             # Database connection, Config, Bcrypt Security
│   │   ├── models/           # SQLAlchemy 2.0 Entity Models
│   │   ├── repositories/     # Database Query Abstractions
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── services/         # Business logic & Dynamic metric computation
│   │   └── main.py           # Application entrypoint & Middleware
│   ├── alembic/              # Database schema migrations
│   ├── tests/                # Automated pytest suite
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React 18 + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── api/              # Typed REST client
│   │   ├── components/       # Layouts, Role Dashboards, User Management
│   │   ├── contexts/         # AuthContext & ThemeContext
│   │   └── types/            # TypeScript definitions
│   └── package.json
├── database/                 # Seeding scripts & vector extension SQL
│   ├── seeds/seed_data.py    # Database population script
│   └── init.sql              # pgvector initialization
├── datasets/                 # Institutional seed datasets (CSV/JSON)
├── docker/                   # Dockerfiles for Backend and Frontend
├── documentation/            # Architecture blueprints, ER diagrams & API specs
└── docker-compose.yml        # Docker composition for PostgreSQL, Backend, Frontend
```

---

## 4. Quickstart Guide

### Option A: Local Development (Instant)

#### 1. Backend Setup
```bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations and seed the database
alembic upgrade head
python ../database/seeds/seed_data.py

# Launch FastAPI development server
uvicorn app.main:app --reload --port 8000
```
- API is available at: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`

#### 2. Frontend Setup
```bash
# In a new terminal window:
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
- Open `http://localhost:5173` in your browser.

---

### Option B: Docker Compose (Full Container Stack)

To run the complete system with PostgreSQL 16 (`pgvector`), Backend, and Frontend:

```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- PostgreSQL with pgvector: `localhost:5432`

---

## 5. Verification & Testing

Execute the automated test suite to verify token issuance, password security, role permissions, and dynamic metric calculation:

```bash
cd backend
.venv/bin/pytest -v
```

All 6 test suites verify:
1. Health check availability (`/health`).
2. Successful student authentication and token receipt.
3. Password rejection for invalid credentials.
4. Nonexistent user handling without timing leaks.
5. Role-based access control (Student blocked from `/users/`, Admin allowed).
6. Real-time dynamic metric generation across all 5 user roles.

---

## 6. Proceeding to Module 1
With Module 0 complete:
- The persistent relational schema is migrated and verified.
- The 5 user roles and navigation structures are functional.
- The platform is primed for **Module 1 (Curriculum Intelligence & AI Syllabus Analysis)** to introduce vector embeddings into `pgvector` and course graph analytics.
