"""
ACEDRA prototype seed — SYNTHETIC DATA ONLY.

Creates:
  * the ACEDRA platform team (super administrator + employees)
  * sample institutional enquiries at different workflow stages
  * three independently configured university tenants:
      - REVA University                 — the main client workspace; generated sample records (seed_reva.py)
      - Northfield University            — fictional; stricter attendance policy, trimester terms
      - Deccan Institute of Technology   — fictional; reduced module set, ACEDRA-assisted email request

Usage (from repository root):
    python database/seeds/seed_all.py            # RESET the development database and seed (destructive)
    python database/seeds/seed_all.py --if-empty # seed only when no universities exist (used by Docker)
"""
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
# The application package is at <repo>/backend/app in a checkout and at /app/app inside the container images
# (where this file is /app/database/seeds/seed_all.py). Add both so the seed runs in either layout.
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(_HERE, "../../backend")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.core.tenancy import TenantScope, set_session_scope, tenant_context  # noqa: E402
import app.models  # noqa: E402,F401
from app.models import (  # noqa: E402
    Department, Faculty, FacultyCourseAssignment, Mentor, Role, Semester, Student, StudentAssessment,
    StudentMentorAssignment, StudentSemesterRecord, StudentSkill, Skill, Subject, SubjectAttendance,
    SubjectResult, User, RiskRule, Certification, Project,
)
from app.models.platform import (  # noqa: E402
    ALL_MODULES, EmployeeAssignment, EmployeeProfile, Enquiry, EnquiryActivity, EnquiryStatus, University,
    UniversityDomain, AccountProvisioningRequest,
)

DEMO_PASSWORDS = {
    "admin": "AdminPass123!", "faculty": "FacultyPass123!", "mentor": "MentorPass123!",
    "placement_officer": "PlacementPass123!", "student": "StudentPass123!",
}
PLATFORM_PASSWORD = "PlatformPass123!"
_HASHES: dict = {}


def pw(raw: str) -> str:
    if raw not in _HASHES:
        _HASHES[raw] = get_password_hash(raw)
    return _HASHES[raw]


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


ROLES = [
    ("student", "Student", "Enrolled student with a personal academic workspace."),
    ("faculty", "Faculty", "Teaching faculty monitoring assigned sections."),
    ("mentor", "Mentor", "Faculty mentor supporting assigned mentees."),
    ("admin", "University Administrator / HOD", "Institutional administrator for one university."),
    ("placement_officer", "Placement Officer", "Career-readiness and placement coordination."),
    ("platform_admin", "ACEDRA Super Administrator", "ACEDRA internal team — tenant management."),
    ("platform_employee", "ACEDRA Employee", "ACEDRA internal team — onboarding and configuration."),
]


def seed_roles(db):
    for name, display, desc in ROLES:
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name, display_name=display, description=desc, permissions=[]))
    db.commit()


def seed_platform(db):
    def mk(email, name, role, title, phone, code, perms=None):
        u = User(email=email, full_name=name, role=role, title=title, phone=phone, hashed_password=pw(PLATFORM_PASSWORD),
                 is_active=True, is_verified=True, university_id=None, is_synthetic=True)
        db.add(u)
        db.flush()
        db.add(EmployeeProfile(user_id=u.id, employee_code=code, title=title, phone=phone,
                               permissions=perms or ["tenant.configure", "tenant.coordinate"]))
        return u

    sa = mk("superadmin@acedra.example", "Meera Krishnan", "platform_admin", "Head of Institutional Partnerships",
            "+91 80 4000 1001", "ACD-0001")
    e1 = mk("arjun.rao@acedra.example", "Arjun Rao", "platform_employee", "Implementation Lead",
            "+91 80 4000 1002", "ACD-0002")
    e2 = mk("fatima.sheikh@acedra.example", "Fatima Sheikh", "platform_employee", "Customer Success Manager",
            "+91 80 4000 1003", "ACD-0003")
    e3 = mk("vikram.nair@acedra.example", "Vikram Nair", "platform_employee", "Onboarding Coordinator",
            "+91 80 4000 1004", "ACD-0004", perms=["tenant.coordinate"])
    db.commit()
    return sa, e1, e2, e3


