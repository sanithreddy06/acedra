"""
REVA University tenant — core records (sample data generated for the demonstration workspace).

Creates one coherent university: 4 departments, 60 subjects across the three running semesters (3, 5, 7),
16 faculty with teaching assignments for every subject and section, 9 mentors, a placement officer, an
administrator and 240 students. Every student has a complete record: completed-semester SGPAs, current
subject results, per-subject attendance, three internal assessments per subject, skills, and (depending on
performance) certifications, projects, internships and hackathons.

The numbers are generated from a fixed random seed, so every run produces the same university. Performance
bands are deliberate: most students are doing fine, a few are borderline and a few need support, so the
early-warning, recommendation and intervention modules all have something real to work with.

The first account created for each role is the one used in demonstrations (see DEMO_ACCOUNTS); the module
seeders that run afterwards (risk rules, recommendations, placement, knowledge base, interventions) pick
those up as "the" administrator, faculty member, mentor and student.

Run through seed_all.py; this module expects the tenant context to be set by the caller.
"""
import os
import random
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog, CareerRole, Certification, Department, Faculty, FacultyCourseAssignment, Hackathon, Internship,
    Mentor, Project, Role, RoleSkill, Semester, Skill, SkillEvidence, Student, StudentAssessment,
    StudentMentorAssignment, StudentSemesterRecord, StudentSkill, Subject, SubjectAttendance, SubjectResult,
    SystemSetting, User,
)

DOMAIN = "reva.in"
ACADEMIC_YEAR = "2026-2027"
CURRENT_SEMESTER_NUMBER = 5  # the term flagged "current" for imports; cohorts run in semesters 3, 5 and 7

PASSWORDS = {
    "admin": "AdminPass123!", "faculty": "FacultyPass123!", "mentor": "MentorPass123!",
    "placement_officer": "PlacementPass123!", "student": "StudentPass123!",
}

# The accounts used in demonstrations. Each is the first account created for its role.
DEMO_ACCOUNTS = {
    "admin": ("Dr. Anitha Rao", f"anitha.rao@{DOMAIN}"),
    "faculty": ("Dr. Kavya Menon", f"kavya.menon@{DOMAIN}"),
    "mentor": ("Prof. Suresh Hegde", f"suresh.hegde@{DOMAIN}"),
    "placement_officer": ("Rahul Deshpande", f"rahul.deshpande@{DOMAIN}"),
    "student": ("Aarav Sharma", f"aarav.sharma@{DOMAIN}"),
}

ROLES = [
    ("student", "Student", "Enrolled student with a personal academic workspace."),
    ("faculty", "Faculty", "Teaching faculty monitoring the sections they teach."),
    ("mentor", "Mentor", "Faculty mentor supporting assigned mentees."),
    ("admin", "University Administrator / HOD", "Institutional administrator for one university."),
    ("placement_officer", "Placement Officer", "Career-readiness and placement coordination."),
]

DEPARTMENTS = [
    # code, name, description, programme, USN letters, students
    ("CSE", "Computer Science & Engineering", "Algorithms, systems, software engineering and networks",
     "B.Tech Computer Science & Engineering", "CS", 80),
    ("AI_DS", "Artificial Intelligence & Data Science", "Machine learning, data engineering and applied AI",
     "B.Tech Artificial Intelligence & Data Science", "AD", 60),
    ("ECE", "Electronics & Communication Engineering", "VLSI, signal processing, embedded systems and communication",
     "B.Tech Electronics & Communication Engineering", "EC", 56),
    ("MECH", "Mechanical Engineering", "Thermal, design, manufacturing and robotics",
     "B.Tech Mechanical Engineering", "ME", 44),
]

# Four theory courses and one lab per department and running semester.
SUBJECTS = {
    "CSE": {
        3: ["Data Structures", "Digital Logic & Computer Organisation", "Discrete Mathematics",
            "Object-Oriented Programming with Java", "Data Structures Lab"],
        5: ["Advanced Data Structures & Algorithms", "Operating Systems", "Database Management Systems",
            "Computer Networks", "Full Stack Web Engineering Lab"],
        7: ["Cloud Computing", "Machine Learning", "Cryptography & Network Security",
            "Software Project Management", "Capstone Project Phase I"],
    },
    "AI_DS": {
        3: ["Probability & Statistics for Data Science", "Data Structures", "Python for Data Analysis",
            "Database Systems", "Data Analysis Lab"],
        5: ["Machine Learning Fundamentals", "Data Mining & Warehousing", "Artificial Intelligence",
            "Big Data Technologies", "Machine Learning Lab"],
        7: ["Deep Learning", "Natural Language Processing", "Reinforcement Learning",
            "MLOps & Model Deployment", "Capstone Project Phase I"],
    },
    "ECE": {
        3: ["Network Analysis", "Analog Electronic Circuits", "Digital System Design",
            "Engineering Electromagnetics", "Analog & Digital Circuits Lab"],
        5: ["Signals & Systems", "Digital Signal Processing", "Microcontrollers & Embedded Systems",
            "Analog & Digital Communication", "Embedded Systems Lab"],
        7: ["VLSI Design", "Wireless & Mobile Communication", "Internet of Things",
            "Optical Fibre Communication", "Capstone Project Phase I"],
    },
    "MECH": {
        3: ["Engineering Thermodynamics", "Mechanics of Materials", "Manufacturing Processes",
            "Fluid Mechanics", "Materials Testing Lab"],
        5: ["Design of Machine Elements", "Heat & Mass Transfer", "Dynamics of Machinery",
            "Computer-Aided Design & Manufacturing", "CAD/CAM Lab"],
        7: ["Finite Element Methods", "Robotics & Automation", "Automobile Engineering",
            "Operations Research", "Capstone Project Phase I"],
    },
}
SUBJECT_PREFIX = {"CSE": "CS", "AI_DS": "AI", "ECE": "EC", "MECH": "ME"}

