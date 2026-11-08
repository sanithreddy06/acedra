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
Smart Campus Intelligence is an institutional SaaS platform designed to unify student academic tracking, faculty workload management, mentorship interventions, placement readiness, and executive governance into a single intelligence dashboard.

This repository contains:
- **MODULE 0 — PROJECT FOUNDATION**: Monorepo structure, persistent relational database architecture, role-based access control (RBAC), and enterprise UI foundation.
- **MODULE 1 — STUDENT INTELLIGENCE & ANALYTICS**: Centralized 360-degree student dossiers, semester-wise academic records, dynamic attendance tracking, continuous internal assessments, verified skill matrix, portfolio & experience showcase, CSV/Excel batch ingestion engine, and role-scoped analytics.
- **MODULE 2 — AI-ASSISTED RISK IDENTIFICATION**: Configurable rule-based early-warning engine, non-punitive risk categorization, fact-grounded natural language explanations, mentor assignment workflows, audit trail history, and real-time in-app notifications.
- **MODULE 3 — PERSONALISED RECOMMENDATION ENGINE**: Transparent rule-based learning roadmap generator, 11 recommendation categories, approved resource catalogue, career goal skill gap analysis, Academic vs. Career segmented plans, progress tracking, 5-star student feedback ratings, and mentor coaching workflows.
- **MODULE 4 — SKILL GAP & PLACEMENT READINESS**: Weighted competency gap scoring against 7 canonical industry roles, explicit self-reported vs. verified evidence workflows (repositories, live URLs, credentials), advisory prototype non-guarantee disclaimers, campus recruitment drive management, multi-factor eligibility verification algorithms, and candidate pipeline tracking.

> [!NOTE]
> **Synthetic Demo Data Disclaimer**: All student academic, attendance, marks, skill, project, and certification profiles seeded in this prototype are **synthetic demo data** created for demonstration and testing purposes. They do not represent real-world student records or institutional data.

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

## 3. Implemented Modules

### Module 0: Project Foundation
- **Monorepo Architecture**: Clean separation between `frontend/`, `backend/`, `database/`, `datasets/`, `docker/`, and `documentation/`.
- **Role-Based Access Control**: Strict JWT token validation and role-scoped authorization for 5 distinct roles.
- **Relational Foundation**: Core schemas for users, roles, departments, faculty, mentors, and audit logs with Alembic migrations.
- **Enterprise Design System**: Modern Tailwind-styled interface with theme toggling (Light/Dark), responsive sidebars, breadcrumbs, and notification badges.

### Module 1: Student Intelligence & Analytics
- **360° Student Dossiers**: Deep profiles tracking personal information, SRN, admission batch, program, status, guardian details, and blood group.
- **Academic Progression**: Semester-wise SGPA and CGPA progression graphs with historical backlog tracking.
- **Calculated Attendance Intelligence**: Attendance percentages computed dynamically from raw class counts (`(attended / total) * 100`) rather than arbitrary percentages.
- **Continuous Internal Assessments (CIA)**: Assignment marks, quizzes, and internal exam scoring with subject benchmarks.
- **Structured Skill Taxonomy**: Technical skills (Languages, Frameworks, Databases, Cloud) and soft skills tagged with proficiency and verification flags (reusable by Module 4).
- **Portfolio & Experience**: Certifications, hackathon participations, industry internships, and academic projects with repository links.
- **Batch CSV & Excel Ingestion**: Full ETL upload center with template downloads, column mapping, duplicate USN/email detection, row-level validation errors, and audit history.
- **Faculty & Admin Analytics**: Faculty cohort comparison dashboards and Administrator institutional analytics with Recharts visualizations.
- **Synthetic Demo Population**: 30 synthetic student records (`1RV22SYN001`–`1RV22SYN030`) across 4 departments (CSE, AI & DS, ECE, MECH) with multi-semester records.

### Module 2: AI-Assisted Risk Identification & Early Warning
- **Configurable Policy Rules**: 9 canonical risk rules with dynamic thresholds for attendance (<65%, <75%), continuous internal assessments (<40%, <50%), SGPA decline drops (>=1.0), and active backlogs.
- **Decoupled Evaluation Engine**: Runs automatically on student record updates, on-demand via administrative reassessment, or scheduled batch jobs.
- **Duplicate Active Alert Prevention**: Updates observed metrics on existing active alerts instead of generating redundant alert records.
- **Non-Punitive Severity Categorization**: `CRITICAL`, `HIGH`, `MODERATE`, and `NORMAL` severities without labeling students as dropouts or failures.
- **Fact-Grounded AI Explanations**: Empathetic, objective natural language summaries generated strictly from verified database records.
- **Alert Workflow & Audit Log**: Transition alerts from `FLAGGED` → `ACKNOWLEDGED` → `UNDER_REVIEW` → `RESOLVED` with documented review notes, mentor assignments, and full immutable audit history.
- **In-App Notification Dispatch**: Automatically alerts assigned mentors, faculty, and department heads on critical/high-risk alerts.

