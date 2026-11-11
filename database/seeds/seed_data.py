import sys
import os
from datetime import date

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User, Role, UserRole
from app.models.department import Department
from app.models.academic import Semester, Subject, FacultyCourseAssignment
from app.models.profile import Student, Faculty, Mentor, StudentMentorAssignment
from app.models.audit import AuditLog
from app.models.system import SystemSetting


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print(">>> Database is already seeded. Skipping initial seed.")
            return

        print(">>> Seeding Roles...")
        roles_data = [
            {
                "name": UserRole.STUDENT.value,
                "display_name": "Student",
                "description": "Enrolled campus student with access to academic progress, courses, and mentoring.",
                "permissions": ["view_own_grades", "view_own_attendance", "view_courses", "contact_mentor"]
            },
            {
                "name": UserRole.FACULTY.value,
                "display_name": "Faculty Member",
                "description": "Teaching faculty managing courses, student performance, and departmental circulars.",
                "permissions": ["manage_courses", "record_attendance", "grade_evaluations", "view_department_analytics"]
            },
            {
                "name": UserRole.MENTOR.value,
                "display_name": "Academic Mentor",
                "description": "Faculty mentor guiding assigned student cohorts and tracking early risk signals.",
                "permissions": ["view_mentees", "log_mentoring_sessions", "flag_risk", "request_intervention"]
            },
            {
                "name": UserRole.ADMIN.value,
                "display_name": "Administrator / HOD",
                "description": "Department Head or Institutional Administrator with full governance privileges.",
                "permissions": ["manage_users", "manage_curriculum", "view_institution_analytics", "manage_settings", "view_audit_logs"]
            },
            {
                "name": UserRole.PLACEMENT_OFFICER.value,
                "display_name": "Placement Officer",
                "description": "Career and placement cell coordinator tracking company drives and student readiness.",
                "permissions": ["view_placement_eligibility", "manage_company_drives", "track_offers", "generate_placement_reports"]
            },
        ]
        roles_map = {}
        for r in roles_data:
            role = db.query(Role).filter(Role.name == r["name"]).first()
            if not role:
                role = Role(**r)
                db.add(role)
                db.flush()
            roles_map[r["name"]] = role

        print(">>> Seeding Departments...")
        depts_data = [
            {"code": "CSE", "name": "Computer Science & Engineering", "description": "Core computer systems, algorithms, software engineering", "hod_name": "Dr. Sarah Jenkins"},
            {"code": "AI_DS", "name": "Artificial Intelligence & Data Science", "description": "Applied intelligence, machine learning and big data systems", "hod_name": "Dr. Rajesh Sharma"},
            {"code": "ECE", "name": "Electronics & Communication Engineering", "description": "VLSI design, signal processing, IoT and communication networks", "hod_name": "Dr. Michael Chen"},
            {"code": "MECH", "name": "Mechanical Engineering", "description": "Thermal, manufacturing, robotics and mechanical systems", "hod_name": "Dr. Robert Vance"},
        ]
        depts_map = {}
        for d in depts_data:
            dept = Department(**d)
            db.add(dept)
            db.flush()
            depts_map[d["code"]] = dept

        print(">>> Seeding Semesters...")
        semesters = []
        for sem_no in range(1, 9):
            is_curr = (sem_no == 5)
            sem = Semester(
                name=f"Semester {sem_no}",
                academic_year="2026-2027",
                semester_number=sem_no,
                start_date=date(2026, 8, 1),
                end_date=date(2026, 12, 20),
                is_current=is_curr
            )
            db.add(sem)
            db.flush()
            semesters.append(sem)

        current_sem = next(s for s in semesters if s.is_current)

        print(">>> Seeding Subjects...")
        subjects_data = [
            {"code": "CS501", "name": "Advanced Data Structures & Algorithms", "dept": "CSE", "sem": 5, "credits": 4, "type": "Theory"},
            {"code": "CS502", "name": "Operating Systems & Kernel Architecture", "dept": "CSE", "sem": 5, "credits": 4, "type": "Theory"},
            {"code": "CS503", "name": "Database Management Systems", "dept": "CSE", "sem": 5, "credits": 4, "type": "Theory"},
            {"code": "CS504", "name": "Computer Networks & Distributed Systems", "dept": "CSE", "sem": 5, "credits": 4, "type": "Theory"},
            {"code": "CS505", "name": "Full Stack Web Engineering Lab", "dept": "CSE", "sem": 5, "credits": 2, "type": "Lab"},
            {"code": "AI501", "name": "Machine Learning Fundamentals", "dept": "AI_DS", "sem": 5, "credits": 4, "type": "Theory"},
            {"code": "EC501", "name": "Signals & Systems", "dept": "ECE", "sem": 5, "credits": 4, "type": "Theory"},
        ]
        subjects_map = {}
        for s in subjects_data:
            subj = Subject(
                code=s["code"],
                name=s["name"],
                department_id=depts_map[s["dept"]].id,
                semester_number=s["sem"],
                credits=s["credits"],
                subject_type=s["type"]
            )
            db.add(subj)
            db.flush()
            subjects_map[s["code"]] = subj

        print(">>> Seeding 5 Primary Role Users...")
        # 1. Admin / HOD
        admin_user = User(
            email="admin@reva-demo.example",
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Dr. Sarah Jenkins (HOD)",
            phone="+1-555-0100",
            role=UserRole.ADMIN.value,
            role_id=roles_map[UserRole.ADMIN.value].id,
            department_id=depts_map["CSE"].id,
            is_active=True,
            is_verified=True
        )
        db.add(admin_user)
        db.flush()

        # 2. Mentor
        mentor_user = User(
            email="mentor@reva-demo.example",
            hashed_password=get_password_hash("MentorPass123!"),
            full_name="Prof. David K. Sterling",
            phone="+1-555-0102",
            role=UserRole.MENTOR.value,
            role_id=roles_map[UserRole.MENTOR.value].id,
            department_id=depts_map["CSE"].id,
            is_active=True,
            is_verified=True
        )
        db.add(mentor_user)
        db.flush()

        mentor_profile = Mentor(
            user_id=mentor_user.id,
            employee_id="MNT-2024-001",
            department_id=depts_map["CSE"].id,
            designation="Chief Academic Mentor & Assoc. Professor",
            max_mentees=30
        )
        db.add(mentor_profile)
        db.flush()

        # 3. Faculty
        faculty_user = User(
            email="faculty@reva-demo.example",
            hashed_password=get_password_hash("FacultyPass123!"),
            full_name="Dr. Elena Rostova",
            phone="+1-555-0103",
            role=UserRole.FACULTY.value,
            role_id=roles_map[UserRole.FACULTY.value].id,
            department_id=depts_map["CSE"].id,
            is_active=True,
            is_verified=True
        )
        db.add(faculty_user)
        db.flush()

        faculty_profile = Faculty(
            user_id=faculty_user.id,
            employee_id="FAC-2023-042",
            department_id=depts_map["CSE"].id,
            designation="Professor of Computer Systems",
            specialization="Distributed Computing & OS"
        )
        db.add(faculty_profile)
        db.flush()

        # Faculty course assignments
        assign1 = FacultyCourseAssignment(
            faculty_id=faculty_profile.id,
            subject_id=subjects_map["CS502"].id,
            semester_id=current_sem.id,
            section="A",
            academic_year="2026-2027"
        )
        assign2 = FacultyCourseAssignment(
            faculty_id=faculty_profile.id,
            subject_id=subjects_map["CS504"].id,
            semester_id=current_sem.id,
            section="A",
            academic_year="2026-2027"
        )
        db.add_all([assign1, assign2])

        # 4. Placement Officer
        placement_user = User(
            email="placement@reva-demo.example",
            hashed_password=get_password_hash("PlacementPass123!"),
            full_name="Marcus Vance",
            phone="+1-555-0104",
            role=UserRole.PLACEMENT_OFFICER.value,
            role_id=roles_map[UserRole.PLACEMENT_OFFICER.value].id,
            department_id=None,
            is_active=True,
            is_verified=True
        )
        db.add(placement_user)
        db.flush()

        # 5. Primary Student
        student_user = User(
            email="student@reva-demo.example",
            hashed_password=get_password_hash("StudentPass123!"),
            full_name="Alex Mercer",
            phone="+1-555-0105",
            role=UserRole.STUDENT.value,
            role_id=roles_map[UserRole.STUDENT.value].id,
            department_id=depts_map["CSE"].id,
            is_active=True,
            is_verified=True
        )
        db.add(student_user)
        db.flush()

        student_profile = Student(
            user_id=student_user.id,
            roll_number="CS22B001",
            usn="1RV22CS001",
            department_id=depts_map["CSE"].id,
            current_semester=5,
            batch_year=2024,
            section="A",
            cgpa=8.84,
            attendance_percentage=92.5,
            placement_status="Eligible",
            assigned_mentor_id=mentor_profile.id
        )
        db.add(student_profile)
        db.flush()

        # Mentor assignment
        ment_assign = StudentMentorAssignment(
            student_id=student_profile.id,
            mentor_id=mentor_profile.id,
            academic_year="2026-2027",
            semester=5,
            is_active=True,
            assigned_date=date(2026, 8, 15),
            notes="Active mentee performing well in algorithms. Target: high tier placements."
        )
        db.add(ment_assign)

        # Additional Student Cohort for realistic metrics
        additional_students_data = [
            ("Rohan Iyer", "rohan.iyer@reva-demo.example", "CS22B002", "1RV22CS002", 9.15, 96.0, "Eligible", mentor_profile.id),
            ("Priya Nair", "priya.nair@reva-demo.example", "CS22B003", "1RV22CS003", 7.85, 88.0, "Eligible", mentor_profile.id),
            ("Kavita Rao", "kavita.rao@reva-demo.example", "CS22B004", "1RV22CS004", 5.65, 68.0, "Ineligible", mentor_profile.id),  # At-risk
            ("Arjun Mehta", "arjun.mehta@reva-demo.example", "CS22B005", "1RV22CS005", 8.42, 91.0, "Placed", mentor_profile.id),
            ("Sneha Patil", "sneha.patil@reva-demo.example", "CS22B006", "1RV22CS006", 6.20, 71.0, "Eligible", mentor_profile.id),  # Borderline
        ]

        for s_name, s_email, roll, usn, cgpa, att, p_stat, m_id in additional_students_data:
            u = User(
                email=s_email,
                hashed_password=get_password_hash("StudentPass123!"),
                full_name=s_name,
                role=UserRole.STUDENT.value,
                role_id=roles_map[UserRole.STUDENT.value].id,
                department_id=depts_map["CSE"].id,
                is_active=True,
                is_verified=True
            )
            db.add(u)
            db.flush()

            st = Student(
                user_id=u.id,
                roll_number=roll,
                usn=usn,
                department_id=depts_map["CSE"].id,
                current_semester=5,
                batch_year=2024,
                section="A",
                cgpa=cgpa,
                attendance_percentage=att,
                placement_status=p_stat,
                assigned_mentor_id=m_id
            )
            db.add(st)
            db.flush()

            db.add(StudentMentorAssignment(
                student_id=st.id,
                mentor_id=m_id,
                academic_year="2026-2027",
                semester=5,
                is_active=True,
                assigned_date=date(2026, 8, 15)
            ))

        print(">>> Seeding System Settings...")
        settings_data = [
            {"key": "institution_name", "value": "Smart Institute of Technology & Intelligence", "desc": "Campus legal identity", "cat": "general"},
            {"key": "academic_calendar_active", "value": "2026-2027 Odd Semester", "desc": "Current academic operational cycle", "cat": "academic"},
            {"key": "attendance_threshold_min", "value": 75.0, "desc": "Mandatory minimum attendance percentage", "cat": "academic"},
            {"key": "cgpa_placement_cutoff_default", "value": 7.0, "desc": "Default cutoff CGPA for placement drive eligibility", "cat": "academic"},
            {"key": "mfa_enforced_for_staff", "value": True, "desc": "Enforce multi-factor authentication for staff and admins", "cat": "security"},
        ]
        for s in settings_data:
            setting = SystemSetting(
                key=s["key"],
                value=s["value"],
                description=s["desc"],
                category=s["cat"],
                updated_by=admin_user.id
            )
            db.add(setting)

        print(">>> Seeding Audit Logs...")
        db.add(AuditLog(
            user_id=admin_user.id,
            action="SYSTEM_INITIALIZED",
            resource_type="system",
            resource_id="foundation",
            ip_address="127.0.0.1",
            user_agent="System Bootstrap CLI",
            details={"version": "0.1.0", "status": "Module 0 Initialized"}
        ))

        db.commit()
        print(">>> Database seed completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"!!! Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
