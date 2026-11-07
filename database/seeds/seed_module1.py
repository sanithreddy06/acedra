import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models.user import User, Role, UserRole
from app.models.department import Department
from app.models.academic import (
    Semester,
    Subject,
    FacultyCourseAssignment,
    StudentSemesterRecord,
    SubjectResult,
    SubjectAttendance,
    StudentAssessment,
)
from app.models.profile import Student, Faculty, Mentor, StudentMentorAssignment
from app.models.student_intelligence import (
    Skill,
    StudentSkill,
    Certification,
    Project,
    Internship,
    Hackathon,
    SkillCategory,
)

# Standard Skills Directory
CORE_SKILLS = [
    # Programming
    ("Python", "programming", "General-purpose scripting and data engineering"),
    ("Java", "programming", "Object-oriented backend and enterprise systems"),
    ("TypeScript", "programming", "Type-safe JavaScript for modern frontend & full stack"),
    ("C++", "programming", "Systems programming and low-level algorithms"),
    ("Go", "programming", "High-concurrency microservices and cloud tooling"),
    ("SQL", "programming", "Relational database querying and DDL/DML"),
    # Frameworks
    ("React", "framework", "Declarative UI component library"),
    ("FastAPI", "framework", "High performance Python async web framework"),
    ("Spring Boot", "framework", "Enterprise Java microservices framework"),
    ("Node.js", "framework", "Asynchronous JavaScript runtime environment"),
    ("Next.js", "framework", "React production full-stack framework"),
    ("Tailwind CSS", "framework", "Utility-first CSS styling system"),
    # Databases
    ("PostgreSQL", "database", "Advanced open-source relational database"),
    ("Redis", "database", "In-memory key-value cache and message broker"),
    ("MongoDB", "database", "NoSQL document database"),
    # Cloud & DevOps
    ("Docker", "cloud", "Containerization platform"),
    ("AWS", "cloud", "Amazon Web Services infrastructure"),
    ("Kubernetes", "cloud", "Container orchestration and deployment"),
    ("Git & GitHub", "tool", "Distributed version control and collaboration"),
    ("Linux", "tool", "UNIX-like operating system environment"),
    # Soft skills
    ("Technical Communication", "soft_skill", "Written documentation and presentation"),
    ("Agile Methodology", "soft_skill", "Sprint planning and Scrum collaboration"),
]

# 30 Synthetic Student Profiles (Explicitly labeled as Synthetic Demo Data)
SYNTHETIC_STUDENT_NAMES = [
    ("Aditya", "Sharma", "M"),
    ("Ananya", "Deshmukh", "F"),
    ("Bharath", "Kumar", "M"),
    ("Bhavana", "Reddy", "F"),
    ("Chetan", "Verma", "M"),
    ("Deepika", "Padukone", "F"),
    ("Divyansh", "Mishra", "M"),
    ("Farhan", "Akhtar", "M"),
    ("Gauri", "Shinde", "F"),
    ("Harish", "Patel", "M"),
    ("Ishaan", "Khatter", "M"),
    ("Janhavi", "Kapoor", "F"),
    ("Karthik", "Subramanian", "M"),
    ("Lavanya", "Sundaram", "F"),
    ("Manish", "Malhotra", "M"),
    ("Meera", "Nambiar", "F"),
    ("Naveen", "Polishetty", "M"),
    ("Neha", "Dhupia", "F"),
    ("Omkar", "Gawande", "M"),
    ("Pooja", "Hegde", "F"),
    ("Pranav", "Mohanlal", "M"),
    ("Rashmika", "Mandanna", "F"),
    ("Rishi", "Kapoor", "M"),
    ("Samyuktha", "Menon", "F"),
    ("Siddharth", "Roy", "M"),
    ("Swathi", "Reddy", "F"),
    ("Tanmay", "Bhat", "M"),
    ("Trisha", "Krishnan", "F"),
    ("Varun", "Dhawan", "M"),
    ("Vidya", "Balan", "F"),
]


