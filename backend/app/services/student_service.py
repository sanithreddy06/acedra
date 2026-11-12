"""Student intelligence & analytics (module 1): profiles, academic records, analytics and CSV/Excel import."""
import csv
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import openpyxl
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.access import faculty_student_ids
from app.core.clock import utcnow
from app.models.academic import (
    FacultyCourseAssignment,
    Semester,
    StudentAssessment,
    StudentSemesterRecord,
    Subject,
    SubjectAttendance,
    SubjectResult,
)
from app.models.department import Department
from app.models.platform import DEFAULT_ACADEMIC_STRUCTURE, University
from app.models.profile import Faculty, Student
from app.models.student_intelligence import (
    Certification,
    ImportError,
    ImportJob,
    Internship,
    Project,
    Skill,
    StudentSkill,
)
from app.models.user import User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.schemas.student_intelligence import (
    AdminAnalyticsOut,
    CertificationCreate,
    FacultyAnalyticsOut,
    ImportPreviewResult,
    InternshipCreate,
    ProjectCreate,
    StudentAnalyticsOut,
    StudentCreate,
    StudentProfileOut,
    StudentSkillCreate,
    StudentUpdate,
)
from app.services.invitation_service import InvitationService

logger = logging.getLogger(__name__)

IMPORT_TYPES = ("students", "academic_records", "attendance")
COLUMN_ALIASES = {"department_code": "department", "attendance_percentage": "attendance", "name": "full_name",
                  "grade_letter": "grade", "letter_grade": "grade"}
# Letter grade -> grade point on the 10-point scale used by the bundled data; F is a backlog.
GRADE_POINTS = {"O": 10.0, "A+": 9.0, "A": 8.0, "B+": 7.0, "B": 6.0, "C": 5.0, "P": 4.0, "F": 0.0}


@dataclass
class _ImportContext:
    university: Any
    departments: Dict[str, int]
    current_term: Optional[Semester]


def _text(row: Dict[str, Any], key: str) -> str:
    value = row.get(key)
    return "" if value is None else str(value).strip()


def _int(row: Dict[str, Any], key: str, *, required: bool = False, default: Optional[int] = None) -> Optional[int]:
    raw = _text(row, key)
    if not raw:
        if required:
            raise ValueError(f"{key} is required.")
        return default
    try:
        return int(float(raw))
    except ValueError:
        raise ValueError(f"{key} must be a whole number (got '{raw}').") from None


def _number_errors(row: Dict[str, Any], *, ints=(), floats=(), required=()) -> List[str]:
    """Preview-time checks mirroring what the import handlers will accept."""
    errors = []
    for key in ints:
        try:
            _int(row, key, required=key in required)
        except ValueError as exc:
            errors.append(str(exc))
    for key in floats:
        try:
            _float(row, key, default=0.0)
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def _float(row: Dict[str, Any], key: str, *, default: float) -> float:
    raw = _text(row, key)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"{key} must be a number (got '{raw}').") from None