def make_tenant(db, *, name, short, slug, domains, employee, actor, status, modules=None, structure=None, sample=True,
                color="#3F5A40", location=None, itype="Private university", tagline=None, email_mode="existing"):
    uni = University(
        name=name, short_name=short, slug=slug, status=status, is_synthetic=sample, brand_color=color,
        location=location, institution_type=itype, tagline=tagline,
        enabled_modules=modules or list(ALL_MODULES), student_email_mode=email_mode,
        academic_structure={
            "term_label": "Semester", "terms_per_year": 2, "programme_duration_years": 4, "grading_scale": "10-point",
            "cgpa_max": 10.0, "pass_grade_point": 4.0, "minimum_attendance_percent": 75, "internal_assessment_max": 50,
            **(structure or {}),
        },
        document_categories=["Academic Regulations", "Attendance Policy", "Examination", "Placement", "Student Handbook"],
        notification_settings={"risk_alerts": True, "intervention_updates": True, "weekly_digest": False},
        primary_employee_id=employee.id, created_by_id=actor.id,
        activated_at=now() if status == "active" else None,
    )
    db.add(uni)
    db.flush()
    for i, d in enumerate(domains):
        db.add(UniversityDomain(university_id=uni.id, domain=d, purpose="all", is_primary=(i == 0), verified_at=now()))
    db.add(EmployeeAssignment(university_id=uni.id, employee_user_id=employee.id, assignment_role="primary",
                              assigned_by_id=actor.id, notes="Dedicated ACEDRA point of contact."))
    db.commit()
    return uni


def seed_reva(uni_id):
    """REVA University: the core records (seed_reva), then each module's own data on top of them."""
    import seed_reva as core, seed_reva_activity, seed_module2, seed_module3, seed_module4, seed_module5, seed_module6
    with tenant_context(uni_id):
        core.seed_reva_core()
        seed_module2.seed_module2()
        seed_module3.seed_module3()
        seed_module4.seed_module4(sample_profiles=False)
        seed_module5.seed_module5_rag_data()
        seed_module6.seed_module6()
        seed_reva_activity.seed_reva_activity()


FIRST = ["Aanya", "Rahul", "Ishita", "Kabir", "Diya", "Aditya", "Meghna", "Rohan", "Sara", "Nikhil", "Tara",
         "Varun", "Pooja", "Siddharth", "Lakshmi", "Omar", "Nandini", "Harsh", "Zoya", "Pranav"]
LAST = ["Menon", "Bhat", "Kulkarni", "Reddy", "Joshi", "Hegde", "Pillai", "Das", "Fernandes", "Iyer", "Gowda",
        "Shetty", "Rao", "Kini", "Banerjee", "Qureshi", "Naidu", "Mishra", "Thomas", "Patel"]