### Module 3: Personalised Recommendation Engine
- **11 Recommendation Categories**: Complete coverage of Subject Improvement, Study Resources, Learning Courses, Programming Practice, Technical Certifications, Soft Skill Development, Exam Prep, Project Suggestions, Internship Prep, Placement Prep, and Hackathons.
- **Approved Resource Catalogue**: 11 administrator-curated verified items with validated links, difficulty tiers, prerequisites, and durations.
- **Transparent Rule-Based Grounding**: Suggestions strictly derive from verified weak subjects (<50%), skill gaps matched against career goals (Full Stack, AI/ML, Cloud, Data, Cyber), and pre-final/final year placement horizons (Semesters 5–8).
- **Dual Plan Architecture**: Automatically categorizes items into an **Academic Improvement Plan** and a **Career Development Plan**.
- **Lifecycle & Feedback Loop**: Full status state machine (`SUGGESTED` → `ACCEPTED` / `REJECTED` → `IN_PROGRESS` → `COMPLETED`) with progress tracking (0–100%) and 5-star ratings with qualitative feedback.
- **Mentor Collaboration**: Allows faculty and mentors to assign custom recommendations with personalized coaching guidance notes.

### Module 4: Skill Gap & Placement Readiness
- **Comprehensive Skill Taxonomy**: Categorized inventory covering Programming Languages, Frameworks, Databases, Cloud & DevOps, Data Science, AI/ML, Cybersecurity, and Soft Skills.
- **Verified vs. Self-Reported Evidence Dossier**: Multi-type proof submission (GitHub repository, live project deployment URL, certificate credentials) with administrative/faculty verification.
- **7 Canonical Career Roles**: Standardized benchmarks for Software Developer, Full Stack Developer, Data Analyst, Data Scientist, AI/ML Engineer, Cloud Engineer, and Cybersecurity Analyst.
- **Weighted Readiness Engine**: Deterministic calculation using skill importance weights (`CRITICAL`: 3.0, `CORE`: 2.0, `PREFERRED`: 1.0) and partial credit for below-proficiency proficiencies.
- **Four Readiness Tiers**: Transparent status classification (`READY` $\ge$ 85%, `NEAR_READY` 70–84%, `DEVELOPING` 50–69%, `EARLY_STAGE` < 50%) with mandatory skill compliance check.
- **Advisory Prototype Disclaimer**: Prominent non-guarantee notices communicating that scores are personal development indicators, not hiring guarantees.
- **Placement Officer Recruitment Console**: Job and internship drive creation with multi-criteria eligibility filtering (min CGPA, max backlogs, min attendance, eligible departments and semesters).
- **Application Pipeline Workflow**: End-to-end recruitment tracking (`APPLIED` → `SHORTLISTED` → `INTERVIEW_SCHEDULED` → `OFFERED` / `REJECTED`).
- **Student Placement Dossier Tab**: Direct integration into the student 360-degree modal and dedicated standalone hub.

---

## 4. Monorepo Directory Structure

