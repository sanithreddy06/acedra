from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.intervention import (
    InterventionCreate,
    InterventionDetailResponse,
    InterventionFollowupCreate,
    InterventionFollowupResponse,
    InterventionFollowupUpdate,
    InterventionNoteCreate,
    InterventionNoteResponse,
    InterventionResponse,
    InterventionStatusUpdate,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    ReportExportCreate,
    ReportExportResponse,
)
from app.services.intervention_service import (
    InterventionService,
    followup_to_dict,
    intervention_summary,
    note_to_dict,
)
from app.services.notification_service import NotificationService
from app.services.report_service import ReportService

router = APIRouter(tags=["Interventions & Notifications"])


# ==========================================
# INTERVENTIONS ENDPOINTS
# ==========================================

@router.get("/interventions", response_model=List[InterventionResponse])
def list_interventions(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, URGENT)"),
    intervention_type: Optional[str] = Query(None, description="Filter by type"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve role-scoped list of interventions."""
    if current_user.role == "placement_officer":
        raise HTTPException(status_code=403, detail="Placement officers do not have access to interventions.")
    items, _ = InterventionService.list_interventions(
        db=db,
        current_user=current_user,
        status_filter=status,
        priority_filter=priority,
        intervention_type=intervention_type,
        student_id=student_id,
        skip=skip,
        limit=limit,
    )
    if current_user.role == "student":
        # Students see that support exists and its status, never staff mentoring notes.
        for it in items:
            if isinstance(it, dict):
                it["initial_notes"] = None
                it["resolution_summary"] = None
    return items


@router.post("/interventions", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
def create_intervention(
    payload: InterventionCreate,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Initiate a new student support intervention case."""
    intervention = InterventionService.create_intervention(
        db=db,
        payload=payload,
        current_user=current_user,
    )
    return intervention_summary(intervention)


@router.get("/interventions/{intervention_id}", response_model=InterventionDetailResponse)
def get_intervention_detail(
    intervention_id: int,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Fetch full intervention dossier including audit notes and scheduled follow-ups."""
    return InterventionService.get_intervention_detail(
        db=db,
        intervention_id=intervention_id,
        current_user=current_user,
    )


@router.put("/interventions/{intervention_id}/status", response_model=InterventionResponse)
def update_intervention_status(
    intervention_id: int,
    payload: InterventionStatusUpdate,
    current_user: User = Depends(require_role(["mentor", "faculty", "admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Transition intervention state through its lifecycle."""
    intervention = InterventionService.update_intervention_status(
        db=db,
        intervention_id=intervention_id,
        payload=payload,
        current_user=current_user,
    )
    return intervention_summary(intervention)


@router.post("/interventions/{intervention_id}/notes", response_model=InterventionNoteResponse, status_code=status.HTTP_201_CREATED)
def add_intervention_note(
    intervention_id: int,
    payload: InterventionNoteCreate,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Add timestamped case note or progress observation."""
    note = InterventionService.add_note(
        db=db,
        intervention_id=intervention_id,
        payload=payload,
        current_user=current_user,
    )
    return note_to_dict(note)


@router.post("/interventions/{intervention_id}/followups", response_model=InterventionFollowupResponse, status_code=status.HTTP_201_CREATED)
def schedule_intervention_followup(
    intervention_id: int,
    payload: InterventionFollowupCreate,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Schedule structured review or counseling session."""
    followup = InterventionService.schedule_followup(
        db=db,
        intervention_id=intervention_id,
        payload=payload,
        current_user=current_user,
    )
    return followup_to_dict(followup)


@router.put("/interventions/followups/{followup_id}", response_model=InterventionFollowupResponse)
def record_followup_outcome(
    followup_id: int,
    payload: InterventionFollowupUpdate,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Record notes, feedback, and outcome of completed follow-up."""
    followup = InterventionService.record_followup_outcome(
        db=db,
        followup_id=followup_id,
        payload=payload,
        current_user=current_user,
    )
    return followup_to_dict(followup)


# ==========================================
# IN-APP NOTIFICATIONS ENDPOINTS
# ==========================================

@router.get("/notifications")
def get_my_notifications(
    unread_only: bool = Query(False, description="Filter only unread messages"),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Fetch notifications for current user with unread counter."""
    notifs, unread_count = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return {
        "notifications": [
            {
                "id": n.id,
                "user_id": n.user_id,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type,
                "severity": n.severity,
                "reference_id": n.reference_id,
                "reference_type": n.reference_type,
                "action_url": n.action_url,
                "is_read": n.is_read,
                "read_at": n.read_at,
                "created_at": n.created_at,
            }
            for n in notifs
        ],
        "unread_count": unread_count,
    }


@router.put("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Mark single notification as read."""
    success = NotificationService.mark_notification_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success", "message": "Notification marked as read"}


@router.put("/notifications/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Mark all active unread notifications as read."""
    count = NotificationService.mark_all_notifications_read(db=db, user_id=current_user.id)
    return {"status": "success", "marked_read_count": count}


@router.get("/notifications/preferences", response_model=NotificationPreferenceResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get delivery preferences for user."""
    return NotificationService.get_or_create_preferences(db=db, user_id=current_user.id)


@router.put("/notifications/preferences", response_model=NotificationPreferenceResponse)
def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update notification preferences."""
    return NotificationService.update_preferences(
        db=db,
        user_id=current_user.id,
        updates=payload.model_dump(exclude_unset=True),
    )


@router.post("/notifications/broadcast")
def broadcast_announcement(
    title: str = Query(..., min_length=3),
    message: str = Query(..., min_length=5),
    target_role: Optional[str] = Query(None, description="Optional target role (e.g., student, faculty)"),
    severity: str = Query("INFO"),
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
) -> Any:
    """Admin-only institutional broadcast announcement."""
    count = NotificationService.broadcast_announcement(
        db=db,
        title=title,
        message=message,
        target_role=target_role,
        severity=severity,
    )
    return {"status": "success", "recipients_count": count}


# ==========================================
# INSTITUTIONAL REPORTS & EXPORTS ENDPOINTS
# ==========================================

@router.post("/reports/export", response_model=ReportExportResponse, status_code=status.HTTP_201_CREATED)
def generate_report_export(
    payload: ReportExportCreate,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin", "placement_officer"])),
    db: Session = Depends(get_db),
) -> Any:
    """Generate institutional CSV/JSON audit report."""
    export = ReportService.generate_report(
        db=db,
        report_type=payload.report_type,
        file_format=payload.file_format,
        department_id=payload.department_id,
        student_id=payload.student_id,
        current_user=current_user,
    )
    return {
        "id": export.id,
        "report_type": export.report_type,
        "title": export.title,
        "generated_by": export.generated_by,
        "generated_by_name": current_user.full_name,
        "department_id": export.department_id,
        "student_id": export.student_id,
        "file_format": export.file_format,
        "file_name": export.file_name,
        "file_size_bytes": export.file_size_bytes,
        "created_at": export.created_at,
    }


@router.get("/reports", response_model=List[ReportExportResponse])
def list_reports(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(require_role(["faculty", "mentor", "admin", "placement_officer"])),
    db: Session = Depends(get_db),
) -> Any:
    """List historical reports and export jobs."""
    reports = ReportService.list_reports(db=db, current_user=current_user, limit=limit)
    return [
        {
            "id": r.id,
            "report_type": r.report_type,
            "title": r.title,
            "generated_by": r.generated_by,
            "generated_by_name": r.generator.full_name if r.generator else "System",
            "department_id": r.department_id,
            "student_id": r.student_id,
            "file_format": r.file_format,
            "file_name": r.file_name,
            "file_size_bytes": r.file_size_bytes,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: int,
    current_user: User = Depends(require_role(["faculty", "mentor", "admin", "placement_officer"])),
    db: Session = Depends(get_db),
) -> Any:
    """Download generated CSV report file."""
    report, content = ReportService.get_report_download(db=db, report_id=report_id, current_user=current_user)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report.file_name}"},
    )
