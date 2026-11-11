from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.clock import utcnow
from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class RiskRule(Base, TimestampMixin, TenantMixin):
    __tablename__ = "risk_rules"
    __table_args__ = (UniqueConstraint("university_id", "code", name="uq_risk_rules_tenant_code"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # ATTENDANCE, ASSESSMENT, ACADEMIC, BACKLOG, COMPOSITE
    severity = Column(String(20), default="MODERATE", nullable=False)  # NORMAL, MODERATE, HIGH, CRITICAL
    indicator_type = Column(
        String(50), nullable=False
    )  # attendance_percentage, assessment_percentage, sgpa_drop, backlog_count, missing_assessments, composite
    operator = Column(String(10), default="<", nullable=False)  # <, <=, >, >=, ==
    threshold_value = Column(Float, nullable=False)
    conditions_config = Column(JSON, nullable=True)  # custom multi-parameter rules
    suggested_action = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    alerts = relationship("RiskAlert", back_populates="rule", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])


class RiskAlert(Base, TimestampMixin, TenantMixin):
    __tablename__ = "risk_alerts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("risk_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluation_id = Column(Integer, ForeignKey("risk_evaluations.id", ondelete="SET NULL"), nullable=True, index=True)
    severity = Column(String(20), nullable=False)  # NORMAL, MODERATE, HIGH, CRITICAL
    status = Column(
        String(30), default="FLAGGED", nullable=False
    )  # FLAGGED, ACKNOWLEDGED, UNDER_REVIEW, RESOLVED, DISMISSED
    observed_value = Column(Float, nullable=False)
    observed_display = Column(String(100), nullable=True)
    threshold_value = Column(Float, nullable=False)
    threshold_display = Column(String(100), nullable=True)
    academic_period = Column(String(100), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    detected_date = Column(DateTime, default=utcnow, nullable=False)
    is_system_generated = Column(Boolean, default=True, nullable=False)
    ai_explanation = Column(Text, nullable=False)
    suggested_action = Column(String(255), nullable=True)
    assigned_mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_reason = Column(String(255), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="risk_alerts")
    rule = relationship("RiskRule", back_populates="alerts")
    evaluation = relationship("RiskEvaluation", back_populates="alerts")
    subject = relationship("Subject")
    assigned_mentor = relationship("Mentor")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    history = relationship(
        "RiskAlertHistory",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="desc(RiskAlertHistory.created_at)",
    )
    assignments = relationship("AlertAssignment", back_populates="alert", cascade="all, delete-orphan")


class RiskEvaluation(Base, TimestampMixin, TenantMixin):
    __tablename__ = "risk_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String(50), default="MANUAL", nullable=False)  # MANUAL, STUDENT_UPDATE, SCHEDULED, BATCH
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    evaluated_students_count = Column(Integer, default=0, nullable=False)
    alerts_generated_count = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    moderate_count = Column(Integer, default=0, nullable=False)
    normal_count = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="COMPLETED", nullable=False)
    summary = Column(JSON, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    initiated_by = relationship("User", foreign_keys=[initiated_by_id])
    alerts = relationship("RiskAlert", back_populates="evaluation")


class RiskAlertHistory(Base, TimestampMixin, TenantMixin):
    __tablename__ = "risk_alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("risk_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(
        String(50), nullable=False
    )  # FLAGGED, ACKNOWLEDGED, NOTE_ADDED, ASSIGNED, STATUS_CHANGED, RESOLVED, REOPENED
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    alert = relationship("RiskAlert", back_populates="history")
    performed_by = relationship("User", foreign_keys=[performed_by_id])


class AlertAssignment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "alert_assignments"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("risk_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=utcnow, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, COMPLETED, REASSIGNED

    # Relationships
    alert = relationship("RiskAlert", back_populates="assignments")
    mentor = relationship("Mentor")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class InAppNotification(Base, TimestampMixin, TenantMixin):
    __tablename__ = "in_app_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        String(50), default="RISK_ALERT", nullable=False
    )  # RISK_ALERT, ALERT_ASSIGNED, ALERT_RESOLVED, SYSTEM
    severity = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, CRITICAL
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(50), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User")