```
RIO Prototype v0.1/
├── backend/                  # FastAPI Application, Services, Repositories, Alembic
│   ├── app/
│   │   ├── api/              # REST Endpoints (Auth, Users, Students, Imports, Risk, Recs, Placement)
│   │   ├── core/             # Database connection, Config, Bcrypt Security
│   │   ├── models/           # SQLAlchemy 2.0 Models (Academic, Profile, Risk, Recommendations, Placement)
│   │   ├── repositories/     # Database Query Abstractions
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── services/         # PlacementService, RecommendationService, RiskService, StudentService
│   │   └── main.py           # Application entrypoint & Middleware
│   ├── alembic/              # Database schema migrations
│   ├── tests/                # Automated pytest suite (34 unit and integration tests across 5 modules)
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React 18 + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── api/              # Typed REST client with Modules 0, 1, 2, 3 & 4 methods
│   │   ├── components/
│   │   │   ├── placement/    # PlacementReadinessDashboard, PlacementOfficerConsole, Modals
│   │   │   ├── recommendations/ # RecommendationHub, Modals, Feedbacks
│   │   │   ├── risk/         # RiskDashboard, AlertDetailModal, RiskRuleConfigModal
│   │   │   ├── analytics/    # FacultyCohortAnalytics, AdminAnalyticsView
│   │   │   ├── imports/      # DataImportCenter (CSV/Excel Ingestion)
│   │   │   ├── students/     # StudentDirectory, StudentProfileModal, StudentFormModal
│   │   │   └── layout/       # AppLayout, Sidebar, TopNavbar (Role-Based Views)
│   │   ├── contexts/         # AuthContext & ThemeContext
│   │   └── types/            # TypeScript definitions
│   └── package.json
├── database/                 # Seeding scripts & vector extension SQL
│   ├── seeds/
│   │   ├── seed_data.py      # Base Module 0 seed script
│   │   ├── seed_module1.py   # Module 1 synthetic data generation (30 students)
│   │   ├── seed_module2.py   # Module 2 canonical rules & evaluation state
│   │   ├── seed_module3.py   # Module 3 recommendation catalogue & demo goals
│   │   └── seed_module4.py   # Module 4 career roles, skills, corporate drives & applications
│   └── init.sql              # pgvector initialization
├── datasets/                 # Institutional seed datasets & import templates
├── docker/                   # Dockerfiles for Backend and Frontend
├── documentation/            # Architecture blueprints, ER diagrams & API specs
│   ├── MODULE_1_STUDENT_INTELLIGENCE.md
│   ├── MODULE_2_RISK_IDENTIFICATION.md
│   ├── MODULE_3_RECOMMENDATIONS.md
│   ├── MODULE_4_SKILL_GAP_PLACEMENT.md
│   ├── ER_DIAGRAM.md
│   └── screenshots/          # 23 High-resolution UI captures (01–23)
└── docker-compose.yml        # Docker composition for PostgreSQL, Backend, Frontend
├── frontend/                 # React 18 + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── api/              # Typed REST client with Module 0, 1 & 2 methods
│   │   ├── components/
│   │   │   ├── risk/         # RiskDashboard, AlertDetailModal, RiskRuleConfigModal
│   │   │   ├── analytics/    # FacultyCohortAnalytics, AdminAnalyticsView
│   │   │   ├── imports/      # DataImportCenter (CSV/Excel Ingestion)
│   │   │   ├── students/     # StudentDirectory, StudentProfileModal, StudentFormModal
│   │   │   └── layout/       # AppLayout, Sidebar, TopNavbar (Real In-App Notifications)
│   │   ├── contexts/         # AuthContext & ThemeContext
│   │   └── types/            # TypeScript definitions
│   └── package.json
├── database/                 # Seeding scripts & vector extension SQL
│   ├── seeds/
│   │   ├── seed_data.py      # Base Module 0 seed script
│   │   ├── seed_module1.py   # Module 1 synthetic data generation (30 students)
│   │   └── seed_module2.py   # Module 2 canonical rules & evaluation state
│   └── init.sql              # pgvector initialization
├── datasets/                 # Institutional seed datasets & import templates
├── docker/                   # Dockerfiles for Backend and Frontend
├── documentation/            # Architecture blueprints, ER diagrams & API specs
│   ├── MODULE_1_STUDENT_INTELLIGENCE.md
│   ├── MODULE_2_RISK_IDENTIFICATION.md
│   ├── ER_DIAGRAM.md
│   └── screenshots/          # 15 High-resolution UI captures
└── docker-compose.yml        # Docker composition for PostgreSQL, Backend, Frontend
```

---

## 5. Quickstart Guide

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

# Run migrations and seed data
alembic upgrade head
python ../database/seeds/seed_data.py
python ../database/seeds/seed_module1.py
python ../database/seeds/seed_module2.py

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

## 6. Verification & Automated Testing

Execute the comprehensive automated test suite covering authentication, RBAC, calculated attendance properties, student data isolation, CSV/Excel import validation, boundary condition testing, SGPA decline detection, duplicate alert prevention, and alert resolution workflows:

```bash
cd backend
.venv/bin/pytest -v
```

