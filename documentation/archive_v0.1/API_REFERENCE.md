> **Archived — prototype v0.1 (historical).** This document describes the retired single-institution prototype and is not current ACEDRA documentation. Current documentation is one folder up, in `documentation/`.

# Smart Campus Intelligence — Complete REST API Reference

Base URL: `/api/v1`

---

## 1. Authentication & Session Security

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/auth/login` | Public | Authenticates credentials and returns JWT access & refresh tokens |
| `POST` | `/auth/refresh` | Public | Refreshes expired access token using valid refresh token |
| `GET` | `/auth/me` | Authenticated | Returns current authenticated user profile and student metadata |
| `POST` | `/auth/logout` | Authenticated | Invalidates current session and issues logout audit event |
| `POST` | `/auth/password-reset-request` | Public | Issues password reset token to registered email |
| `POST` | `/auth/password-reset-confirm` | Public | Sets new password using verified reset token |

---

## 2. Health & Readiness Probes

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Service heartbeat (returns service status, version, environment) |
| `GET` | `/ready` | Public | Database readiness probe (verifies active SQL connection) |

---

## 3. Student Intelligence & 360° Profile (Module 1)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/students/` | Faculty, Mentor, Admin | Search and filter students by department, semester, section |
| `POST` | `/students/` | Admin | Create new student record with user account |
| `GET` | `/students/{id}` | Self, Faculty, Mentor, Admin | Retrieve complete student 360° dossier |
| `PUT` | `/students/{id}` | Admin | Update student demographic and administrative details |
| `GET` | `/students/{id}/analytics` | Self, Faculty, Mentor, Admin | Longitudinal CGPA, SGPA, attendance, and backlog analytics |
| `POST` | `/imports/preview` | Admin | Validate uploaded CSV student batch import without committing |
| `POST` | `/imports/execute` | Admin | Execute validated CSV import job |

---

## 4. Risk Early-Warning Intelligence (Module 2)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/risk/rules` | Admin, Faculty | List configurable risk early-warning rules |
| `POST` | `/risk/rules` | Admin | Create or update configurable risk policy threshold |
| `POST` | `/risk/evaluate` | Admin, Faculty | Trigger deterministic risk evaluation across student cohort |
| `GET` | `/risk/alerts` | Faculty, Mentor, Admin | List active risk alerts with severity filters |
| `GET` | `/risk/alerts/{id}` | Faculty, Mentor, Admin | Get detailed explanation and observed metric breakdown |
| `POST` | `/risk/alerts/{id}/acknowledge`| Mentor, Faculty | Acknowledge alert and mark under review |
| `POST` | `/risk/alerts/{id}/resolve`| Mentor, Faculty, Admin | Resolve alert with resolution audit notes |
| `GET` | `/risk/students/{id}` | Self, Faculty, Mentor, Admin | View risk evaluation history for specific student |

---

## 5. Personalized Recommendation Engine (Module 3)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/recommendations/catalogue` | All Authenticated | Browse curated roadmap items and learning resources |
| `POST` | `/recommendations/generate/{student_id}` | Admin, Mentor | Synthesize personalized recommendations based on gaps |
| `GET` | `/recommendations/` | Authenticated Student | View active personalized recommendations for self |
| `POST` | `/recommendations/{id}/accept` | Authenticated Student | Accept recommendation and add to personal learning plan |
| `POST` | `/recommendations/{id}/progress` | Authenticated Student | Update completion percentage for accepted item |
| `POST` | `/recommendations/{id}/feedback` | Authenticated Student | Submit rating and feedback on recommendation utility |

---

## 6. Skill Gap & Placement Readiness (Module 4)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/placement/skills` | All Authenticated | Search and list institutional skill taxonomy |
| `GET` | `/placement/roles` | All Authenticated | List career roles with required skill benchmarks |
| `GET` | `/placement/readiness/{student_id}` | Self, Placement, Admin | Compute readiness score and skill gap breakdown against role |
| `GET` | `/placement/students/{student_id}/skills` | Self, Faculty, Placement | View student skill inventory with verified status |
| `POST` | `/placement/students/{student_id}/skills` | Self | Add self-reported skill or update proficiency level |
| `POST` | `/placement/students/{student_id}/evidence` | Self | Submit project repo, certificate or link evidence |
| `POST` | `/placement/evidence/{id}/verify` | Faculty, Placement | Verify or reject submitted student skill evidence |
| `GET` | `/placement/opportunities` | All Authenticated | List active corporate recruitment drives and internships |

---

## 7. Conversational AI Assistant & RAG Grounding (Module 5)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/ai/conversations` | Public / Authenticated | Create new AI conversation thread (Mode A or Mode B) |
| `GET` | `/ai/conversations` | Authenticated | List user conversational history |
| `POST` | `/ai/conversations/{id}/messages` | Public / Authenticated | Send message, trigger RAG grounding and generate answer |
| `GET` | `/ai/conversations/{id}/messages/stream`| Public / Authenticated | Server-Sent Events (SSE) token streaming endpoint |
| `POST` | `/ai/documents/text` | Admin | Ingest and chunk text regulations into vector store |
| `POST` | `/ai/documents/upload` | Admin | Upload institutional PDF/DOCX handbook (15MB limit) |
| `POST` | `/ai/rag/search` | Authenticated | Semantic vector search for handbook regulation snippets |

---

## 8. Role-Based Dashboards & Interventions (Module 6)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/dashboards/student` | Student | Summary metrics, attendance, CGPA, roadmap, and AI summary |
| `GET` | `/dashboards/faculty` | Faculty | Assigned cohort analytics, grade distribution, active alerts |
| `GET` | `/dashboards/mentor` | Mentor | Mentee caseload, pending follow-ups, development progress |
| `GET` | `/dashboards/placement`| Placement Officer | Institutional placement readiness, hiring drives, gap stats |
| `GET` | `/dashboards/admin` | Admin | Institutional executive intelligence, retention, department KPIs |
| `GET` | `/interventions` | Mentor, Faculty, Admin | Filter and list student support interventions |
| `POST` | `/interventions` | Mentor, Faculty, Admin | Create support action plan and assign mentor |
| `POST` | `/interventions/{id}/followups`| Mentor, Faculty | Schedule follow-up milestone for intervention |
| `PATCH` | `/interventions/{id}/status` | Mentor, Faculty | Update intervention lifecycle state |
| `GET` | `/reports/export` | Admin, Faculty, Mentor | Generate PDF/CSV export of cohort analytics and audits |
