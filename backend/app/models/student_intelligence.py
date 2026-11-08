import enum
from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Date as SqlDate, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class SkillCategory(str, enum.Enum):
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), default="programming", index=True, nullable=False)  # SkillCategory value
    description = Column(String(255), nullable=True)

    student_skills = relationship("StudentSkill", back_populates="skill", cascade="all, delete-orphan")


class StudentSkill(Base, TimestampMixin):
    __tablename__ = "student_skills"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_level = Column(String(50), default="Intermediate", nullable=False)  # Beginner, Intermediate, Advanced, Expert
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)

    student = relationship("Student", back_populates="skills")
    skill = relationship("Skill", back_populates="student_skills")
    verified_by = relationship("Faculty")
    evidence_records = relationship("SkillEvidence", back_populates="student_skill", cascade="all, delete-orphan")


class Certification(Base, TimestampMixin):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    issuing_organization = Column(String(200), nullable=False)
    issue_date = Column(SqlDate, nullable=True)
    expiry_date = Column(SqlDate, nullable=True)
    credential_id = Column(String(100), nullable=True)
    credential_url = Column(String(500), nullable=True)
    verification_status = Column(String(50), default="Verified", nullable=False)  # Verified, Pending, Rejected

    student = relationship("Student", back_populates="certifications")


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    tech_stack = Column(String(255), nullable=False)
    role = Column(String(100), default="Developer", nullable=False)
    github_url = Column(String(500), nullable=True)
    live_url = Column(String(500), nullable=True)
    semester_number = Column(Integer, default=5, nullable=False)

    student = relationship("Student", back_populates="projects")


class Internship(Base, TimestampMixin):
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    role = Column(String(100), nullable=False)
    start_date = Column(SqlDate, nullable=False)
    end_date = Column(SqlDate, nullable=True)
    stipend = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="Completed", nullable=False)  # Completed, Ongoing

    student = relationship("Student", back_populates="internships")


class Hackathon(Base, TimestampMixin):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(String(200), nullable=False)
    organizer = Column(String(200), nullable=False)
    year = Column(Integer, nullable=False)
    achievement = Column(String(100), default="Participant", nullable=False)  # Winner, 1st Runner Up, Finalist, Participant
    project_title = Column(String(200), nullable=True)

    student = relationship("Student", back_populates="hackathons")


# Data Import Audit & Tracking
class ImportJob(Base, TimestampMixin):
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # csv, xlsx
    import_type = Column(String(50), nullable=False)  # students, academic_records, attendance
    status = Column(String(50), default="completed", nullable=False)  # completed, failed, partially_completed
    total_rows = Column(Integer, default=0, nullable=False)
    successful_rows = Column(Integer, default=0, nullable=False)
    failed_rows = Column(Integer, default=0, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User")
    errors = relationship("ImportError", back_populates="job", cascade="all, delete-orphan")


class ImportError(Base, TimestampMixin):
    __tablename__ = "import_errors"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=True)
    raw_data = Column(Text, nullable=True)
    error_message = Column(String(500), nullable=False)

    job = relationship("ImportJob", back_populates="errors")
