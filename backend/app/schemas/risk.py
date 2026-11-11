from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Indicators the evaluation engine can observe (services/risk_service._INDICATOR_OBSERVERS) and the
# comparison operators it understands. Rules using anything else would silently never trigger.
RISK_INDICATOR_TYPES = (
    "attendance_percentage", "assessment_percentage", "sgpa_drop", "backlog_count", "missing_assessments", "composite",
)
RISK_OPERATORS = ("<", "<=", ">", ">=", "==")


def _check_rule_fields(indicator_type: Optional[str], operator: Optional[str]) -> None:
    if indicator_type is not None and indicator_type not in RISK_INDICATOR_TYPES:
        raise ValueError(f"indicator_type must be one of: {', '.join(RISK_INDICATOR_TYPES)}")
    if operator is not None and operator not in RISK_OPERATORS:
        raise ValueError(f"operator must be one of: {' '.join(RISK_OPERATORS)}")


# ----------------------------------------------------
# Risk Rules Schemas
# ----------------------------------------------------
class RiskRuleBase(BaseModel):
    name: str = Field(..., max_length=150)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    category: str = Field(..., description="ATTENDANCE, ASSESSMENT, ACADEMIC, BACKLOG, COMPOSITE")
    severity: str = Field("MODERATE", description="NORMAL, MODERATE, HIGH, CRITICAL")
    indicator_type: str = Field(..., description="attendance_percentage, assessment_percentage, sgpa_drop, backlog_count, missing_assessments, composite")
    operator: str = Field("<", description="<, <=, >, >=, ==")
    threshold_value: float
    conditions_config: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None
    is_active: bool = True


class RiskRuleCreate(RiskRuleBase):
    @field_validator("indicator_type", "operator")
    @classmethod
    def _supported(cls, v: str, info):
        _check_rule_fields(v if info.field_name == "indicator_type" else None, v if info.field_name == "operator" else None)
        return v


class RiskRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    indicator_type: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[float] = None
    conditions_config: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("indicator_type", "operator")
    @classmethod
    def _supported(cls, v: Optional[str], info):
        _check_rule_fields(v if info.field_name == "indicator_type" else None, v if info.field_name == "operator" else None)
        return v


class RiskRuleResponse(RiskRuleBase):
    id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Risk Alert History & Assignment Schemas
# ----------------------------------------------------
class RiskAlertHistoryResponse(BaseModel):
    id: int
    alert_id: int
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    notes: Optional[str] = None
    performed_by_id: Optional[int] = None
    performed_by_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertAssignmentRequest(BaseModel):
    mentor_id: int
    notes: Optional[str] = None


class AlertAssignmentResponse(BaseModel):
    id: int
    alert_id: int
    mentor_id: int
    mentor_name: Optional[str] = None
    assigned_by_id: Optional[int] = None
    assigned_at: datetime
    notes: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Risk Alert Actions Schemas
# ----------------------------------------------------
class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None


class AlertAddNoteRequest(BaseModel):
    notes: str = Field(..., min_length=1)


class AlertResolveRequest(BaseModel):
    resolution_reason: str = Field(..., min_length=2)
    review_notes: Optional[str] = None


class AlertReopenRequest(BaseModel):
    reason: str = Field(..., min_length=2)


# ----------------------------------------------------
# Risk Alert Schemas
# ----------------------------------------------------
class RiskAlertResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_usn: Optional[str] = None
    student_srn: Optional[str] = None
    student_department: Optional[str] = None
    student_semester: Optional[int] = None
    student_section: Optional[str] = None
    rule_id: int
    rule_name: Optional[str] = None
    rule_code: Optional[str] = None
    rule_category: Optional[str] = None
    severity: str
    status: str
    observed_value: float
    observed_display: Optional[str] = None
    threshold_value: float
    threshold_display: Optional[str] = None
    academic_period: Optional[str] = None
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    detected_date: datetime
    is_system_generated: bool
    ai_explanation: str
    suggested_action: Optional[str] = None
    assigned_mentor_id: Optional[int] = None
    assigned_mentor_name: Optional[str] = None
    review_notes: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAlertListResponse(BaseModel):
    items: List[RiskAlertResponse]
    total: int
    skip: int
    limit: int


class RiskAlertDetailResponse(BaseModel):
    alert: RiskAlertResponse
    history: List[RiskAlertHistoryResponse]
    assignments: List[AlertAssignmentResponse]


class StudentRiskProfileResponse(BaseModel):
    student_id: int
    student_name: str
    usn: str
    srn: Optional[str] = None
    department: str
    current_semester: int
    section: str
    overall_cgpa: float
    overall_attendance: float
    active_alerts_count: int
    highest_severity: str
    alerts: List[RiskAlertResponse] = []


# ----------------------------------------------------
# Risk Evaluation Execution
# ----------------------------------------------------
class RiskEvaluationTriggerRequest(BaseModel):
    student_id: Optional[int] = None  # None evaluates all students
    department_id: Optional[int] = None
    run_type: str = "MANUAL"  # MANUAL, BATCH, STUDENT_UPDATE


class RiskEvaluationResponse(BaseModel):
    id: int
    run_type: str
    status: str
    evaluated_students_count: int
    alerts_generated_count: int
    critical_count: int
    high_count: int
    moderate_count: int
    normal_count: int
    summary: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Risk Statistics & Dashboard Analytics
# ----------------------------------------------------
class SeverityCount(BaseModel):
    critical: int = 0
    high: int = 0
    moderate: int = 0
    normal: int = 0


class RiskStatisticsResponse(BaseModel):
    total_active_alerts: int
    total_students_at_risk: int
    severity_distribution: SeverityCount
    status_distribution: Dict[str, int]
    department_distribution: List[Dict[str, Any]]
    semester_distribution: List[Dict[str, Any]]
    rule_distribution: List[Dict[str, Any]]
    recent_evaluations: List[RiskEvaluationResponse] = []


# ----------------------------------------------------
# In-App Notifications
# ----------------------------------------------------
class InAppNotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    severity: str
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
