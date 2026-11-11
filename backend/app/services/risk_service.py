"""Early-warning risk identification (module 2).

Risk is rule-based and explainable — there is no predictive model. ``evaluate_risk`` derives indicators
once per student (``_StudentRiskMetrics``), checks each active rule with the observer registered for
its ``indicator_type`` (``_INDICATOR_OBSERVERS``) and raises an alert when it triggers. An alert that is
still open for the same student and rule is refreshed instead of duplicated. ``alert_summary`` and
``alert_detail`` are the serialisers used by the API.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.clock import utcnow
from app.models.academic import (
    StudentAssessment,
    StudentSemesterRecord,
    SubjectAttendance,
    SubjectResult,
)
from app.models.profile import Mentor, Student
from app.models.risk import (
    AlertAssignment,
    InAppNotification,
    RiskAlert,
    RiskAlertHistory,
    RiskEvaluation,
    RiskRule,
)
from app.models.user import User

logger = logging.getLogger(__name__)


# Alerts in these statuses still need attention; RESOLVED and CLOSED do not.
ACTIVE_ALERT_STATUSES = ("FLAGGED", "ACKNOWLEDGED", "UNDER_REVIEW")
SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "NORMAL": 1}


def alert_summary(alert: RiskAlert) -> Dict[str, Any]:
    """Flat, display-ready view of an alert with its student, rule, subject and assigned mentor."""
    student = alert.student
    rule = alert.rule
    mentor = alert.assigned_mentor
    return {
        "id": alert.id,
        "student_id": alert.student_id,
        "student_name": student.user.full_name if student and student.user else student.roll_number,
        "student_usn": student.usn if student else None,
        "student_srn": student.srn if student else None,
        "student_department": student.department.name if student and student.department else None,
        "student_semester": student.current_semester if student else None,
        "student_section": student.section if student else None,
        "rule_id": alert.rule_id,
        "rule_name": rule.name if rule else None,
        "rule_code": rule.code if rule else None,
        "rule_category": rule.category if rule else None,
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
        "assigned_mentor_name": mentor.user.full_name if mentor and mentor.user else None,
        "review_notes": alert.review_notes,
        "resolved_by_id": alert.resolved_by_id,
        "resolved_at": alert.resolved_at,
        "resolution_reason": alert.resolution_reason,
        "created_at": alert.created_at,
    }


def alert_detail(alert: RiskAlert) -> Dict[str, Any]:
    """Alert summary plus its audit history and mentor assignments."""
    return {
        "alert": alert_summary(alert),
        "history": [
            {
                "id": h.id,
                "alert_id": h.alert_id,
                "action": h.action,
                "old_status": h.old_status,
                "new_status": h.new_status,
                "notes": h.notes,
                "performed_by_id": h.performed_by_id,
                "performed_by_name": h.performed_by.full_name if h.performed_by else f"User {h.performed_by_id}",
                "created_at": h.created_at,
            }
            for h in alert.history
        ],
        "assignments": [
            {
                "id": a.id,
                "alert_id": a.alert_id,
                "mentor_id": a.mentor_id,
                "mentor_name": a.mentor.user.full_name if a.mentor and a.mentor.user else f"Mentor {a.mentor_id}",
                "assigned_by_id": a.assigned_by_id,
                "assigned_at": a.assigned_at,
                "notes": a.notes,
                "status": a.status,
            }
            for a in alert.assignments
        ],
    }


def highest_active_severity(alerts: List[RiskAlert]) -> str:
    """The most severe level among alerts that are still open; NORMAL when none are."""
    highest, highest_rank = "NORMAL", 0
    for alert in alerts:
        if alert.status not in ACTIVE_ALERT_STATUSES:
            continue
        rank = SEVERITY_RANK.get(alert.severity, 0)
        if rank > highest_rank:
            highest, highest_rank = alert.severity, rank
    return highest


class AIExplanationService:
    """
    Converts verified, quantitative risk alert evidence into clear, objective,
    supportive, and empathetic natural language explanations.
    Strictly grounded in observed database metrics; never invents reasons,
    never modifies underlying risk scores, and avoids punitive labelling.
    """

    @staticmethod
    def generate_explanation(
        student_name: str,
        student_usn: str,
        rule_category: str,
        indicator_type: str,
        observed_value: float,
        threshold_value: float,
        operator: str,
        academic_period: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        ctx = context_data or {}
        student_ref = f"{student_name} ({student_usn})"

        if indicator_type == "attendance_percentage":
            attended = ctx.get("attended_classes", 0)
            total = ctx.get("total_classes", 0)
            subject = ctx.get("subject_name", "enrolled courses")
            diff = round(threshold_value - observed_value, 1)
            return (
                f"Attendance Evaluation for {student_ref}: Observed attendance in {subject} "
                f"for {academic_period} is {observed_value:.1f}% ({attended}/{total} classes attended), "
                f"which is {diff:.1f}% below the institutional threshold of {threshold_value:.1f}%. "
                f"Early intervention is recommended to assist the student in resuming regular class attendance "
                f"before semester eligibility thresholds are impacted."
            )

        elif indicator_type == "assessment_percentage":
            subject = ctx.get("subject_name", "active courses")
            assessment_name = ctx.get("assessment_name", "continuous internal assessments")
            marks_obtained = ctx.get("marks_obtained", 0)
            max_marks = ctx.get("max_marks", 0)
            diff = round(threshold_value - observed_value, 1)
            return (
                f"Academic Assessment Record for {student_ref}: Continuous evaluation in {subject} "
                f"({assessment_name}) reflects an average score of {observed_value:.1f}% "
                f"({marks_obtained:.1f}/{max_marks:.1f} marks), falling {diff:.1f}% below the target benchmark "
                f"of {threshold_value:.1f}%. Formative academic guidance and topic review sessions are recommended "
                f"to bolster foundational conceptual grasp."
            )

        elif indicator_type == "sgpa_drop":
            prev_sgpa = ctx.get("prev_sgpa", 0.0)
            curr_sgpa = ctx.get("curr_sgpa", 0.0)
            prev_sem = ctx.get("prev_sem", "previous semester")
            curr_sem = ctx.get("curr_sem", academic_period)
            return (
                f"Academic Trajectory Analysis for {student_ref}: Semester grade point average decreased by "
                f"{observed_value:.2f} points (from {prev_sgpa:.2f} in {prev_sem} down to {curr_sgpa:.2f} in {curr_sem}), "
                f"exceeding the declining performance threshold of {threshold_value:.2f}. "
                f"A collaborative mentor check-in is recommended to identify potential study bottlenecks or personal obstacles."
            )

        elif indicator_type == "backlog_count":
            backlogs = int(observed_value)
            failed_subjects = ctx.get("failed_subjects", [])
            subjects_str = ", ".join(failed_subjects) if failed_subjects else "active curriculum"
            return (
                f"Curricular Progression Monitor for {student_ref}: Identified {backlogs} uncleared subject course(s) "
                f"({subjects_str}) in {academic_period}, matching or exceeding the review threshold of {threshold_value:.0f}. "
                f"Dedicated remedial schedules and academic advisor alignment are advised to facilitate backlog clearance."
            )

        elif indicator_type == "missing_assessments":
            missing_count = int(observed_value)
            subject = ctx.get("subject_name", "active courses")
            return (
                f"Assessment Completion Audit for {student_ref}: {missing_count} scheduled continuous internal evaluation(s) "
                f"in {subject} appear unrecorded or unsubmitted for {academic_period}. "
                f"Prompt verification is recommended with course instructors to determine if make-up evaluations are eligible."
            )

        elif indicator_type == "composite":
            att_val = ctx.get("attendance_val", 0.0)
            cia_val = ctx.get("cia_val", 0.0)
            return (
                f"Multi-Indicator Early Warning for {student_ref}: Concurrent risk indicators detected during {academic_period}. "
                f"Student displays both reduced attendance ({att_val:.1f}%) and assessment scores ({cia_val:.1f}%). "
                f"Holistic multi-disciplinary support involving the assigned faculty mentor and student counselor is strongly advised."
            )

        return (
            f"Rule Alert for {student_ref}: Observed metric of {observed_value:.2f} satisfies condition "
            f"'{operator} {threshold_value:.2f}' under rule {rule_category} in {academic_period}."
        )


class RiskService:
    """
    Core Rule-Based Risk Detection and Management Service.
    """

    DEFAULT_RULES = [
        {
            "name": "Critical Attendance Shortfall (<65%)",
            "code": "RULE_ATT_CRITICAL",
            "description": "Flags students whose attendance drops below 65%, threatening course eligibility.",
            "category": "ATTENDANCE",
            "severity": "CRITICAL",
            "indicator_type": "attendance_percentage",
            "operator": "<",
            "threshold_value": 65.0,
            "suggested_action": "Immediate academic counseling and parental notification.",
            "is_active": True,
        },
        {
            "name": "Attendance Early Warning (<75%)",
            "code": "RULE_ATT_WARNING",
            "description": "Flags students falling below the mandatory 75% institutional attendance threshold.",
            "category": "ATTENDANCE",
            "severity": "HIGH",
            "indicator_type": "attendance_percentage",
            "operator": "<",
            "threshold_value": 75.0,
            "suggested_action": "Faculty advisor 1-on-1 review and attendance warning notice.",
            "is_active": True,
        },
        {
            "name": "Continuous Internal Assessment Deficit (<40%)",
            "code": "RULE_CIA_DEFICIT",
            "description": "Flags students scoring under 40% on continuous internal evaluations and quizzes.",
            "category": "ASSESSMENT",
            "severity": "HIGH",
            "indicator_type": "assessment_percentage",
            "operator": "<",
            "threshold_value": 40.0,
            "suggested_action": "Remedial tutorial assignments and subject faculty consultation.",
            "is_active": True,
        },
        {
            "name": "Marginal Assessment Performance (<50%)",
            "code": "RULE_CIA_MARGINAL",
            "description": "Flags students performing in the 40-50% bracket on internal assessments.",
            "category": "ASSESSMENT",
            "severity": "MODERATE",
            "indicator_type": "assessment_percentage",
            "operator": "<",
            "threshold_value": 50.0,
            "suggested_action": "Encourage peer study groups and supplementary coursework.",
            "is_active": True,
        },
        {
            "name": "Consecutive SGPA Decline (Drop >= 1.0)",
            "code": "RULE_SGPA_DROP",
            "description": "Detects sharp academic downturns where current semester SGPA drops by 1.0 or more from prior semester.",
            "category": "ACADEMIC",
            "severity": "HIGH",
            "indicator_type": "sgpa_drop",
            "operator": ">=",
            "threshold_value": 1.0,
            "suggested_action": "Comprehensive academic progress review with department mentor.",
            "is_active": True,
        },
        {
            "name": "Multiple Active Backlogs (>= 2)",
            "code": "RULE_BACKLOGS_MULTIPLE",
            "description": "Flags students with 2 or more uncleared course backlogs.",
            "category": "BACKLOG",
            "severity": "CRITICAL",
            "indicator_type": "backlog_count",
            "operator": ">=",
            "threshold_value": 2.0,
            "suggested_action": "Mandatory exam prep coaching and credit load balancing.",
            "is_active": True,
        },
        {
            "name": "Single Active Backlog (>= 1)",
            "code": "RULE_BACKLOGS_SINGLE",
            "description": "Flags students with an uncleared course backlog.",
            "category": "BACKLOG",
            "severity": "MODERATE",
            "indicator_type": "backlog_count",
            "operator": ">=",
            "threshold_value": 1.0,
            "suggested_action": "Re-examination schedule planning with faculty advisor.",
            "is_active": True,
        },
        {
            "name": "Missing Continuous Assessments (>= 1)",
            "code": "RULE_MISSING_ASSESSMENTS",
            "description": "Flags missing or unrecorded internal evaluation records for enrolled subjects.",
            "category": "ASSESSMENT",
            "severity": "MODERATE",
            "indicator_type": "missing_assessments",
            "operator": ">=",
            "threshold_value": 1.0,
            "suggested_action": "Coordinate makeup assessment window with course instructor.",
            "is_active": True,
        },
        {
            "name": "Combined Attendance & Assessment Risk",
            "code": "RULE_COMPOUND_RISK",
            "description": "Flags students with concurrent attendance deficits (<75%) and low assessment scores (<50%).",
            "category": "COMPOSITE",
            "severity": "CRITICAL",
            "indicator_type": "composite",
            "operator": "==",
            "threshold_value": 1.0,
            "conditions_config": {"min_attendance": 75.0, "max_assessment_pct": 50.0},
            "suggested_action": "Multi-disciplinary intervention with mentor, course instructor, and HOD.",
            "is_active": True,
        },
    ]

    # -------------------------------------------------------------------------
    # RULE MANAGEMENT
    # -------------------------------------------------------------------------
    @classmethod
    def seed_default_rules_if_needed(cls, db: Session, user_id: Optional[int] = None) -> List[RiskRule]:
        """Ensure canonical rules exist in database without hardcoding fixed thresholds."""
        existing_codes = {r.code for r in db.query(RiskRule).all()}
        created_rules = []

        for rule_data in cls.DEFAULT_RULES:
            if rule_data["code"] not in existing_codes:
                rule = RiskRule(
                    name=rule_data["name"],
                    code=rule_data["code"],
                    description=rule_data["description"],
                    category=rule_data["category"],
                    severity=rule_data["severity"],
                    indicator_type=rule_data["indicator_type"],
                    operator=rule_data["operator"],
                    threshold_value=rule_data["threshold_value"],
                    conditions_config=rule_data.get("conditions_config"),
                    suggested_action=rule_data["suggested_action"],
                    is_active=rule_data["is_active"],
                    created_by_id=user_id,
                )
                db.add(rule)
                created_rules.append(rule)

        if created_rules:
            db.commit()
            for r in created_rules:
                db.refresh(r)

        return db.query(RiskRule).all()

    @staticmethod
    def get_rules(db: Session, category: Optional[str] = None, is_active: Optional[bool] = None) -> List[RiskRule]:
        query = db.query(RiskRule)
        if category:
            query = query.filter(RiskRule.category == category)
        if is_active is not None:
            query = query.filter(RiskRule.is_active == is_active)
        return query.order_by(RiskRule.severity.desc(), RiskRule.id.asc()).all()

    @staticmethod
    def get_rule_by_id(db: Session, rule_id: int) -> Optional[RiskRule]:
        return db.query(RiskRule).filter(RiskRule.id == rule_id).first()

    @staticmethod
    def create_rule(db: Session, rule_data: Dict[str, Any], user_id: Optional[int] = None) -> RiskRule:
        rule = RiskRule(
            name=rule_data["name"],
            code=rule_data["code"],
            description=rule_data.get("description"),
            category=rule_data["category"],
            severity=rule_data.get("severity", "MODERATE"),
            indicator_type=rule_data["indicator_type"],
            operator=rule_data.get("operator", "<"),
            threshold_value=rule_data["threshold_value"],
            conditions_config=rule_data.get("conditions_config"),
            suggested_action=rule_data.get("suggested_action"),
            is_active=rule_data.get("is_active", True),
            created_by_id=user_id,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def update_rule(db: Session, rule: RiskRule, update_data: Dict[str, Any]) -> RiskRule:
        for k, v in update_data.items():
            if v is not None and hasattr(rule, k):
                setattr(rule, k, v)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete_rule(db: Session, rule: RiskRule) -> None:
        db.delete(rule)
        db.commit()

    # -------------------------------------------------------------------------
    # EVALUATION & DETECTION ENGINE
    # -------------------------------------------------------------------------
    @classmethod
    def evaluate_risk(
        cls,
        db: Session,
        student_id: Optional[int] = None,
        department_id: Optional[int] = None,
        run_type: str = "MANUAL",
        user_id: Optional[int] = None,
    ) -> RiskEvaluation:
        """
        Executes rule-based risk evaluation against active students and rules.
        Prevents duplicate active alerts for the same student and rule.
        """
        # Ensure rules exist
        cls.seed_default_rules_if_needed(db, user_id)
        active_rules = db.query(RiskRule).filter(RiskRule.is_active.is_(True)).all()

        # Build student query
        student_query = db.query(Student).filter(Student.status == "Active")
        if student_id:
            student_query = student_query.filter(Student.id == student_id)
        if department_id:
            student_query = student_query.filter(Student.department_id == department_id)

        students = student_query.options(
            joinedload(Student.user),
            joinedload(Student.department),
            # One query per collection. Joining four collections in a single statement multiplies rows
            # (attendance × assessments × terms × results per student) and does not scale.
            selectinload(Student.attendance_records).joinedload(SubjectAttendance.subject),
            selectinload(Student.assessments).joinedload(StudentAssessment.subject),
            selectinload(Student.semester_records),
            selectinload(Student.subject_results).joinedload(SubjectResult.subject),
        ).all()

        evaluation = RiskEvaluation(
            run_type=run_type,
            initiated_by_id=user_id,
            evaluated_students_count=len(students),
            alerts_generated_count=0,
            status="IN_PROGRESS",
            completed_at=None,
        )
        db.add(evaluation)
        db.flush()

        new_alerts = []
        updated_alerts = []
        critical_c = high_c = moderate_c = normal_c = 0

        # Existing active alerts mapped by (student_id, rule_id)
        existing_alerts = db.query(RiskAlert).filter(
            RiskAlert.status.in_(["FLAGGED", "ACKNOWLEDGED", "UNDER_REVIEW"])
        ).all()
        active_alert_map: Dict[Tuple[int, int], RiskAlert] = {
            (a.student_id, a.rule_id): a for a in existing_alerts
        }

        for student in students:
            student_alerts = cls._evaluate_student_against_rules(
                db=db,
                student=student,
                rules=active_rules,
                evaluation_id=evaluation.id,
                active_alert_map=active_alert_map,
            )
            for alert, is_new in student_alerts:
                if is_new:
                    new_alerts.append(alert)
                else:
                    updated_alerts.append(alert)

                if alert.severity == "CRITICAL":
                    critical_c += 1
                elif alert.severity == "HIGH":
                    high_c += 1
                elif alert.severity == "MODERATE":
                    moderate_c += 1
                else:
                    normal_c += 1

        db.commit()

        # Notifications dispatch for new critical/high alerts
        for alert in new_alerts:
            cls._dispatch_alert_notifications(db, alert)

        evaluation.alerts_generated_count = len(new_alerts) + len(updated_alerts)
        evaluation.critical_count = critical_c
        evaluation.high_count = high_c
        evaluation.moderate_count = moderate_c
        evaluation.normal_count = normal_c
        evaluation.status = "COMPLETED"
        evaluation.completed_at = utcnow()
        evaluation.summary = {
            "new_alerts_count": len(new_alerts),
            "updated_alerts_count": len(updated_alerts),
            "evaluated_students": len(students),
        }
        db.commit()
        db.refresh(evaluation)
        return evaluation

    @classmethod
    def _evaluate_student_against_rules(
        cls,
        db: Session,
        student: Student,
        rules: List[RiskRule],
        evaluation_id: int,
        active_alert_map: Dict[Tuple[int, int], RiskAlert],
    ) -> List[Tuple[RiskAlert, bool]]:
        """Apply every active rule to one student; return (alert, is_new) for each rule that triggered.

        An alert that is still open for the same (student, rule) is refreshed in place rather than
        duplicated, so repeated evaluations never stack alerts.
        """
        metrics = _StudentRiskMetrics.from_student(student)
        results: List[Tuple[RiskAlert, bool]] = []
        for rule in rules:
            observe = _INDICATOR_OBSERVERS.get(rule.indicator_type)
            if observe is None:
                continue
            observation = observe(metrics, rule)
            if observation.triggered:
                results.append(cls._record_alert(db, metrics, rule, observation, evaluation_id, active_alert_map))
        return results

    @staticmethod
    def _record_alert(
        db: Session,
        metrics: "_StudentRiskMetrics",
        rule: RiskRule,
        observation: "_RuleObservation",
        evaluation_id: int,
        active_alert_map: Dict[Tuple[int, int], RiskAlert],
    ) -> Tuple[RiskAlert, bool]:
        student = metrics.student
        key = (student.id, rule.id)
        if "percentage" in rule.indicator_type:
            threshold_display = f"{rule.operator} {rule.threshold_value:.1f}%"
        else:
            threshold_display = f"{rule.operator} {rule.threshold_value}"
        explanation = AIExplanationService.generate_explanation(
            student_name=metrics.student_name,
            student_usn=student.usn,
            rule_category=rule.category,
            indicator_type=rule.indicator_type,
            observed_value=observation.value,
            threshold_value=rule.threshold_value,
            operator=rule.operator,
            academic_period=metrics.current_period,
            context_data=observation.context,
        )

        existing = active_alert_map.get(key)
        if existing is not None:
            existing.evaluation_id = evaluation_id
            existing.observed_value = observation.value
            existing.observed_display = observation.display
            existing.threshold_value = rule.threshold_value
            existing.threshold_display = threshold_display
            existing.ai_explanation = explanation
            existing.detected_date = utcnow()
            return existing, False

        alert = RiskAlert(
            student_id=student.id,
            rule_id=rule.id,
            evaluation_id=evaluation_id,
            severity=rule.severity,
            status="FLAGGED",
            observed_value=observation.value,
            observed_display=observation.display,
            threshold_value=rule.threshold_value,
            threshold_display=threshold_display,
            academic_period=metrics.current_period,
            subject_id=observation.subject_id,
            detected_date=utcnow(),
            is_system_generated=True,
            ai_explanation=explanation,
            suggested_action=rule.suggested_action,
            assigned_mentor_id=student.assigned_mentor_id,
        )
        db.add(alert)
        db.flush()
        db.add(RiskAlertHistory(
            alert_id=alert.id,
            action="FLAGGED",
            old_status=None,
            new_status="FLAGGED",
            notes=f"System generated early-warning alert based on rule '{rule.name}' ({rule.code}).",
            performed_by_id=student.user_id,
        ))
        active_alert_map[key] = alert
        return alert, True

    @staticmethod
    def _dispatch_alert_notifications(db: Session, alert: RiskAlert) -> None:
        """Create in-app notifications for assigned mentor and faculty."""
        student = alert.student
        if not student:
            return

        notif_severity = "CRITICAL" if alert.severity == "CRITICAL" else ("WARNING" if alert.severity == "HIGH" else "INFO")
        title = f"Early Warning: {alert.severity} Risk Flagged for {student.roll_number}"
        message = (
            f"Rule '{alert.rule.name}' triggered ({alert.observed_display} vs threshold {alert.threshold_display}). "
            f"Action: {alert.suggested_action or 'Review student performance.'}"
        )

        users_to_notify = set()
        # 1. Assigned Mentor
        if student.mentor and student.mentor.user_id:
            users_to_notify.add(student.mentor.user_id)

        # 2. HOD or Department Admin
        dept_admins = db.query(User).filter(
            User.department_id == student.department_id,
            User.role.in_(["administrator", "faculty"])
        ).limit(3).all()
        for u in dept_admins:
            users_to_notify.add(u.id)

        for uid in users_to_notify:
            notif = InAppNotification(
                user_id=uid,
                title=title,
                message=message,
                notification_type="RISK_ALERT",
                severity=notif_severity,
                reference_id=alert.id,
                reference_type="risk_alert",
                is_read=False,
            )
            db.add(notif)

    # -------------------------------------------------------------------------
    # ALERT MANAGEMENT & WORKFLOW
    # -------------------------------------------------------------------------
    @staticmethod
    def get_alerts(
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        department_id: Optional[int] = None,
        semester: Optional[int] = None,
        rule_id: Optional[int] = None,
        student_id: Optional[int] = None,
        mentor_id: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[RiskAlert], int]:
        query = db.query(RiskAlert).join(RiskAlert.student).join(RiskAlert.rule)

        if status == "ACTIVE":  # any alert still awaiting resolution
            query = query.filter(RiskAlert.status.notin_(["RESOLVED", "CLOSED"]))
        elif status:
            query = query.filter(RiskAlert.status == status)
        if severity:
            query = query.filter(RiskAlert.severity == severity)
        if department_id:
            query = query.filter(Student.department_id == department_id)
        if semester:
            query = query.filter(Student.current_semester == semester)
        if rule_id:
            query = query.filter(RiskAlert.rule_id == rule_id)
        if student_id:
            query = query.filter(RiskAlert.student_id == student_id)
        if mentor_id:
            query = query.filter(RiskAlert.assigned_mentor_id == mentor_id)
        if search:
            search_fmt = f"%{search}%"
            query = query.join(Student.user).filter(
                (Student.roll_number.ilike(search_fmt)) |
                (Student.usn.ilike(search_fmt)) |
                (User.full_name.ilike(search_fmt)) |
                (RiskRule.name.ilike(search_fmt))
            )

        total = query.count()
        alerts = (
            query.options(
                joinedload(RiskAlert.student).joinedload(Student.user),
                joinedload(RiskAlert.student).joinedload(Student.department),
                joinedload(RiskAlert.rule),
                joinedload(RiskAlert.subject),
                joinedload(RiskAlert.assigned_mentor).joinedload(Mentor.user),
                joinedload(RiskAlert.resolved_by),
            )
            .order_by(
                # Order by severity priority
                desc(RiskAlert.severity == "CRITICAL"),
                desc(RiskAlert.severity == "HIGH"),
                desc(RiskAlert.severity == "MODERATE"),
                desc(RiskAlert.created_at),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return alerts, total

    @staticmethod
    def get_alert_by_id(db: Session, alert_id: int) -> Optional[RiskAlert]:
        return (
            db.query(RiskAlert)
            .options(
                joinedload(RiskAlert.student).joinedload(Student.user),
                joinedload(RiskAlert.student).joinedload(Student.department),
                joinedload(RiskAlert.rule),
                joinedload(RiskAlert.subject),
                joinedload(RiskAlert.assigned_mentor).joinedload(Mentor.user),
                joinedload(RiskAlert.resolved_by),
                joinedload(RiskAlert.history).joinedload(RiskAlertHistory.performed_by),
                joinedload(RiskAlert.assignments).joinedload(AlertAssignment.mentor).joinedload(Mentor.user),
            )
            .filter(RiskAlert.id == alert_id)
            .first()
        )

    @staticmethod
    def acknowledge_alert(db: Session, alert: RiskAlert, user_id: int, notes: Optional[str] = None) -> RiskAlert:
        old_status = alert.status
        alert.status = "ACKNOWLEDGED"
        if notes:
            alert.review_notes = (alert.review_notes or "") + f"\n[{utcnow().strftime('%Y-%m-%d %H:%M')}] Acknowledged: {notes}"

        history = RiskAlertHistory(
            alert_id=alert.id,
            action="ACKNOWLEDGED",
            old_status=old_status,
            new_status="ACKNOWLEDGED",
            notes=notes or "Alert reviewed and acknowledged by user.",
            performed_by_id=user_id,
        )
        db.add(history)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def add_review_note(db: Session, alert: RiskAlert, user_id: int, notes: str) -> RiskAlert:
        time_tag = utcnow().strftime("%Y-%m-%d %H:%M")
        alert.review_notes = (alert.review_notes or "") + f"\n[{time_tag}] {notes}"

        history = RiskAlertHistory(
            alert_id=alert.id,
            action="NOTE_ADDED",
            old_status=alert.status,
            new_status=alert.status,
            notes=notes,
            performed_by_id=user_id,
        )
        db.add(history)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def assign_mentor(
        db: Session,
        alert: RiskAlert,
        mentor_id: int,
        user_id: int,
        notes: Optional[str] = None,
    ) -> RiskAlert:
        old_status = alert.status
        alert.assigned_mentor_id = mentor_id
        alert.status = "UNDER_REVIEW"

        assignment = AlertAssignment(
            alert_id=alert.id,
            mentor_id=mentor_id,
            assigned_by_id=user_id,
            notes=notes,
            status="ACTIVE",
        )
        db.add(assignment)

        history = RiskAlertHistory(
            alert_id=alert.id,
            action="ASSIGNED",
            old_status=old_status,
            new_status="UNDER_REVIEW",
            notes=f"Assigned to Mentor ID {mentor_id}. {notes or ''}".strip(),
            performed_by_id=user_id,
        )
        db.add(history)

        # Notify mentor
        mentor = db.query(Mentor).filter(Mentor.id == mentor_id).first()
        if mentor and mentor.user_id:
            notif = InAppNotification(
                user_id=mentor.user_id,
                title=f"New At-Risk Student Assigned: {alert.student.roll_number}",
                message=f"You have been assigned to review alert '{alert.rule.name}' for {alert.student.roll_number}. Notes: {notes or 'None'}",
                notification_type="ALERT_ASSIGNED",
                severity="WARNING",
                reference_id=alert.id,
                reference_type="risk_alert",
            )
            db.add(notif)

        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def resolve_alert(
        db: Session,
        alert: RiskAlert,
        user_id: int,
        resolution_reason: str,
        review_notes: Optional[str] = None,
    ) -> RiskAlert:
        old_status = alert.status
        alert.status = "RESOLVED"
        alert.resolution_reason = resolution_reason
        alert.resolved_by_id = user_id
        alert.resolved_at = utcnow()
        if review_notes:
            alert.review_notes = (alert.review_notes or "") + f"\n[{utcnow().strftime('%Y-%m-%d %H:%M')}] Resolved: {review_notes}"

        history = RiskAlertHistory(
            alert_id=alert.id,
            action="RESOLVED",
            old_status=old_status,
            new_status="RESOLVED",
            notes=f"Resolved with reason: '{resolution_reason}'. {review_notes or ''}".strip(),
            performed_by_id=user_id,
        )
        db.add(history)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def reopen_alert(db: Session, alert: RiskAlert, user_id: int, reason: str) -> RiskAlert:
        old_status = alert.status
        alert.status = "UNDER_REVIEW"
        alert.resolution_reason = None
        alert.resolved_by_id = None
        alert.resolved_at = None
        alert.review_notes = (alert.review_notes or "") + f"\n[{utcnow().strftime('%Y-%m-%d %H:%M')}] Reopened: {reason}"

        history = RiskAlertHistory(
            alert_id=alert.id,
            action="REOPENED",
            old_status=old_status,
            new_status="UNDER_REVIEW",
            notes=f"Alert reopened: {reason}",
            performed_by_id=user_id,
        )
        db.add(history)
        db.commit()
        db.refresh(alert)
        return alert

    # -------------------------------------------------------------------------
    # STATISTICS & DASHBOARD METRICS
    # -------------------------------------------------------------------------
    @staticmethod
    def get_risk_statistics(db: Session, department_id: Optional[int] = None) -> Dict[str, Any]:
        base_query = db.query(RiskAlert).join(RiskAlert.student)
        if department_id:
            base_query = base_query.filter(Student.department_id == department_id)

        active_query = base_query.filter(RiskAlert.status.in_(["FLAGGED", "ACKNOWLEDGED", "UNDER_REVIEW"]))

        total_active = active_query.count()
        total_students_at_risk = active_query.with_entities(func.count(func.distinct(RiskAlert.student_id))).scalar() or 0

        # Severity breakdown
        sev_counts = dict(
            active_query.with_entities(RiskAlert.severity, func.count(RiskAlert.id))
            .group_by(RiskAlert.severity)
            .all()
        )
        severity_distribution = {
            "critical": sev_counts.get("CRITICAL", 0),
            "high": sev_counts.get("HIGH", 0),
            "moderate": sev_counts.get("MODERATE", 0),
            "normal": sev_counts.get("NORMAL", 0),
        }

        # Status breakdown
        stat_counts = dict(
            base_query.with_entities(RiskAlert.status, func.count(RiskAlert.id))
            .group_by(RiskAlert.status)
            .all()
        )

        # Department distribution
        dept_dist = (
            db.query(
                Student.department_id,
                func.count(RiskAlert.id).label("alert_count"),
                func.count(func.distinct(Student.id)).label("student_count"),
            )
            .join(RiskAlert, RiskAlert.student_id == Student.id)
            .filter(RiskAlert.status.in_(["FLAGGED", "ACKNOWLEDGED", "UNDER_REVIEW"]))
            .group_by(Student.department_id)
            .all()
        )
        departments_data = []
        for d_id, a_cnt, s_cnt in dept_dist:
            from app.models.department import Department
            dept = db.query(Department).filter(Department.id == d_id).first()
            departments_data.append({
                "department_id": d_id,
                "department_code": dept.code if dept else f"Dept {d_id}",
                "department_name": dept.name if dept else f"Department {d_id}",
                "alert_count": a_cnt,
                "student_count": s_cnt,
            })

        # Semester distribution
        sem_dist = (
            active_query.with_entities(Student.current_semester, func.count(RiskAlert.id))
            .group_by(Student.current_semester)
            .order_by(Student.current_semester.asc())
            .all()
        )
        semester_data = [{"semester": sem, "alert_count": cnt} for sem, cnt in sem_dist]

        # Rule distribution
        rule_dist = (
            active_query.join(RiskAlert.rule)
            .with_entities(RiskRule.name, RiskRule.category, func.count(RiskAlert.id))
            .group_by(RiskRule.name, RiskRule.category)
            .all()
        )
        rule_data = [{"rule_name": name, "category": cat, "count": cnt} for name, cat, cnt in rule_dist]

        # Recent evaluations
        recent_evals = db.query(RiskEvaluation).order_by(desc(RiskEvaluation.created_at)).limit(5).all()

        return {
            "total_active_alerts": total_active,
            "total_students_at_risk": total_students_at_risk,
            "severity_distribution": severity_distribution,
            "status_distribution": stat_counts,
            "department_distribution": departments_data,
            "semester_distribution": semester_data,
            "rule_distribution": rule_data,
            "recent_evaluations": recent_evals,
        }

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------
    @staticmethod
    def get_user_notifications(db: Session, user_id: int, unread_only: bool = False, limit: int = 20) -> List[InAppNotification]:
        query = db.query(InAppNotification).filter(InAppNotification.user_id == user_id)
        if unread_only:
            query = query.filter(InAppNotification.is_read.is_(False))
        return query.order_by(desc(InAppNotification.created_at)).limit(limit).all()

    @staticmethod
    def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
        notif = db.query(InAppNotification).filter(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            db.commit()
            return True
        return False


# ---------------------------------------------------------------------------
# Rule evaluation building blocks
# ---------------------------------------------------------------------------
def compare(value: float, operator: str, threshold: float) -> bool:
    """Apply a rule operator; unknown operators never trigger."""
    if operator == "<":
        return value < threshold
    if operator == "<=":
        return value <= threshold
    if operator == ">":
        return value > threshold
    if operator == ">=":
        return value >= threshold
    if operator == "==":
        return abs(value - threshold) < 1e-4
    return False


@dataclass
class _StudentRiskMetrics:
    """Indicators derived once per student, then checked against every rule."""

    student: Student
    student_name: str
    current_period: str
    attendance_records: List[SubjectAttendance]
    overall_attendance: float
    lowest_subject_attendance: Optional[SubjectAttendance]
    assessments: List[StudentAssessment]
    average_assessment: float
    lowest_assessment: Optional[StudentAssessment]
    previous_semester: Optional[StudentSemesterRecord]
    current_semester: Optional[StudentSemesterRecord]
    sgpa_drop: float
    backlog_count: int
    failed_subject_names: List[str]

    @classmethod
    def from_student(cls, student: Student) -> "_StudentRiskMetrics":
        # Attendance: recomputed from subject records when available, else the stored percentage.
        records = student.attendance_records or []
        overall = student.attendance_percentage
        if records:
            total = sum(r.total_classes for r in records)
            attended = sum(r.attended_classes for r in records)
            if total > 0:
                overall = round((attended / total) * 100.0, 2)
        lowest_att = min(records, key=lambda r: r.attendance_percentage) if records else None

        assessments = student.assessments or []
        average = round(sum(a.percentage for a in assessments) / len(assessments), 2) if assessments else 0.0
        lowest_asm = min(assessments, key=lambda a: a.percentage) if assessments else None

        # SGPA drop between the two most recent semesters (never negative).
        semesters = sorted(student.semester_records or [], key=lambda r: r.semester_number)
        previous = current = None
        drop = 0.0
        if len(semesters) >= 2:
            previous, current = semesters[-2], semesters[-1]
            drop = max(0.0, round(previous.sgpa - current.sgpa, 2))

        # Backlogs: the larger of the latest semester's count and distinct failed subjects on record.
        failed: List[str] = []
        for res in student.subject_results or []:
            if res.is_backlog and res.subject and res.subject.name not in failed:
                failed.append(res.subject.name)
        backlogs = max(semesters[-1].backlogs_count if semesters else 0, len(failed))

        return cls(
            student=student,
            student_name=student.user.full_name if student.user else student.roll_number,
            current_period=f"Semester {student.current_semester}",
            attendance_records=records,
            overall_attendance=overall,
            lowest_subject_attendance=lowest_att,
            assessments=assessments,
            average_assessment=average,
            lowest_assessment=lowest_asm,
            previous_semester=previous,
            current_semester=current,
            sgpa_drop=drop,
            backlog_count=backlogs,
            failed_subject_names=failed,
        )


@dataclass
class _RuleObservation:
    triggered: bool = False
    value: float = 0.0
    display: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    subject_id: Optional[int] = None


def _observe_attendance(m: _StudentRiskMetrics, rule: RiskRule) -> _RuleObservation:
    """Checks whichever is lower: overall attendance or the weakest subject's attendance."""
    obs = _RuleObservation(value=m.overall_attendance)
    lowest = m.lowest_subject_attendance
    if lowest and lowest.attendance_percentage < obs.value:
        obs.value = lowest.attendance_percentage
        obs.subject_id = lowest.subject_id
        obs.context = {"subject_name": lowest.subject.name if lowest.subject else "Course",
                       "attended_classes": lowest.attended_classes, "total_classes": lowest.total_classes}
    else:
        records = m.attendance_records
        obs.context = {"subject_name": "Overall Curriculum",
                       "attended_classes": sum(r.attended_classes for r in records) if records else 0,
                       "total_classes": sum(r.total_classes for r in records) if records else 0}
    obs.display = f"{obs.value:.1f}% ({obs.context['attended_classes']}/{obs.context['total_classes']} classes)"
    obs.triggered = compare(obs.value, rule.operator, rule.threshold_value)
    return obs