# Faculty per department; the first is head of department. (title, name, designation, specialisation)
FACULTY = {
    "CSE": [("Dr.", "Ramesh Kulkarni", "Professor & Head", "Algorithms & Theory of Computation"),
            ("Dr.", "Kavya Menon", "Professor", "Operating Systems & Distributed Computing"),
            ("Dr.", "Vinay Shetty", "Associate Professor", "Databases & Information Systems"),
            ("Prof.", "Shruti Bhat", "Assistant Professor", "Web Engineering"),
            ("Prof.", "Nikhil Joshi", "Assistant Professor", "Cloud & Network Security")],
    "AI_DS": [("Dr.", "Lakshmi Narayanan", "Professor & Head", "Machine Learning"),
              ("Dr.", "Arvind Pillai", "Associate Professor", "Data Mining & Big Data"),
              ("Prof.", "Sowmya Reddy", "Assistant Professor", "Natural Language Processing"),
              ("Prof.", "Imran Khan", "Assistant Professor", "Deep Learning & MLOps")],
    "ECE": [("Dr.", "Padmini Iyengar", "Professor & Head", "VLSI & Embedded Systems"),
            ("Dr.", "Mahesh Gowda", "Associate Professor", "Signal Processing"),
            ("Prof.", "Divya Nambiar", "Assistant Professor", "Communication Systems"),
            ("Prof.", "Sandeep Patil", "Assistant Professor", "Internet of Things")],
    "MECH": [("Dr.", "Girish Naik", "Professor & Head", "Thermal Engineering"),
             ("Dr.", "Usha Krishnamurthy", "Associate Professor", "Machine Design"),
             ("Prof.", "Prakash Hiremath", "Assistant Professor", "Manufacturing & Robotics")],
}

MENTORS = {
    "CSE": [("Prof.", "Suresh Hegde", "Associate Professor & Chief Mentor"), ("Prof.", "Deepika Rao", "Assistant Professor"),
            ("Prof.", "Manoj Kamath", "Assistant Professor")],
    "AI_DS": [("Prof.", "Revathi Subramanian", "Assistant Professor"), ("Prof.", "Ajay Verma", "Assistant Professor")],
    "ECE": [("Prof.", "Chitra Raghavan", "Assistant Professor"), ("Prof.", "Naveen Shenoy", "Assistant Professor")],
    "MECH": [("Prof.", "Bhaskar Murthy", "Assistant Professor"), ("Prof.", "Anjali Desai", "Assistant Professor")],
}

# The first six CSE semester-5 section-A students are fixed, so demonstrations always tell the same story.
# name, CGPA, attendance %, placement status, band
FEATURED_STUDENTS = [
    ("Aarav Sharma", 7.42, 76.0, "Eligible", "attendance"),   # the demo student: sound grades, attendance slipping
    ("Rohan Iyer", 9.15, 96.0, "Eligible", "high"),
    ("Priya Nair", 7.85, 88.0, "Eligible", "average"),
    ("Kavita Rao", 5.65, 66.0, "Ineligible", "support"),
    ("Arjun Mehta", 8.42, 91.0, "Eligible", "average"),
    ("Sneha Patil", 6.20, 71.0, "Eligible", "borderline"),
]

FIRST_NAMES = [
    "Aditya", "Ananya", "Bharath", "Bhavana", "Chetan", "Deepa", "Divyansh", "Faisal", "Gauri", "Harish", "Ishan",
    "Jahnavi", "Karthik", "Lavanya", "Manish", "Meera", "Naveen", "Neha", "Omkar", "Pallavi", "Pranav", "Ramya",
    "Rishabh", "Samyuktha", "Siddharth", "Swathi", "Tanmay", "Tejaswini", "Varun", "Vidya", "Akash", "Anjana",
    "Abhishek", "Aishwarya", "Darshan", "Keerthana", "Gautam", "Harini", "Jayanth", "Kriti", "Lokesh", "Madhuri",
    "Nitin", "Nandita", "Pavan", "Pooja", "Rakesh", "Rachana", "Sagar", "Sahana", "Tarun", "Trisha", "Uday",
    "Vaishnavi", "Yash", "Zara", "Kiran", "Megha", "Rohit", "Shreya", "Vikram", "Sanjana", "Mohan", "Nisha",
]
LAST_NAMES = [
    "Deshmukh", "Kumar", "Reddy", "Verma", "Ranganath", "Mishra", "Ahmed", "Shinde", "Patel", "Kulkarni",
    "Subramanian", "Sundaram", "Agarwal", "Nambiar", "Prakash", "Joshi", "Gawande", "Hiremath", "Menon", "Shetty",
    "Kamath", "Iyengar", "Roy", "Nair", "Deshpande", "Gowda", "Bhandari", "Shankar", "Bhat", "Pai", "Hegde",
    "Rao", "Naidu", "Thomas", "Fernandes", "Pillai", "Banerjee", "Chauhan", "Saxena", "Gupta",
]

