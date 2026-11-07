from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User
from app.models.profile import Student, Mentor
from app.schemas.risk import (
    RiskRuleCreate,
    RiskRuleUpdate,
    RiskRuleResponse,
    RiskAlertResponse,
    RiskAlertHistoryResponse,
    AlertAcknowledgeRequest,
    AlertAddNoteRequest,
    AlertAssignmentRequest,
    AlertAssignmentResponse,
    AlertResolveRequest,
    AlertReopenRequest,
    StudentRiskProfileResponse,
    RiskEvaluationTriggerRequest,
    RiskEvaluationResponse,
    RiskStatisticsResponse,
    InAppNotificationResponse,
)
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["Risk Early-Warning Intelligence"])


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
@router.get("/alerts")
def get_risk_alerts(
    status: Optional[str] = Query(None),
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
    # Role-based scoping: Student can only view their own alerts
    if current_user.role == "student":
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return {"items": [], "total": 0, "skip": skip, "limit": limit}
        student_id = student.id

    # Mentor scoping if requested
    mentor_id = None
    if current_user.role == "mentor":
        mentor = db.query(Mentor).filter(Mentor.user_id == current_user.id).first()
        # mentors see all dept alerts by default, or filtered

    alerts, total = RiskService.get_alerts(
        db=db,
        status=status,
        severity=severity,
        department_id=department_id,
        semester=semester,
        rule_id=rule_id,
        student_id=student_id,
        mentor_id=mentor_id,
        search=search,
        skip=skip,
        limit=limit,
    )

    items = []
    for a in alerts:
        items.append({
            "id": a.id,
            "student_id": a.student_id,
            "student_name": a.student.user.full_name if a.student and a.student.user else a.student.roll_number,
            "student_usn": a.student.usn if a.student else None,
            "student_srn": a.student.srn if a.student else None,
            "student_department": a.student.department.name if a.student and a.student.department else None,
            "student_semester": a.student.current_semester if a.student else None,
            "student_section": a.student.section if a.student else None,
            "rule_id": a.rule_id,
            "rule_name": a.rule.name if a.rule else None,
            "rule_code": a.rule.code if a.rule else None,
            "rule_category": a.rule.category if a.rule else None,
            "severity": a.severity,
            "status": a.status,
            "observed_value": a.observed_value,
            "observed_display": a.observed_display,
            "threshold_value": a.threshold_value,
            "threshold_display": a.threshold_display,
            "academic_period": a.academic_period,
            "subject_id": a.subject_id,
            "subject_name": a.subject.name if a.subject else None,
            "detected_date": a.detected_date,
            "is_system_generated": a.is_system_generated,
            "ai_explanation": a.ai_explanation,
            "suggested_action": a.suggested_action,
            "assigned_mentor_id": a.assigned_mentor_id,
            "assigned_mentor_name": a.assigned_mentor.user.full_name if a.assigned_mentor and a.assigned_mentor.user else None,
            "review_notes": a.review_notes,
            "resolved_by_id": a.resolved_by_id,
            "resolved_at": a.resolved_at,
            "resolution_reason": a.resolution_reason,
            "created_at": a.created_at,
        })

    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/alerts/{alert_id}")
def get_risk_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve comprehensive alert detail, audit history, and mentor assignments."""
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    # Student security isolation
    if current_user.role == "student":
        if not alert.student or alert.student.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students can only view their own alerts.",
            )

    history_items = []
    for h in alert.history:
        history_items.append({
            "id": h.id,
            "alert_id": h.alert_id,
            "action": h.action,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "notes": h.notes,
            "performed_by_id": h.performed_by_id,
            "performed_by_name": h.performed_by.full_name if h.performed_by else f"User {h.performed_by_id}",
            "created_at": h.created_at,
        })

    assignments_items = []
    for asg in alert.assignments:
        assignments_items.append({
            "id": asg.id,
            "alert_id": asg.alert_id,
            "mentor_id": asg.mentor_id,
            "mentor_name": asg.mentor.user.full_name if asg.mentor and asg.mentor.user else f"Mentor {asg.mentor_id}",
            "assigned_by_id": asg.assigned_by_id,
            "assigned_at": asg.assigned_at,
            "notes": asg.notes,
            "status": asg.status,
        })

    return {
        "alert": {
            "id": alert.id,
            "student_id": alert.student_id,
            "student_name": alert.student.user.full_name if alert.student and alert.student.user else alert.student.roll_number,
            "student_usn": alert.student.usn,
            "student_srn": alert.student.srn,
            "student_department": alert.student.department.name if alert.student.department else None,
            "student_semester": alert.student.current_semester,
            "student_section": alert.student.section,
            "rule_id": alert.rule_id,
            "rule_name": alert.rule.name,
            "rule_code": alert.rule.code,
            "rule_category": alert.rule.category,
            "severity": alert.severity,
            "status": alert.status,
            "observed_value": alert.observed_value,
            "observed_display": alert.observed_display,
            "threshold_value": alert.threshold_value,
            "threshold_display": alert.threshold_display,
            "academic_period": alert.academic_period,
            "subject_id": alert.subject_id,
            "subject_name": alert.subject.name if alert.subject else None,
            "detected_date": alert.detected_date,
            "is_system_generated": alert.is_system_generated,
            "ai_explanation": alert.ai_explanation,
            "suggested_action": alert.suggested_action,
            "assigned_mentor_id": alert.assigned_mentor_id,
            "assigned_mentor_name": alert.assigned_mentor.user.full_name if alert.assigned_mentor and alert.assigned_mentor.user else None,
            "review_notes": alert.review_notes,
            "resolved_by_id": alert.resolved_by_id,
            "resolved_at": alert.resolved_at,
            "resolution_reason": alert.resolution_reason,
            "created_at": alert.created_at,
        },
        "history": history_items,
        "assignments": assignments_items,
    }


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
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
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
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
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
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
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
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
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
    alert = RiskService.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
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

    # Student isolation check
    if current_user.role == "student" and student.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Students can only access their own profile.",
        )

    alerts, _ = RiskService.get_alerts(db, student_id=student.id, limit=100)
    active_alerts = [a for a in alerts if a.status in ["FLAGGED", "ACKNOWLEDGED", "UNDER_REVIEW"]]

    # Severity priority order
    sev_rank = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "NORMAL": 1}
    highest_sev = "NORMAL"
    highest_val = 0
    for a in active_alerts:
        val = sev_rank.get(a.severity, 0)
        if val > highest_val:
            highest_val = val
            highest_sev = a.severity

    serialized_alerts = []
    for a in alerts:
        serialized_alerts.append(RiskAlertResponse(
            id=a.id,
            student_id=a.student_id,
            student_name=student.user.full_name if student.user else student.roll_number,
            student_usn=student.usn,
            student_srn=student.srn,
            student_department=student.department.name if student.department else None,
            student_semester=student.current_semester,
            student_section=student.section,
            rule_id=a.rule_id,
            rule_name=a.rule.name if a.rule else None,
            rule_code=a.rule.code if a.rule else None,
            rule_category=a.rule.category if a.rule else None,
            severity=a.severity,
            status=a.status,
            observed_value=a.observed_value,
            observed_display=a.observed_display,
            threshold_value=a.threshold_value,
            threshold_display=a.threshold_display,
            academic_period=a.academic_period,
            subject_id=a.subject_id,
            subject_name=a.subject.name if a.subject else None,
            detected_date=a.detected_date,
            is_system_generated=a.is_system_generated,
            ai_explanation=a.ai_explanation,
            suggested_action=a.suggested_action,
            assigned_mentor_id=a.assigned_mentor_id,
            assigned_mentor_name=a.assigned_mentor.user.full_name if a.assigned_mentor and a.assigned_mentor.user else None,
            review_notes=a.review_notes,
            resolved_by_id=a.resolved_by_id,
            resolved_at=a.resolved_at,
            resolution_reason=a.resolution_reason,
            created_at=a.created_at,
        ))

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
        active_alerts_count=len(active_alerts),
        highest_severity=highest_sev,
        alerts=serialized_alerts,
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