### Passing Test Suites (27/27 Passed):
1. `test_health_check`: Service availability (`/health`).
2. `test_login_success_student`: Successful student authentication & JWT token issuance.
3. `test_login_invalid_password`: Password rejection for invalid credentials.
4. `test_login_nonexistent_user`: Nonexistent user handling without timing leaks.
5. `test_user_management_role_protection`: Student blocked from `/users/`, Admin authorized.
6. `test_dynamic_metrics_generation`: Real-time dynamic metric generation across all 5 user roles.
7. `test_rules_retrieval_and_admin_crud`: Configurable rule retrieval and admin CRUD workflows.
8. `test_attendance_boundary_conditions`: Strict boundary testing (74% triggers alert, 75% exactly does not).
9. `test_declining_performance_trigger`: Triggers alert when consecutive semester SGPA drops >= 1.0.
10. `test_healthy_no_trigger_student`: High-performing student with 95% attendance generates zero alerts.
11. `test_duplicate_alert_prevention`: Evaluating low-attendance student multiple times updates in-place without duplicate alerts.
12. `test_alert_lifecycle_workflow`: Acknowledge, add note, and resolve with audit history; verifies unauthorized rejection.
13. `test_student_risk_isolation`: Student restricted to viewing their own risk profile.
14. `test_student_list_admin_and_student_isolation`: Student listing permissions and isolation.
15. `test_student_profile_security_isolation`: Cross-student profile access protection.
16. `test_admin_create_and_edit_student`: Admin full CRUD workflow for student profiles.
17. `test_calculated_attendance_and_analytics_integrity`: Verifies dynamic attendance percentage and SGPA trends.
18. `test_student_skill_persistence`: Adding skills and verification persistence.
19. `test_csv_import_preview_validation`: Validation errors on missing required fields during import preview.
20. `test_faculty_and_admin_analytics_endpoints`: Faculty cohort and admin institutional analytics access.
21. `test_weak_subject_performance_recommendation`: Weak subject marks (<50%) trigger remedial course and exam prep recommendations.
22. `test_missing_technical_skills_recommendation`: Career goal missing skill gap analysis triggers approved courses and certifications.
23. `test_career_goal_learning_path`: Segmented Academic Improvement and Career Development plans.
24. `test_healthy_profile_recommendations`: High-performing students receive advanced capstones and hackathons without remedial courses.
25. `test_recommendation_lifecycle_and_feedback`: Status machine (`SUGGESTED` → `ACCEPTED` → `IN_PROGRESS` → `COMPLETED`) and 5-star feedback logging.
26. `test_mentor_suggest_and_guidance`: Mentor custom resource recommendation with coaching guidance.
27. `test_unauthorized_access_protection`: Multi-tenant security isolation preventing students from accessing other students' learning plans.

---

## 7. UI Screenshot Gallery

High-resolution captures of the implemented interfaces are preserved in `documentation/screenshots/`:

| Screenshot | Description |
| :--- | :--- |
| `01_login_screen.png` | Role-based authentication portal with 1-click demo presets. |
| `02_student_directory.png` | Directory table with department/semester filters and search. |
| `03_student_profile_overview.png` | 360° Student Dossier modal header with KPI metrics and quick actions. |
| `04_student_academic_progression.png`| Semester-wise SGPA Recharts line chart and backlog tracker. |
| `05_student_attendance_intelligence.png` | Calculated attendance status with subject threshold progress bars. |
| `06_student_assessments.png` | Continuous internal evaluation marks and component breakdowns. |
| `07_student_skill_matrix.png` | Categorized technical and soft skills with inline skill adder. |
| `08_student_portfolio_experience.png`| Certifications, hackathons, and internship project cards. |
| `09_data_import_center.png` | CSV/Excel upload zone with live validation preview table. |
| `10_admin_institutional_analytics.png`| Executive analytics with department CGPA comparisons. |
| `11_faculty_cohort_analytics.png` | Faculty cohort benchmark comparison charts and student roster. |
| `12_risk_early_warning_dashboard.png` | Executive early-warning center with severity donut, department bar charts, and alerts roster. |
| `13_risk_alert_detail_modal.png` | Comprehensive alert detail drawer with quantitative evidence, AI explanation, and action timeline. |
| `14_risk_policy_rule_configuration.png`| Administrator rule configuration modal for dynamic threshold tuning and active toggling. |
| `15_student_dossier_early_warning_tab.png`| 360° Student dossier modal featuring the dedicated Early-Warning Alerts tab. |
| `16_recommendations_dashboard.png` | Personalized Recommendation Engine dashboard with Academic & Career split plans, KPIs, and career target banner. |
| `17_recommendation_detail_modal.png` | Grounded recommendation detail modal with gap analysis, progress tracking slider, and 5-star feedback review. |
| `18_career_goals_interests_modal.png` | Student career goal selection modal (AI/ML Engineer, Full Stack, Cloud) and interest tag manager. |
| `19_catalogue_browser_modal.png` | Approved Resource Catalogue browser modal with category filters, difficulty tags, and verified external links. |

---

## 8. Proceeding to Module 4

With Module 0, Module 1, Module 2, and Module 3 completed and verified against all automated acceptance tests:
- The persistent relational schema and Alembic migrations are synchronized (`e33f06c9e0a9`).
- Grounded recommendation catalogues, learning paths, progress milestones, and feedback loops are active and audited.
- The platform is primed for **Module 4 — Placement Readiness & Skill Verification**, which will build upon student skill matrices, career paths, and recommendation progress to calculate placement readiness scores and corporate drive eligibility.
