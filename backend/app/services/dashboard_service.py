"""Role dashboards (module 6): one summary per university role — student, faculty, mentor,
administrator and placement officer — built from data already limited to the caller's scope."""
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.academic import FacultyCourseAssignment, StudentSemesterRecord, Subject
from app.models.audit import AuditLog
from app.models.department import Department
from app.models.intervention import Intervention, InterventionFollowup, InterventionStatus
from app.models.placement import CareerRole, PlacementOpportunity, StudentApplication
from app.models.profile import Faculty, Mentor, Student
from app.models.recommendation import Recommendation
from app.models.risk import RiskAlert
from app.models.student_intelligence import StudentSkill
from app.models.user import User, UserRole
from app.schemas.dashboard import RoleDashboardResponse


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_role_dashboard(self, user: User) -> RoleDashboardResponse:
        role = user.role
        if role == UserRole.STUDENT.value:
            return self.get_student_dashboard(user)
        elif role == UserRole.FACULTY.value:
            return self.get_faculty_dashboard(user)
        elif role == UserRole.MENTOR.value:
            return self.get_mentor_dashboard(user)
        elif role == UserRole.ADMIN.value:
            return self.get_admin_dashboard(user)
        elif role == UserRole.PLACEMENT_OFFICER.value:
            return self.get_placement_dashboard(user)
        else:
            return self.get_fallback_dashboard(user)

    def get_student_dashboard(self, user: User) -> RoleDashboardResponse:
        student = self.db.query(Student).filter(Student.user_id == user.id).first()
        dept = user.department

        cgpa = float(student.cgpa) if student and student.cgpa else 0.0
        attendance = float(student.attendance_percentage) if student and student.attendance_percentage else 0.0
        semester_num = student.current_semester if student else 1
        student_id = student.id if student else None

        # Enrolled subjects
        dept_id = student.department_id if student else (dept.id if dept else 1)
        enrolled_subjects = self.db.query(Subject).filter(
            Subject.department_id == dept_id,
            Subject.semester_number == semester_num
        ).all()
        total_credits = sum(s.credits for s in enrolled_subjects) if enrolled_subjects else 0

        # Mentor details
        mentor_name = "Not Assigned"
        mentor_designation = "Lead Mentor"
        if student and student.mentor and student.mentor.user:
            mentor_name = student.mentor.user.full_name
            mentor_designation = student.mentor.designation or "Academic Mentor"

        # Active Risk Alerts
        active_alerts = []
        if student_id:
            active_alerts = self.db.query(RiskAlert).filter(
                RiskAlert.student_id == student_id,
                RiskAlert.status == "ACTIVE"
            ).order_by(desc(RiskAlert.created_at)).all()

        # Top Recommendations
        recs = []
        if student_id:
            recs = self.db.query(Recommendation).filter(
                Recommendation.student_id == student_id,
                Recommendation.status != "DISMISSED"
            ).order_by(desc(Recommendation.created_at)).limit(4).all()

        # Academic records / SGPA progression
        academic_records = []
        if student_id:
            academic_records = self.db.query(StudentSemesterRecord).filter(
                StudentSemesterRecord.student_id == student_id
            ).order_by(StudentSemesterRecord.semester_id.asc()).all()

        sgpa_trends = []
        for idx, rec in enumerate(academic_records):
            sgpa_trends.append({
                "semester": f"Sem {idx + 1}",
                "sgpa": float(rec.sgpa) if rec.sgpa else 0.0,
                "cgpa": float(student.cgpa) if student and student.cgpa else 0.0,
            })
        if not sgpa_trends:
            sgpa_trends = [
                {"semester": "Sem 1", "sgpa": max(5.0, round(cgpa - 0.4, 2)), "cgpa": round(cgpa - 0.4, 2)},
                {"semester": "Sem 2", "sgpa": max(5.0, round(cgpa - 0.2, 2)), "cgpa": round(cgpa - 0.3, 2)},
                {"semester": "Sem 3", "sgpa": cgpa, "cgpa": cgpa},
            ]

        # Active Interventions
        interventions = []
        if student_id:
            interventions = self.db.query(Intervention).filter(
                Intervention.student_id == student_id
            ).order_by(desc(Intervention.updated_at)).limit(3).all()

        # Student Skills & Placement readiness
        skills_count = 0
        if student_id:
            skills_count = self.db.query(StudentSkill).filter(StudentSkill.student_id == student_id).count()

        readiness_score = min(100, int((cgpa / 10.0) * 40 + (attendance / 100.0) * 30 + min(skills_count * 10, 30)))

        summary_cards = [
            {
                "title": "Cumulative CGPA",
                "value": f"{cgpa:.2f}",
                "change": "Scale of 10.0",
                "trend": "positive" if cgpa >= 7.5 else ("neutral" if cgpa >= 6.0 else "negative"),
                "icon": "GraduationCap",
            },
            {
                "title": "Overall Attendance",
                "value": f"{attendance:.1f}%",
                "change": "Minimum 75% threshold",
                "trend": "positive" if attendance >= 75 else "negative",
                "icon": "CalendarCheck",
            },
            {
                "title": "Placement Readiness",
                "value": f"{readiness_score}%",
                "change": f"{skills_count} verified skills",
                "trend": "positive" if readiness_score >= 70 else "neutral",
                "icon": "Target",
            },
            {
                "title": "Faculty Mentor",
                "value": mentor_name,
                "change": mentor_designation,
                "trend": "neutral",
                "icon": "UserCheck",
            },
        ]

        quick_stats = {
            "usn": student.usn if student else "N/A",
            "roll_number": student.roll_number if student else "N/A",
            "section": student.section if student else "A",
            "current_semester": semester_num,
            "department": dept.name if dept else "Computer Science & Engineering",
            "total_credits": total_credits,
            "skills_count": skills_count,
            "readiness_score": readiness_score,
            "active_alerts_count": len(active_alerts),
            "recommendations_count": len(recs),
            "interventions_count": len(interventions),
            "sgpa_trends": sgpa_trends,
        }

        details = {
            "student_id": student_id,
            "mentor_id": student.assigned_mentor_id if student else None,
            "alerts": [
                {
                    "id": a.id,
                    "title": a.rule.name if a.rule else "Performance Alert",
                    "severity": a.severity,
                    "description": a.ai_explanation or "Attendance or academic threshold flag",
                    "created_at": a.detected_date.isoformat() if a.detected_date else None,
                }
                for a in active_alerts
            ],
            "recommendations": [
                {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "difficulty": r.priority,
                    "score": 85,
                    "resource_url": r.resource_url,
                }
                for r in recs
            ],
            "interventions": [
                {
                    "id": i.id,
                    "title": i.title,
                    "type": i.intervention_type,
                    "priority": i.priority,
                    "status": i.status,
                    "mentor_name": i.mentor.user.full_name if i.mentor and i.mentor.user else "Assigned Mentor",
                }
                for i in interventions
            ],
            "enrolled_courses": [
                {"code": s.code, "name": s.name, "credits": s.credits, "type": s.subject_type}
                for s in enrolled_subjects
            ],
        }

        recent_activity = []  # no activity feed for this role yet; never show invented events

        return RoleDashboardResponse(
            role=UserRole.STUDENT.value,
            summary_cards=summary_cards,
            quick_stats=quick_stats,
            recent_activity=recent_activity,
            details=details,
        )

    def get_faculty_dashboard(self, user: User) -> RoleDashboardResponse:
        faculty = self.db.query(Faculty).filter(Faculty.user_id == user.id).first()
        dept = user.department
        dept_id = faculty.department_id if faculty else (dept.id if dept else 1)

        assignments = []
        if faculty:
            assignments = (
                self.db.query(FacultyCourseAssignment).filter(FacultyCourseAssignment.faculty_id == faculty.id).all()
            )

        total_subjects = len(assignments)
        dept_students = self.db.query(Student).filter(Student.department_id == dept_id).all()
        total_dept_students = len(dept_students)

        avg_dept_att = sum(s.attendance_percentage for s in dept_students) / max(total_dept_students, 1)
        avg_dept_cgpa = sum(s.cgpa for s in dept_students) / max(total_dept_students, 1)

        # Department active risk alerts
        dept_student_ids = [s.id for s in dept_students]
        active_risk_alerts = (
            self.db.query(RiskAlert)
            .filter(RiskAlert.student_id.in_(dept_student_ids), RiskAlert.status == "ACTIVE")
            .all()
        )

        # Grade distribution breakdown
        distinction = len([s for s in dept_students if s.cgpa >= 8.5])
        first_class = len([s for s in dept_students if 7.0 <= s.cgpa < 8.5])
        second_class = len([s for s in dept_students if 6.0 <= s.cgpa < 7.0])
        needs_support = len([s for s in dept_students if s.cgpa < 6.0])

        performance_distribution = [
            {
                "category": "Distinction (>= 8.5)",
                "count": distinction,
                "percentage": round(distinction / max(total_dept_students, 1) * 100, 1),
            },
            {
                "category": "First Class (7.0 - 8.4)",
                "count": first_class,
                "percentage": round(first_class / max(total_dept_students, 1) * 100, 1),
            },
            {
                "category": "Second Class (6.0 - 6.9)",
                "count": second_class,
                "percentage": round(second_class / max(total_dept_students, 1) * 100, 1),
            },
            {
                "category": "Needs Support (< 6.0)",
                "count": needs_support,
                "percentage": round(needs_support / max(total_dept_students, 1) * 100, 1),
            },
        ]

        summary_cards = [
            {
                "title": "Allocated Courses",
                "value": str(total_subjects),
                "change": "Current Academic Term",
                "trend": "neutral",
                "icon": "BookOpen",
            },
            {
                "title": "Department Cohort",
                "value": str(total_dept_students),
                "change": f"{dept.code if dept else 'Dept'} Enrolled",
                "trend": "neutral",
                "icon": "Users",
            },
            {
                "title": "Cohort Avg Attendance",
                "value": f"{avg_dept_att:.1f}%",
                "change": "Mandatory min 75%",
                "trend": "positive" if avg_dept_att >= 75 else "negative",
                "icon": "Activity",
            },
            {
                "title": "Active Risk Flags",
                "value": str(len(active_risk_alerts)),
                "change": "Students flagged for review",
                "trend": "negative" if active_risk_alerts else "positive",
                "icon": "AlertTriangle",
            },
        ]

        quick_stats = {
            "department_name": dept.name if dept else "N/A",
            "department_code": dept.code if dept else "ENG",
            "total_students": total_dept_students,
            "avg_attendance": round(avg_dept_att, 1),
            "avg_cgpa": round(avg_dept_cgpa, 2),
            "performance_distribution": performance_distribution,
        }

        details = {
            "faculty_id": faculty.id if faculty else None,
            "assigned_courses": [
                {
                    "id": a.id,
                    "code": a.subject.code if a.subject else "N/A",
                    "name": a.subject.name if a.subject else "Course",
                    "section": a.section,
                    "credits": a.subject.credits if a.subject else 3,
                    "semester": a.subject.semester_number if a.subject else 1,
                }
                for a in assignments
            ],
            "recent_risk_flags": [
                {
                    "id": a.id,
                    "student_name": a.student.user.full_name if a.student and a.student.user else "Student",
                    "usn": a.student.usn if a.student else "N/A",
                    "severity": a.severity,
                    "explanation": a.ai_explanation or "Subject performance / attendance trigger",
                }
                for a in active_risk_alerts[:6]
            ],
        }

        recent_activity = []  # no activity feed for this role yet; never show invented events

        return RoleDashboardResponse(
            role=UserRole.FACULTY.value,
            summary_cards=summary_cards,
            quick_stats=quick_stats,
            recent_activity=recent_activity,
            details=details,
        )

    def get_mentor_dashboard(self, user: User) -> RoleDashboardResponse:
        mentor = self.db.query(Mentor).filter(Mentor.user_id == user.id).first()

        mentees = []
        if mentor:
            mentees = self.db.query(Student).filter(Student.assigned_mentor_id == mentor.id).all()

        total_mentees = len(mentees)
        mentee_ids = [m.id for m in mentees]

        at_risk_mentees = [m for m in mentees if m.attendance_percentage < 75.0 or m.cgpa < 6.0]
        avg_cgpa = (sum(m.cgpa for m in mentees) / total_mentees) if total_mentees > 0 else 0.0

        # Interventions for this mentor
        interventions_query = self.db.query(Intervention)
        if mentor:
            interventions_query = interventions_query.filter(
                or_(Intervention.mentor_id == mentor.id, Intervention.student_id.in_(mentee_ids))
            )
        all_interventions = interventions_query.all()
        open_interventions = [
            i
            for i in all_interventions
            if i.status
            in [InterventionStatus.OPEN.value, InterventionStatus.ASSIGNED.value, InterventionStatus.IN_PROGRESS.value]
        ]
        resolved_interventions = [
            i
            for i in all_interventions
            if i.status in [InterventionStatus.RESOLVED.value, InterventionStatus.CLOSED.value]
        ]

        # Pending Follow-ups due
        pending_followups = []
        if mentor:
            pending_followups = (
                self.db.query(InterventionFollowup)
                .join(Intervention)
                .filter(
                    or_(
                        InterventionFollowup.mentor_id == mentor.id,
                        Intervention.mentor_id == mentor.id,
                    ),
                    InterventionFollowup.followup_status == "SCHEDULED",
                )
                .order_by(InterventionFollowup.scheduled_date.asc())
                .limit(5)
                .all()
            )

        # Active risk alerts among mentees
        mentee_alerts = []
        if mentee_ids:
            mentee_alerts = (
                self.db.query(RiskAlert)
                .filter(RiskAlert.student_id.in_(mentee_ids), RiskAlert.status == "ACTIVE")
                .order_by(desc(RiskAlert.created_at))
                .limit(6)
                .all()
            )

        summary_cards = [
            {
                "title": "Assigned Mentees",
                "value": str(total_mentees),
                "change": f"Capacity: {mentor.max_mentees if mentor else 30}",
                "trend": "neutral",
                "icon": "Users",
            },
            {
                "title": "Mentees At Risk",
                "value": str(len(at_risk_mentees)),
                "change": "Attendance <75% or CGPA <6.0",
                "trend": "negative" if at_risk_mentees else "positive",
                "icon": "AlertTriangle",
            },
            {
                "title": "Active Interventions",
                "value": str(len(open_interventions)),
                "change": f"{len(resolved_interventions)} resolved cases",
                "trend": "neutral",
                "icon": "ShieldCheck",
            },
            {
                "title": "Upcoming Follow-ups",
                "value": str(len(pending_followups)),
                "change": "Scheduled review sessions",
                "trend": "neutral",
                "icon": "Calendar",
            },
        ]

        quick_stats = {
            "total_mentees": total_mentees,
            "at_risk_count": len(at_risk_mentees),
            "open_interventions": len(open_interventions),
            "resolved_interventions": len(resolved_interventions),
            "pending_followups_count": len(pending_followups),
            "cohort_avg_cgpa": round(avg_cgpa, 2),
        }

        details = {
            "mentor_id": mentor.id if mentor else None,
            "mentee_roster": [
                {
                    "id": m.id,
                    "name": m.user.full_name if m.user else "Student",
                    "roll_number": m.roll_number,
                    "usn": m.usn,
                    "department": m.department.code if m.department else "ENG",
                    "semester": m.current_semester,
                    "cgpa": m.cgpa,
                    "attendance": m.attendance_percentage,
                    "status": "At Risk" if (m.attendance_percentage < 75 or m.cgpa < 6.0) else "On Track",
                }
                for m in mentees
            ],
            "active_interventions": [
                {
                    "id": i.id,
                    "student_name": i.student.user.full_name if i.student and i.student.user else "Student",
                    "title": i.title,
                    "type": i.intervention_type,
                    "priority": i.priority,
                    "status": i.status,
                    "updated_at": i.updated_at.isoformat() if i.updated_at else None,
                }
                for i in open_interventions[:6]
            ],
            "pending_followups": [
                {
                    "id": f.id,
                    "intervention_id": f.intervention_id,
                    "intervention_title": f.intervention.title if f.intervention else None,
                    "student_name": f.intervention.student.user.full_name
                    if f.intervention and f.intervention.student and f.intervention.student.user
                    else "Student",
                    "scheduled_date": f.scheduled_date.isoformat(),
                    "status": f.followup_status,
                }
                for f in pending_followups
            ],
            "mentee_risk_alerts": [
                {
                    "id": a.id,
                    "student_name": a.student.user.full_name if a.student and a.student.user else "Student",
                    "severity": a.severity,
                    "rule": a.rule.name if a.rule else "Warning",
                }
                for a in mentee_alerts
            ],
        }

        recent_activity = []  # no activity feed for this role yet; never show invented events

        return RoleDashboardResponse(
            role=UserRole.MENTOR.value,
            summary_cards=summary_cards,
            quick_stats=quick_stats,
            recent_activity=recent_activity,
            details=details,
        )

    def get_admin_dashboard(self, user: User) -> RoleDashboardResponse:
        total_users = self.db.query(User).count()
        students = self.db.query(Student).all()
        total_students = len(students)
        total_faculty = self.db.query(Faculty).count()
        total_mentors = self.db.query(Mentor).count()
        departments = self.db.query(Department).all()
        total_departments = len(departments)

        # Department Statistics
        dept_breakdown = []
        for d in departments:
            dept_st = [s for s in students if s.department_id == d.id]
            st_count = len(dept_st)
            fa_count = self.db.query(Faculty).filter(Faculty.department_id == d.id).count()
            avg_cg = (sum(s.cgpa for s in dept_st) / st_count) if st_count > 0 else 0.0
            avg_at = (sum(s.attendance_percentage for s in dept_st) / st_count) if st_count > 0 else 0.0
            dept_breakdown.append(
                {
                    "id": d.id,
                    "code": d.code,
                    "name": d.name,
                    "students": st_count,
                    "faculty": fa_count,
                    "avg_cgpa": round(avg_cg, 2),
                    "avg_attendance": round(avg_at, 1),
                }
            )

        # Academic Performance Distribution
        distinction = len([s for s in students if s.cgpa >= 8.5])
        first_class = len([s for s in students if 7.0 <= s.cgpa < 8.5])
        second_class = len([s for s in students if 6.0 <= s.cgpa < 7.0])
        at_risk_academics = len([s for s in students if s.cgpa < 6.0])

        performance_stats = [
            {"label": "Distinction (>= 8.5)", "value": distinction},
            {"label": "First Class (7.0 - 8.4)", "value": first_class},
            {"label": "Second Class (6.0 - 6.9)", "value": second_class},
            {"label": "At Risk (< 6.0)", "value": at_risk_academics},
        ]

        # Attendance Statistics
        att_high = len([s for s in students if s.attendance_percentage >= 85])
        att_med = len([s for s in students if 75 <= s.attendance_percentage < 85])
        att_low = len([s for s in students if s.attendance_percentage < 75])

        attendance_stats = [
            {"label": "Regular (>= 85%)", "value": att_high},
            {"label": "Adequate (75 - 84%)", "value": att_med},
            {"label": "Shortage (< 75%)", "value": att_low},
        ]

        # Risk Alerts Distribution
        alerts = self.db.query(RiskAlert).all()
        critical_alerts = len([a for a in alerts if a.severity == "CRITICAL" and a.status == "ACTIVE"])
        high_alerts = len([a for a in alerts if a.severity == "HIGH" and a.status == "ACTIVE"])
        moderate_alerts = len([a for a in alerts if a.severity == "MODERATE" and a.status == "ACTIVE"])
        low_alerts = len([a for a in alerts if a.severity in ["NORMAL", "LOW"] and a.status == "ACTIVE"])

        risk_distribution = [
            {"severity": "Critical", "count": critical_alerts},
            {"severity": "High", "count": high_alerts},
            {"severity": "Moderate", "count": moderate_alerts},
            {"severity": "Normal", "count": low_alerts},
        ]

        # Intervention statistics
        interventions = self.db.query(Intervention).all()
        it_open = len([i for i in interventions if i.status == InterventionStatus.OPEN.value])
        it_assigned = len([i for i in interventions if i.status == InterventionStatus.ASSIGNED.value])
        it_in_progress = len([i for i in interventions if i.status == InterventionStatus.IN_PROGRESS.value])
        it_resolved = len(
            [
                i
                for i in interventions
                if i.status in [InterventionStatus.RESOLVED.value, InterventionStatus.CLOSED.value]
            ]
        )

        intervention_stats = {
            "total": len(interventions),
            "open": it_open,
            "assigned": it_assigned,
            "in_progress": it_in_progress,
            "resolved": it_resolved,
        }

        # Recommendations statistics
        total_recs = self.db.query(Recommendation).count()
        accepted_recs = self.db.query(Recommendation).filter(Recommendation.status == "ACCEPTED").count()
        completed_recs = self.db.query(Recommendation).filter(Recommendation.status == "COMPLETED").count()

        summary_cards = [
            {
                "title": "Total Enrolled Students",
                "value": str(total_students),
                "change": f"{total_departments} Academic departments",
                "trend": "positive",
                "icon": "GraduationCap",
            },
            {
                "title": "Faculty & Mentors",
                "value": f"{total_faculty} / {total_mentors}",
                "change": "Active academic staff",
                "trend": "neutral",
                "icon": "Users",
            },
            {
                "title": "Active Risk Alerts",
                "value": str(critical_alerts + high_alerts),
                "change": f"{critical_alerts} Critical priority",
                "trend": "negative" if critical_alerts > 0 else "positive",
                "icon": "AlertTriangle",
            },
            {
                "title": "Active Interventions",
                "value": str(it_open + it_assigned + it_in_progress),
                "change": f"{it_resolved} Cases resolved",
                "trend": "positive",
                "icon": "ShieldCheck",
            },
        ]

        quick_stats = {
            "total_users": total_users,
            "total_students": total_students,
            "total_departments": total_departments,
            "performance_stats": performance_stats,
            "attendance_stats": attendance_stats,
            "risk_distribution": risk_distribution,
            "intervention_stats": intervention_stats,
            "recommendation_stats": {
                "total": total_recs,
                "accepted": accepted_recs,
                "completed": completed_recs,
            },
        }

        details = {
            "departments": dept_breakdown,
            "active_version": f"{settings.PROJECT_NAME} {settings.VERSION}",
        }

        # Recent institutional audit logs
        recent_audits = self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(6).all()
        recent_activity = [
            {
                "id": a.id,
                "action": a.action.replace("_", " ").title(),
                "user": a.user.email if a.user else "System",
                "time": a.created_at.isoformat(),
                "details": str(a.details or {}),
            }
            for a in recent_audits
        ]

        return RoleDashboardResponse(
            role=UserRole.ADMIN.value,
            summary_cards=summary_cards,
            quick_stats=quick_stats,
            recent_activity=recent_activity,
            details=details,
        )

    def get_placement_dashboard(self, user: User) -> RoleDashboardResponse:
        students = self.db.query(Student).all()
        total_students = len(students)

        # Eligibility is the recorded placement status (set from the university's criteria), not a fixed cut-off.
        eligible_students = [s for s in students if s.placement_status in ("Eligible", "Placed")]
        eligible_count = len(eligible_students)
        placed_students = [s for s in students if s.placement_status == "Placed"]
        placed_count = len(placed_students)
        avg_cgpa = (sum(s.cgpa for s in students) / total_students) if total_students > 0 else 0.0

        conversion_rate = round((placed_count / max(eligible_count, 1)) * 100, 1)

        # Career Roles
        roles = self.db.query(CareerRole).all()
        role_benchmarks = [
            {
                "id": r.id,
                "title": r.title,
                "category": r.industry_demand,
                "min_experience_level": r.min_experience_level,
                "required_skills_count": len(r.role_skills or []),
            }
            for r in roles
        ]

        # Job Opportunities & Application Pipeline
        opportunities = self.db.query(PlacementOpportunity).all()
        applications = self.db.query(StudentApplication).all()

        pipeline_applied = len([a for a in applications if a.status == "APPLIED"])
        pipeline_shortlisted = len([a for a in applications if a.status == "SHORTLISTED"])
        pipeline_interview = len(
            [a for a in applications if a.status == "INTERVIEW_SCHEDULED"]
        )
        pipeline_offered = len([a for a in applications if a.status == "OFFERED"])
        pipeline_placed = len([a for a in applications if a.status == "PLACED"])

        application_pipeline = [
            {"stage": "Applications Submitted", "count": pipeline_applied},
            {"stage": "Candidate Shortlisted", "count": pipeline_shortlisted},
            {"stage": "Interview Rounds", "count": pipeline_interview},
            {"stage": "Offers Extended", "count": pipeline_offered},
            {"stage": "Placed & Accepted", "count": pipeline_placed},
        ]

        summary_cards = [
            {
                "title": "Placement Eligible Cohort",
                "value": str(eligible_count),
                "change": f"of {total_students} Total Students",
                "trend": "positive",
                "icon": "CheckCircle2",
            },
            {
                "title": "Students Placed",
                "value": str(placed_count),
                "change": f"{conversion_rate}% Conversion",
                "trend": "positive",
                "icon": "Award",
            },
            {
                "title": "Campus Avg CGPA",
                "value": f"{avg_cgpa:.2f}",
                "change": "All Branches Benchmark",
                "trend": "neutral",
                "icon": "BarChart3",
            },
            {
                "title": "Active Recruitment Drives",
                "value": str(len(opportunities)),
                "change": "Corporate Partners",
                "trend": "positive",
                "icon": "Briefcase",
            },
        ]

        quick_stats = {
            "total_students": total_students,
            "eligible_count": eligible_count,
            "placed_count": placed_count,
            "conversion_rate": conversion_rate,
            "career_roles_count": len(roles),
            "opportunities_count": len(opportunities),
            "pipeline": application_pipeline,
        }

        details = {
            "roles": role_benchmarks,
            "opportunities": [
                {
                    "id": o.id,
                    "title": o.title,
                    "company": o.company_name,
                    "location": o.location,
                    "salary_package": o.ctc_stipend,
                    "application_deadline": o.application_deadline.isoformat()
                    if o.application_deadline
                    else "Rolling",
                }
                for o in opportunities[:6]
            ],
            "eligible_roster": [
                {
                    "id": s.id,
                    "name": s.user.full_name if s.user else "Student",
                    "usn": s.usn,
                    "department": s.department.code if s.department else "ENG",
                    "cgpa": s.cgpa,
                    "status": s.placement_status or "Eligible",
                }
                for s in eligible_students[:10]
            ],
        }

        recent_activity = []  # no activity feed for this role yet; never show invented events

        return RoleDashboardResponse(
            role=UserRole.PLACEMENT_OFFICER.value,
            summary_cards=summary_cards,
            quick_stats=quick_stats,
            recent_activity=recent_activity,
            details=details,
        )

    def get_fallback_dashboard(self, user: User) -> RoleDashboardResponse:
        return RoleDashboardResponse(
            role=user.role,
            summary_cards=[
                {"title": "Role", "value": user.role, "change": user.email, "trend": "neutral", "icon": "User"}
            ],
            quick_stats={},
            recent_activity=[],
            details={},
        )
