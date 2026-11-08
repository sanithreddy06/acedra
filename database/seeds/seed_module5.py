import os
import sys
from pathlib import Path

# Add project roots to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.ai_assistant import (
    Document,
    DocumentCategory,
    DocumentAccessPermission,
    Conversation,
    Message,
    AssistantMode,
    MessageRole,
)
from app.services.ai_assistant_service import AIAssistantService

CANONICAL_DOCUMENTS = [
    {
        "title": "REVA Academic Regulations & Grading System",
        "category": DocumentCategory.ACADEMIC_REGULATIONS.value,
        "description": "Official university regulations governing the 10-point grading system, SGPA/CGPA formulas, minimum credit requirements, and degree qualification criteria.",
        "file_name": "REVA_Academic_Regulations_2026.md",
        "access_permission": DocumentAccessPermission.PUBLIC.value,
        "content": """# REVA Academic Regulations & Degree Requirements

## Section 1: 10-Point Choice Based Credit System (CBCS)
The university adopts the standard 10-point grading system for all undergraduate and postgraduate engineering programs.
- Grade 'O' (Outstanding): Marks 90% - 100%, Grade Points: 10.0
- Grade 'A+' (Excellent): Marks 80% - 89%, Grade Points: 9.0
- Grade 'A' (Very Good): Marks 70% - 79%, Grade Points: 8.0
- Grade 'B+' (Good): Marks 60% - 69%, Grade Points: 7.0
- Grade 'B' (Above Average): Marks 55% - 59%, Grade Points: 6.0
- Grade 'C' (Average): Marks 50% - 54%, Grade Points: 5.0
- Grade 'P' (Pass): Marks 40% - 49%, Grade Points: 4.0
- Grade 'F' (Fail): Marks Below 40%, Grade Points: 0.0

## Section 2: SGPA and CGPA Calculation Formulas
1. Semester Grade Point Average (SGPA):
   SGPA = Sum(Ci * Gi) / Sum(Ci), where Ci is the credits allocated to course i and Gi is the grade point earned.
2. Cumulative Grade Point Average (CGPA):
   CGPA = Sum(Cj * Gj) / Sum(Cj) evaluated across all registered courses up to the current semester.
3. Degree Award Criterion: A candidate must secure a minimum cumulative CGPA of 5.00 and clear all mandatory program credits (minimum 160 credits for 4-year B.Tech) with zero outstanding backlogs.

## Section 3: Makeup and Supplementary Examinations
Students securing an 'F' grade or prevented from taking end-semester exams due to approved medical hospitalization (submitted within 72 hours of exam date) are eligible to register for the Makeup Examination window conducted before the start of the subsequent semester. A maximum of 4 makeup courses can be attempted in a single window.
""",
    },
    {
        "title": "REVA Attendance Policy and Condonation Guidelines",
        "category": DocumentCategory.ATTENDANCE_GUIDELINES.value,
        "description": "Comprehensive guidelines specifying mandatory 85% attendance, 75%-84% medical condonation procedures, and detention consequences.",
        "file_name": "REVA_Attendance_Policy_and_Condonation.md",
        "access_permission": DocumentAccessPermission.PUBLIC.value,
        "content": """# REVA University Attendance Policy & Condonation Guidelines

## Section 1: Standard Attendance Mandate (85% Rule)
All undergraduate and postgraduate students are strictly required to maintain a minimum attendance of 85% in individual course theory classes and 85% in laboratory practical sessions. Attendance counts are calculated dynamically from verified biometric and LMS classroom logs.

## Section 2: Medical Condonation Band (75% to 84%)
Students who fail to achieve 85% but maintain at least 75% aggregate attendance in a course may apply for attendance condonation subject to the following stringent conditions:
1. Valid medical hospitalization with a signed certificate from a registered medical practitioner submitted to the HOD within 3 days of resuming campus.
2. Representation of the university in recognized national or inter-university sports, cultural, or academic hackathons approved by the Dean of Student Affairs.
3. Payment of the official condonation administrative processing fee of Rs. 1,000 per subject.
4. Final approval rests with the Dean of Academic Affairs.

## Section 3: Critical Attendance Deficit (< 75% Detention)
Students with attendance strictly below 75% in any registered subject are designated as 'Not Eligible' (NE) and are automatically detained from taking the Semester End Examination (SEE) for that course. Detained students must re-register for the course during the summer remedial term or supplementary semester by paying the prescribed course tuition fee. No condonation is granted under any circumstances below 75%.
""",
    },
    {
        "title": "REVA Continuous Internal Assessment (CIA) Guidelines",
        "category": DocumentCategory.EXAMINATION_GUIDELINES.value,
        "description": "Regulations governing the 50% internal assessment components, minimum 40% qualifying marks, and assignment submissions.",
        "file_name": "REVA_Continuous_Internal_Assessment_Guidelines.md",
        "access_permission": DocumentAccessPermission.PUBLIC.value,
        "content": """# REVA Continuous Internal Assessment (CIA) Guidelines

## Section 1: CIA Evaluation Framework (50 Marks Weightage)
Each theoretical course carries a total of 100 marks, evenly split between Continuous Internal Assessment (50%) and Semester End Examination (50%).
The CIA 50 marks are distributed as follows:
- Internal Assessment Tests (IAT): 3 tests of 50 marks each conducted during weeks 5, 10, and 15. The average of the best 2 performances is normalized to 30 Marks.
- Continuous Course Assignments / Case Studies: 2 assignments evaluated for critical thinking and plagiarism check (10 Marks).
- Surprise Quizzes & In-Class Interactive Participation: 2 micro-quizzes (10 Marks).

## Section 2: CIA Passing Benchmark (Minimum 40%)
To qualify for writing the Semester End Examination (SEE), a student must secure a minimum of 40% (20 marks out of 50) in the aggregate CIA evaluation. Students securing less than 20 marks in CIA are marked as 'Ineligible due to CIA' and must repeat the internal continuous assessment components during the supplementary semester.

## Section 3: Lab Course Continuous Evaluation
Practical laboratory courses are evaluated every session on a 100% continuous assessment basis:
- Weekly experiment conduction & record journal: 30 marks
- Mid-term lab test: 20 marks
- End-semester lab practical examination & viva voce: 50 marks.
""",
    },
    {
        "title": "REVA Campus Placement and Corporate Recruitment Policy",
        "category": DocumentCategory.PLACEMENT_GUIDELINES.value,
        "description": "Rules for corporate recruitment drives, Dream Offer exceptions, eligibility criteria, and zero-backlog policies.",
        "file_name": "REVA_Campus_Placement_and_Recruitment_Rules.md",
        "access_permission": DocumentAccessPermission.PUBLIC.value,
        "content": """# REVA Campus Placement and Corporate Recruitment Policy

## Section 1: Standard Placement Drive Eligibility Criteria
1. Academic Standing: Candidates must maintain a minimum cumulative CGPA of 6.00 (or 60% aggregate) across all completed semesters without any active backlogs at the commencement of the recruitment drive.
2. Discipline & Attendance: Candidates must possess a minimum of 85% attendance in mandatory Placement Preparation & Aptitude Training sessions conducted by the Career Development Center.
3. Departmental Clearance: The candidate must obtain No Objection Certificate (NOC) from their respective Head of Department.

## Section 2: 'One Student, One Offer' Policy & Dream Offer Exceptions
To ensure equitable career placement opportunities for all graduating students, REVA enforces the 'One Student, One Offer' principle:
1. Base Placement: Once a student secures a confirmed job offer with an annual CTC below Rs. 8.00 LPA, their profile is marked as 'Placed' and deregistered from subsequent tier-3 and tier-2 company drives.
2. Dream Company Exception: A placed student is permitted to participate in 'Dream Company' recruitments offering an annual package of Rs. 12.00 LPA or higher.
3. Super Dream Exception: A student holding a Dream Offer may participate in 'Super Dream' drives offering Rs. 20.00 LPA or higher.
4. Dual Offer Acceptance: Upon receiving a Dream or Super Dream offer, the student must forfeit the earlier lower-tier offer within 48 hours.

## Section 3: Code of Conduct & Interview Decorum
Shortlisted candidates must attend interview rounds in formal business attire, carrying 3 printed copies of their verified resume and institutional photo ID. Any unexcused absence after confirming attendance for an interview round will result in debarment from campus placements for 60 calendar days.
""",
    },
    {
        "title": "REVA Mandatory Internship and Capstone Project Norms",
        "category": DocumentCategory.INTERNSHIP_GUIDELINES.value,
        "description": "Guidelines for mandatory 6-8 week summer industry internships, faculty mentorship, credits, and viva voce examinations.",
        "file_name": "REVA_Mandatory_Internship_and_Capstone_Norms.md",
        "access_permission": DocumentAccessPermission.PUBLIC.value,
        "content": """# REVA Mandatory Internship and Capstone Project Norms

## Section 1: Summer Internship Mandate
All B.Tech students must complete a mandatory industry internship of 6 to 8 weeks duration during the summer vacation between their 6th and 7th semesters.
1. Approved Organizations: Internships can be undertaken in registered IT companies, research laboratories (ISRO, DRDO, CSIR), startups, or approved institutional research centers.
2. Prior Approval: Students must submit an internship offer letter and obtain formal NOC approval from the Departmental Internship Coordinator prior to joining.

## Section 2: Evaluation and Credit Weightage
The internship carries 3 academic credits awarded in the 7th semester curriculum based on:
- Weekly progress logs and company mentor evaluation: 40 marks
- Formal technical internship report: 30 marks
- Viva voce and technical presentation before departmental evaluation committee: 30 marks.
Unsatisfactory performance or non-completion requires repeating the internship in the subsequent term.
""",
    },
    {
        "title": "REVA Student Handbook, Campus Facilities and Conduct",
        "category": DocumentCategory.CAMPUS_HANDBOOK.value,
        "description": "Campus facilities, Central Library operating hours, code of conduct, digital ID cards, and anti-ragging helpline.",
        "file_name": "REVA_Student_Handbook_and_Conduct.md",
        "access_permission": DocumentAccessPermission.PUBLIC.value,
        "content": """# REVA Student Handbook, Campus Facilities & Code of Conduct

## Section 1: Central Library and Learning Resource Center
The Central Library houses over 120,000 volumes, digital IEEE/ACM research databases, and 500 quiet study carrels.
- Working Hours: Monday through Saturday: 8:00 AM to 10:00 PM.
- Sundays and University Holidays: 9:00 AM to 5:00 PM.
- Exam Revision Extended Hours: Remains open until 12:00 Midnight during end-semester examination weeks.
- Borrowing Privileges: Undergraduate students may borrow up to 4 books simultaneously for a 14-day renewal period.

## Section 2: Campus Security and Digital ID Card Policy
Every student must carry their RFID-enabled Smart Campus Digital ID card at all times. Turnstile entry at academic blocks, laboratory check-in, library borrowing, and hostel mess access are authenticated strictly via the digital ID card. Lost ID cards must be reported immediately to the IT Helpdesk for deactivation.

## Section 3: Anti-Ragging and Zero-Tolerance Discipline
REVA University maintains strict zero tolerance towards ragging in any form on campus, in hostels, or on university transport buses.
- National Anti-Ragging Toll-Free Helpline: 1800-180-5522
- Campus Proctorial Office: Available 24x7 at block C, ground floor.
- Penalties: Any student found guilty of harassment or ragging will face immediate suspension, rustication, and criminal lodging with law enforcement authorities as mandated by Supreme Court and UGC directives.
""",
    },
]


