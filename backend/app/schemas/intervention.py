from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.intervention import (
    InterventionStatus,
    InterventionType,
    NotificationType,
    ReportType,
)


class InterventionNoteCreate(BaseModel):
    note_text: str = Field(..., min_length=2)
    note_type: str = "GENERAL"  # GENERAL, OBSERVATION, ACTION_ITEM, PARENT_COMMUNICATION, COUNSELING


class InterventionNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intervention_id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_role: Optional[str] = None
    note_text: str
    note_type: str
    created_at: datetime


class InterventionFollowupCreate(BaseModel):
    scheduled_date: date
    mentor_id: Optional[int] = None
    outcome_notes: Optional[str] = None
    next_review_date: Optional[date] = None


class InterventionFollowupUpdate(BaseModel):
    followup_status: str  # SCHEDULED, COMPLETED, MISSED, RESCHEDULED
    outcome_notes: Optional[str] = None
    student_feedback: Optional[str] = None
    next_review_date: Optional[date] = None


class InterventionFollowupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intervention_id: int
    mentor_id: Optional[int] = None
    mentor_name: Optional[str] = None
    scheduled_date: date
    conducted_date: Optional[datetime] = None
    followup_status: str
    outcome_notes: Optional[str] = None
    student_feedback: Optional[str] = None
    next_review_date: Optional[date] = None
    created_at: datetime


class InterventionCreate(BaseModel):
    student_id: int
    mentor_id: Optional[int] = None
    risk_alert_id: Optional[int] = None
    title: str = Field(..., min_length=3, max_length=255)
    intervention_type: str = InterventionType.ACADEMIC_REMEDIAL.value
    priority: str = "MEDIUM"  # LOW, MEDIUM, HIGH, URGENT
    initial_notes: Optional[str] = None
    target_resolution_date: Optional[date] = None


class InterventionUpdate(BaseModel):
    mentor_id: Optional[int] = None
    title: Optional[str] = None
    priority: Optional[str] = None
    initial_notes: Optional[str] = None
    target_resolution_date: Optional[date] = None


class InterventionStatusUpdate(BaseModel):
    status: str  # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
    resolution_summary: Optional[str] = None


class InterventionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: Optional[str] = None
    student_usn: Optional[str] = None
    student_department: Optional[str] = None
    student_semester: Optional[int] = None
    mentor_id: Optional[int] = None
    mentor_name: Optional[str] = None
    assigned_by: Optional[int] = None
    assigned_by_name: Optional[str] = None
    risk_alert_id: Optional[int] = None
    title: str
    intervention_type: str
    priority: str
    status: str
    initial_notes: Optional[str] = None
    target_resolution_date: Optional[date] = None
    resolved_at: Optional[datetime] = None
    resolution_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    notes_count: Optional[int] = 0
    followups_count: Optional[int] = 0


class InterventionDetailResponse(InterventionResponse):
    notes: List[InterventionNoteResponse] = []
    followups: List[InterventionFollowupResponse] = []


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    severity: str
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    action_url: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email_alerts_enabled: bool
    risk_notifications: bool
    recommendation_notifications: bool
    intervention_notifications: bool
    placement_notifications: bool
    announcement_notifications: bool
    updated_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    email_alerts_enabled: Optional[bool] = None
    risk_notifications: Optional[bool] = None
    recommendation_notifications: Optional[bool] = None
    intervention_notifications: Optional[bool] = None
    placement_notifications: Optional[bool] = None
    announcement_notifications: Optional[bool] = None


class ReportExportCreate(BaseModel):
    report_type: str  # STUDENT_PROGRESS, MENTOR_INTERVENTIONS, DEPARTMENT_SUMMARY, RISK_SUMMARY, PLACEMENT_READINESS
    file_format: str = "CSV"  # CSV, PDF, JSON
    department_id: Optional[int] = None
    student_id: Optional[int] = None


class ReportExportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    title: str
    generated_by: Optional[int] = None
    generated_by_name: Optional[str] = None
    department_id: Optional[int] = None
    student_id: Optional[int] = None
    file_format: str
    file_name: str
    file_size_bytes: int
    created_at: datetime