def seed_generic(uni_id, domain, cfg, rng):
    from app.services.risk_service import RiskService
    from app.services.recommendation_service import RecommendationService
    from app.services.placement_service import PlacementService
    from app.services.ai_assistant_service import AIAssistantService

    with tenant_context(uni_id):
        db = SessionLocal()
        try:
            roles = {r.name: r.id for r in db.query(Role).all()}

            def user(email, name, role, dept=None, title=None):
                u = User(email=f"{email}@{domain}", full_name=name, role=role, role_id=roles[role],
                         department_id=dept.id if dept else None, title=title, hashed_password=pw(DEMO_PASSWORDS[role]),
                         is_active=True, is_verified=True, is_synthetic=True)
                db.add(u)
                db.flush()
                return u

            depts = []
            for code, dname, hod in cfg["departments"]:
                d = Department(code=code, name=dname, hod_name=hod, description=f"{dname} (synthetic)")
                db.add(d)
                depts.append(d)
            db.flush()
            cur = cfg["current_semester"]
            sems = {}
            for n in range(1, 9):
                s = Semester(name=f"{cfg['term_label']} {n}", academic_year="2026-2027", semester_number=n,
                             is_current=(n == cur), start_date=date(2026, 7, 15), end_date=date(2026, 12, 15))
                db.add(s)
                sems[n] = s
            db.flush()

            subjects = {}
            for d in depts:
                subjects[d.code] = []
                for i, (sc, sn) in enumerate(cfg["subjects"][d.code]):
                    sub = Subject(code=sc, name=sn, department_id=d.id, semester_number=cur, credits=4 if i < 3 else 2,
                                  subject_type="Theory" if i < 3 else "Lab")
                    db.add(sub)
                    subjects[d.code].append(sub)
            db.flush()

            admin = user("admin", cfg["admin_name"], "admin", depts[0], "Registrar (Academics)")
            po = user("placement", cfg["placement_name"], "placement_officer", None, "Training & Placement Officer")
            faculty_users = []
            for idx, d in enumerate(depts[:2]):
                fu = user(f"faculty{'' if idx == 0 else idx + 1}", cfg["faculty_names"][idx], "faculty", d, "Associate Professor")
                fac = Faculty(user_id=fu.id, employee_id=f"{cfg['prefix']}F{100 + idx}", department_id=d.id,
                              designation="Associate Professor", specialization=d.name)
                db.add(fac)
                db.flush()
                for sub in subjects[d.code]:
                    db.add(FacultyCourseAssignment(faculty_id=fac.id, subject_id=sub.id, semester_id=sems[cur].id,
                                                   section="A", academic_year="2026-2027"))
                faculty_users.append(fu)
            mu = user("mentor", cfg["mentor_name"], "mentor", depts[0], "Faculty Mentor")
            mentor = Mentor(user_id=mu.id, employee_id=f"{cfg['prefix']}M200", department_id=depts[0].id,
                            designation="Faculty Mentor", max_mentees=25)
            db.add(mentor)
            db.flush()

            skills = {}
            for nm, cat in [("Python", "programming"), ("Java", "programming"), ("SQL", "database"),
                            ("Data Structures", "core_cs"), ("Machine Learning", "ai_ml"), ("React", "web"),
                            ("Communication", "soft_skill"), ("Git", "tools")]:
                sk = Skill(name=nm, category=cat, description=f"{nm} (catalogue)")
                db.add(sk)
                skills[nm] = sk
            db.flush()

            students = []
            n_students = cfg["students"]
            for i in range(n_students):
                d = depts[i % 2]
                fn, ln = FIRST[(i + cfg["name_offset"]) % len(FIRST)], LAST[(i * 3 + cfg["name_offset"]) % len(LAST)]
                email = "student" if i == 0 else f"{fn.lower()}.{ln.lower()}{i}"
                su = user(email, f"{fn} {ln}", "student", d)
                profile = rng.choice(["strong", "steady", "steady", "at_risk", "declining"]) if i else "steady"
                if i in (3, 7):
                    profile = "at_risk"
                usn = f"{cfg['prefix']}{24}{d.code[:2]}{i + 1:03d}"
                st = Student(user_id=su.id, usn=usn, roll_number=usn, department_id=d.id, program=f"B.Tech {d.name}",
                             current_semester=cur, batch_year=2024, admission_year=2024, section="A",
                             assigned_mentor_id=mentor.id if d == depts[0] else None, cgpa=0, attendance_percentage=0,
                             career_goals=[rng.choice(["Software Developer", "Data Analyst", "AI/ML Engineer"])],
                             interests=[rng.choice(["Web development", "Data science", "Embedded systems", "Cloud"])])
                db.add(st)
                db.flush()
                if st.assigned_mentor_id:
                    db.add(StudentMentorAssignment(student_id=st.id, mentor_id=mentor.id, academic_year="2026-2027",
                                                   semester=cur, is_active=True, assigned_date=date(2026, 7, 20)))
                base = {"strong": 8.8, "steady": 7.6, "at_risk": 5.6, "declining": 7.9}[profile]
                sgpas = []
                for n in range(1, cur):
                    drift = -0.55 * (n - 1) if profile == "declining" else rng.uniform(-0.3, 0.3)
                    sg = round(max(4.0, min(9.9, base + drift + rng.uniform(-0.2, 0.2))), 2)
                    sgpas.append(sg)
                    db.add(StudentSemesterRecord(student_id=st.id, semester_id=sems[n].id, semester_number=n, sgpa=sg,
                                                 credits_registered=22, credits_earned=22 if sg >= 5 else 18,
                                                 backlogs_count=0 if sg >= 5 else 1, status="Pass" if sg >= 5 else "Backlog"))
                cgpa = round(sum(sgpas) / len(sgpas), 2) if sgpas else 0
                att_total, att_seen = 0, 0
                for sub in subjects[d.code]:
                    total = 40
                    att_pct = {"strong": 0.94, "steady": 0.84, "at_risk": 0.64, "declining": 0.73}[profile] + rng.uniform(-0.05, 0.04)
                    attended = max(0, min(total, int(round(total * att_pct))))
                    att_total += total
                    att_seen += attended
                    db.add(SubjectAttendance(student_id=st.id, subject_id=sub.id, semester_id=sems[cur].id,
                                             total_classes=total, attended_classes=attended))
                    ia_scale = {"strong": 0.85, "steady": 0.7, "at_risk": 0.38, "declining": 0.5}[profile]
                    ia_marks = []
                    for k, label in enumerate(["Internal Assessment 1", "Internal Assessment 2", "Assignment"]):
                        if profile == "at_risk" and k == 2 and rng.random() < 0.5:
                            continue  # missing assessment
                        mx = 25.0 if k < 2 else 10.0
                        got = round(max(0, min(mx, mx * (ia_scale + rng.uniform(-0.1, 0.1)))), 1)
                        ia_marks.append(got / mx)
                        db.add(StudentAssessment(student_id=st.id, subject_id=sub.id, semester_id=sems[cur].id,
                                                 assessment_type=label, max_marks=mx, marks_obtained=got,
                                                 assessment_date=date(2026, 8, 20) + timedelta(days=30 * k)))
                st.cgpa = cgpa
                st.attendance_percentage = round(100 * att_seen / att_total, 1) if att_total else 0
                st.placement_status = "Eligible" if cgpa >= 6.5 else "Ineligible"
                for nm in rng.sample(list(skills), k=3 if profile != "at_risk" else 2):
                    db.add(StudentSkill(student_id=st.id, skill_id=skills[nm].id,
                                        proficiency_level=rng.choice(["Beginner", "Intermediate", "Advanced"]),
                                        is_verified=rng.random() < 0.4))
                if profile == "strong":
                    db.add(Project(student_id=st.id, title="Campus timetable optimiser", tech_stack="Python, OR-Tools",
                                   description="Synthetic demo project.", semester_number=cur - 1))
                    db.add(Certification(student_id=st.id, title="Cloud Practitioner (demo)", issuing_organization="Example Cloud",
                                         verification_status="Pending"))
                students.append(st)
            db.commit()

            # Module configuration that differs per university
            RiskService.seed_default_rules_if_needed(db, admin.id)
            for rule in db.query(RiskRule).all():
                if rule.indicator_type == "attendance_percentage" and rule.operator in ("<", "<="):
                    rule.threshold_value = float(cfg["attendance_threshold"])
                    rule.description = (f"Attendance below {cfg['attendance_threshold']}% "
                                        f"({cfg['short']} attendance regulation).")
            db.commit()
            RiskService.evaluate_risk(db, run_type="SCHEDULED", user_id=admin.id)
            RecommendationService.seed_default_catalogue_if_needed(db, admin.id)
            for st in students:
                RecommendationService.generate_recommendations_for_student(db, st.id)
            PlacementService.seed_canonical_career_roles(db)
            PlacementService.seed_canonical_opportunities(db)

            for title, cat, perm, body in cfg["documents"]:
                AIAssistantService.process_and_index_document(
                    db=db, title=title, category=cat, file_bytes=body.encode(), file_name=title.lower().replace(" ", "_") + ".md",
                    file_type="md", description="Synthetic demo policy document.", access_permission=perm,
                    created_by_user_id=admin.id)
            db.commit()
            return admin
        finally:
            db.close()


