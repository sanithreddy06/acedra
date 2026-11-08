# Smart Campus Intelligence — 11-Step Final Demonstration Guide

This guide provides an executable walkthrough of the entire platform lifecycle across all six modules, matching the automated test `backend/tests/test_final_demonstration_workflow.py`.

---

## Pre-Requisites & Test Accounts

Start the backend and frontend development servers:
```bash
# Terminal 1: Backend
cd backend && .venv/bin/uvicorn app.main:app --port 8000 --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

Open your browser to: `http://localhost:5173`

### Demo Credentials
| Role | Email | Password | Primary Mission |
|---|---|---|---|
| **Student** | `student@smartcampus.edu` | `StudentPass123!` | Alex Mercer, 5th Sem CSE student |
| **Faculty** | `faculty@smartcampus.edu` | `FacultyPass123!` | Prof. Charles Babbage, Dept of CSE |
| **Mentor** | `mentor@smartcampus.edu` | `MentorPass123!` | Dr. Alan Turing, Student Academic Mentor |
| **Placement**| `placement@smartcampus.edu` | `PlacementPass123!` | Sarah Connor, Head of Placement & Careers |
| **Admin** | `admin@smartcampus.edu` | `AdminPass123!` | Dr. Grace Hopper, Dean of Academic Affairs |

---

## 11-Step Demonstration Workflow

### Step 1: Admin Imports Student Records (Module 1)
1. Sign in as **Admin** (`admin@smartcampus.edu`).
2. Navigate to **Data Import Center** (`CSV/XLS` badge in sidebar).
3. Select import type **Students**, choose `datasets/students_import_template.csv`, and click **Validate & Preview**.
4. The system validates all columns (USN, Name, Email, Semester, CGPA) without errors. Click **Execute Batch Ingestion**.

### Step 2: Student Views Personal Academic Dashboard (Modules 1 & 6)
1. Sign in as **Student** (`student@smartcampus.edu`).
2. The Academic Dashboard renders:
   - **Cumulative CGPA**: `8.84`
   - **Current Semester SGPA**: `8.90`
   - **Overall Attendance**: `92.5%`
   - **Active Backlogs**: `0`
3. Review the longitudinal semester bar chart displaying performance across Semesters 1 to 5.

### Step 3: Risk Engine Identifies an Early-Warning Concern (Module 2)
1. In the background or via the Risk Management tab, the deterministic risk engine scans student records against active policy rules.
2. For students with attendance below 65% or missing continuous assessment scores, early-warning alerts are generated.
3. Notice Alert `#214`: *Critical Attendance Shortfall (<65%)* flagged for an at-risk student.

### Step 4: System Explains the Risk Alert with Transparent Breakdown (Module 2)
1. Switch to **Faculty** or **Mentor** persona.
2. Navigate to **Early-Warning Radar** in the sidebar.
3. Click on the flagged student alert to open the **Transparent Audit Breakdown**:
   - **Observed Metric**: `60.0% (24/40 classes attended)`
   - **Institutional Threshold**: `< 65.0%`
   - **Severity**: `CRITICAL`
   - **AI/Deterministic Explanation**: Transparent calculation with suggested remedial action.

### Step 5: Recommendations Engine Generates Adaptive Roadmap (Module 3)
1. Switch back to **Student** (`student@smartcampus.edu`) and click **Personalized Roadmap**.
2. Notice adaptive recommendations synthesized based on the student's profile:
   - *Technical Communication & Structured Interview Storytelling* (Soft skills)
   - *Advanced Database Query Optimization & Index Tuning* (Subject improvement)
3. Click **Accept Recommendation** to add it to your active study plan, and update progress to `50%`.

### Step 6: Skill-Gap Analysis Evaluates Career Goal Readiness (Module 4)
1. In the Student Portal, click **Placement Readiness**.
2. Select target career goal: **Software Developer**.
3. View the placement radar:
   - **Readiness Score**: `100%` (Ready)
   - **Required Skills**: Python (Expert), SQL (Advanced), Data Structures (Advanced), Git (Advanced)
   - Verified competency matches are highlighted in green with supporting project evidence.

### Step 7: Public AI Chatbot Answers Campus Policy Inquiry (Module 5)
1. Click **Smart Campus AI** in the navigation bar.
2. In **Mode A (Public Campus Assistant)**, submit:
   > *"What is the official minimum attendance percentage required to be eligible for end-semester exams?"*
3. The AI assistant responds with an official policy summary grounded in **REVA Academic Regulations & Grading System**, complete with citations (Section 3, Page 5).

### Step 8: Student AI Assistant Answers Personal Academic Query (Module 5)
1. Toggle the interface switch to **Mode B (Personal Student Assistant)**.
2. Submit:
   > *"Summarize my current semester academic progress, attendance percentage, and active alerts."*
3. The AI assistant retrieves Alex Mercer's personal context and answers with specific grades, subject attendance numbers, and personalized study suggestions.

### Step 9: Mentor Creates Proactive Support Intervention (Module 6)
1. Sign in as **Mentor** (`mentor@smartcampus.edu`).
2. Navigate to **Interventions Hub** in the sidebar.
3. Click **Create New Intervention**:
   - **Student**: Alex Mercer (or at-risk student)
   - **Type**: `Academic Counseling`
   - **Priority**: `HIGH`
   - **Action Plan**: 1. Review core concepts. 2. Establish weekly check-in schedule.
4. Click **Create Intervention**. A new active intervention card appears in the mentor caseload.
5. Click **Schedule Follow-Up** to set a review milestone for next week.

### Step 10: Placement Officer Reviews Institutional Readiness & Recruitment (Modules 4 & 6)
1. Sign in as **Placement Officer** (`placement@smartcampus.edu`).
2. Review the **Placement Dashboard**:
   - Total students eligible for recruitment.
   - Skill coverage across engineering departments.
   - 5 active recruitment drives (Google, Microsoft, Amazon, Infosys, Cisco).
3. Filter candidates eligible for the upcoming Software Development drive.

### Step 11: Administrator Reviews Holistic Institutional Executive Intelligence (Module 6)
1. Sign in as **Administrator** (`admin@smartcampus.edu`).
2. View the **Executive Intelligence Dashboard**:
   - Total Enrolled Students: `160+`
   - Faculty & Mentor Ratios
   - Active Risk Alert Distribution (Critical, High, Moderate)
   - Intervention Success & Resolution Rate
3. Navigate to **Reports & Audits Center** and generate an institutional audit export (CSV/PDF) documenting full regulatory compliance.