SKILLS = [
    ("Python", "programming", "General-purpose programming and data engineering"),
    ("Java", "programming", "Object-oriented backend and enterprise systems"),
    ("TypeScript", "programming", "Type-safe JavaScript for frontend and full stack"),
    ("C++", "programming", "Systems programming and algorithms"),
    ("Go", "programming", "Concurrent services and cloud tooling"),
    ("SQL", "programming", "Relational querying and schema design"),
    ("React", "framework", "Component-based user interfaces"),
    ("FastAPI", "framework", "Python web APIs"),
    ("Spring Boot", "framework", "Java microservices"),
    ("Node.js", "framework", "JavaScript server runtime"),
    ("Next.js", "framework", "React full-stack framework"),
    ("Tailwind CSS", "framework", "Utility-first styling"),
    ("PostgreSQL", "database", "Relational database"),
    ("Redis", "database", "In-memory cache and message broker"),
    ("MongoDB", "database", "Document database"),
    ("Docker", "cloud", "Containerisation"),
    ("AWS", "cloud", "Amazon Web Services infrastructure"),
    ("Kubernetes", "cloud", "Container orchestration"),
    ("Git & GitHub", "tool", "Version control and collaboration"),
    ("Linux", "tool", "UNIX-like operating systems"),
    ("Technical Communication", "soft_skill", "Documentation and presentation"),
    ("Agile Methodology", "soft_skill", "Sprint planning and Scrum collaboration"),
]
# Career goals students declare, by department (goal, share), and what each goal's role asks for. The first
# seven goals are the standard ACEDRA career roles; the last two are roles REVA's placement cell added for
# its core-engineering departments.
DEPARTMENT_GOALS = {
    "CSE": [("Software Developer", 45), ("Full Stack Developer", 30), ("Cloud Solutions Engineer", 15),
            ("Cybersecurity Analyst", 10)],
    "AI_DS": [("Data Scientist", 35), ("AI/ML Engineer", 35), ("Data Analyst", 30)],
    "ECE": [("Embedded Systems Engineer", 60), ("Software Developer", 25), ("Cybersecurity Analyst", 15)],
    "MECH": [("Mechanical Design Engineer", 70), ("Data Analyst", 15), ("Software Developer", 15)],
}
GOAL_INTERESTS = {
    "Software Developer": ["Algorithms", "Backend Systems", "Open Source"],
    "Full Stack Developer": ["Web Performance", "Distributed Systems", "Cloud Native"],
    "Cloud Solutions Engineer": ["DevOps", "Kubernetes", "Infrastructure as Code"],
    "Cybersecurity Analyst": ["Network Security", "Cryptography", "Ethical Hacking"],
    "Data Scientist": ["Statistics", "Machine Learning", "Experiment Design"],
    "AI/ML Engineer": ["Deep Learning", "Natural Language Processing", "Computer Vision"],
    "Data Analyst": ["Data Visualisation", "Business Analytics", "SQL"],
    "Embedded Systems Engineer": ["Microcontrollers", "Internet of Things", "Signal Processing"],
    "Mechanical Design Engineer": ["CAD", "Finite Element Analysis", "Robotics"],
}
# (skill, level the role expects, category)
GOAL_SKILLS = {
    "Software Developer": [("Python", "Advanced", "programming"), ("Java", "Intermediate", "programming"),
                           ("Data Structures", "Advanced", "problem_solving"), ("Algorithms", "Advanced", "problem_solving"),
                           ("SQL", "Intermediate", "database"), ("Git Collaboration", "Intermediate", "teamwork"),
                           ("System Design", "Intermediate", "architecture")],
    "Full Stack Developer": [("React", "Advanced", "framework"), ("TypeScript", "Intermediate", "programming"),
                             ("Node.js", "Intermediate", "framework"), ("Python", "Intermediate", "programming"),
                             ("PostgreSQL", "Intermediate", "database"), ("Docker", "Intermediate", "cloud"),
                             ("REST APIs", "Advanced", "architecture"), ("Git Collaboration", "Intermediate", "teamwork")],
    "Data Analyst": [("SQL", "Advanced", "database"), ("Python", "Intermediate", "programming"),
                     ("Pandas", "Advanced", "data_analysis"), ("Tableau", "Intermediate", "data_analysis"),
                     ("Data Visualization", "Intermediate", "data_analysis"), ("Statistics", "Intermediate", "mathematics"),
                     ("Technical Writing", "Intermediate", "communication")],
    "Data Scientist": [("Python", "Advanced", "programming"), ("Statistics", "Advanced", "mathematics"),
                       ("Machine Learning", "Advanced", "artificial_intelligence"), ("SQL", "Intermediate", "database"),
                       ("Pandas", "Advanced", "data_analysis"), ("Scikit-Learn", "Intermediate", "artificial_intelligence"),
                       ("Deep Learning", "Intermediate", "artificial_intelligence")],
    "AI/ML Engineer": [("Python", "Advanced", "programming"), ("Machine Learning", "Advanced", "artificial_intelligence"),
                       ("Deep Learning", "Advanced", "artificial_intelligence"), ("PyTorch", "Intermediate", "artificial_intelligence"),
                       ("Computer Vision", "Intermediate", "artificial_intelligence"), ("NLP", "Intermediate", "artificial_intelligence"),
                       ("Docker", "Intermediate", "cloud"), ("System Design", "Intermediate", "architecture")],
    "Cloud Solutions Engineer": [("Linux", "Advanced", "tool"), ("Cloud Computing", "Advanced", "cloud"),
                                 ("AWS", "Intermediate", "cloud"), ("Docker", "Advanced", "cloud"),
                                 ("Kubernetes", "Intermediate", "cloud"), ("Terraform", "Intermediate", "cloud"),
                                 ("Network Security", "Intermediate", "security")],
    "Cybersecurity Analyst": [("Network Security", "Advanced", "security"), ("Linux", "Intermediate", "tool"),
                              ("Cryptography", "Intermediate", "security"), ("Ethical Hacking", "Intermediate", "security"),
                              ("SOC Analysis", "Intermediate", "security"), ("Python", "Intermediate", "programming")],
    "Embedded Systems Engineer": [("Embedded C", "Advanced", "programming"), ("Microcontrollers", "Advanced", "hardware"),
                                  ("Digital Electronics", "Intermediate", "hardware"), ("RTOS", "Intermediate", "hardware"),
                                  ("PCB Design", "Intermediate", "hardware"), ("Python", "Intermediate", "programming"),
                                  ("Communication Protocols", "Intermediate", "hardware")],
    "Mechanical Design Engineer": [("CAD Modelling", "Advanced", "design"), ("Finite Element Analysis", "Intermediate", "design"),
                                   ("Engineering Drawing & GD&T", "Advanced", "design"), ("Manufacturing Processes", "Intermediate", "manufacturing"),
                                   ("MATLAB", "Intermediate", "programming"), ("Technical Writing", "Intermediate", "communication")],
}
LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
# Per band: chance of having a required skill, chance it is at the required level or better, chance it is verified.
BAND_SKILL_ODDS = {"high": (0.95, 0.88, 0.75), "average": (0.78, 0.58, 0.50),
                   "borderline": (0.55, 0.30, 0.25), "support": (0.38, 0.15, 0.15)}