def seed_module5_rag_data():
    db = SessionLocal()
    print(">>> Seeding Module 5 Conversational AI & RAG Knowledge Base...")

    # Find admin user for creator assignment
    admin = db.query(User).filter(User.role == "admin").first()
    admin_id = admin.id if admin else 1

    seeded_docs = 0
    for doc_def in CANONICAL_DOCUMENTS:
        existing = db.query(Document).filter(Document.title == doc_def["title"]).first()
        if existing:
            existing.content_raw = doc_def["content"]
            db.commit()
            AIAssistantService.reindex_document(db, existing.id)
            print(f"    - Updated & Reindexed: {doc_def['title']} ({existing.chunk_count} chunks)")
            continue

        raw_bytes = doc_def["content"].encode("utf-8")
        doc = AIAssistantService.process_and_index_document(
            db=db,
            title=doc_def["title"],
            category=doc_def["category"],
            file_bytes=raw_bytes,
            file_name=doc_def["file_name"],
            file_type="md",
            description=doc_def["description"],
            access_permission=doc_def["access_permission"],
            created_by_user_id=admin_id,
        )
        seeded_docs += 1
        print(f"    + Indexed Document [{doc.id}]: {doc.title} ({doc.chunk_count} chunks)")

    # Seed Sample Public and Personal Demo Conversations
    student = db.query(User).filter(User.role == "student").first()

    # Public Conversation Seed
    public_conv = db.query(Conversation).filter(Conversation.title == "Campus Attendance & Grading Inquiries").first()
    if not public_conv:
        public_conv = Conversation(
            session_id="public-demo-session-2026-xyz",
            mode=AssistantMode.PUBLIC_MODE_A.value,
            title="Campus Attendance & Grading Inquiries",
        )
        db.add(public_conv)
        db.flush()

        msg1 = Message(
            conversation_id=public_conv.id,
            role=MessageRole.USER.value,
            content="What are the official attendance condonation rules and minimum percentage?",
            token_count=11,
        )
        db.add(msg1)

        msg2 = Message(
            conversation_id=public_conv.id,
            role=MessageRole.ASSISTANT.value,
            content=(
                "### Official University Policy Summary\n"
                "Based on **REVA Attendance Policy and Condonation Guidelines** (*Section 1: Standard Attendance Mandate*, Page 1):\n"
                "All undergraduate and postgraduate students are strictly required to maintain a minimum attendance of **85%** in individual course theory classes and 85% in laboratory practical sessions.\n\n"
                "#### Medical Condonation Band (75% to 84%):\n"
                "Students between 75% and 84% may apply for condonation on genuine medical grounds (hospitalization) or university sports representation with a Rs. 1,000 fee and Dean approval. Below 75% results in detention from end-semester exams."
            ),
            sources_json=[
                {
                    "document_id": 2,
                    "document_title": "REVA Attendance Policy and Condonation Guidelines",
                    "category": "ATTENDANCE_GUIDELINES",
                    "section": "Section 1: Standard Attendance Mandate",
                    "page": 1,
                    "relevance_score": 0.92,
                    "snippet": "All undergraduate and postgraduate students are strictly required to maintain a minimum attendance of 85% in individual course theory classes...",
                }
            ],
            token_count=120,
            processing_time_ms=18.5,
        )
        db.add(msg2)

    # Personal Student Conversation Seed
    if student:
        personal_conv = db.query(Conversation).filter(Conversation.title == "Alex's Academic & Career Coaching").first()
        if not personal_conv:
            personal_conv = Conversation(
                session_id="personal-demo-alex-mercer",
                user_id=student.id,
                mode=AssistantMode.PERSONAL_MODE_B.value,
                title="Alex's Academic & Career Coaching",
            )
            db.add(personal_conv)
            db.flush()

            pmsg1 = Message(
                conversation_id=personal_conv.id,
                role=MessageRole.USER.value,
                content="Can you summarize my academic progress, attendance, and what skills I need to work on?",
                token_count=15,
            )
            db.add(pmsg1)

            pmsg2 = Message(
                conversation_id=personal_conv.id,
                role=MessageRole.ASSISTANT.value,
                content=(
                    "### Personal Student Intelligence Dossier for Alex Mercer (1RV22CS001)\n\n"
                    "- **Current Standing**: 5th Semester &bull; Computer Science & Engineering\n"
                    "- **Cumulative CGPA**: **8.42 / 10.00** &bull; **Active Backlogs**: 0 (Clear standing)\n"
                    "- **Aggregate Attendance**: **87.5%** (Meets 85% standard requirement)\n"
                    "- **Target Career Goal**: **Software Developer** (Readiness: **88%** - READY)\n\n"
                    "#### Actionable Growth Recommendations:\n"
                    "1. Practice production Docker deployments to transition your containerization competency from Intermediate to Advanced.\n"
                    "2. Complete the approved AWS Cloud Practitioner certification before campus placement drives open in Semester 7."
                ),
                sources_json=[],
                token_count=110,
                processing_time_ms=22.1,
            )
            db.add(pmsg2)

    db.commit()
    db.close()
    print(f"✅ Module 5 RAG Seeding complete. Indexed {seeded_docs} documents successfully.")


if __name__ == "__main__":
    seed_module5_rag_data()