NORTHFIELD = {
    "short": "Northfield", "prefix": "NF", "current_semester": 4, "term_label": "Term", "students": 14, "name_offset": 2,
    "attendance_threshold": 80,
    "departments": [("CSE", "Computer Science", "Dr. Anita Desai"), ("DS", "Data Science", "Dr. Paul Mathew"),
                    ("ME", "Mechanical Engineering", "Dr. K. Srinivas")],
    "subjects": {
        "CSE": [("NF-CS401", "Design and Analysis of Algorithms"), ("NF-CS402", "Database Systems"),
                ("NF-CS403", "Computer Organisation"), ("NF-CS404", "Database Lab")],
        "DS": [("NF-DS401", "Statistical Inference"), ("NF-DS402", "Machine Learning I"),
               ("NF-DS403", "Data Engineering"), ("NF-DS404", "Python for Data Lab")],
        "ME": [],
    },
    "admin_name": "Dr. Helen D'Souza", "placement_name": "Ravi Shankar", "mentor_name": "Prof. Leela Varghese",
    "faculty_names": ["Dr. Sameer Kulkarni", "Dr. Ritu Agarwal"],
    "documents": [
        ("Northfield Attendance Regulation", "ATTENDANCE_GUIDELINES", "PUBLIC",
         "# Northfield University Attendance Regulation (synthetic)\n\n## Minimum attendance\nStudents must maintain at "
         "least 80% attendance in every course in each term. Students below 80% are not permitted to sit the end-term "
         "examination for that course unless condonation is approved.\n\n## Condonation\nThe Dean may condone up to 5% "
         "shortfall for documented medical reasons. Applications are submitted to the department office within 7 days."),
        ("Northfield Examination Rules", "EXAMINATION_GUIDELINES", "PUBLIC",
         "# Northfield University Examination Rules (synthetic)\n\n## Term structure\nThe academic year has three terms. "
         "Each course has two internal assessments (25 marks each) and an end-term examination.\n\n## Re-evaluation\n"
         "Re-evaluation requests must be filed within 10 days of results being published."),
    ],
}
DECCAN = {
    "short": "Deccan Tech", "prefix": "DT", "current_semester": 6, "term_label": "Semester", "students": 10, "name_offset": 9,
    "attendance_threshold": 75,
    "departments": [("ECE", "Electronics & Communication", "Dr. M. Prakash"), ("IT", "Information Technology", "Dr. S. Bhatia")],
    "subjects": {
        "ECE": [("DT-EC601", "VLSI Design"), ("DT-EC602", "Digital Signal Processing"), ("DT-EC603", "Embedded Systems"),
                ("DT-EC604", "VLSI Lab")],
        "IT": [("DT-IT601", "Cloud Computing"), ("DT-IT602", "Software Engineering"), ("DT-IT603", "Information Security"),
               ("DT-IT604", "Cloud Lab")],
    },
    "admin_name": "Prof. Ganesh Murthy", "placement_name": "Shalini Gupta", "mentor_name": "Dr. Kavya Raman",
    "faculty_names": ["Dr. Imran Khan", "Dr. Neha Saxena"],
    "documents": [
        ("Deccan Tech Student Handbook", "CAMPUS_HANDBOOK", "PUBLIC",
         "# Deccan Institute of Technology Student Handbook (synthetic)\n\n## Attendance\nA minimum of 75% attendance is "
         "required in each subject.\n\n## Placement eligibility\nStudents need a CGPA of 6.5 or above and no active "
         "backlogs to register for campus placement drives."),
    ],
}