# Roles the placement cell maintains in addition to the standard catalogue.
EXTRA_ROLES = [
    ("EMBEDDED_SYSTEMS_ENGINEER", "Embedded Systems Engineer",
     "Designs firmware and hardware interfaces for microcontroller-based products in automotive, IoT and consumer electronics.",
     "5 - 9 LPA", "High"),
    ("MECHANICAL_DESIGN_ENGINEER", "Mechanical Design Engineer",
     "Designs, analyses and documents mechanical components and assemblies for manufacturing.",
     "4.5 - 8 LPA", "High"),
]
# The demo student's skills are fixed so the readiness page always tells the same story.
DEMO_STUDENT_GOAL = "Full Stack Developer"
DEMO_STUDENT_SKILLS = [("React", "Intermediate", True), ("TypeScript", "Intermediate", False), ("Node.js", "Beginner", False),
                       ("Python", "Advanced", True), ("PostgreSQL", "Intermediate", False),
                       ("Git Collaboration", "Intermediate", True)]

CERTIFICATIONS = [
    ("AWS Certified Cloud Practitioner", "Amazon Web Services"),
    ("Google Associate Cloud Engineer", "Google Cloud"),
    ("Oracle Certified Associate, Java SE Programmer", "Oracle"),
    ("Meta Front-End Developer Certificate", "Meta"),
    ("NPTEL: Programming, Data Structures and Algorithms", "NPTEL / IIT Madras"),
    ("NPTEL: Introduction to Machine Learning", "NPTEL / IIT Kharagpur"),
    ("Microsoft Azure Fundamentals (AZ-900)", "Microsoft"),
]
PROJECTS = {
    "CSE": [("Campus Event Booking Portal", "Role-based booking system for halls and labs with approval workflow.",
             "React, FastAPI, PostgreSQL", "Full Stack Developer"),
            ("Distributed Key-Value Cache", "In-memory cache with consistent hashing and replication.",
             "Go, Redis, Docker", "Backend Developer"),
            ("Library Seat Availability Tracker", "Live seat map for the central library using occupancy sensors.",
             "Node.js, MongoDB, MQTT", "Team Lead")],
    "AI_DS": [("Crop Disease Detection from Leaf Images", "CNN classifier served through a mobile-friendly web app.",
               "Python, PyTorch, FastAPI", "ML Engineer"),
              ("Student Feedback Sentiment Analyser", "Topic and sentiment analysis of course feedback comments.",
               "Python, scikit-learn, Streamlit", "Data Analyst"),
              ("Bengaluru Traffic Flow Forecasting", "Time-series forecasting of junction traffic volumes.",
               "Python, Prophet, PostgreSQL", "Data Scientist")],
    "ECE": [("Smart Energy Meter with LoRa", "Low-power metering node with LoRa uplink and dashboard.",
             "C++, ESP32, LoRa", "Embedded Developer"),
            ("FPGA-based FIR Filter", "Configurable FIR filter implemented and verified on an FPGA board.",
             "Verilog, Vivado", "Design Engineer"),
            ("Wearable Pulse Oximeter", "Battery-powered SpO2 monitor with Bluetooth logging.",
             "C, nRF52, BLE", "Hardware Lead")],
    "MECH": [("Solar-Assisted Cold Storage Unit", "Design and thermal analysis of a small solar cold room.",
              "SolidWorks, ANSYS", "Design Lead"),
             ("Pick-and-Place Robotic Arm", "Four-axis arm with inverse kinematics and gripper control.",
              "Arduino, C++, Fusion 360", "Mechatronics Engineer"),
             ("Brake Disc Thermal Analysis", "Finite element study of heat dissipation in ventilated discs.",
              "ANSYS, MATLAB", "Analyst")],
}
INTERNSHIPS = [
    ("Infosys", "Software Engineering Intern", "20,000 INR/month"),
    ("Bosch Global Software Technologies", "Embedded Systems Intern", "25,000 INR/month"),
    ("Tata Consultancy Services", "Digital Intern", "18,000 INR/month"),
    ("Wipro", "Project Intern", "15,000 INR/month"),
    ("Mu Sigma", "Decision Scientist Intern", "30,000 INR/month"),
    ("Toyota Kirloskar Motor", "Graduate Engineering Intern", "17,000 INR/month"),
]
LOCALITIES = ["Yelahanka", "Hebbal", "Kattigenahalli", "Jakkur", "Sahakar Nagar", "Vidyaranyapura", "Thanisandra",
              "Kogilu", "Bagalur", "RT Nagar"]

