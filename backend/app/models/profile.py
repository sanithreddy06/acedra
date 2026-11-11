from sqlalchemy import JSON, Boolean, Column, Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class Student(Base, TimestampMixin, TenantMixin):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("university_id", "roll_number", name="uq_students_tenant_roll_number"),
        UniqueConstraint("university_id", "usn", name="uq_students_tenant_usn"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    roll_number = Column(String(50), index=True, nullable=False)
    usn = Column(String(50), index=True, nullable=False)
    srn = Column(String(50), index=True, nullable=True)  # Student Registration Number
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    program = Column(String(100), default="B.Tech Computer Science & Engineering", nullable=False)
    current_semester = Column(Integer, default=1, nullable=False)
    batch_year = Column(Integer, nullable=False)  # e.g., 2024
    admission_year = Column(Integer, default=2022, nullable=False)
    section = Column(String(10), default="A", nullable=False)
    status = Column(String(50), default="Active", nullable=False)  # Active, Inactive, Graduated, Suspended
    cgpa = Column(Float, default=0.0, nullable=False)
    attendance_percentage = Column(Float, default=100.0, nullable=False)
    placement_status = Column(String(50), default="Eligible", nullable=False)  # Eligible, Placed, Ineligible
    assigned_mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=True)

    # Module 3 Career & Interests
    career_goals = Column(JSON, default=list, nullable=True)  # e.g., ["AI/ML Engineer", "Cloud Architect"]
    interests = Column(
        JSON, default=list, nullable=True
    )  # e.g., ["Deep Learning", "Robotics", "Competitive Programming"]

    # Personal profile details
    gender = Column(String(20), nullable=True)
    dob = Column(Date, nullable=True)
    blood_group = Column(String(10), nullable=True)
    guardian_name = Column(String(100), nullable=True)
    guardian_contact = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    mentor = relationship("Mentor", back_populates="mentees", foreign_keys=[assigned_mentor_id])
    mentor_assignments = relationship("StudentMentorAssignment", back_populates="student", cascade="all, delete-orphan")

    # Module 1 Analytics Relationships
    semester_records = relationship("StudentSemesterRecord", back_populates="student", cascade="all, delete-orphan")
    subject_results = relationship("SubjectResult", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship("SubjectAttendance", back_populates="student", cascade="all, delete-orphan")
    assessments = relationship("StudentAssessment", back_populates="student", cascade="all, delete-orphan")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="student", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="student", cascade="all, delete-orphan")
    internships = relationship("Internship", back_populates="student", cascade="all, delete-orphan")
    hackathons = relationship("Hackathon", back_populates="student", cascade="all, delete-orphan")
    risk_alerts = relationship("RiskAlert", back_populates="student", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="student", cascade="all, delete-orphan")
    skill_evidences = relationship("SkillEvidence", back_populates="student", cascade="all, delete-orphan")
    applications = relationship("StudentApplication", back_populates="student", cascade="all, delete-orphan")


class Faculty(Base, TimestampMixin, TenantMixin):
    __tablename__ = "faculty"
    __table_args__ = (UniqueConstraint("university_id", "employee_id", name="uq_faculty_tenant_employee_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100), default="Assistant Professor", nullable=False)
    specialization = Column(String(200), nullable=True)
    qualification = Column(String(100), default="Ph.D.", nullable=True)

    # Relationships
    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty_members")
    course_assignments = relationship("FacultyCourseAssignment", back_populates="faculty")


class Mentor(Base, TimestampMixin, TenantMixin):
    __tablename__ = "mentors"
    __table_args__ = (UniqueConstraint("university_id", "employee_id", name="uq_mentors_tenant_employee_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100), default="Senior Faculty Mentor", nullable=False)
    max_mentees = Column(Integer, default=30, nullable=False)

    # Relationships
    user = relationship("User", back_populates="mentor_profile")
    department = relationship("Department", back_populates="mentors")
    mentees = relationship("Student", back_populates="mentor", foreign_keys=[Student.assigned_mentor_id])
    assignments = relationship("StudentMentorAssignment", back_populates="mentor")


class StudentMentorAssignment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "student_mentor_assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=False)
    academic_year = Column(String(50), nullable=False)  # e.g., 2026-2027
    semester = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    assigned_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    student = relationship("Student", back_populates="mentor_assignments")
    mentor = relationship("Mentor", back_populates="assignments")
