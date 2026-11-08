# Smart Campus Intelligence — Role-Based User Manual

The platform provides dedicated, security-enforced interfaces for five core institutional roles:

---

## 1. Student User Guide

### 1.1 Overview & Dashboard
- **Academic Dashboard**: Shows current cumulative CGPA, semester SGPA, overall aggregate attendance percentage, and active backlogs.
- **Dynamic Attendance Radar**: Displays subject-wise class attendance with early warning color codes (Green > 85%, Yellow 75–85%, Red < 75%).
- **Personalized Roadmap**: Displays recommended courses, coding exercises, and certifications based on weak academic areas or target career choices.

### 1.2 Placement Readiness & Skill Inventory
- **Self-Reported Skills**: Students add technical skills (e.g., Python, Docker, React) and select their proficiency level.
- **Evidence Submission**: Students attach verification evidence (GitHub repository URLs, live demo links, certification credentials) to substantiate their self-reported skills.
- **Career Role Readiness**: Select a target career goal (e.g., *Software Developer*, *Data Scientist*) to see a real-time readiness score (0–100%) and missing skill breakdown.

### 1.3 Conversational AI Assistant
- **Mode A (Public)**: Ask general questions about campus schedules, university policies, or technical concepts.
- **Mode B (Personal)**: Switch to Mode B to ask: *"What is my current semester attendance?"*, *"Why do I have an alert in Data Structures?"*, or *"Generate a 4-week study schedule for my upcoming exams."*

---

## 2. Faculty User Guide

### 2.1 Student 360° Directory & Analytics
- Search and filter students by Department, Program, Semester, Section, or Risk Status.
- View individual student profiles with comprehensive semester-wise grade transcripts and attendance logs.

### 2.2 Skill Verification
- Review pending skill verification requests submitted by students.
- Inspect submitted repository links and certificates, then mark evidence as **Verified** or **Rejected** with constructive feedback.

### 2.3 Early-Warning Alerts
- Monitor active early-warning flags across enrolled course cohorts.
- Acknowledge alerts, log preliminary faculty notes, or refer students to assigned faculty mentors.

---

## 3. Mentor User Guide

### 3.1 Mentee Caseload Central
- Access the list of assigned student mentees.
- Review holistic student dossiers including academic progression, attendance trends, and behavioral alerts.

### 3.2 Intervention Workflow Hub
- **Create Interventions**: Initiate structured support action plans (Academic Counseling, Attendance Remediation, Career Coaching, Wellbeing Support).
- **Follow-up Timeline**: Schedule check-in meetings and milestones with specific due dates.
- **Progress Tracking**: Update status across the intervention lifecycle (`ASSIGNED` -> `IN_PROGRESS` -> `RESOLVED`).

---

## 4. Placement Officer User Guide

### 4.1 Career Role & Benchmark Management
- Configure required technical skills, minimum proficiency thresholds, and importance weights for target campus roles.
- Monitor cohort placement readiness distribution across departments.

### 4.2 Corporate Recruitment Drives
- Post upcoming campus recruitment opportunities and internship listings with eligibility criteria (minimum CGPA, allowed active backlogs).
- Filter and export lists of eligible students matching company criteria.

---

## 5. Administrator & HOD User Guide

### 5.1 Institutional Intelligence
- View executive campus metrics: total enrollment, retention health, risk alert distribution across departments, and mentor intervention throughput.

### 5.2 Batch Data Ingestion Center
- Upload institutional student rosters, semester results, and attendance records via CSV or Excel (`.xlsx`) files.
- Preview data validation errors prior to database ingestion to guarantee schema integrity.

### 5.3 Policy Rule & Knowledge Base Configuration
- Configure transparent early-warning thresholds (minimum attendance %, CIA failure conditions).
- Upload and manage official university regulatory handbooks (PDF/DOCX) for RAG vector search indexing.
- View tamper-evident system audit logs for administrative actions.
