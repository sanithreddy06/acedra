from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Date as SqlDate
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class SkillEvidence(Base, TimestampMixin, TenantMixin):
    """
    Supporting evidence, projects, certifications, or code repositories submitted for a skill.
    Allows students to back self-reported proficiencies with verifiable artifacts.
    """
    __tablename__ = "skill_evidence"

    id = Column(Integer, primary_key=True, index=True)
    student_skill_id = Column(Integer, ForeignKey("student_skills.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(50), default="PROJECT", nullable=False)  # PROJECT, CERTIFICATION, GITHUB_REPO, LIVE_DEMO, PUBLICATION, OTHER
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    certification_id = Column(Integer, ForeignKey("certifications.id", ondelete="SET NULL"), nullable=True)
    verification_status = Column(String(50), default="SELF_REPORTED", nullable=False)  # SELF_REPORTED, PENDING_REVIEW, VERIFIED, REJECTED
    verified_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_feedback = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="skill_evidences")
    student_skill = relationship("StudentSkill", back_populates="evidence_records")
    project = relationship("Project")
    certification = relationship("Certification")
    verified_by_user = relationship("User", foreign_keys=[verified_by_user_id])


class CareerRole(Base, TimestampMixin, TenantMixin):
    """
    Configurable career roles against which student profiles are evaluated for placement readiness.
    Curated by Placement Officers and Academic Administrators.
    """
    __tablename__ = "career_roles"
    __table_args__ = (UniqueConstraint("university_id", "code", name="uq_career_roles_tenant_code"),)

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), index=True, nullable=False)  # e.g., SOFTWARE_DEVELOPER, FULL_STACK_DEVELOPER, AI_ML_ENGINEER
    title = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    min_experience_level = Column(String(50), default="Entry Level", nullable=False)  # Entry Level, Junior, Associate
    average_salary_range = Column(String(50), default="6-12 LPA", nullable=False)
    industry_demand = Column(String(50), default="High", nullable=False)  # Critical, High, Moderate
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    department = relationship("Department")
    role_skills = relationship("RoleSkill", back_populates="role", cascade="all, delete-orphan")
    opportunities = relationship("PlacementOpportunity", back_populates="role")


class RoleSkill(Base, TimestampMixin, TenantMixin):
    """
    Skills required or preferred for a specific Career Role, with target proficiency levels.
    """
    __tablename__ = "role_skills"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    min_proficiency = Column(String(50), default="Intermediate", nullable=False)  # Beginner, Intermediate, Advanced, Expert
    importance = Column(String(50), default="CORE", nullable=False)  # CRITICAL, CORE, PREFERRED
    importance_weight = Column(Float, default=2.0, nullable=False)  # e.g. Critical=3.0, Core=2.0, Preferred=1.0
    is_mandatory = Column(Boolean, default=True, nullable=False)

    # Relationships
    role = relationship("CareerRole", back_populates="role_skills")
    skill = relationship("Skill")


class PlacementOpportunity(Base, TimestampMixin, TenantMixin):
    """
    Job or Internship drives posted by Placement Officers with explicit eligibility criteria.
    """
    __tablename__ = "placement_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(150), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    opportunity_type = Column(String(50), default="JOB", nullable=False)  # JOB, INTERNSHIP
    role_id = Column(Integer, ForeignKey("career_roles.id", ondelete="SET NULL"), nullable=True)
    location = Column(String(100), default="Bangalore", nullable=False)
    work_mode = Column(String(50), default="HYBRID", nullable=False)  # ONSITE, REMOTE, HYBRID
    ctc_stipend = Column(String(100), nullable=False)  # e.g., "14.5 LPA" or "45,000/month"
    min_cgpa = Column(Float, default=6.5, nullable=False)
    max_backlogs = Column(Integer, default=0, nullable=False)
    min_attendance = Column(Float, default=75.0, nullable=False)
    eligible_departments = Column(JSON, default=list, nullable=False)  # e.g. ["CSE", "AI_DS", "ECE"]
    eligible_semesters = Column(JSON, default=list, nullable=False)    # e.g. [6, 7, 8]
    application_deadline = Column(SqlDate, nullable=False)
    open_positions = Column(Integer, default=5, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="OPEN", nullable=False)  # OPEN, CLOSED, ARCHIVED
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    role = relationship("CareerRole", back_populates="opportunities")
    requirements = relationship("OpportunityRequirement", back_populates="opportunity", cascade="all, delete-orphan")
    applications = relationship("StudentApplication", back_populates="opportunity", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_user_id])


class OpportunityRequirement(Base, TimestampMixin, TenantMixin):
    """
    Specific skill requirements for a given job/internship opportunity.
    """
    __tablename__ = "opportunity_requirements"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("placement_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    min_proficiency = Column(String(50), default="Intermediate", nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)

    # Relationships
    opportunity = relationship("PlacementOpportunity", back_populates="requirements")
    skill = relationship("Skill")


class StudentApplication(Base, TimestampMixin, TenantMixin):
    """
    Tracks a student's application to a placement job or internship opportunity.
    """
    __tablename__ = "student_applications"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("placement_opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="APPLIED", nullable=False)  # APPLIED, SHORTLISTED, INTERVIEW_SCHEDULED, OFFERED, REJECTED, WITHDRAWN
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resume_url = Column(String(500), nullable=True)
    cover_notes = Column(Text, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    readiness_score_at_application = Column(Float, default=0.0, nullable=False)

    # Relationships
    opportunity = relationship("PlacementOpportunity", back_populates="applications")
    student = relationship("Student", back_populates="applications")