def _observe_assessments(m: _StudentRiskMetrics, rule: RiskRule) -> _RuleObservation:
    """Flags the weakest assessment if it breaches the threshold, otherwise checks the average."""
    if not m.assessments:
        return _RuleObservation()
    lowest = m.lowest_assessment
    if lowest and compare(lowest.percentage, rule.operator, rule.threshold_value):
        return _RuleObservation(
            triggered=True,
            value=lowest.percentage,
            display=f"{lowest.percentage:.1f}% ({lowest.marks_obtained}/{lowest.max_marks})",
            subject_id=lowest.subject_id,
            context={"subject_name": lowest.subject.name if lowest.subject else "Course",
                     "assessment_name": lowest.assessment_type,
                     "marks_obtained": lowest.marks_obtained, "max_marks": lowest.max_marks},
        )
    average = m.average_assessment
    return _RuleObservation(
        triggered=compare(average, rule.operator, rule.threshold_value),
        value=average,
        display=f"{average:.1f}% CIA Average",
        context={"subject_name": "All Subjects CIA Average", "assessment_name": "Internal Evaluations Average",
                 "marks_obtained": average, "max_marks": 100.0},
    )


def _observe_sgpa_drop(m: _StudentRiskMetrics, rule: RiskRule) -> _RuleObservation:
    prev, curr = m.previous_semester, m.current_semester
    return _RuleObservation(
        triggered=m.sgpa_drop > 0.0 and compare(m.sgpa_drop, rule.operator, rule.threshold_value),
        value=m.sgpa_drop,
        display=f"Δ -{m.sgpa_drop:.2f} SGPA",
        context={"prev_sgpa": prev.sgpa if prev else 0.0,
                 "curr_sgpa": curr.sgpa if curr else 0.0,
                 "prev_sem": f"Semester {prev.semester_number}" if prev else "Previous",
                 "curr_sem": f"Semester {curr.semester_number}" if curr else m.current_period},
    )


