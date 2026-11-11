import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.clock import utcnow
from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class InterventionStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class InterventionType(str, enum.Enum):
    ACADEMIC_REMEDIAL = "ACADEMIC_REMEDIAL"
    ATTENDANCE_CONDONATION_COUNSELING = "ATTENDANCE_CONDONATION_COUNSELING"
    CAREER_SKILL_COACHING = "CAREER_SKILL_COACHING"
    BEHAVIORAL_WELLBEING = "BEHAVIORAL_WELLBEING"
    EXAMINATION_PREPARATION = "EXAMINATION_PREPARATION"
    PLACEMENT_INTERVIEW_PREPARATION = "PLACEMENT_INTERVIEW_PREPARATION"


class NotificationType(str, enum.Enum):
    RISK_ALERT = "RISK_ALERT"
    MENTOR_ASSIGNMENT = "MENTOR_ASSIGNMENT"
    NEW_RECOMMENDATION = "NEW_RECOMMENDATION"
    INTERVENTION_FOLLOWUP = "INTERVENTION_FOLLOWUP"
    STATUS_UPDATE = "STATUS_UPDATE"
    ADMINISTRATIVE_ANNOUNCEMENT = "ADMINISTRATIVE_ANNOUNCEMENT"


class ReportType(str, enum.Enum):
    STUDENT_PROGRESS = "STUDENT_PROGRESS"
    MENTOR_INTERVENTIONS = "MENTOR_INTERVENTIONS"
    DEPARTMENT_SUMMARY = "DEPARTMENT_SUMMARY"
    RISK_SUMMARY = "RISK_SUMMARY"
    PLACEMENT_READINESS = "PLACEMENT_READINESS"


class Intervention(Base, TimestampMixin, TenantMixin):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    risk_alert_id = Column(Integer, ForeignKey("risk_alerts.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    intervention_type = Column(String(50), nullable=False, default=InterventionType.ACADEMIC_REMEDIAL.value, index=True)
    priority = Column(String(20), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(30), default=InterventionStatus.OPEN.value, nullable=False, index=True)

    initial_notes = Column(Text, nullable=True)
    target_resolution_date = Column(Date, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_summary = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", backref="interventions")
    mentor = relationship("Mentor", backref="assigned_interventions")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    risk_alert = relationship("RiskAlert", backref="intervention")
    notes = relationship("InterventionNote", back_populates="intervention", cascade="all, delete-orphan", order_by="InterventionNote.created_at")
    followups = relationship(
        "InterventionFollowup",
        back_populates="intervention",
        cascade="all, delete-orphan",
        order_by="InterventionFollowup.scheduled_date",
    )


class InterventionNote(Base, TenantMixin):
    __tablename__ = "intervention_notes"

    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note_text = Column(Text, nullable=False)
    note_type = Column(
        String(30), default="GENERAL", nullable=False
    )  # GENERAL, OBSERVATION, ACTION_ITEM, PARENT_COMMUNICATION, COUNSELING
    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    intervention = relationship("Intervention", back_populates="notes")
    author = relationship("User")


class InterventionFollowup(Base, TenantMixin):
    __tablename__ = "intervention_followups"

    id = Column(Integer, primary_key=True, index=True)
    intervention_id = Column(Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="SET NULL"), nullable=True)

    scheduled_date = Column(Date, nullable=False, index=True)
    conducted_date = Column(DateTime, nullable=True)
    followup_status = Column(
        String(30), default="SCHEDULED", nullable=False, index=True
    )  # SCHEDULED, COMPLETED, MISSED, RESCHEDULED

    outcome_notes = Column(Text, nullable=True)
    student_feedback = Column(Text, nullable=True)
    next_review_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    intervention = relationship("Intervention", back_populates="followups")
    mentor = relationship("Mentor")


class Notification(Base, TenantMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default=NotificationType.STATUS_UPDATE.value, nullable=False, index=True)
    severity = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, SUCCESS, CRITICAL
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(50), nullable=True)
    action_url = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    user = relationship("User", backref="app_notifications")


class NotificationPreference(Base, TenantMixin):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    email_alerts_enabled = Column(Boolean, default=True)
    risk_notifications = Column(Boolean, default=True)
    recommendation_notifications = Column(Boolean, default=True)
    intervention_notifications = Column(Boolean, default=True)
    placement_notifications = Column(Boolean, default=True)
    announcement_notifications = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    user = relationship("User", backref="notification_preference")


class ReportExport(Base, TenantMixin):
    __tablename__ = "report_exports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    generated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)

    file_format = Column(String(20), default="CSV", nullable=False)  # CSV, PDF, JSON
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    report_data_json = Column(JSON, nullable=True)
    content_payload = Column(Text, nullable=True)  # Stored CSV or serialized content
    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    generator = relationship("User", foreign_keys=[generated_by])
    department = relationship("Department")
    student = relationship("Student")