GRADE_BANDS = [(90, "O", 10.0), (80, "A+", 9.0), (70, "A", 8.0), (60, "B+", 7.0), (50, "B", 6.0), (40, "C", 5.0)]


def _grade(total: float):
    for minimum, letter, points in GRADE_BANDS:
        if total >= minimum:
            return letter, points
    return "F", 0.0


def _slug(name: str) -> str:
    return ".".join(part.lower() for part in name.replace(".", "").split())


def _band_profile(rng: random.Random, band: str):
    """CGPA and overall attendance for a performance band."""
    if band == "support":
        return round(rng.uniform(5.0, 5.95), 2), round(rng.uniform(58.0, 71.0), 1)
    if band == "borderline":
        return round(rng.uniform(6.0, 6.95), 2), round(rng.uniform(70.0, 79.0), 1)
    if band == "high":
        return round(rng.uniform(8.7, 9.8), 2), round(rng.uniform(89.0, 98.0), 1)
    return round(rng.uniform(7.0, 8.65), 2), round(rng.uniform(78.0, 94.0), 1)


def seed_reva_core() -> None:
    rng = random.Random(20260801)
    db = SessionLocal()
    hashes = {role: get_password_hash(password) for role, password in PASSWORDS.items()}
    try:
        # ------------------------------------------------------------------ roles
        roles = {}
        for name, display, description in ROLES:
            role = db.query(Role).filter(Role.name == name).first()
            if not role:
                role = Role(name=name, display_name=display, description=description, permissions=[])
                db.add(role)
                db.flush()
            roles[name] = role

        def make_user(full_name, role, department_id=None, title=None, phone=None, email=None):
            user = User(
                email=email or f"{_slug(full_name.split(' ', 1)[1] if full_name.startswith(('Dr.', 'Prof.')) else full_name)}@{DOMAIN}",
                hashed_password=hashes[role], full_name=full_name, phone=phone, role=role, role_id=roles[role].id,
                department_id=department_id, title=title, is_active=True, is_verified=True,
            )
            db.add(user)
            db.flush()
            return user

        staff_phone = iter(f"+91 80 4696 {n:04d}" for n in range(6001, 6100))

        # ------------------------------------------------------------------ structure
        departments = {}
        for code, name, description, _programme, _letters, _count in DEPARTMENTS:
            head = FACULTY[code][0]
            dept = Department(code=code, name=name, description=description, hod_name=f"{head[0]} {head[1]}")
            db.add(dept)
            db.flush()
            departments[code] = dept

        semesters = {}
        for number in range(1, 9):
            odd = number % 2 == 1
            semester = Semester(
                name=f"Semester {number}", academic_year=ACADEMIC_YEAR, semester_number=number,
                start_date=date(2026, 8, 3) if odd else date(2027, 1, 18),
                end_date=date(2026, 12, 19) if odd else date(2027, 5, 29),
                is_current=(number == CURRENT_SEMESTER_NUMBER),
            )
            db.add(semester)
            db.flush()
            semesters[number] = semester

        subjects = {}  # (dept code, semester) -> [Subject]
        for code, by_semester in SUBJECTS.items():
            for number, names in by_semester.items():
                rows = []
                for index, name in enumerate(names, start=1):
                    is_lab = index == 5
                    subject = Subject(
                        code=f"{SUBJECT_PREFIX[code]}{number}0{index}", name=name, department_id=departments[code].id,
                        semester_number=number, credits=2 if is_lab else 4,
                        subject_type="Project" if name.startswith("Capstone") else ("Lab" if is_lab else "Theory"),
                    )
                    db.add(subject)
                    rows.append(subject)
                db.flush()
                subjects[(code, number)] = rows

        # ------------------------------------------------------------------ demo accounts first
        admin_name, admin_email = DEMO_ACCOUNTS["admin"]
        admin = make_user(admin_name, "admin", title="Dean, Academic Affairs", phone=next(staff_phone), email=admin_email)

        mentor_profiles = {}  # dept code -> [Mentor]
        faculty_profiles = {}  # dept code -> [Faculty]

        def add_mentor(code, title, name, designation, number):
            user = make_user(f"{title} {name}", "mentor", departments[code].id, designation, next(staff_phone))
            mentor = Mentor(user_id=user.id, employee_id=f"REVA-MNT-{number:03d}", department_id=departments[code].id,
                            designation=designation, max_mentees=30)
            db.add(mentor)
            db.flush()
            mentor_profiles.setdefault(code, []).append(mentor)

        def add_faculty(code, title, name, designation, specialization, number):
            user = make_user(f"{title} {name}", "faculty", departments[code].id, designation, next(staff_phone))
            faculty = Faculty(user_id=user.id, employee_id=f"REVA-FAC-{number:03d}", department_id=departments[code].id,
                              designation=designation, specialization=specialization,
                              qualification="Ph.D." if title == "Dr." else "M.Tech")
            db.add(faculty)
            db.flush()
            faculty_profiles.setdefault(code, []).append(faculty)
            return faculty

        add_mentor("CSE", *MENTORS["CSE"][0], number=1)                    # Prof. Suresh Hegde
        demo_faculty = add_faculty("CSE", *FACULTY["CSE"][1], number=1)     # Dr. Kavya Menon
        placement_name, placement_email = DEMO_ACCOUNTS["placement_officer"]
        make_user(placement_name, "placement_officer", title="Head, Career Development Centre",
                  phone=next(staff_phone), email=placement_email)

        # ------------------------------------------------------------------ remaining staff
        number = 2
        for code in departments:
            for index, entry in enumerate(FACULTY[code]):
                if code == "CSE" and index == 1:
                    continue  # the demo faculty member already exists
                add_faculty(code, *entry, number=number)
                number += 1
        number = 2
        for code in departments:
            for index, entry in enumerate(MENTORS[code]):
                if code == "CSE" and index == 0:
                    continue
                add_mentor(code, *entry, number=number)
                number += 1
        # Keep each department's list in its declared order (head of department first).
        faculty_profiles["CSE"] = [faculty_profiles["CSE"][1], faculty_profiles["CSE"][0], *faculty_profiles["CSE"][2:]]

        # Teaching assignments: every subject and section has exactly one teacher. The demo faculty member
        # teaches Operating Systems and Computer Networks to CSE semester 5, section A.
        demo_subject_codes = {"CS502", "CS504"}
        for code in departments:
            pool = faculty_profiles[code]
            rotation = 0
            for number_, rows in sorted((n, r) for (c, n), r in subjects.items() if c == code):
                for subject in rows:
                    for section in ("A", "B"):
                        if code == "CSE" and subject.code in demo_subject_codes and section == "A":
                            teacher = demo_faculty
                        else:
                            candidates = [f for f in pool if f.id != demo_faculty.id] or pool
                            teacher = candidates[rotation % len(candidates)]
                            rotation += 1
                        db.add(FacultyCourseAssignment(faculty_id=teacher.id, subject_id=subject.id,
                                                       semester_id=semesters[number_].id, section=section,
                                                       academic_year=ACADEMIC_YEAR))
        db.flush()

        # ------------------------------------------------------------------ skills catalogue
        skills = {}
        for name, category, description in SKILLS:
            skill = db.query(Skill).filter(Skill.name == name).first()
            if not skill:
                skill = Skill(name=name, category=category, description=description)
                db.add(skill)
                db.flush()
            skills[name] = skill

        # Career roles for the core-engineering departments (the standard seven are added by the placement seeder).
        for role_code, title, description, salary, demand in EXTRA_ROLES:
            role = CareerRole(code=role_code, title=title, description=description, min_experience_level="Entry Level",
                              average_salary_range=salary, industry_demand=demand, is_active=True)
            db.add(role)
            db.flush()
            for position, (name, level, category) in enumerate(GOAL_SKILLS[title]):
                if name not in skills:
                    skills[name] = Skill(name=name, category=category)
                    db.add(skills[name])
                    db.flush()
                importance = "CRITICAL" if position < 2 else ("PREFERRED" if position == len(GOAL_SKILLS[title]) - 1 else "CORE")
                db.add(RoleSkill(role_id=role.id, skill_id=skills[name].id, min_proficiency=level, importance=importance,
                                 importance_weight={"CRITICAL": 3.0, "CORE": 2.0, "PREFERRED": 1.0}[importance],
                                 is_mandatory=(importance == "CRITICAL")))
        db.flush()

        # ------------------------------------------------------------------ students
        used_names = {name for name, *_ in FEATURED_STUDENTS}
        used_names |= {entry[1] for rows in FACULTY.values() for entry in rows}
        used_names |= {entry[1] for rows in MENTORS.values() for entry in rows}
        used_names |= {admin_name.split(" ", 1)[1], placement_name}

        def next_name():
            while True:
                name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
                if name not in used_names:
                    used_names.add(name)
                    return name

        # Semester split per department: 35% in semester 3, 40% in semester 5, 25% in semester 7.
        plan = []  # (dept code, semester, section, featured-or-None)
        for code, _name, _desc, _programme, _letters, count in DEPARTMENTS:
            sizes = {3: round(count * 0.35), 5: round(count * 0.40)}
            sizes[7] = count - sizes[3] - sizes[5]
            for number_ in (5, 3, 7):
                for position in range(sizes[number_]):
                    plan.append((code, number_, "A" if position % 2 == 0 else "B"))
        # The featured students open the CSE semester-5 section-A list.
        featured_slots = [i for i, slot in enumerate(plan) if slot == ("CSE", 5, "A")][:len(FEATURED_STUDENTS)]
        ordered = [plan[i] for i in featured_slots] + [slot for i, slot in enumerate(plan) if i not in featured_slots]

        bands = (["support"] * 8 + ["borderline"] * 13 + ["high"] * 20 + ["average"] * 59)  # per 100 students
        counters = {}
        mentor_load = {}
        programme = {code: prog for code, _n, _d, prog, _l, _c in DEPARTMENTS}
        letters = {code: lt for code, _n, _d, _p, lt, _c in DEPARTMENTS}

        for index, (code, number_, section) in enumerate(ordered):
            featured = FEATURED_STUDENTS[index] if index < len(FEATURED_STUDENTS) else None
            if featured:
                full_name, cgpa, attendance, placement_status, band = featured
                band = "average" if band == "attendance" else band
            else:
                full_name = next_name()
                band = rng.choice(bands)
                cgpa, attendance = _band_profile(rng, band)
                placement_status = "Eligible" if cgpa >= 6.0 and attendance >= 75.0 else "Ineligible"
                if number_ == 7 and band in ("high", "average") and rng.random() < 0.30:
                    placement_status = "Placed"
            admission_year = 2026 - (number_ - 1) // 2
            sequence = counters[(code, admission_year)] = counters.get((code, admission_year), 0) + 1
            usn = f"R{admission_year % 100}{letters[code]}{sequence:03d}"

            user = make_user(full_name, "student", departments[code].id,
                             phone=f"+91 9{rng.randint(1000, 9999)} {rng.randint(10000, 99999)}",
                             email=DEMO_ACCOUNTS["student"][1] if index == 0 else None)
            mentors = mentor_profiles[code]
            mentor = mentors[0] if featured else min(mentors, key=lambda m: mentor_load.get(m.id, 0))
            mentor_load[mentor.id] = mentor_load.get(mentor.id, 0) + 1
            surname = full_name.split()[-1]
            student = Student(
                user_id=user.id, roll_number=usn, usn=usn, srn=usn, department_id=departments[code].id,
                program=programme[code], current_semester=number_, batch_year=admission_year,
                admission_year=admission_year, section=section, status="Active", cgpa=cgpa,
                attendance_percentage=attendance, placement_status=placement_status, assigned_mentor_id=mentor.id,
                gender=rng.choice(["Male", "Female"]),
                dob=date(admission_year - 18, rng.randint(1, 12), rng.randint(1, 28)),
                blood_group=rng.choice(["A+", "B+", "O+", "AB+", "O-", "B-"]),
                guardian_name=f"{rng.choice(['Mr.', 'Mrs.'])} {rng.choice(FIRST_NAMES)} {surname}",
                guardian_contact=f"+91 9{rng.randint(1000, 9999)} {rng.randint(10000, 99999)}",
                address=f"No. {rng.randint(3, 240)}, {rng.randint(1, 12)}th Cross, {rng.choice(LOCALITIES)}, Bengaluru 5600{rng.randint(24, 97)}",
            )
            db.add(student)
            db.flush()
            db.add(StudentMentorAssignment(student_id=student.id, mentor_id=mentor.id, academic_year=ACADEMIC_YEAR,
                                           semester=number_, is_active=True, assigned_date=date(2026, 8, 10)))
            _seed_academics(db, rng, student, band, subjects[(code, number_)], semesters, index)
            _seed_portfolio(db, rng, student, code, band, skills, demo=(index == 0),
                            verifier_id=demo_faculty.user_id)

        # ------------------------------------------------------------------ settings and first audit entry
        for key, value, description, category in [
            ("institution_name", "REVA University", "Name shown on reports and exports", "general"),
            ("academic_calendar_active", "2026-2027 Odd Semester", "Current academic cycle", "academic"),
            ("attendance_threshold_min", 75.0, "Minimum attendance percentage", "academic"),
            ("cgpa_placement_cutoff_default", 6.0, "Default CGPA cut-off for placement eligibility", "academic"),
        ]:
            db.add(SystemSetting(key=key, value=value, description=description, category=category, updated_by=admin.id))
        db.add(AuditLog(user_id=admin.id, action="WORKSPACE_CONFIGURED", resource_type="system", resource_id="reva",
                        details={"departments": len(departments), "students": len(ordered)}))
        db.commit()
        print(f">>> REVA University: {len(ordered)} students, "
              f"{sum(len(v) for v in faculty_profiles.values())} faculty, "
              f"{sum(len(v) for v in mentor_profiles.values())} mentors, "
              f"{sum(len(v) for v in subjects.values())} subjects")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _seed_academics(db, rng, student, band, current_subjects, semesters, index) -> None:
    """Completed-semester SGPAs, and results, attendance and internal assessments for the current subjects."""
    current = student.current_semester
    # A student who needs support carries a backlog from the last completed semester; a few carry two.
    backlogs = 0
    if band == "support":
        backlogs = 2 if rng.random() < 0.35 else 1
    elif band == "borderline" and rng.random() < 0.2:
        backlogs = 1
    # One in twelve average students had a sharp dip last semester (drives the SGPA-decline rule).
    dipped = band == "average" and rng.random() < 0.08

    for number in range(1, current):
        sgpa = min(10.0, max(4.0, round(student.cgpa + rng.uniform(-0.3, 0.3), 2)))
        last = number == current - 1
        if last and dipped:
            sgpa = max(4.0, round(student.cgpa - rng.uniform(1.1, 1.5), 2))
        lost = backlogs if last else 0
        db.add(StudentSemesterRecord(
            student_id=student.id, semester_id=semesters[number].id, semester_number=number, sgpa=sgpa,
            credits_registered=22, credits_earned=22 - 4 * lost, backlogs_count=lost,
            status="Backlog" if lost else "Pass",
        ))

    # A handful of students have not had their internal marks entered yet (missing-assessment rule).
    marks_missing = index >= 6 and rng.random() < 0.025
    base = student.cgpa / 10.0
    for position, subject in enumerate(current_subjects):
        # Attendance varies by subject around the student's overall figure.
        total_classes = 30 if subject.subject_type != "Theory" else 45
        offset = rng.uniform(-6.0, 6.0)
        if index == 0:  # the demo student: two core courses below 75%, the rest above
            offset = {1: -5.0, 3: -7.0}.get(position, 4.5)
        percentage = max(35.0, min(100.0, student.attendance_percentage + offset))
        attended = max(0, min(total_classes, round(total_classes * percentage / 100.0)))
        db.add(SubjectAttendance(student_id=student.id, subject_id=subject.id, semester_id=semesters[current].id,
                                 total_classes=total_classes, attended_classes=attended))

        ability = max(0.3, min(0.99, base + rng.uniform(-0.08, 0.08)))
        internal = round(50.0 * ability, 1)
        external = round(50.0 * max(0.25, min(0.99, ability + rng.uniform(-0.07, 0.07))), 1)
        total = round(internal + external, 1)
        letter, points = _grade(total)
        db.add(SubjectResult(student_id=student.id, subject_id=subject.id, semester_id=semesters[current].id,
                             internal_marks=internal, external_marks=external, total_marks=total,
                             letter_grade=letter, grade_point=points, is_backlog=(letter == "F")))

        if marks_missing:
            continue
        for kind, maximum, when in (("Internal Assessment 1", 25.0, date(2026, 9, 14)),
                                    ("Internal Assessment 2", 25.0, date(2026, 10, 19)),
                                    ("Assignment", 10.0, date(2026, 10, 30))):
            score = round(maximum * max(0.2, min(1.0, ability + rng.uniform(-0.1, 0.1))) * 2) / 2
            db.add(StudentAssessment(student_id=student.id, subject_id=subject.id, semester_id=semesters[current].id,
                                     assessment_type=kind, max_marks=maximum, marks_obtained=score,
                                     remarks=None, assessment_date=when + timedelta(days=position)))


