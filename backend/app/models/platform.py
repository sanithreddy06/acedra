"""
Platform-level (ACEDRA internal) models: university tenants, institutional domains,
ACEDRA employees and their assignments, auditable student-data access grants,
institutional enquiries and onboarding, invitations, auth tokens, the email
outbox and account-provisioning requests.

These tables are NOT tenant-scoped automatically; access is enforced explicitly
in the platform and tenant-admin services.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


def _now():
    return datetime.now(timezone.utc)


class TenantStatus:
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    ALL = [ONBOARDING, ACTIVE, SUSPENDED, INACTIVE]


ALL_MODULES = [
    "student_intelligence",
    "risk_identification",
    "recommendations",
    "placement_readiness",
    "ai_assistant",
    "interventions",
]

DEFAULT_ACADEMIC_STRUCTURE = {
    "term_label": "Semester",
    "terms_per_year": 2,
    "programme_duration_years": 4,
    "grading_scale": "10-point",
    "cgpa_max": 10.0,
    "pass_grade_point": 4.0,
    "minimum_attendance_percent": 75,
    "internal_assessment_max": 50,
}


class University(Base, TimestampMixin):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=False)
    slug = Column(String(80), unique=True, index=True, nullable=False)
    official_website = Column(String(255), nullable=True)
    institution_type = Column(String(80), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(String(30), default=TenantStatus.ONBOARDING, index=True, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)

    # Branding
    logo_url = Column(String(500), nullable=True)
    brand_color = Column(String(20), default="#3F5A40", nullable=False)
    tagline = Column(String(255), nullable=True)

    # Configuration (per-tenant; never hard-coded in application logic)
    academic_structure = Column(JSON, default=lambda: dict(DEFAULT_ACADEMIC_STRUCTURE), nullable=False)
    enabled_modules = Column(JSON, default=lambda: list(ALL_MODULES), nullable=False)
    document_categories = Column(JSON, default=list, nullable=False)
    notification_settings = Column(JSON, default=dict, nullable=False)
    workflow_settings = Column(JSON, default=dict, nullable=False)
    enforce_email_domains = Column(Boolean, default=True, nullable=False)

    # Student email provisioning: "existing" (university provides) or "rio_assisted" (chargeable add-on)
    student_email_mode = Column(String(30), default="existing", nullable=False)

    # Dedicated ACEDRA employee (explicitly recorded). History lives in employee_assignments.
    primary_employee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_universities_primary_employee"), nullable=True)

    enquiry_id = Column(Integer, ForeignKey("enquiries.id", ondelete="SET NULL", use_alter=True, name="fk_universities_enquiry"), nullable=True)
    agreement_reference = Column(String(120), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", use_alter=True, name="fk_universities_created_by"), nullable=True)

    domains = relationship("UniversityDomain", back_populates="university", cascade="all, delete-orphan")
    primary_employee = relationship("User", foreign_keys=[primary_employee_id])
    assignments = relationship("EmployeeAssignment", back_populates="university", cascade="all, delete-orphan")


class UniversityDomain(Base, TimestampMixin):
    __tablename__ = "university_domains"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    purpose = Column(String(20), default="all", nullable=False)  # all | staff | student
    is_primary = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    university = relationship("University", back_populates="domains")


class EmployeeProfile(Base, TimestampMixin):
    """ACEDRA internal employee details and permission categories.

    Permission categories (kept deliberately separate):
      * tenant.configure   — configure assigned tenants (branding, domains, modules, structure)
      * tenant.coordinate  — onboarding, enquiries, meeting notes, provisioning requests
    Student-data access is NEVER a standing permission; it requires a StudentDataAccessGrant.
    """
    __tablename__ = "employee_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    employee_code = Column(String(40), unique=True, nullable=False)
    title = Column(String(150), nullable=True)
    phone = Column(String(40), nullable=True)
    permissions = Column(JSON, default=lambda: ["tenant.configure", "tenant.coordinate"], nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User")


class EmployeeAssignment(Base, TimestampMixin):
    __tablename__ = "employee_assignments"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False)
    employee_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assignment_role = Column(String(20), default="primary", nullable=False)  # primary | support
    is_active = Column(Boolean, default=True, nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, default=_now, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    university = relationship("University", back_populates="assignments")
    employee = relationship("User", foreign_keys=[employee_user_id])


class StudentDataAccessGrant(Base, TimestampMixin):
    """Explicit, time-boxed, auditable permission for an ACEDRA employee to read student data."""
    __tablename__ = "student_data_access_grants"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False)
    employee_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    scope = Column(String(50), default="student_directory_read", nullable=False)
    reason = Column(Text, nullable=False)
    university_authorised_by = Column(String(255), nullable=False)  # named institutional approver
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    starts_at = Column(DateTime, default=_now, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    employee = relationship("User", foreign_keys=[employee_user_id])
    university = relationship("University")


class EnquiryStatus:
    NEW = "new"
    UNDER_REVIEW = "under_review"
    CONTACTED = "contacted"
    MEETING_SCHEDULED = "meeting_scheduled"
    REQUIREMENTS_GATHERING = "requirements_gathering"
    PROPOSAL = "proposal_agreement"
    APPROVED = "approved"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    REJECTED = "rejected"
    CLOSED = "closed"

    ORDER = [NEW, UNDER_REVIEW, CONTACTED, MEETING_SCHEDULED, REQUIREMENTS_GATHERING, PROPOSAL, APPROVED,
             ONBOARDING, ACTIVE]
    TERMINAL = [REJECTED, CLOSED]
    ALL = ORDER + TERMINAL
    LABELS = {
        NEW: "New", UNDER_REVIEW: "Under Review", CONTACTED: "Contacted", MEETING_SCHEDULED: "Meeting Scheduled",
        REQUIREMENTS_GATHERING: "Requirements Gathering", PROPOSAL: "Proposal / Agreement", APPROVED: "Approved",
        ONBOARDING: "Onboarding", ACTIVE: "Active", REJECTED: "Rejected", CLOSED: "Closed",
    }


class Enquiry(Base, TimestampMixin):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True)
    reference = Column(String(30), unique=True, index=True, nullable=False)
    status = Column(String(40), default=EnquiryStatus.NEW, index=True, nullable=False)

    # Institutional details
    university_name = Column(String(255), nullable=False)
    official_website = Column(String(255), nullable=True)
    institution_type = Column(String(80), nullable=False)
    location = Column(String(255), nullable=False)
    student_population = Column(String(40), nullable=False)
    department_count = Column(Integer, nullable=True)
    campus_count = Column(Integer, nullable=True)

    # Contact
    contact_name = Column(String(255), nullable=False)
    contact_designation = Column(String(150), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(40), nullable=True)
    preferred_contact_method = Column(String(20), default="email", nullable=False)

    # Requirements
    requested_modules = Column(JSON, default=list, nullable=False)
    existing_sis = Column(String(255), nullable=True)
    existing_academic_systems = Column(String(255), nullable=True)
    has_student_emails = Column(Boolean, default=True, nullable=False)
    email_provisioning = Column(String(30), default="existing", nullable=False)  # existing | rio_assisted
    accounts_required = Column(Integer, nullable=True)
    institutional_requirements = Column(Text, nullable=True)
    expected_outcomes = Column(Text, nullable=True)
    additional_information = Column(Text, nullable=True)
    consent_to_contact = Column(Boolean, default=False, nullable=False)

    # Internal handling
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    finalized_requirements = Column(Text, nullable=True)
    agreement_reference = Column(String(120), nullable=True)
    agreement_recorded_at = Column(DateTime, nullable=True)
    agreed_modules = Column(JSON, default=list, nullable=False)
    email_service_estimate = Column(JSON, nullable=True)  # documented add-on estimate, not a charge
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="SET NULL"), nullable=True)
    source_ip_hash = Column(String(64), nullable=True)

    owner = relationship("User", foreign_keys=[owner_id])
    activities = relationship("EnquiryActivity", back_populates="enquiry", cascade="all, delete-orphan",
                              order_by="EnquiryActivity.created_at")


class EnquiryActivity(Base):
    __tablename__ = "enquiry_activities"

    id = Column(Integer, primary_key=True)
    enquiry_id = Column(Integer, ForeignKey("enquiries.id", ondelete="CASCADE"), index=True, nullable=False)
    kind = Column(String(30), nullable=False)  # status_change | note | meeting | requirements | agreement | system
    from_status = Column(String(40), nullable=True)
    to_status = Column(String(40), nullable=True)
    body = Column(Text, nullable=True)
    meeting_at = Column(DateTime, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    enquiry = relationship("Enquiry", back_populates="activities")
    author = relationship("User")


class Invitation(Base, TimestampMixin):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    email = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False)
    token_hash = Column(String(128), unique=True, index=True, nullable=False)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    purpose = Column(String(30), nullable=False)  # password_reset | email_verification
    token_hash = Column(String(128), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)


class EmailMessage(Base):
    """Outbound email log. In development the message is only logged (never sent)."""
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=True)
    to_email = Column(String(255), index=True, nullable=False)
    subject = Column(String(255), nullable=False)
    body_text = Column(Text, nullable=False)
    template = Column(String(50), nullable=False)
    provider = Column(String(30), default="log", nullable=False)
    status = Column(String(20), default="logged", nullable=False)  # logged | sent | failed
    error = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)


class ProvisioningStatus:
    REQUESTED = "requested"
    ESTIMATED = "estimated"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ALL = [REQUESTED, ESTIMATED, APPROVED, IN_PROGRESS, COMPLETED, CANCELLED]


class AccountProvisioningRequest(Base, TimestampMixin):
    """Recorded account-provisioning requirement. ACEDRA does not create real mailboxes in this build."""
    __tablename__ = "account_provisioning_requests"

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False)
    method = Column(String(30), nullable=False)  # existing | rio_assisted
    accounts_requested = Column(Integer, nullable=False)
    accounts_completed = Column(Integer, default=0, nullable=False)
    is_chargeable = Column(Boolean, default=False, nullable=False)
    estimated_cost = Column(Float, nullable=True)
    currency = Column(String(8), default="INR", nullable=False)
    status = Column(String(20), default=ProvisioningStatus.REQUESTED, nullable=False)
    notes = Column(Text, nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    university = relationship("University")


class StaffStudentAccess(Base, TimestampMixin):
    """Explicit authorisation for a faculty member to view a student outside their teaching assignments."""
    __tablename__ = "staff_student_access"
    __table_args__ = (UniqueConstraint("user_id", "student_id", name="uq_staff_student_access"),)

    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False)
    reason = Column(String(255), nullable=True)
    granted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


Index("ix_enquiry_status_created", Enquiry.status, Enquiry.created_at)
