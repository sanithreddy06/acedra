from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.access import own_student_record
from app.core.database import get_db
from app.models.profile import Mentor, Student
from app.models.risk import RiskAlert
from app.models.user import User, UserRole
from app.schemas.risk import (
    AlertAcknowledgeRequest,
    AlertAddNoteRequest,
    AlertAssignmentRequest,
    AlertReopenRequest,
    AlertResolveRequest,
    InAppNotificationResponse,
    RiskAlertDetailResponse,
    RiskAlertListResponse,
    RiskAlertResponse,
    RiskEvaluationResponse,
    RiskEvaluationTriggerRequest,
    RiskRuleCreate,
    RiskRuleResponse,
    RiskRuleUpdate,
    RiskStatisticsResponse,
    StudentRiskProfileResponse,
)
from app.services.risk_service import (
    ACTIVE_ALERT_STATUSES,
    RiskService,
    alert_detail,
    alert_summary,
    highest_active_severity,
)

router = APIRouter(prefix="/risk", tags=["Risk Early-Warning Intelligence"])


def _get_alert_or_404(db: Session, alert_id: int) -> RiskAlert:
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return alert


# -----------------------------------------------------------------------------
# 1. RISK RULES MANAGEMENT
# -----------------------------------------------------------------------------
@router.get("/rules", response_model=List[RiskRuleResponse])
def get_risk_rules(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all configurable risk rules."""
    # Ensure canonical default rules are initialized
    RiskService.seed_default_rules_if_needed(db, current_user.id)
    rules = RiskService.get_rules(db, category=category, is_active=is_active)
    return rules


@router.post("/rules", response_model=RiskRuleResponse, status_code=status.HTTP_201_CREATED)
def create_risk_rule(
    rule_in: RiskRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Administrator creates a custom risk rule with specific thresholds."""
    existing = RiskService.get_rules(db)
    if any(r.code == rule_in.code for r in existing):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rule with code '{rule_in.code}' already exists.",
        )
    return RiskService.create_rule(db, rule_in.model_dump(), user_id=current_user.id)


@router.put("/rules/{rule_id}", response_model=RiskRuleResponse)
def update_risk_rule(
    rule_id: int,
    rule_in: RiskRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Administrator updates rule thresholds, activation status, or parameters."""
    rule = RiskService.get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk rule not found.")
    return RiskService.update_rule(db, rule, rule_in.model_dump(exclude_unset=True))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Administrator deletes a risk rule."""
    rule = RiskService.get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk rule not found.")
    RiskService.delete_rule(db, rule)
    return None


# -----------------------------------------------------------------------------
# 2. RISK EVALUATION ENGINE TRIGGER
# -----------------------------------------------------------------------------
@router.post("/evaluate", response_model=RiskEvaluationResponse)
def trigger_risk_evaluation(
    eval_req: RiskEvaluationTriggerRequest = RiskEvaluationTriggerRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor")),
):
    """
    Executes rule-based risk evaluation across active students.
    Prevents duplicate active alerts for the same rule and student.
    """
    evaluation = RiskService.evaluate_risk(
        db=db,
        student_id=eval_req.student_id,
        department_id=eval_req.department_id,
        run_type=eval_req.run_type,
        user_id=current_user.id,
    )
    return evaluation


# -----------------------------------------------------------------------------
# 3. RISK ALERTS LISTING & DETAIL
# -----------------------------------------------------------------------------
@router.get("/alerts", response_model=RiskAlertListResponse)
def get_risk_alerts(
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    rule_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Filterable list of risk alerts with role-scoped access control.
    """
    if current_user.role == UserRole.STUDENT.value:  # students only ever see their own alerts
        student = own_student_record(db, current_user)
        if not student:
            return {"items": [], "total": 0, "skip": skip, "limit": limit}
        student_id = student.id

    alerts, total = RiskService.get_alerts(
        db=db,
        status=status_filter,
        severity=severity,
        department_id=department_id,
        semester=semester,
        rule_id=rule_id,
        student_id=student_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    return {"items": [alert_summary(a) for a in alerts], "total": total, "skip": skip, "limit": limit}


@router.get("/alerts/{alert_id}", response_model=RiskAlertDetailResponse)
def get_risk_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve comprehensive alert detail, audit history, and mentor assignments."""
    alert = _get_alert_or_404(db, alert_id)
    is_student = current_user.role == UserRole.STUDENT.value
    if is_student and (not alert.student or alert.student.user_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students can only view their own alerts.",
        )

    return alert_detail(alert)


# -----------------------------------------------------------------------------
# 4. ALERT WORKFLOW ACTIONS
# -----------------------------------------------------------------------------
@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    req: AlertAcknowledgeRequest = AlertAcknowledgeRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor")),
):
    """Authorized faculty/mentor acknowledges an active early warning alert."""
    alert = _get_alert_or_404(db, alert_id)
    updated = RiskService.acknowledge_alert(db, alert, current_user.id, req.notes)
    return {"message": "Alert acknowledged successfully.", "status": updated.status}


@router.post("/alerts/{alert_id}/notes")
def add_alert_note(
    alert_id: int,
    req: AlertAddNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor")),
):
    """Add a documented review note to an alert."""
    alert = _get_alert_or_404(db, alert_id)
    updated = RiskService.add_review_note(db, alert, current_user.id, req.notes)
    return {"message": "Review note added.", "review_notes": updated.review_notes}


@router.post("/alerts/{alert_id}/assign")
def assign_alert_mentor(
    alert_id: int,
    req: AlertAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor")),
):
    """Assign alert to a designated mentor for targeted academic support."""
    alert = _get_alert_or_404(db, alert_id)
    mentor = db.query(Mentor).filter(Mentor.id == req.mentor_id).first()
    if not mentor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor not found.")

    updated = RiskService.assign_mentor(db, alert, req.mentor_id, current_user.id, req.notes)
    return {"message": "Alert assigned to mentor.", "status": updated.status}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    req: AlertResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor")),
):
    """Resolve alert once supportive intervention is completed."""
    alert = _get_alert_or_404(db, alert_id)
    updated = RiskService.resolve_alert(db, alert, current_user.id, req.resolution_reason, req.review_notes)
    return {"message": "Alert marked as resolved.", "status": updated.status}