class StudentIntelligenceService:
    def __init__(self, db: Session):
        self.db = db

    # 1. Student Listing & Search
    def list_students(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        semester: Optional[int] = None,
        section: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[StudentProfileOut], int]:
        query = self.db.query(Student).join(User, Student.user_id == User.id)

        # Who appears here is decided by the session's student scope (core/access.py), the same rule that
        # governs opening a record directly; this list adds no extra filters of its own.
        if current_user.role == UserRole.STUDENT.value:
            query = query.filter(Student.user_id == current_user.id)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    func.lower(User.full_name).like(search_term),
                    func.lower(User.email).like(search_term),
                    func.lower(Student.usn).like(search_term),
                    func.lower(Student.roll_number).like(search_term),
                    func.lower(Student.srn).like(search_term),
                )
            )

        if department_id:
            query = query.filter(Student.department_id == department_id)
        if semester:
            query = query.filter(Student.current_semester == semester)
        if section:
            query = query.filter(Student.section == section.upper())
        if status_filter and status_filter != "all":
            query = query.filter(Student.status == status_filter)

        total = query.count()
        students = query.order_by(Student.id.desc()).offset(skip).limit(limit).all()

        results = [self._format_student_profile(s) for s in students]
        return results, total

    # 2. Get Single Student Profile (with strict RBAC)
    def get_student_by_id(self, student_id: int, current_user: User) -> StudentProfileOut:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student ID {student_id} not found.")

        # RBAC verification: Student can only view their own profile
        if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Students are only authorized to view their own personal records.",
            )

        return self._format_student_profile(student)

    # 3. Create Student Profile (Admin only)
    def create_student(self, data: StudentCreate, current_user: User) -> StudentProfileOut:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Only administrators can create student accounts.")

        # Check duplicate USN or Roll Number
        existing_student = (
            self.db.query(Student)
            .filter(or_(Student.usn == data.usn.upper(), Student.roll_number == data.roll_number.upper()))
            .first()
        )
        if existing_student:
            raise HTTPException(
                status_code=400,
                detail=f"Student with USN '{data.usn}' or Roll Number '{data.roll_number}' already exists.",
            )

        # No default passwords: the student receives an invitation and sets their own credentials.
        user, _, _ = InvitationService(self.db).create_user_with_invitation(
            email=data.email,
            full_name=data.full_name,
            role=UserRole.STUDENT.value,
            university=self._university(current_user),
            invited_by=current_user,
            department_id=data.department_id,
        )

        srn_val = data.srn.upper() if data.srn else f"SRN-{data.usn.upper()}"

        student = Student(
            user_id=user.id,
            roll_number=data.roll_number.upper(),
            usn=data.usn.upper(),
            srn=srn_val,
            department_id=data.department_id,
            program=data.program,
            current_semester=data.current_semester,
            batch_year=data.batch_year,
            admission_year=data.admission_year,
            section=data.section.upper(),
            status=data.status,
            placement_status=data.placement_status,
            assigned_mentor_id=data.assigned_mentor_id,
            gender=data.gender,
            dob=data.dob,
            blood_group=data.blood_group,
            guardian_name=data.guardian_name,
            guardian_contact=data.guardian_contact,
            address=data.address,
            cgpa=0.0,
            attendance_percentage=100.0,
        )
        self.db.add(student)
        self.db.commit()
        self.db.refresh(student)

        # Log audit entry
        self._log_audit(
            action="STUDENT_CREATED",
            user_id=current_user.id,
            resource_type="student",
            resource_id=str(student.id),
            details={"usn": student.usn, "email": user.email, "srn": student.srn},
        )

        return self._format_student_profile(student)

    # 4. Update Student Profile
    def update_student(self, student_id: int, data: StudentUpdate, current_user: User) -> StudentProfileOut:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found.")

        # Only an administrator may change a student record. Students may update their own contact
        # details. Faculty, mentors and placement officers have read access only.
        is_admin = current_user.role == UserRole.ADMIN.value
        is_self = current_user.role == UserRole.STUDENT.value and student.user_id == current_user.id
        if not (is_admin or is_self):
            raise HTTPException(status_code=403, detail="You are not authorised to modify this student record.")

        update_dict = data.model_dump(exclude_unset=True)

        if is_self:
            allowed_fields = {"address", "blood_group", "guardian_contact", "guardian_name"}
            update_dict = {k: v for k, v in update_dict.items() if k in allowed_fields}

        # Columns that can never be empty: an explicit null is ignored rather than written.
        for required in ("full_name", "program", "current_semester", "section", "status"):
            if required in update_dict and update_dict[required] in (None, ""):
                del update_dict[required]

        if update_dict.get("assigned_mentor_id") is not None:
            from app.models import Mentor
            if not self.db.query(Mentor.id).filter(Mentor.id == update_dict["assigned_mentor_id"]).first():
                raise HTTPException(status_code=422, detail="Mentor not found in your university.")

        if "full_name" in update_dict and current_user.role == UserRole.ADMIN.value:
            student.user.full_name = update_dict.pop("full_name")

        for key, val in update_dict.items():
            setattr(student, key, val)

        self.db.commit()
        self.db.refresh(student)

        self._log_audit(
            action="STUDENT_UPDATED",
            user_id=current_user.id,
            resource_type="student",
            resource_id=str(student.id),
            details={"fields_updated": list(update_dict.keys())},
        )

        # Trigger automatic risk evaluation on student record update
        try:
            from app.services.risk_service import RiskService

            RiskService.evaluate_risk(
                db=self.db, student_id=student.id, run_type="STUDENT_UPDATE", user_id=current_user.id
            )
        except Exception:
            # The profile update is already committed; a failed re-evaluation must not turn it into an error.
            logger.warning("Automatic risk evaluation failed after updating student %s", student.id, exc_info=True)

        return self._format_student_profile(student)

    # 5. Full Individual Student Analytics Dashboard
    def get_student_analytics(self, student_id: int, current_user: User) -> StudentAnalyticsOut:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found.")

        # RBAC Check: Student only access own records
        if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied. You may only view your personal records.")

        profile_out = self._format_student_profile(student)

        # 1. Semester-wise academic progress & SGPA progression
        sem_records = (
            self.db.query(StudentSemesterRecord)
            .filter(StudentSemesterRecord.student_id == student.id)
            .order_by(StudentSemesterRecord.semester_number.asc())
            .all()
        )

        sgpa_trend = [
            {
                "semester": f"Sem {r.semester_number}",
                "semester_number": r.semester_number,
                "sgpa": r.sgpa,
                "credits_registered": r.credits_registered,
                "credits_earned": r.credits_earned,
                "backlogs": r.backlogs_count,
                "status": r.status,
            }
            for r in sem_records
        ]

        # 2. Subject Results for current / latest semester
        results = self.db.query(SubjectResult).filter(SubjectResult.student_id == student.id).all()

        subject_performance = [
            {
                "subject_code": r.subject.code if r.subject else "N/A",
                "subject_name": r.subject.name if r.subject else "Subject",
                "internal_marks": r.internal_marks,
                "external_marks": r.external_marks,
                "total_marks": r.total_marks,
                "letter_grade": r.letter_grade,
                "grade_point": r.grade_point,
                "is_backlog": r.is_backlog,
            }
            for r in results
        ]

        # 3. Attendance Breakdown (calculated from raw counts)
        att_records = self.db.query(SubjectAttendance).filter(SubjectAttendance.student_id == student.id).all()

        attendance_breakdown = []
        total_classes_sum = 0
        attended_classes_sum = 0

        for a in att_records:
            total_classes_sum += a.total_classes
            attended_classes_sum += a.attended_classes
            pct = round((a.attended_classes / a.total_classes * 100.0), 1) if a.total_classes > 0 else 100.0
            attendance_breakdown.append(
                {
                    "id": a.id,
                    "student_id": a.student_id,
                    "subject_id": a.subject_id,
                    "subject_code": a.subject.code if a.subject else "N/A",
                    "subject_name": a.subject.name if a.subject else "N/A",
                    "semester_id": a.semester_id,
                    "total_classes": a.total_classes,
                    "attended_classes": a.attended_classes,
                    "missed_classes": max(0, a.total_classes - a.attended_classes),
                    "attendance_percentage": pct,
                }
            )

        calculated_overall_attendance = (
            round((attended_classes_sum / total_classes_sum * 100.0), 1)
            if total_classes_sum > 0
            else student.attendance_percentage
        )

        # 4. Continuous Assessments & CIA average
        assessments = (
            self.db.query(StudentAssessment)
            .filter(StudentAssessment.student_id == student.id)
            .order_by(StudentAssessment.created_at.desc())
            .all()
        )

        assessment_history = [
            {
                "id": ass.id,
                "student_id": ass.student_id,
                "subject_id": ass.subject_id,
                "subject_code": ass.subject.code if ass.subject else "N/A",
                "subject_name": ass.subject.name if ass.subject else "N/A",
                "semester_id": ass.semester_id,
                "assessment_type": ass.assessment_type,
                "max_marks": ass.max_marks,
                "marks_obtained": ass.marks_obtained,
                "percentage": round((ass.marks_obtained / ass.max_marks * 100.0), 1) if ass.max_marks > 0 else 0.0,
                "remarks": ass.remarks,
                "assessment_date": ass.assessment_date,
            }
            for ass in assessments
        ]

        internal_avg = (
            round(sum(a["percentage"] for a in assessment_history) / len(assessment_history), 1)
            if assessment_history
            else 0.0
        )

        # 5. Skills categorized for Module 4 compatibility
        student_skills = self.db.query(StudentSkill).filter(StudentSkill.student_id == student.id).join(Skill).all()

        skills_by_category: Dict[str, List[Any]] = {
            "programming": [],
            "framework": [],
            "database": [],
            "cloud": [],
            "tool": [],
            "soft_skill": [],
        }

        for sk in student_skills:
            cat = sk.skill.category if sk.skill and sk.skill.category in skills_by_category else "tool"
            skills_by_category[cat].append(
                {
                    "id": sk.id,
                    "skill_id": sk.skill_id,
                    "skill_name": sk.skill.name if sk.skill else "Skill",
                    "category": cat,
                    "proficiency_level": sk.proficiency_level,
                    "is_verified": sk.is_verified,
                }
            )

        # 6. Certifications, Projects, Internships, Hackathons
        certs = [
            {
                "id": c.id,
                "student_id": c.student_id,
                "title": c.title,
                "issuing_organization": c.issuing_organization,
                "issue_date": c.issue_date,
                "expiry_date": c.expiry_date,
                "credential_id": c.credential_id,
                "credential_url": c.credential_url,
                "verification_status": c.verification_status,
            }
            for c in student.certifications
        ]

        projs = [
            {
                "id": p.id,
                "student_id": p.student_id,
                "title": p.title,
                "description": p.description,
                "tech_stack": p.tech_stack,
                "role": p.role,
                "github_url": p.github_url,
                "live_url": p.live_url,
                "semester_number": p.semester_number,
            }
            for p in student.projects
        ]

        interns = [
            {
                "id": i.id,
                "student_id": i.student_id,
                "company_name": i.company_name,
                "role": i.role,
                "start_date": i.start_date,
                "end_date": i.end_date,
                "stipend": i.stipend,
                "description": i.description,
                "status": i.status,
            }
            for i in student.internships
        ]

        hacks = [
            {
                "id": h.id,
                "student_id": h.student_id,
                "event_name": h.event_name,
                "organizer": h.organizer,
                "year": h.year,
                "achievement": h.achievement,
                "project_title": h.project_title,
            }
            for h in student.hackathons
        ]

        total_backlogs = sum(r.backlogs_count for r in sem_records)
        total_credits_earned = sum(r.credits_earned for r in sem_records)

        metrics = {
            "cgpa": student.cgpa,
            "calculated_attendance_percentage": calculated_overall_attendance,
            "internal_assessment_average": internal_avg,
            "total_credits_earned": total_credits_earned,
            "total_backlogs": total_backlogs,
            "total_skills_count": len(student_skills),
            "certifications_count": len(certs),
            "projects_count": len(projs),
            "internships_count": len(interns),
            "hackathons_count": len(hacks),
        }

        return StudentAnalyticsOut(
            student_profile=profile_out,
            metrics=metrics,
            sgpa_trend=sgpa_trend,
            subject_performance=subject_performance,
            attendance_breakdown=attendance_breakdown,
            assessment_history=assessment_history,
            skills_by_category=skills_by_category,
            certifications=certs,
            projects=projs,
            internships=interns,
            hackathons=hacks,
        )

    # 6. Faculty Analytics (Authorized Assigned Students)
    def get_faculty_analytics(self, current_user: User) -> FacultyAnalyticsOut:
        """Teaching view for the caller's own faculty profile: their sections and the students in them.

        Without a faculty profile there is nothing taught, so the response is an explicit empty state
        (``profile_configured = False``) rather than another department's data.
        """
        if current_user.role not in [UserRole.FACULTY.value, UserRole.ADMIN.value]:
            raise HTTPException(status_code=403, detail="Authorized to Faculty and Administrators only.")

        faculty = current_user.faculty_profile
        dept = current_user.department or (faculty.department if faculty else None)
        if faculty is None:
            return FacultyAnalyticsOut(
                faculty_id=None, faculty_name=current_user.full_name, department_name=dept.name if dept else None,
                assigned_courses=[], total_assigned_students=0, average_cohort_attendance=0.0,
                average_cohort_marks=0.0, students_summary=[], profile_configured=False,
            )

        assignments = (
            self.db.query(FacultyCourseAssignment).filter(FacultyCourseAssignment.faculty_id == faculty.id).all()
        )
        assigned_courses = [
            {
                "assignment_id": a.id,
                "subject_code": a.subject.code if a.subject else "N/A",
                "subject_name": a.subject.name if a.subject else "N/A",
                "section": a.section,
                "academic_year": a.academic_year,
            }
            for a in assignments
        ]

        # The cohort is exactly the students this faculty member is authorised to see.
        cohort_ids = faculty_student_ids(self.db, current_user, faculty)
        students = (
            self.db.query(Student).filter(Student.id.in_(cohort_ids)).order_by(Student.attendance_percentage).all()
            if cohort_ids else []
        )
        faculty_id = faculty.id
        faculty_name = current_user.full_name
        dept_name = dept.name if dept else None

        total_students = len(students)
        avg_att = (sum(s.attendance_percentage for s in students) / total_students) if total_students > 0 else 0.0
        avg_cgpa = (sum(s.cgpa for s in students) / total_students) if total_students > 0 else 0.0

        students_summary = [
            {
                "id": s.id,
                "name": s.user.full_name if s.user else "Student",
                "usn": s.usn,
                "roll_number": s.roll_number,
                "semester": s.current_semester,
                "section": s.section,
                "cgpa": s.cgpa,
                "attendance": s.attendance_percentage,
                "status": s.status,
            }
            for s in students[:20]  # lowest attendance first
        ]

        return FacultyAnalyticsOut(
            faculty_id=faculty_id,
            faculty_name=faculty_name,
            department_name=dept_name,
            assigned_courses=assigned_courses,
            total_assigned_students=total_students,
            average_cohort_attendance=round(avg_att, 1),
            average_cohort_marks=round(avg_cgpa * 10, 1),  # Scale out of 100
            students_summary=students_summary,
        )

    # 7. Administrator / HOD Analytics
    def get_admin_analytics(self, current_user: User) -> AdminAnalyticsOut:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Authorized to Administrators / HOD only.")

        total_students = self.db.query(Student).count()
        active_students = self.db.query(Student).filter(Student.status == "Active").count()
        total_faculty = self.db.query(Faculty).count()
        total_departments = self.db.query(Department).count()

        avg_campus_cgpa = float(self.db.query(func.avg(Student.cgpa)).scalar() or 0.0)
        avg_campus_attendance = float(self.db.query(func.avg(Student.attendance_percentage)).scalar() or 0.0)

        # Department-wise statistics, aggregated in the database (no student rows are loaded).
        from app.models.risk import RiskAlert
        depts = self.db.query(Department).all()
        per_dept = {
            dept_id: (count, cgpa, att)
            for dept_id, count, cgpa, att in self.db.query(
                Student.department_id, func.count(Student.id), func.avg(Student.cgpa),
                func.avg(Student.attendance_percentage)).group_by(Student.department_id).all()
        }
        # "Needing support" means the same thing everywhere on the dashboard: students with an open early alert.
        open_alerts = dict(
            self.db.query(Student.department_id, func.count(func.distinct(RiskAlert.student_id)))
            .join(RiskAlert, RiskAlert.student_id == Student.id)
            .filter(RiskAlert.status.in_(["FLAGGED", "ACKNOWLEDGED", "UNDER_REVIEW"]))
            .group_by(Student.department_id).all()
        )
        dept_stats = []
        for d in depts:
            d_count, d_avg_cgpa, d_avg_att = per_dept.get(d.id, (0, 0.0, 0.0))
            dept_stats.append(
                {
                    "department_code": d.code,
                    "department_name": d.name,
                    "total_students": d_count,
                    "average_cgpa": round(float(d_avg_cgpa or 0.0), 2),
                    "average_attendance": round(float(d_avg_att or 0.0), 1),
                    "at_risk_count": open_alerts.get(d.id, 0),
                    "hod_name": d.hod_name,
                }
            )

        # Term-wise statistics, following this university's configured academic structure
        sem_stats = self._term_breakdown(current_user)

        # Attendance Distribution
        att_dist = {
            "above_85": self.db.query(Student).filter(Student.attendance_percentage >= 85.0).count(),
            "between_75_85": self.db.query(Student)
            .filter(and_(Student.attendance_percentage >= 75.0, Student.attendance_percentage < 85.0))
            .count(),
            "below_75_at_risk": self.db.query(Student).filter(Student.attendance_percentage < 75.0).count(),
        }

        # CGPA Distribution
        cgpa_dist = {
            "tier_1_above_9": self.db.query(Student).filter(Student.cgpa >= 9.0).count(),
            "tier_2_8_to_9": self.db.query(Student).filter(and_(Student.cgpa >= 8.0, Student.cgpa < 9.0)).count(),
            "tier_3_7_to_8": self.db.query(Student).filter(and_(Student.cgpa >= 7.0, Student.cgpa < 8.0)).count(),
            "tier_4_6_to_7": self.db.query(Student).filter(and_(Student.cgpa >= 6.0, Student.cgpa < 7.0)).count(),
            "below_6_at_risk": self.db.query(Student).filter(Student.cgpa < 6.0).count(),
        }

        # Import Jobs Statistics
        import_jobs_count = self.db.query(ImportJob).count()
        recent_jobs = self.db.query(ImportJob).order_by(ImportJob.created_at.desc()).limit(5).all()

        import_stats = {
            "total_import_batches": import_jobs_count,
            "recent_batches": [
                {
                    "id": j.id,
                    "filename": j.filename,
                    "type": j.import_type,
                    "status": j.status,
                    "success": j.successful_rows,
                    "failed": j.failed_rows,
                    "date": j.created_at.strftime("%b %d, %H:%M"),
                }
                for j in recent_jobs
            ],
        }

        institutional_stats = {
            "total_students": total_students,
            "active_students": active_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "campus_average_cgpa": round(avg_campus_cgpa, 2),
            "campus_average_attendance": round(avg_campus_attendance, 1),
        }

        return AdminAnalyticsOut(
            institutional_stats=institutional_stats,
            department_wise_stats=dept_stats,
            semester_wise_performance=sem_stats,
            attendance_distribution=att_dist,
            cgpa_distribution=cgpa_dist,
            import_stats=import_stats,
        )

    def _term_breakdown(self, current_user: User) -> List[Dict[str, Any]]:
        """Students and averages for every term of the university's programme.

        The number of terms is ``terms_per_year × programme_duration_years`` from the tenant's academic
        structure (defaults in ``DEFAULT_ACADEMIC_STRUCTURE``), labelled with its ``term_label``. Terms with
        no students are included so the structure is visible; any recorded term beyond the configured range
        is appended rather than hidden.
        """
        university = self.db.query(University).filter(University.id == current_user.university_id).first()
        structure = {**DEFAULT_ACADEMIC_STRUCTURE, **((university.academic_structure if university else None) or {})}
        label = str(structure.get("term_label") or "Semester")
        try:
            configured = int(structure["terms_per_year"]) * int(structure["programme_duration_years"])
        except (TypeError, ValueError):
            configured = 8
        configured = max(1, min(configured, 24))

        rows = (
            self.db.query(Student.current_semester, func.count(Student.id), func.avg(Student.cgpa),
                          func.avg(Student.attendance_percentage))
            .group_by(Student.current_semester)
            .all()
        )
        by_term = {term: (count, cgpa, att) for term, count, cgpa, att in rows if term is not None}
        terms = sorted(set(range(1, configured + 1)) | set(by_term))
        breakdown = []
        for term in terms:
            count, cgpa, att = by_term.get(term, (0, None, None))
            breakdown.append({
                "semester": f"{label} {term}",
                "semester_number": term,
                "student_count": count,
                "average_cgpa": round(float(cgpa or 0.0), 2),
                "average_attendance": round(float(att or 0.0), 1),
            })
        return breakdown

    # 8. Add Student Skill
    def add_student_skill(self, student_id: int, data: StudentSkillCreate, current_user: User) -> StudentSkill:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found.")

        if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized.")

        # Find or create skill
        skill = self.db.query(Skill).filter(func.lower(Skill.name) == data.skill_name.lower()).first()
        if not skill:
            skill = Skill(name=data.skill_name.strip(), category=data.category)
            self.db.add(skill)
            self.db.flush()

        # Check existing student skill
        existing = (
            self.db.query(StudentSkill)
            .filter(StudentSkill.student_id == student.id, StudentSkill.skill_id == skill.id)
            .first()
        )

        if existing:
            existing.proficiency_level = data.proficiency_level
            self.db.commit()
            return existing

        st_skill = StudentSkill(
            student_id=student.id, skill_id=skill.id, proficiency_level=data.proficiency_level, is_verified=False
        )
        self.db.add(st_skill)
        self.db.commit()
        self.db.refresh(st_skill)
        return st_skill

    # 9. Add Certification, Project, Internship, Hackathon
    def add_certification(self, student_id: int, data: CertificationCreate, current_user: User) -> Certification:
        student = self._verify_student_access(student_id, current_user)
        cert = Certification(
            student_id=student.id,
            title=data.title,
            issuing_organization=data.issuing_organization,
            issue_date=data.issue_date,
            expiry_date=data.expiry_date,
            credential_id=data.credential_id,
            credential_url=data.credential_url,
            verification_status="Verified",
        )
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def add_project(self, student_id: int, data: ProjectCreate, current_user: User) -> Project:
        student = self._verify_student_access(student_id, current_user)
        proj = Project(
            student_id=student.id,
            title=data.title,
            description=data.description,
            tech_stack=data.tech_stack,
            role=data.role,
            github_url=data.github_url,
            live_url=data.live_url,
            semester_number=data.semester_number,
        )
        self.db.add(proj)
        self.db.commit()
        self.db.refresh(proj)
        return proj

    def add_internship(self, student_id: int, data: InternshipCreate, current_user: User) -> Internship:
        student = self._verify_student_access(student_id, current_user)
        intern = Internship(
            student_id=student.id,
            company_name=data.company_name,
            role=data.role,
            start_date=data.start_date,
            end_date=data.end_date,
            stipend=data.stipend,
            description=data.description,
            status=data.status,
        )
        self.db.add(intern)
        self.db.commit()
        self.db.refresh(intern)
        return intern

    # 10. Data Import: Preview CSV/Excel
    def preview_import_file(
        self, file: UploadFile, import_type: str, current_user: User, column_mapping: Optional[Dict[str, str]] = None
    ) -> ImportPreviewResult:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Data import requires administrator privileges.")

        filename = file.filename or "uploaded_data.csv"
        # Security: extension whitelist
        allowed_exts = (".csv", ".xlsx", ".xls")
        if not any(filename.lower().endswith(ext) for ext in allowed_exts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format '{filename}'. Only CSV and Excel (.xlsx, .xls) files are accepted for import.",
            )

        content = file.file.read()  # blocking read: these handlers run in the worker thread pool
        # Security: maximum 10MB file size limit
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds maximum permitted limit (10MB)."
            )

        is_excel = filename.endswith(".xlsx") or filename.endswith(".xls")
        rows, columns = self._parse_file_rows(content, is_excel)
        rows, columns = self._apply_mapping(rows, columns, column_mapping)

        # Validate rows
        valid_rows = []
        errors = []

        existing_usns = {s[0].upper() for s in self.db.query(Student.usn).all()}
        existing_emails = {u[0].lower() for u in self.db.query(User.email).all()}

        seen_in_batch_usn = set()
        seen_in_batch_email = set()
        dept_codes = {d[0].upper() for d in self.db.query(Department.code).all()}
        subject_codes = {c[0].upper() for c in self.db.query(Subject.code).all()}

        for idx, row in enumerate(rows, start=1):
            row_errors = []
            # Check required fields for student import
            if import_type == "students":
                usn = str(row.get("usn", "")).strip().upper()
                email = str(row.get("email", "")).strip().lower()
                name = str(row.get("name", "")).strip() or str(row.get("full_name", "")).strip()

                if not usn:
                    row_errors.append("Missing required field: USN")
                elif usn in existing_usns:
                    row_errors.append(f"Duplicate USN '{usn}' already exists in database")
                elif usn in seen_in_batch_usn:
                    row_errors.append(f"Duplicate USN '{usn}' found within this upload batch")
                else:
                    seen_in_batch_usn.add(usn)

                if not email:
                    row_errors.append("Missing required field: Email")
                elif "@" not in email:
                    row_errors.append(f"Invalid email format: '{email}'")
                elif email in existing_emails:
                    row_errors.append(f"Duplicate email '{email}' already registered")
                elif email in seen_in_batch_email:
                    row_errors.append(f"Duplicate email '{email}' found within this upload batch")
                else:
                    seen_in_batch_email.add(email)

                if not name:
                    row_errors.append("Missing required field: Full Name")
                dept_code = _text(row, "department").upper()
                if dept_code not in dept_codes:
                    row_errors.append(f"Unknown department code '{dept_code or '(blank)'}'")
                row_errors += _number_errors(row, ints=["semester"], required=["semester"], floats=["cgpa", "attendance"])

            elif import_type == "academic_records":
                usn = str(row.get("usn", "")).strip().upper()
                if not usn:
                    row_errors.append("Missing USN")
                elif usn not in existing_usns and usn not in seen_in_batch_usn:
                    row_errors.append(f"Student USN '{usn}' does not exist")
                if _text(row, "subject_code").upper() not in subject_codes:
                    row_errors.append(f"Subject '{_text(row, 'subject_code') or '(blank)'}' not found")
                if _text(row, "grade").upper() not in GRADE_POINTS:
                    row_errors.append(f"Unknown grade '{_text(row, 'grade') or '(blank)'}'")
                row_errors += _number_errors(row, ints=["semester_number"], required=["semester_number"],
                                             floats=["internal_marks", "external_marks", "total_marks"])

            elif import_type == "attendance":
                usn = str(row.get("usn", "")).strip().upper()
                if not usn:
                    row_errors.append("Missing USN")
                elif usn not in existing_usns:
                    row_errors.append(f"Student USN '{usn}' does not exist")
                if _text(row, "subject_code").upper() not in subject_codes:
                    row_errors.append(f"Subject '{_text(row, 'subject_code') or '(blank)'}' not found")

                total = row.get("total_classes")
                attended = row.get("attended_classes")
                try:
                    if int(attended) > int(total):
                        row_errors.append(f"Attended classes ({attended}) cannot exceed total classes ({total})")
                except (ValueError, TypeError):
                    row_errors.append("Classes counts must be valid integers")

            if row_errors:
                errors.append(
                    {
                        "row_number": idx,
                        "row_data": row,
                        "error_message": "; ".join(row_errors),
                    }
                )
            else:
                valid_rows.append(row)

        return ImportPreviewResult(
            filename=filename,
            import_type=import_type,
            total_rows=len(rows),
            valid_rows_count=len(valid_rows),
            invalid_rows_count=len(errors),
            columns_detected=columns,
            preview_rows=rows[:10],
            errors=errors[:20],
        )

    # --- import row handlers (each raises ValueError with a message shown to the administrator) ---
    def _import_student_row(self, row: Dict[str, Any], ctx: "_ImportContext", current_user: User) -> None:
        """Create an invited (inactive) student account and profile. CGPA and attendance start empty
        (0 and no recorded absences, as for manually created students) unless the file provides them."""
        usn = _text(row, "usn").upper()
        email = _text(row, "email").lower()
        name = _text(row, "name") or _text(row, "full_name")
        if not usn or not email or not name:
            raise ValueError("usn, email and full_name are required.")
        dept_code = _text(row, "department").upper()
        if dept_code not in ctx.departments:
            raise ValueError(f"Unknown department code '{dept_code or '(blank)'}'. "
                             f"Known codes: {', '.join(sorted(ctx.departments)) or 'none — add departments first'}.")
        semester = _int(row, "semester", required=True)
        if self.db.query(Student).filter(Student.usn == usn).first():
            raise ValueError(f"Student USN '{usn}' already exists.")
        cgpa = _float(row, "cgpa", default=0.0)
        attendance = _float(row, "attendance", default=100.0)
        try:
            user, _, _ = InvitationService(self.db).create_user_with_invitation(
                email=email, full_name=name, role=UserRole.STUDENT.value, university=ctx.university,
                invited_by=current_user, department_id=ctx.departments[dept_code],
            )
        except HTTPException as exc:
            raise ValueError(str(exc.detail)) from exc
        admission_year = _int(row, "admission_year", default=None)
        batch_year = _int(row, "batch_year", default=None) or admission_year or utcnow().year
        self.db.add(Student(
            user_id=user.id,
            roll_number=(_text(row, "roll_number") or f"R-{usn}").upper(),
            usn=usn,
            srn=(_text(row, "srn") or f"SRN-{usn}").upper(),
            department_id=ctx.departments[dept_code],
            current_semester=semester,
            batch_year=batch_year,
            admission_year=admission_year or batch_year,
            section=(_text(row, "section") or "A").upper(),
            status="Active",
            cgpa=cgpa,
            attendance_percentage=attendance,
            placement_status="Eligible" if (cgpa >= 7.0 and attendance >= 75.0) else "Ineligible",
        ))
        self.db.flush()

    def _import_attendance_row(self, row: Dict[str, Any], ctx: "_ImportContext", current_user: User) -> None:
        """Record class attendance for one student and subject in the current term."""
        student = self._student_by_usn(row)
        subject = self._subject_by_code(row)
        if ctx.current_term is None:
            raise ValueError("No current term is configured; mark one term as current first.")
        total = _int(row, "total_classes", required=True)
        attended = _int(row, "attended_classes", required=True)
        if total <= 0 or attended < 0 or attended > total:
            raise ValueError(f"Attended ({attended}) must be between 0 and total classes ({total}).")
        self.db.add(SubjectAttendance(student_id=student.id, subject_id=subject.id, semester_id=ctx.current_term.id,
                                      total_classes=total, attended_classes=attended))

    def _import_result_row(self, row: Dict[str, Any], ctx: "_ImportContext", current_user: User) -> None:
        """Create or update a student's result for one subject in one term."""
        student = self._student_by_usn(row)
        subject = self._subject_by_code(row)
        term_number = _int(row, "semester_number", required=True)
        term = self.db.query(Semester).filter(Semester.semester_number == term_number).first()
        if term is None:
            raise ValueError(f"Term {term_number} is not configured for this university.")
        internal = _float(row, "internal_marks", default=0.0)
        external = _float(row, "external_marks", default=0.0)
        total = _float(row, "total_marks", default=internal + external)
        if not 0 <= total <= 100:
            raise ValueError(f"total_marks must be between 0 and 100 (got {total}).")
        grade = _text(row, "grade").upper()
        if grade not in GRADE_POINTS:
            raise ValueError(f"Unknown grade '{grade or '(blank)'}'. Use one of: {', '.join(GRADE_POINTS)}.")
        result = self.db.query(SubjectResult).filter(
            SubjectResult.student_id == student.id, SubjectResult.subject_id == subject.id,
            SubjectResult.semester_id == term.id).first()
        if result is None:
            result = SubjectResult(student_id=student.id, subject_id=subject.id, semester_id=term.id)
            self.db.add(result)
        result.internal_marks = internal
        result.external_marks = external
        result.total_marks = total
        result.letter_grade = grade
        result.grade_point = GRADE_POINTS[grade]
        result.is_backlog = grade == "F"

    def _student_by_usn(self, row: Dict[str, Any]) -> Student:
        usn = _text(row, "usn").upper()
        student = self.db.query(Student).filter(Student.usn == usn).first() if usn else None
        if student is None:
            raise ValueError(f"Student USN '{usn or '(blank)'}' not found.")
        return student

    def _subject_by_code(self, row: Dict[str, Any]) -> Subject:
        code = _text(row, "subject_code").upper()
        subject = self.db.query(Subject).filter(Subject.code == code).first() if code else None
        if subject is None:
            raise ValueError(f"Subject '{code or '(blank)'}' not found.")
        return subject

    # 11. Execute Batch Import
    def execute_import(
        self, file: UploadFile, import_type: str, current_user: User, column_mapping: Optional[Dict[str, str]] = None
    ) -> ImportJob:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Administrator privileges required.")

        filename = file.filename or "import_data.csv"
        # Security: extension whitelist
        allowed_exts = (".csv", ".xlsx", ".xls")
        if not any(filename.lower().endswith(ext) for ext in allowed_exts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format '{filename}'. Only CSV and Excel (.xlsx, .xls) files are accepted for import.",
            )

        if import_type not in IMPORT_TYPES:
            raise HTTPException(status_code=422, detail=f"Unknown import type '{import_type}'. "
                                                        f"Use one of: {', '.join(IMPORT_TYPES)}.")

        content = file.file.read()  # blocking read: these handlers run in the worker thread pool
        # Security: maximum 10MB file size limit
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds maximum permitted limit (10MB)."
            )

        is_excel = filename.endswith(".xlsx") or filename.endswith(".xls")
        rows, _ = self._parse_file_rows(content, is_excel)
        rows, _ = self._apply_mapping(rows, _, column_mapping)

        job = ImportJob(
            filename=filename,
            file_type="xlsx" if is_excel else "csv",
            import_type=import_type,
            status="processing",
            total_rows=len(rows),
            successful_rows=0,
            failed_rows=0,
            created_by=current_user.id,
        )
        self.db.add(job)
        self.db.flush()

        ctx = _ImportContext(
            university=self._university(current_user),
            departments={d.code.upper(): d.id for d in self.db.query(Department).all()},
            current_term=self.db.query(Semester).filter(Semester.is_current.is_(True)).first(),
        )
        handlers = {
            "students": self._import_student_row,
            "attendance": self._import_attendance_row,
            "academic_records": self._import_result_row,
        }
        handle = handlers[import_type]

        successful = 0
        failed = 0

        for idx, row in enumerate(rows, start=1):
            try:
                with self.db.begin_nested():  # a failed row leaves nothing half-written
                    handle(row, ctx, current_user)
                successful += 1
            except Exception as e:  # noqa: BLE001 — each bad row is recorded as an import error and the job continues
                failed += 1
                err = ImportError(job_id=job.id, row_number=idx, raw_data=str(row), error_message=str(e))
                self.db.add(err)

        job.successful_rows = successful
        job.failed_rows = failed
        job.status = "completed" if failed == 0 else ("partially_completed" if successful > 0 else "failed")
        self.db.commit()
        self.db.refresh(job)

        self._log_audit(
            action="DATA_IMPORTED",
            user_id=current_user.id,
            resource_type="import_job",
            resource_id=str(job.id),
            details={"type": import_type, "successful": successful, "failed": failed},
        )

        return job

    # 12. Generate Downloadable CSV Template
    def generate_csv_template(self, template_type: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        if template_type == "students":
            writer.writerow(
                [
                    "usn",
                    "srn",
                    "roll_number",
                    "full_name",
                    "email",
                    "department",
                    "program",
                    "semester",
                    "section",
                    "batch_year",
                    "admission_year",
                    "cgpa",
                    "attendance",
                ]
            )
            writer.writerow(
                [
                    "1RV22CS099",
                    "SRN-1RV22CS099",
                    "CS22B099",
                    "Sample Student",
                    "sample.student@your-university.example",
                    "CSE",
                    "B.Tech Computer Science & Engineering",
                    "5",
                    "A",
                    "2024",
                    "2022",
                    "8.50",
                    "92.0",
                ]
            )
        elif template_type == "academic_records":
            writer.writerow(
                [
                    "usn",
                    "semester_number",
                    "subject_code",
                    "internal_marks",
                    "external_marks",
                    "total_marks",
                    "letter_grade",
                    "grade_point",
                ]
            )
            writer.writerow(["1RV22CS001", "5", "CS501", "42", "48", "90", "O", "10.0"])
        elif template_type == "attendance":
            writer.writerow(["usn", "subject_code", "total_classes", "attended_classes"])
            writer.writerow(["1RV22CS001", "CS501", "45", "42"])
        else:
            writer.writerow(["usn", "data"])

        return output.getvalue()

    # Helpers
    def _university(self, current_user: User):
        from app.models.platform import University

        return self.db.query(University).filter(University.id == current_user.university_id).first()

    def _verify_student_access(self, student_id: int, current_user: User) -> Student:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found.")
        if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized access to student record.")
        return student

    def _format_student_profile(self, s: Student) -> StudentProfileOut:
        u = s.user
        dept = s.department
        mentor_name = s.mentor.user.full_name if s.mentor and s.mentor.user else None

        return StudentProfileOut(
            id=s.id,
            user_id=s.user_id,
            full_name=u.full_name if u else "Student",
            email=u.email if u else "",
            phone=u.phone if u else None,
            roll_number=s.roll_number,
            usn=s.usn,
            srn=s.srn or f"SRN-{s.usn}",
            department_id=s.department_id,
            department_code=dept.code if dept else "ENG",
            department_name=dept.name if dept else "Engineering",
            program=s.program,
            current_semester=s.current_semester,
            batch_year=s.batch_year,
            admission_year=s.admission_year,
            section=s.section,
            status=s.status,
            cgpa=s.cgpa,
            attendance_percentage=s.attendance_percentage,
            placement_status=s.placement_status,
            assigned_mentor_id=s.assigned_mentor_id,
            mentor_name=mentor_name,
            gender=s.gender,
            dob=s.dob,
            blood_group=s.blood_group,
            guardian_name=s.guardian_name,
            guardian_contact=s.guardian_contact,
            address=s.address,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )

    @staticmethod
    def _apply_mapping(rows, columns, mapping: Optional[Dict[str, str]]):
        """Rename source columns to ACEDRA field names, e.g. {"Student Email": "email"}, then accept the common
        alternative headers in ``COLUMN_ALIASES`` (used by the bundled sample files)."""
        if mapping:
            clean = {str(k).strip().lower(): str(v).strip().lower() for k, v in mapping.items() if v}
            rows = [{clean.get(str(k).strip().lower(), k): v for k, v in r.items()} for r in rows]
            columns = [clean.get(str(c).strip().lower(), c) for c in columns]
        for alias, field in COLUMN_ALIASES.items():
            if alias in columns and field not in columns:
                rows = [{(field if k == alias else k): v for k, v in r.items()} for r in rows]
                columns = [field if c == alias else c for c in columns]
        return rows, columns

    def _parse_file_rows(self, content: bytes, is_excel: bool) -> Tuple[List[Dict[str, Any]], List[str]]:
        rows = []
        columns = []
        if is_excel:
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            sheet = wb.active
            header_row = next(sheet.iter_rows(values_only=True))
            columns = [str(c).strip().lower() for c in header_row if c is not None]
            for r in sheet.iter_rows(min_row=2, values_only=True):
                if not any(r):
                    continue
                row_dict = {}
                for col_idx, col_name in enumerate(columns):
                    val = r[col_idx] if col_idx < len(r) else None
                    row_dict[col_name] = val
                rows.append(row_dict)
        else:
            text = content.decode("utf-8-sig", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            if reader.fieldnames:
                columns = [c.strip().lower() for c in reader.fieldnames]
            for r in reader:
                cleaned = {k.strip().lower(): v.strip() if isinstance(v, str) else v for k, v in r.items() if k}
                rows.append(cleaned)
        return rows, columns

    def _log_audit(
        self, action: str, user_id: Optional[int], resource_type: str, resource_id: str, details: Dict[str, Any]
    ):
        AuditRepository(self.db).log(
            action=action, user_id=user_id, resource_type=resource_type, resource_id=resource_id, details=details
        )
