from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.academic import Semester, Subject, FacultyCourseAssignment
from app.models.profile import Student, Faculty, Mentor, StudentMentorAssignment
from app.models.audit import AuditLog
from app.schemas.dashboard import RoleDashboardResponse


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_for_user(self, user: User) -> RoleDashboardResponse:
        role = user.role
        if role == UserRole.STUDENT.value:
            return self._get_student_dashboard(user)
        elif role == UserRole.FACULTY.value:
            return self._get_faculty_dashboard(user)
        elif role == UserRole.MENTOR.value:
            return self._get_mentor_dashboard(user)
        elif role == UserRole.ADMIN.value:
            return self._get_admin_dashboard(user)
        elif role == UserRole.PLACEMENT_OFFICER.value:
            return self._get_placement_dashboard(user)
        else:
            return self._get_fallback_dashboard(user)

    def _get_student_dashboard(self, user: User) -> RoleDashboardResponse:
        student = self.db.query(Student).filter(Student.user_id == user.id).first()
        dept = user.department

        cgpa = float(student.cgpa) if student else 0.0
        attendance = float(student.attendance_percentage) if student else 0.0
        semester_num = student.current_semester if student else 1

        # Real count of subjects offered for this student's department & semester
        dept_id = student.department_id if student else (dept.id if dept else 1)
        enrolled_subjects = self.db.query(Subject).filter(
            Subject.department_id == dept_id,
            Subject.semester_number == semester_num
        ).all()

        total_credits = sum(s.credits for s in enrolled_subjects) if enrolled_subjects else 0

        mentor_name = "Not Assigned"
        mentor_email = "N/A"
        if student and student.mentor and student.mentor.user:
            mentor_name = student.mentor.user.full_name
            mentor_email = student.mentor.user.email

        summary_cards = [
            {"title": "Cumulative CGPA", "value": f"{cgpa:.2f}", "change": "Scale 10.0", "trend": "neutral", "icon": "GraduationCap"},
            {"title": "Overall Attendance", "value": f"{attendance:.1f}%", "change": "Required min 75%", "trend": "positive" if attendance >= 75 else "negative", "icon": "CalendarCheck"},
            {"title": "Active Courses", "value": str(len(enrolled_subjects)), "change": f"{total_credits} Credit hours", "trend": "neutral", "icon": "BookOpen"},
            {"title": "Faculty Mentor", "value": mentor_name, "change": mentor_email, "trend": "neutral", "icon": "UserCheck"},
        ]

        # Recent audit logs for student
        user_audits = self.db.query(AuditLog).filter(
            AuditLog.user_id == user.id
        ).order_by(AuditLog.created_at.desc()).limit(5).all()

        recent_activity = [
            {
                "id": a.id,
                "action": a.action.replace("_", " ").title(),
                "time": a.created_at.strftime("%b %d, %H:%M"),
                "details": str(a.details.get("reason") or a.details.get("role") or "User activity recorded")
            }
            for a in user_audits
        ]

        return RoleDashboardResponse(
            role=UserRole.STUDENT.value,
            summary_cards=summary_cards,
            quick_stats={
                "usn": student.usn if student else "N/A",
                "roll_number": student.roll_number if student else "N/A",
                "section": student.section if student else "A",
                "batch_year": student.batch_year if student else 2024,
                "department": dept.name if dept else "Engineering",
                "courses": [{"code": s.code, "name": s.name, "credits": s.credits, "type": s.subject_type} for s in enrolled_subjects]
            },
            recent_activity=recent_activity,
            details={"student_id": student.id if student else None}
        )

    def _get_faculty_dashboard(self, user: User) -> RoleDashboardResponse:
        faculty = self.db.query(Faculty).filter(Faculty.user_id == user.id).first()
        dept = user.department

        # Course assignments
        assignments = []
        if faculty:
            assignments = self.db.query(FacultyCourseAssignment).filter(
                FacultyCourseAssignment.faculty_id == faculty.id
            ).all()

        total_subjects = len(assignments)

        # Count students in department
        dept_id = faculty.department_id if faculty else (dept.id if dept else 1)
        total_dept_students = self.db.query(Student).filter(Student.department_id == dept_id).count()

        avg_dept_att = self.db.query(func.avg(Student.attendance_percentage)).filter(
            Student.department_id == dept_id
        ).scalar() or 0.0

        summary_cards = [
            {"title": "Allocated Subjects", "value": str(total_subjects), "change": "Current semester", "trend": "neutral", "icon": "BookOpen"},
            {"title": "Department Students", "value": str(total_dept_students), "change": f"{dept.code if dept else 'Dept'}", "trend": "neutral", "icon": "Users"},
            {"title": "Dept Avg Attendance", "value": f"{float(avg_dept_att):.1f}%", "change": "Cohort average", "trend": "positive" if avg_dept_att >= 75 else "negative", "icon": "Activity"},
            {"title": "Designation", "value": faculty.designation if faculty else "Faculty", "change": faculty.employee_id if faculty else "", "trend": "neutral", "icon": "Award"},
        ]

        # Recent activities
        audits = self.db.query(AuditLog).filter(
            AuditLog.user_id == user.id
        ).order_by(AuditLog.created_at.desc()).limit(5).all()

        recent_activity = [
            {
                "id": a.id,
                "action": a.action.replace("_", " ").title(),
                "time": a.created_at.strftime("%b %d, %H:%M"),
                "details": str(a.details.get("role") or a.details.get("reason") or "Faculty session activity")
            }
            for a in audits
        ]

        assigned_details = [
            {
                "id": a.id,
                "subject_code": a.subject.code if a.subject else "N/A",
                "subject_name": a.subject.name if a.subject else "N/A",
                "section": a.section,
                "credits": a.subject.credits if a.subject else 3
            }
            for a in assignments
        ]

        return RoleDashboardResponse(
            role=UserRole.FACULTY.value,
            summary_cards=summary_cards,
            quick_stats={
                "employee_id": faculty.employee_id if faculty else "N/A",
                "department": dept.name if dept else "N/A",
                "assigned_courses": assigned_details
            },
            recent_activity=recent_activity,
            details={"faculty_id": faculty.id if faculty else None}
        )

    def _get_mentor_dashboard(self, user: User) -> RoleDashboardResponse:
        mentor = self.db.query(Mentor).filter(Mentor.user_id == user.id).first()

        mentees = []
        if mentor:
            mentees = self.db.query(Student).filter(Student.assigned_mentor_id == mentor.id).all()

        total_mentees = len(mentees)
        at_risk_mentees = [m for m in mentees if m.attendance_percentage < 75.0 or m.cgpa < 6.0]
        avg_cgpa = (sum(m.cgpa for m in mentees) / total_mentees) if total_mentees > 0 else 0.0

        summary_cards = [
            {"title": "Assigned Mentees", "value": str(total_mentees), "change": f"Capacity: {mentor.max_mentees if mentor else 30}", "trend": "neutral", "icon": "Users"},
            {"title": "Mentees Needing Attention", "value": str(len(at_risk_mentees)), "change": "Attendance <75% or CGPA <6.0", "trend": "negative" if at_risk_mentees else "positive", "icon": "AlertTriangle"},
            {"title": "Cohort Avg CGPA", "value": f"{avg_cgpa:.2f}", "change": "Scale of 10.0", "trend": "positive" if avg_cgpa >= 7.5 else "neutral", "icon": "TrendingUp"},
            {"title": "Mentorship Status", "value": "Active", "change": f"{mentor.designation if mentor else 'Lead Mentor'}", "trend": "positive", "icon": "ShieldCheck"},
        ]

        mentee_roster = [
            {
                "id": m.id,
                "name": m.user.full_name if m.user else "Student",
                "roll_number": m.roll_number,
                "usn": m.usn,
                "cgpa": m.cgpa,
                "attendance": m.attendance_percentage,
                "status": "At Risk" if (m.attendance_percentage < 75 or m.cgpa < 6.0) else "On Track"
            }
            for m in mentees
        ]

        return RoleDashboardResponse(
            role=UserRole.MENTOR.value,
            summary_cards=summary_cards,
            quick_stats={
                "total_mentees": total_mentees,
                "at_risk_count": len(at_risk_mentees),
                "mentee_roster": mentee_roster
            },
            recent_activity=[],
            details={"mentor_id": mentor.id if mentor else None}
        )

    def _get_admin_dashboard(self, user: User) -> RoleDashboardResponse:
        total_users = self.db.query(User).count()
        total_students = self.db.query(Student).count()
        total_faculty = self.db.query(Faculty).count()
        total_departments = self.db.query(Department).count()
        total_subjects = self.db.query(Subject).count()

        summary_cards = [
            {"title": "Total Users Registered", "value": str(total_users), "change": "Across 5 roles", "trend": "positive", "icon": "Users"},
            {"title": "Active Departments", "value": str(total_departments), "change": f"{total_subjects} Courses configured", "trend": "neutral", "icon": "Building2"},
            {"title": "Enrolled Students", "value": str(total_students), "change": "All semesters", "trend": "neutral", "icon": "GraduationCap"},
            {"title": "Academic Faculty", "value": str(total_faculty), "change": "Active teaching staff", "trend": "neutral", "icon": "Briefcase"},
        ]

        # Recent audit logs
        recent_audits = self.db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(8).all()
        recent_activity = [
            {
                "id": a.id,
                "action": a.action.replace("_", " ").title(),
                "user": a.user.email if a.user else "System",
                "time": a.created_at.strftime("%b %d, %H:%M:%S"),
                "ip": a.ip_address or "Internal",
                "details": str(a.details or {})
            }
            for a in recent_audits
        ]

        # Department breakdown
        dept_breakdown = []
        for d in self.db.query(Department).all():
            st_count = self.db.query(Student).filter(Student.department_id == d.id).count()
            fa_count = self.db.query(Faculty).filter(Faculty.department_id == d.id).count()
            dept_breakdown.append({
                "code": d.code,
                "name": d.name,
                "students": st_count,
                "faculty": fa_count
            })

        return RoleDashboardResponse(
            role=UserRole.ADMIN.value,
            summary_cards=summary_cards,
            quick_stats={
                "departments": dept_breakdown,
                "total_users": total_users,
                "total_subjects": total_subjects,
                "system_status": "Operational (v0.1.0)"
            },
            recent_activity=recent_activity,
            details={}
        )

    def _get_placement_dashboard(self, user: User) -> RoleDashboardResponse:
        total_students = self.db.query(Student).count()
        # Genuine query for eligible students (CGPA >= 7.0 and attendance >= 75%)
        eligible_students = self.db.query(Student).filter(
            Student.cgpa >= 7.0,
            Student.attendance_percentage >= 75.0
        ).all()
        eligible_count = len(eligible_students)

        placed_count = self.db.query(Student).filter(Student.placement_status == "Placed").count()
        avg_campus_cgpa = self.db.query(func.avg(Student.cgpa)).scalar() or 0.0

        summary_cards = [
            {"title": "Placement Eligible Cohort", "value": str(eligible_count), "change": f"of {total_students} total students", "trend": "positive", "icon": "CheckCircle2"},
            {"title": "Campus Avg CGPA", "value": f"{float(avg_campus_cgpa):.2f}", "change": "Across all departments", "trend": "neutral", "icon": "BarChart3"},
            {"title": "Already Placed", "value": str(placed_count), "change": f"{(placed_count/total_students*100 if total_students > 0 else 0):.1f}% Conversion", "trend": "positive", "icon": "Award"},
            {"title": "Participating Branches", "value": str(self.db.query(Department).count()), "change": "All departments active", "trend": "neutral", "icon": "Briefcase"},
        ]

        eligible_roster = [
            {
                "id": s.id,
                "name": s.user.full_name if s.user else "Student",
                "usn": s.usn,
                "roll": s.roll_number,
                "department": s.department.code if s.department else "ENG",
                "cgpa": s.cgpa,
                "status": s.placement_status
            }
            for s in eligible_students[:10]
        ]

        return RoleDashboardResponse(
            role=UserRole.PLACEMENT_OFFICER.value,
            summary_cards=summary_cards,
            quick_stats={
                "total_students": total_students,
                "eligible_count": eligible_count,
                "placed_count": placed_count,
                "eligible_roster": eligible_roster
            },
            recent_activity=[],
            details={}
        )

    def _get_fallback_dashboard(self, user: User) -> RoleDashboardResponse:
        return RoleDashboardResponse(
            role=user.role,
            summary_cards=[{"title": "Role", "value": user.role, "change": user.email, "trend": "neutral", "icon": "User"}],
            quick_stats={},
            recent_activity=[],
            details={}
        )