def seed_enquiries(db, sa, e1, e2, reva, northfield, deccan):
    def enquiry(ref, status, uni_name, contact, email, modules, owner, extra=None, university=None, activities=(),
                designation="Dean, Academic Affairs", location="Bengaluru, Karnataka", itype="Private university",
                population="5,000 – 15,000"):
        e = Enquiry(reference=ref, status=status, university_name=uni_name, institution_type=itype,
                    location=location, student_population=population, department_count=8,
                    contact_name=contact, contact_designation=designation, contact_email=email,
                    preferred_contact_method="email", requested_modules=modules, consent_to_contact=True,
                    owner_id=owner.id if owner else None, university_id=university.id if university else None,
                    **(extra or {}))
        db.add(e)
        db.flush()
        db.add(EnquiryActivity(enquiry_id=e.id, kind="system", to_status="new",
                               body="Enquiry submitted through the public ACEDRA website."))
        for kind, body, to in activities:
            db.add(EnquiryActivity(enquiry_id=e.id, kind=kind, body=body, to_status=to, author_id=sa.id))
        return e

    e = enquiry("ENQ-2607-A1B2C3", "active", "REVA University", "Dr. Anitha Rao",
                "anitha.rao@reva.in", list(ALL_MODULES), e1, university=reva,
                extra={"agreement_reference": "ACD-SA-2026-001", "agreed_modules": list(ALL_MODULES)},
                activities=[("meeting", "Discovery meeting held with the academic office.", None),
                            ("agreement", "Service agreement ACD-SA-2026-001 recorded.", None)])
    reva.enquiry_id = e.id
    reva.agreement_reference = "ACD-SA-2026-001"
    e = enquiry("ENQ-2608-D4E5F6", "active", "Northfield University", "Prof. Sunita Kelkar",
                "registrar@northfield.example", list(ALL_MODULES), e2, university=northfield,
                designation="Registrar", location="Pune, Maharashtra", itype="Deemed university",
                extra={"agreement_reference": "ACD-SA-2026-002", "agreed_modules": list(ALL_MODULES)})
    northfield.enquiry_id = e.id
    northfield.agreement_reference = "ACD-SA-2026-002"
    e = enquiry("ENQ-2609-778899", "active", "Deccan Institute of Technology", "Dr. Venkat Raman",
                "principal@deccan-tech.example", ["student_intelligence", "risk_identification", "interventions"], e1,
                designation="Principal", location="Hyderabad, Telangana", itype="Autonomous college", population="Under 2,000",
                university=deccan, extra={"agreement_reference": "ACD-SA-2026-003",
                                          "agreed_modules": ["student_intelligence", "risk_identification", "interventions"],
                                          "email_provisioning": "rio_assisted", "has_student_emails": False,
                                          "accounts_required": 1200,
                                          "email_service_estimate": {"accounts": 1200, "unit_cost_inr_per_year": 120.0,
                                                                     "estimated_total_inr_per_year": 144000.0}})
    deccan.enquiry_id = e.id
    deccan.agreement_reference = "ACD-SA-2026-003"
    db.add(AccountProvisioningRequest(university_id=deccan.id, method="rio_assisted", accounts_requested=1200,
                                      is_chargeable=True, estimated_cost=144000.0, status="estimated",
                                      notes="Recorded from enquiry ENQ-2609-778899 — additional chargeable service.",
                                      requested_by_id=sa.id))
    enquiry("ENQ-2611-11AA22", "new", "Lakeview College of Engineering", "Ms. Rekha Thomas",
            "iqac@lakeview.example", ["student_intelligence", "risk_identification"], None,
            designation="IQAC Coordinator", location="Kochi, Kerala", itype="Affiliated college", population="2,000 – 5,000",
            extra={"institutional_requirements": "Early warning for first-year students; integration with existing ERP "
                                                 "exports (CSV).", "existing_sis": "Custom ERP"})
    enquiry("ENQ-2611-33BB44", "meeting_scheduled", "Sahyadri School of Management", "Dr. Milind Sathe",
            "director@sahyadri.example", ["placement_readiness", "recommendations", "ai_assistant"], e2,
            designation="Director", location="Nashik, Maharashtra", itype="Autonomous college", population="Under 2,000",
            activities=[("contact", "Introductory call completed.", None),
                        ("meeting", "Product walkthrough scheduled with placement cell.", "meeting_scheduled")])
    enquiry("ENQ-2610-55CC66", "requirements_gathering", "Coastal University of Science", "Prof. Shalini D'Souza",
            "hod.cse@coastal.example", list(ALL_MODULES), e1,
            designation="Head, Computer Science", location="Mangaluru, Karnataka", population="15,000 – 30,000",
            extra={"email_provisioning": "rio_assisted", "has_student_emails": False, "accounts_required": 3500,
                   "email_service_estimate": {"accounts": 3500, "unit_cost_inr_per_year": 120.0,
                                              "estimated_total_inr_per_year": 420000.0}})
    db.commit()