@router.post("/alerts/{alert_id}/reopen")
def reopen_alert(
    alert_id: int,
    req: AlertReopenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor")),
):
    """Reopen a previously resolved alert if condition re-emerges."""
    alert = _get_alert_or_404(db, alert_id)
    updated = RiskService.reopen_alert(db, alert, current_user.id, req.reason)
    return {"message": "Alert reopened.", "status": updated.status}


# -----------------------------------------------------------------------------
# 5. STUDENT RISK SUMMARY
# -----------------------------------------------------------------------------
@router.get("/students/{student_id}", response_model=StudentRiskProfileResponse)
def get_student_risk_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full risk profile for an individual student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

    if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students can only access their own profile.",
        )

    alerts, _ = RiskService.get_alerts(db, student_id=student.id, limit=100)
    return StudentRiskProfileResponse(
        student_id=student.id,
        student_name=student.user.full_name if student.user else student.roll_number,
        usn=student.usn,
        srn=student.srn,
        department=student.department.name if student.department else "",
        current_semester=student.current_semester,
        section=student.section,
        overall_cgpa=student.cgpa,
        overall_attendance=student.attendance_percentage,
        active_alerts_count=sum(1 for a in alerts if a.status in ACTIVE_ALERT_STATUSES),
        highest_severity=highest_active_severity(alerts),
        alerts=[RiskAlertResponse(**alert_summary(a)) for a in alerts],
    )


# -----------------------------------------------------------------------------
# 6. RISK STATISTICS DASHBOARD
# -----------------------------------------------------------------------------
@router.get("/statistics", response_model=RiskStatisticsResponse)
def get_risk_statistics(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty", "mentor", "placement_officer")),
):
    """Executive & faculty aggregate early-warning statistics."""
    stats = RiskService.get_risk_statistics(db, department_id=department_id)
    return stats


# -----------------------------------------------------------------------------
# 7. IN-APP NOTIFICATIONS
# -----------------------------------------------------------------------------
@router.get("/notifications", response_model=List[InAppNotificationResponse])
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fetch notifications for the logged in user."""
    return RiskService.get_user_notifications(db, current_user.id, unread_only=unread_only, limit=limit)


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a notification as read."""
    success = RiskService.mark_notification_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return {"message": "Notification marked as read."}