def _seed_portfolio(db, rng, student, code, band, skills, demo=False, verifier_id=None) -> None:
    """Career goal, the skills that goal's role asks for (in proportion to performance and seniority),
    then certifications, projects, internships and hackathons."""
    senior = student.current_semester >= 5
    if demo:
        goal = DEMO_STUDENT_GOAL
        owned = list(DEMO_STUDENT_SKILLS)
    else:
        goals, shares = zip(*DEPARTMENT_GOALS[code])
        goal = rng.choices(goals, weights=shares)[0]
        have, at_level, verified = BAND_SKILL_ODDS[band]
        if not senior:
            have *= 0.7
        owned = []
        for name, required, _category in GOAL_SKILLS[goal]:
            if rng.random() > have:
                continue
            target = LEVELS.index(required)
            if rng.random() < at_level:
                level = LEVELS[min(3, target + (1 if band == "high" and rng.random() < 0.25 else 0))]
            else:
                level = LEVELS[max(0, target - 1)]
            owned.append((name, level, rng.random() < verified))
    student.career_goals = [goal]
    student.interests = GOAL_INTERESTS[goal]

    categories = {name: category for rows in GOAL_SKILLS.values() for name, _level, category in rows}
    for name, level, is_verified in owned:
        if name not in skills:
            skills[name] = Skill(name=name, category=categories.get(name, "technical"))
            db.add(skills[name])
            db.flush()
        student_skill = StudentSkill(student_id=student.id, skill_id=skills[name].id, proficiency_level=level,
                                     is_verified=is_verified)
        db.add(student_skill)
        if is_verified:
            db.flush()
            kind = rng.choice(["PROJECT", "CERTIFICATION", "GITHUB_REPO"])
            db.add(SkillEvidence(
                student_skill_id=student_skill.id, student_id=student.id, evidence_type=kind,
                title={"PROJECT": f"{name}: course project", "CERTIFICATION": f"{name}: course certificate",
                       "GITHUB_REPO": f"{name}: code repository"}[kind],
                description=f"Reviewed by the course teacher as evidence of {level.lower()} proficiency in {name}.",
                verification_status="VERIFIED", verified_by_user_id=verifier_id,
                verified_at=datetime(2026, 10, rng.randint(1, 28), 10, 30),
                verification_feedback="Work reviewed and accepted."))

    if band in ("high", "average") and (senior or band == "high") and rng.random() < 0.7:
        title, issuer = rng.choice(CERTIFICATIONS)
        db.add(Certification(student_id=student.id, title=title, issuing_organization=issuer,
                             issue_date=date(2026, rng.randint(1, 9), rng.randint(1, 28)),
                             credential_id=f"{issuer.split()[0].upper()[:4]}-{rng.randint(100000, 999999)}",
                             verification_status="Verified" if rng.random() < 0.75 else "Pending"))

    if senior or band == "high":
        title, description, stack, role = rng.choice(PROJECTS[code])
        db.add(Project(student_id=student.id, title=title, description=description, tech_stack=stack, role=role,
                       semester_number=max(3, student.current_semester - 1)))

    if student.current_semester == 7 and band in ("high", "average") and rng.random() < 0.65:
        company, role, stipend = rng.choice(INTERNSHIPS)
        db.add(Internship(student_id=student.id, company_name=company, role=role, start_date=date(2026, 6, 1),
                          end_date=date(2026, 7, 31), stipend=stipend,
                          description="Eight-week summer internship with a mentor-reviewed final report.",
                          status="Completed"))

    if band == "high" and senior and rng.random() < 0.5:
        db.add(Hackathon(student_id=student.id, event_name="Smart India Hackathon 2026",
                         organizer="Ministry of Education, Government of India", year=2026,
                         achievement=rng.choice(["Finalist", "Finalist", "Winner, institute round"]),
                         project_title=rng.choice(PROJECTS[code])[0]))


if __name__ == "__main__":
    seed_reva_core()