def main():
    from app.core.config import settings
    if settings.is_production:
        # The sample universities sign in with published demonstration passwords.
        sys.exit("Refusing to load sample data: ENVIRONMENT=production. Use an empty database in production.")
    if "--if-empty" in sys.argv:
        from sqlalchemy import inspect, text
        if inspect(engine).has_table("universities"):
            with engine.connect() as c:
                if c.execute(text("select count(*) from universities")).scalar():
                    print(">>> Database already contains universities — skipping demo seed.")
                    return
    rng = random.Random(2026)
    db_path = engine.url.database if engine.url.drivername.startswith("sqlite") else None
    if "--if-empty" in sys.argv:
        Base.metadata.create_all(bind=engine)  # schema normally comes from Alembic; this is a no-op then
    else:
        print(f">>> Resetting schema ({engine.url.drivername})")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    seed_roles(db)
    sa, e1, e2, e3 = seed_platform(db)
    reva = make_tenant(db, name="REVA University", short="REVA", slug="reva",
                       domains=["reva.in"], employee=e1, actor=sa, status="active", sample=False,
                       location="Bengaluru, Karnataka", color="#3F5A40",
                       tagline="Student success, early support and placement readiness in one workspace")
    northfield = make_tenant(db, name="Northfield University", short="Northfield", slug="northfield",
                             domains=["northfield.example"], employee=e2, actor=sa, status="active",
                             location="Pune, Maharashtra", color="#5B4A3A", itype="Deemed university",
                             structure={"term_label": "Term", "terms_per_year": 3, "minimum_attendance_percent": 80})
    deccan = make_tenant(db, name="Deccan Institute of Technology", short="Deccan Tech", slug="deccan-tech",
                         domains=["deccan-tech.example"], employee=e1, actor=sa, status="active",
                         location="Hyderabad, Telangana", color="#2F4F4F", itype="Autonomous college",
                         modules=["student_intelligence", "risk_identification", "interventions"],
                         email_mode="rio_assisted")
    ids = (reva.id, northfield.id, deccan.id)
    db.close()

    print(">>> Seeding REVA University")
    seed_reva(ids[0])
    print(">>> Seeding Northfield University")
    seed_generic(ids[1], "northfield.example", NORTHFIELD, rng)
    print(">>> Seeding Deccan Institute of Technology")
    seed_generic(ids[2], "deccan-tech.example", DECCAN, rng)

    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    db.query(User).filter(User.university_id.in_(ids[1:])).update({User.is_synthetic: True}, synchronize_session=False)
    unis = {u.id: u for u in db.query(University).all()}
    sa, e1, e2 = (db.query(User).filter(User.email == e).first() for e in
                  ("superadmin@acedra.example", "arjun.rao@acedra.example", "fatima.sheikh@acedra.example"))
    seed_enquiries(db, sa, e1, e2, unis[ids[0]], unis[ids[1]], unis[ids[2]])
    db.commit()
    counts = {u.short_name: db.query(Student).execution_options(acedra_unscoped=True).filter(Student.university_id == u.id).count()
              for u in unis.values()}
    db.close()
    print(f">>> Done. Students per tenant: {counts}")


if __name__ == "__main__":
    main()