def seed_module1():
    print(">>> Initializing Module 1 schema additions...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed standard skills if not present
        skills_map = {}
        for name, cat, desc in CORE_SKILLS:
            skill = db.query(Skill).filter(Skill.name == name).first()
            if not skill:
                skill = Skill(name=name, category=cat, description=desc)
                db.add(skill)
                db.flush()
            skills_map[name] = skill

        # Fetch existing departments, semesters, mentor, faculty
        depts = db.query(Department).all()
        dept_ids = [d.id for d in depts]
        semesters = db.query(Semester).order_by(Semester.semester_number.asc()).all()
        mentor = db.query(Mentor).first()
        mentor_id = mentor.id if mentor else None
        student_role = db.query(Role).filter(Role.name == UserRole.STUDENT.value).first()
        role_id = student_role.id if student_role else 1

        # Populate semester records and attendance for early students (1-6) if missing
        early_students = db.query(Student).filter(Student.id <= 6).all()
        dept_subjects = db.query(Subject).all()
        for es in early_students:
            if not es.semester_records:
                for sem_no in range(1, es.current_semester + 1):
                    sem_obj = next((s for s in semesters if s.semester_number == sem_no), None)
                    if sem_obj:
                        delta = round(random.uniform(-0.25, 0.25), 2)
                        sem_sgpa = min(10.0, max(4.0, round(es.cgpa + delta, 2)))
                        db.add(StudentSemesterRecord(
                            student_id=es.id,
                            semester_id=sem_obj.id,
                            semester_number=sem_no,
                            sgpa=sem_sgpa,
                            credits_registered=24,
                            credits_earned=24,
                            backlogs_count=0,
                            status="Pass"
                        ))
            if not es.attendance_records:
                for subj in dept_subjects[:5]:
                    tot_classes = 45
                    target_ratio = es.attendance_percentage / 100.0
                    attended = int(round(tot_classes * target_ratio))
                    attended = max(10, min(tot_classes, attended))
                    db.add(SubjectAttendance(
                        student_id=es.id,
                        subject_id=subj.id,
                        semester_id=semesters[4].id if len(semesters) >= 5 else 1,
                        total_classes=tot_classes,
                        attended_classes=attended
                    ))
        db.commit()

        # Check if synthetic records already created
        existing_synthetic = db.query(Student).filter(Student.usn.like("1RV22SYN%")).count()
        if existing_synthetic >= 25:
            print(f">>> Found {existing_synthetic} synthetic students already present. Skipping creation.")
            return

        print(f">>> Seeding 30 Synthetic Student Profiles with rich analytics (Module 1)...")

        # Program names by department
        program_by_dept = {
            "CSE": "B.Tech Computer Science & Engineering",
            "AI_DS": "B.Tech Artificial Intelligence & Data Science",
            "ECE": "B.Tech Electronics & Communication Engineering",
            "MECH": "B.Tech Mechanical Engineering",
        }

        created_students = []

        for idx, (first_name, last_name, gender) in enumerate(SYNTHETIC_STUDENT_NAMES, start=1):
            num_str = f"{idx:03d}"
            usn = f"1RV22SYN{num_str}"
            srn = f"SRN-2022-SYN{num_str}"
            roll_number = f"SYN22-{num_str}"
            email = f"{first_name.lower()}.{last_name.lower()}.syn@smartcampus.edu"
            full_name = f"{first_name} {last_name} [Synthetic Demo]"

            # Distribute across departments and semesters
            dept = depts[(idx - 1) % len(depts)]
            current_sem_num = 5 if idx <= 20 else (3 if idx <= 26 else 7)
            section = "A" if idx % 2 == 1 else "B"

            # Realistic variation in CGPA (5.4 to 9.85)
            # Create a nice bell curve with high performers, average performers, and at-risk students
            if idx in [4, 11, 23]:
                cgpa = round(random.uniform(5.2, 5.9), 2)  # At risk academically
                att_pct = round(random.uniform(62.0, 71.0), 1)  # At risk attendance
                status_val = "Active"
                placement_status = "Ineligible"
            elif idx in [1, 2, 7, 14, 20]:
                cgpa = round(random.uniform(9.0, 9.85), 2)  # High achiever
                att_pct = round(random.uniform(92.0, 98.0), 1)
                status_val = "Active"
                placement_status = "Eligible"
            elif idx == 28:
                cgpa = round(random.uniform(7.8, 8.5), 2)
                att_pct = round(random.uniform(85.0, 92.0), 1)
                status_val = "Graduated"
                placement_status = "Placed"
            else:
                cgpa = round(random.uniform(7.1, 8.9), 2)  # Healthy average
                att_pct = round(random.uniform(76.0, 91.0), 1)
                status_val = "Active"
                placement_status = "Eligible" if (cgpa >= 7.0 and att_pct >= 75.0) else "Ineligible"

            # Check if user exists
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    hashed_password=get_password_hash("StudentPass123!"),
                    full_name=full_name,
                    phone=f"+91-98450{num_str}12",
                    role=UserRole.STUDENT.value,
                    role_id=role_id,
                    department_id=dept.id,
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.flush()

            # Check if student profile exists
            student = db.query(Student).filter(Student.usn == usn).first()
            if not student:
                student = Student(
                    user_id=user.id,
                    roll_number=roll_number,
                    usn=usn,
                    srn=srn,
                    department_id=dept.id,
                    program=program_by_dept.get(dept.code, "B.Tech Engineering"),
                    current_semester=current_sem_num,
                    batch_year=2024,
                    admission_year=2022,
                    section=section,
                    status=status_val,
                    cgpa=cgpa,
                    attendance_percentage=att_pct,
                    placement_status=placement_status,
                    assigned_mentor_id=mentor_id,
                    gender="Male" if gender == "M" else "Female",
                    dob=date(2004, (idx % 12) + 1, (idx % 28) + 1),
                    blood_group=["A+", "B+", "O+", "AB+"][idx % 4],
                    guardian_name=f"Mr./Mrs. {last_name}",
                    guardian_contact=f"+91-98440{num_str}99",
                    address=f"Flat #{idx*10}, Block-{section}, Campus Residency, Bangalore, India [Synthetic Demo]",
                )
                db.add(student)
                db.flush()

            created_students.append(student)

            # 2. Seed Semester Records & SGPA Progression (Semesters 1 through current)
            for sem_no in range(1, current_sem_num + 1):
                sem_obj = next((s for s in semesters if s.semester_number == sem_no), None)
                if not sem_obj:
                    continue

                existing_sem_rec = db.query(StudentSemesterRecord).filter(
                    StudentSemesterRecord.student_id == student.id,
                    StudentSemesterRecord.semester_id == sem_obj.id,
                ).first()

                if not existing_sem_rec:
                    # SGPA variation around CGPA
                    delta = round(random.uniform(-0.35, 0.35), 2)
                    sem_sgpa = min(10.0, max(4.0, round(cgpa + delta, 2)))
                    has_backlog = (cgpa < 6.0 and sem_no == current_sem_num - 1)

                    sem_rec = StudentSemesterRecord(
                        student_id=student.id,
                        semester_id=sem_obj.id,
                        semester_number=sem_no,
                        sgpa=sem_sgpa,
                        credits_registered=24,
                        credits_earned=20 if has_backlog else 24,
                        backlogs_count=1 if has_backlog else 0,
                        status="Backlog" if has_backlog else "Pass",
                    )
                    db.add(sem_rec)

            # 3. Seed Subject Results & Attendance for Current Semester Courses
            dept_subjects = db.query(Subject).filter(Subject.department_id == dept.id).all()
            if not dept_subjects:
                dept_subjects = db.query(Subject).limit(4).all()

            for subj in dept_subjects:
                # Subject Result
                existing_res = db.query(SubjectResult).filter(
                    SubjectResult.student_id == student.id,
                    SubjectResult.subject_id == subj.id,
                ).first()

                if not existing_res:
                    # Marks derived from CGPA
                    base_ratio = cgpa / 10.0
                    internal = round(min(50.0, max(15.0, 50.0 * base_ratio + random.uniform(-4, 4))), 1)
                    external = round(min(50.0, max(15.0, 50.0 * base_ratio + random.uniform(-4, 4))), 1)
                    total = internal + external
                    if total >= 90:
                        letter, gp = "O", 10.0
                    elif total >= 80:
                        letter, gp = "A+", 9.0
                    elif total >= 70:
                        letter, gp = "A", 8.0
                    elif total >= 60:
                        letter, gp = "B+", 7.0
                    elif total >= 50:
                        letter, gp = "B", 6.0
                    else:
                        letter, gp = "F", 0.0

                    db.add(SubjectResult(
                        student_id=student.id,
                        subject_id=subj.id,
                        semester_id=semesters[current_sem_num - 1].id if len(semesters) >= current_sem_num else 1,
                        internal_marks=internal,
                        external_marks=external,
                        total_marks=total,
                        letter_grade=letter,
                        grade_point=gp,
                        is_backlog=(letter == "F"),
                    ))

                # Subject Attendance (Stored raw class counts)
                existing_att = db.query(SubjectAttendance).filter(
                    SubjectAttendance.student_id == student.id,
                    SubjectAttendance.subject_id == subj.id,
                ).first()

                if not existing_att:
                    tot_classes = 45
                    target_ratio = att_pct / 100.0
                    attended = int(round(tot_classes * target_ratio + random.randint(-2, 2)))
                    attended = max(10, min(tot_classes, attended))

                    db.add(SubjectAttendance(
                        student_id=student.id,
                        subject_id=subj.id,
                        semester_id=semesters[current_sem_num - 1].id if len(semesters) >= current_sem_num else 1,
                        total_classes=tot_classes,
                        attended_classes=attended,
                    ))

                # Continuous Assessment Record
                existing_ass = db.query(StudentAssessment).filter(
                    StudentAssessment.student_id == student.id,
                    StudentAssessment.subject_id == subj.id,
                ).first()

                if not existing_ass:
                    db.add(StudentAssessment(
                        student_id=student.id,
                        subject_id=subj.id,
                        semester_id=semesters[current_sem_num - 1].id if len(semesters) >= current_sem_num else 1,
                        assessment_type="Internal Assessment 1",
                        max_marks=25.0,
                        marks_obtained=round(min(25.0, max(8.0, 25.0 * (cgpa / 10.0) + random.uniform(-2, 2))), 1),
                        remarks="Synthetic performance evaluation",
                        assessment_date=date(2026, 9, 15),
                    ))

            # 4. Student Skills (3 to 6 skills per student)
            selected_skills = random.sample(list(skills_map.values()), k=random.randint(3, 6))
            for sk in selected_skills:
                existing_sk = db.query(StudentSkill).filter(
                    StudentSkill.student_id == student.id,
                    StudentSkill.skill_id == sk.id,
                ).first()

                if not existing_sk:
                    prof = "Expert" if cgpa > 8.8 else ("Advanced" if cgpa > 7.8 else "Intermediate")
                    db.add(StudentSkill(
                        student_id=student.id,
                        skill_id=sk.id,
                        proficiency_level=prof,
                        is_verified=(cgpa > 8.0),
                    ))

            # 5. Certifications (1 to 2 for students with CGPA > 7.5)
            if cgpa >= 7.5 and not student.certifications:
                cert_titles = [
                    ("AWS Certified Cloud Practitioner", "Amazon Web Services"),
                    ("Meta Certified Frontend Developer", "Meta"),
                    ("Google Associate Cloud Engineer", "Google Cloud"),
                    ("Oracle Certified Java SE 17 Developer", "Oracle"),
                ]
                chosen_cert, issuer = random.choice(cert_titles)
                db.add(Certification(
                    student_id=student.id,
                    title=f"{chosen_cert} [Synthetic Demo]",
                    issuing_organization=issuer,
                    issue_date=date(2025, random.randint(1, 12), random.randint(1, 28)),
                    credential_id=f"SYN-CERT-{student.id:04d}",
                    credential_url="https://credentials.smartcampus.edu/verify/demo",
                    verification_status="Verified",
                ))

            # 6. Projects (1 to 2 projects per student)
            if not student.projects:
                project_templates = [
                    ("Distributed Cache System", "High-throughput in-memory cache utilizing Redis clustering & consistent hashing.", "Python, Redis, Docker", "Backend Lead"),
                    ("Microservices Job Portal", "Scalable recruitment portal with role-based access and JWT tokenization.", "FastAPI, PostgreSQL, React", "Full Stack Developer"),
                    ("Automated Attendance Intelligence", "Face recognition attendance tracking integrated with academic loggers.", "Python, OpenCV, SQLite", "ML Engineer"),
                    ("Autonomous IoT Sensor Hub", "Low-power environmental monitoring mesh network with MQTT gateway.", "C++, ESP32, MQTT", "Embedded Developer"),
                ]
                p_title, p_desc, p_stack, p_role = random.choice(project_templates)
                db.add(Project(
                    student_id=student.id,
                    title=f"{p_title} [Synthetic Demo]",
                    description=p_desc,
                    tech_stack=p_stack,
                    role=p_role,
                    github_url="https://github.com/synthetic-campus/project-demo",
                    live_url="https://demo-projects.smartcampus.edu",
                    semester_number=current_sem_num,
                ))

            # 7. Internships (for students with CGPA >= 8.2)
            if cgpa >= 8.2 and not student.internships:
                intern_companies = [
                    ("Amazon Development Centre", "SDE Intern", "35,000 INR/mo"),
                    ("Bosch Global Software Technologies", "Embedded Systems Intern", "25,000 INR/mo"),
                    ("Infosys Springboard", "Full Stack Engineer Intern", "20,000 INR/mo"),
                    ("Zeta Payments", "Backend Engineering Intern", "40,000 INR/mo"),
                ]
                comp, i_role, stp = random.choice(intern_companies)
                db.add(Internship(
                    student_id=student.id,
                    company_name=f"{comp} [Synthetic Demo]",
                    role=i_role,
                    start_date=date(2026, 6, 1),
                    end_date=date(2026, 8, 1),
                    stipend=stp,
                    description="Contributed to core microservices APIs and latency reduction sprints.",
                    status="Completed",
                ))

            # 8. Hackathon (for top students)
            if cgpa >= 8.5 and not student.hackathons:
                db.add(Hackathon(
                    student_id=student.id,
                    event_name="National Smart Campus Hackathon 2026 [Synthetic Demo]",
                    organizer="Ministry of Education & Institutional Cell",
                    year=2026,
                    achievement="1st Runner Up" if idx % 2 == 0 else "Finalist",
                    project_title="AI Curriculum Anomaly Detector",
                ))

        db.commit()
        print(f">>> Successfully seeded 30 synthetic student records with full academic, attendance, assessment, skill & project profiles!")

    except Exception as e:
        db.rollback()
        print(f"!!! Error seeding Module 1 data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_module1()
