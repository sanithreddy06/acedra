"""Intervention tracking (module 6): support cases, notes, follow-ups and their notifications.

Faculty and administrators can manage any case in their scope; mentors manage cases assigned to them.
Students see only their own cases.
"""
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.intervention import (
    Intervention,
    InterventionFollowup,
    InterventionNote,
    InterventionStatus,
    Notification,
    NotificationType,
)
from app.models.profile import Mentor, Student
from app.models.risk import RiskAlert
from app.models.user import User, UserRole
from app.schemas.intervention import (
    InterventionCreate,
    InterventionFollowupCreate,
    InterventionFollowupUpdate,
    InterventionNoteCreate,
    InterventionStatusUpdate,
)


def intervention_summary(it: Intervention) -> Dict[str, Any]:
    """Display-ready view of an intervention case with student, mentor and counts."""
    student = it.student
    mentor = it.mentor
    assigned_by = it.assigned_by_user
    return {
        "id": it.id,
        "student_id": it.student_id,
        "student_name": student.user.full_name if student and student.user else "Unknown",
        "student_usn": student.usn if student else "N/A",
        "student_department": student.department.name if student and student.department else None,
        "student_semester": student.current_semester if student else None,
        "mentor_id": it.mentor_id,
        "mentor_name": mentor.user.full_name if mentor and mentor.user else None,
        "assigned_by": it.assigned_by,
        "assigned_by_name": assigned_by.full_name if assigned_by else None,
        "risk_alert_id": it.risk_alert_id,
        "title": it.title,
        "intervention_type": it.intervention_type,
        "priority": it.priority,
        "status": it.status,
        "initial_notes": it.initial_notes,
        "target_resolution_date": it.target_resolution_date,
        "resolved_at": it.resolved_at,
        "resolution_summary": it.resolution_summary,
        "created_at": it.created_at,
        "updated_at": it.updated_at,
        "notes_count": len(it.notes),
        "followups_count": len(it.followups),
    }


def note_to_dict(note: InterventionNote) -> Dict[str, Any]:
    return {
        "id": note.id,
        "intervention_id": note.intervention_id,
        "author_id": note.author_id,
        "author_name": note.author.full_name if note.author else "System",
        "author_role": note.author.role if note.author else "system",
        "note_text": note.note_text,
        "note_type": note.note_type,
        "created_at": note.created_at,
    }


def followup_to_dict(followup: InterventionFollowup) -> Dict[str, Any]:
    mentor = followup.mentor
    return {
        "id": followup.id,
        "intervention_id": followup.intervention_id,
        "mentor_id": followup.mentor_id,
        "mentor_name": mentor.user.full_name if mentor and mentor.user else None,
        "scheduled_date": followup.scheduled_date,
        "conducted_date": followup.conducted_date,
        "followup_status": followup.followup_status,
        "outcome_notes": followup.outcome_notes,
        "student_feedback": followup.student_feedback,
        "next_review_date": followup.next_review_date,
        "created_at": followup.created_at,
    }