def _observe_backlogs(m: _StudentRiskMetrics, rule: RiskRule) -> _RuleObservation:
    value = float(m.backlog_count)
    return _RuleObservation(
        triggered=m.backlog_count > 0 and compare(value, rule.operator, rule.threshold_value),
        value=value,
        display=f"{m.backlog_count} Active Backlog(s)",
        context={"failed_subjects": m.failed_subject_names},
    )


def _observe_missing_assessments(m: _StudentRiskMetrics, rule: RiskRule) -> _RuleObservation:
    """An enrolled student with no recorded assessments counts as one missing evaluation."""
    missing = 1 if not m.assessments and (m.attendance_records or m.student.current_semester >= 1) else 0
    return _RuleObservation(
        triggered=compare(float(missing), rule.operator, rule.threshold_value),
        value=float(missing),
        display=f"{missing} Missing Evaluation(s)",
        context={"subject_name": "Enrolled Curriculum"},
    )


def _observe_composite(m: _StudentRiskMetrics, rule: RiskRule) -> _RuleObservation:
    """Low attendance AND a low assessment average together (limits from the rule's conditions_config)."""
    config = rule.conditions_config or {}
    low_attendance = m.overall_attendance < float(config.get("min_attendance", 75.0))
    low_assessments = m.average_assessment < float(config.get("max_assessment_pct", 50.0)) and len(m.assessments) > 0
    if not (low_attendance and low_assessments):
        return _RuleObservation()
    return _RuleObservation(
        triggered=True,
        value=1.0,
        display=f"Att: {m.overall_attendance:.1f}%, CIA: {m.average_assessment:.1f}%",
        context={"attendance_val": m.overall_attendance, "cia_val": m.average_assessment},
    )


# RiskRule.indicator_type -> how that indicator is observed for one student.
_INDICATOR_OBSERVERS = {
    "attendance_percentage": _observe_attendance,
    "assessment_percentage": _observe_assessments,
    "sgpa_drop": _observe_sgpa_drop,
    "backlog_count": _observe_backlogs,
    "missing_assessments": _observe_missing_assessments,
    "composite": _observe_composite,
}