class InterventionService:
    """
    Manages complete mentor intervention lifecycle, notes history,
    follow-up tracking, and role-based permissions.
    """

    @staticmethod
    def _create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = NotificationType.STATUS_UPDATE.value,
        severity: str = "INFO",
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = "INTERVENTION",
    ):
        """Helper to dispatch in-app notification."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
            created_at=utcnow(),
        )
        db.add(notif)

    @classmethod
    def create_intervention(
        cls,
        db: Session,
        payload: InterventionCreate,
        current_user: User,
    ) -> Intervention:
        """Create new student intervention case."""
        student = db.query(Student).filter(Student.id == payload.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        # Referenced records must exist in this university (the session is tenant-scoped, so another
        # university's mentor or alert is indistinguishable from a missing one).
        if payload.mentor_id and not db.query(Mentor).filter(Mentor.id == payload.mentor_id).first():
            raise HTTPException(status_code=422, detail="Mentor not found in your university.")
        if payload.risk_alert_id:
            alert = db.query(RiskAlert).filter(RiskAlert.id == payload.risk_alert_id).first()
            if not alert or alert.student_id != student.id:
                raise HTTPException(status_code=422, detail="The linked alert does not belong to this student.")

        # Resolve mentor: use payload mentor_id, or student's assigned mentor, or current user if mentor
        mentor_id = payload.mentor_id
        if not mentor_id and current_user.role == "mentor" and current_user.mentor_profile:
            mentor_id = current_user.mentor_profile.id
        elif not mentor_id and student.assigned_mentor_id:
            mentor_id = student.assigned_mentor_id

        initial_status = InterventionStatus.ASSIGNED.value if mentor_id else InterventionStatus.OPEN.value

        intervention = Intervention(
            student_id=student.id,
            mentor_id=mentor_id,
            assigned_by=current_user.id,
            risk_alert_id=payload.risk_alert_id,
            title=payload.title,
            intervention_type=payload.intervention_type,
            priority=payload.priority.upper(),
            status=initial_status,
            initial_notes=payload.initial_notes,
            target_resolution_date=payload.target_resolution_date,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.add(intervention)
        db.flush()

        # Add initial note if provided
        if payload.initial_notes:
            initial_note = InterventionNote(
                intervention_id=intervention.id,
                author_id=current_user.id,
                note_text=payload.initial_notes,
                note_type="OBSERVATION",
                created_at=utcnow(),
            )
            db.add(initial_note)

        # Dispatch notifications
        # 1. Notify Student
        if student.user_id:
            cls._create_notification(
                db=db,
                user_id=student.user_id,
                title="Academic & Mentorship Support Case Opened",
                message=f"An intervention support plan '{intervention.title}' has been initiated to assist your academic success.",
                notification_type=NotificationType.MENTOR_ASSIGNMENT.value,
                severity="INFO",
                reference_id=intervention.id,
            )

        # 2. Notify Mentor if assigned
        if mentor_id:
            mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
            if mentor and mentor.user_id:
                st_name = student.user.full_name if student and student.user else "a student"
                cls._create_notification(
                    db=db,
                    user_id=mentor.user_id,
                    title="Student Intervention Assigned",
                    message=f"You have been assigned to mentor {st_name} for '{intervention.title}'.",
                    notification_type=NotificationType.MENTOR_ASSIGNMENT.value,
                    severity="WARNING" if intervention.priority in ["HIGH", "URGENT"] else "INFO",
                    reference_id=intervention.id,
                )

        db.commit()
        db.refresh(intervention)
        return intervention

    @classmethod
    def update_intervention_status(
        cls,
        db: Session,
        intervention_id: int,
        payload: InterventionStatusUpdate,
        current_user: User,
    ) -> Intervention:
        """Transition intervention status through the full state machine."""
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")
        if not cls._can_manage_intervention(intervention, current_user):
            raise HTTPException(status_code=403, detail="Unauthorized to modify this intervention")

        old_status = intervention.status
        new_status = payload.status.upper()
        if new_status not in {st.value for st in InterventionStatus}:
            raise HTTPException(status_code=422, detail=f"Unknown status '{payload.status}'.")
        if new_status == InterventionStatus.RESOLVED.value and len((payload.resolution_summary or "").strip()) < 3:
            raise HTTPException(status_code=422, detail="Record the outcome (resolution summary) before resolving.")
        intervention.status = new_status
        intervention.updated_at = utcnow()

        if new_status in [InterventionStatus.RESOLVED.value, InterventionStatus.CLOSED.value]:
            intervention.resolved_at = utcnow()
            if payload.resolution_summary:
                intervention.resolution_summary = payload.resolution_summary

        # Add system audit note
        summary_note = f"Status transitioned from {old_status} to {new_status}."
        if payload.resolution_summary:
            summary_note += f" Resolution Summary: {payload.resolution_summary}"

        db.add(InterventionNote(
            intervention_id=intervention.id,
            author_id=current_user.id,
            note_text=summary_note,
            note_type="ACTION_ITEM" if new_status != "RESOLVED" else "COUNSELING",
            created_at=utcnow(),
        ))

        # Notify student of resolution / status change
        if intervention.student and intervention.student.user_id:
            cls._create_notification(
                db=db,
                user_id=intervention.student.user_id,
                title=f"Intervention Support Status: {new_status}",
                message=f"Your support case '{intervention.title}' status has been updated to {new_status}.",
                notification_type=NotificationType.STATUS_UPDATE.value,
                severity="SUCCESS" if new_status == "RESOLVED" else "INFO",
                reference_id=intervention.id,
            )

        db.commit()
        db.refresh(intervention)
        return intervention

    @classmethod
    def add_note(
        cls,
        db: Session,
        intervention_id: int,
        payload: InterventionNoteCreate,
        current_user: User,
    ) -> InterventionNote:
        """Add timestamped note to intervention record."""
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention not found")

        note = InterventionNote(
            intervention_id=intervention.id,
            author_id=current_user.id,
            note_text=payload.note_text,
            note_type=payload.note_type,
            created_at=utcnow(),
        )
        db.add(note)
        intervention.updated_at = utcnow()
        db.commit()
        db.refresh(note)
        return note

    @classmethod
    def schedule_followup(
        cls,
        db: Session,
        intervention_id: int,
        payload: InterventionFollowupCreate,
        current_user: User,
    ) -> InterventionFollowup:
        """Schedule future review / counseling follow-up session."""
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not cls._can_manage_intervention(intervention, current_user):
            raise HTTPException(status_code=403, detail="Unauthorized to schedule follow-up")

        mentor_id = payload.mentor_id or intervention.mentor_id

        followup = InterventionFollowup(
            intervention_id=intervention.id,
            mentor_id=mentor_id,
            scheduled_date=payload.scheduled_date,
            followup_status="SCHEDULED",
            outcome_notes=payload.outcome_notes,
            next_review_date=payload.next_review_date,
            created_at=utcnow(),
        )
        db.add(followup)

        # Notify student of scheduled session
        if intervention.student and intervention.student.user_id:
            cls._create_notification(
                db=db,
                user_id=intervention.student.user_id,
                title="Mentorship Follow-Up Scheduled",
                message=f"A follow-up session for '{intervention.title}' is scheduled for {payload.scheduled_date}.",
                notification_type=NotificationType.INTERVENTION_FOLLOWUP.value,
                severity="INFO",
                reference_id=intervention.id,
            )

        intervention.updated_at = utcnow()
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def record_followup_outcome(
        cls,
        db: Session,
        followup_id: int,
        payload: InterventionFollowupUpdate,
        current_user: User,
    ) -> InterventionFollowup:
        """Record notes, student feedback, and status of completed follow-up."""
        followup = db.query(InterventionFollowup).filter(InterventionFollowup.id == followup_id).first()
        if not followup:
            raise HTTPException(status_code=404, detail="Followup session not found")

        followup.followup_status = payload.followup_status.upper()
        if payload.followup_status.upper() == "COMPLETED":
            followup.conducted_date = utcnow()
        if payload.outcome_notes:
            followup.outcome_notes = payload.outcome_notes
        if payload.student_feedback:
            followup.student_feedback = payload.student_feedback
        if payload.next_review_date:
            followup.next_review_date = payload.next_review_date

        followup.intervention.updated_at = utcnow()
        db.commit()
        db.refresh(followup)
        return followup

    @classmethod
    def list_interventions(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        intervention_type: Optional[str] = None,
        student_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Role-scoped retrieval of interventions."""
        query = db.query(Intervention)

        # Security scoping
        if current_user.role == UserRole.STUDENT.value:
            if not current_user.student_profile:
                return [], 0
            query = query.filter(Intervention.student_id == current_user.student_profile.id)
        elif current_user.role == UserRole.MENTOR.value and current_user.mentor_profile:
            query = query.filter(
                or_(
                    Intervention.mentor_id == current_user.mentor_profile.id,
                    Intervention.student_id.in_(
                        db.query(Student.id).filter(Student.assigned_mentor_id == current_user.mentor_profile.id)
                    )
                )
            )
        # Faculty: the session's student scope (sections taught + explicitly shared students) already limits
        # which interventions are visible, matching what they can open directly.

        if student_id:
            query = query.filter(Intervention.student_id == student_id)
        if status_filter:
            query = query.filter(Intervention.status == status_filter.upper())
        if priority_filter:
            query = query.filter(Intervention.priority == priority_filter.upper())
        if intervention_type:
            query = query.filter(Intervention.intervention_type == intervention_type)

        total = query.count()
        interventions = query.order_by(desc(Intervention.updated_at)).offset(skip).limit(limit).all()

        results = [intervention_summary(it) for it in interventions]
        return results, total

    @classmethod
    def get_intervention_detail(cls, db: Session, intervention_id: int, current_user: User) -> Dict[str, Any]:
        """Fetch full intervention dossier including notes and followups."""
        it = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not it:
            raise HTTPException(status_code=404, detail="Intervention not found")

        # Security check
        if current_user.role == "student" and current_user.student_profile and it.student_id != current_user.student_profile.id:
            raise HTTPException(status_code=403, detail="Unauthorized to access this student intervention")

        return {
            **intervention_summary(it),
            "notes": [note_to_dict(n) for n in it.notes],
            "followups": [followup_to_dict(f) for f in it.followups],
        }

    @staticmethod
    def _can_manage_intervention(intervention: Optional[Intervention], user: User) -> bool:
        if not intervention:
            return False
        if user.role in ["admin", "faculty"]:
            return True
        if user.role == "mentor" and user.mentor_profile:
            return intervention.mentor_id == user.mentor_profile.id
        return False
