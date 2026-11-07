import io
import csv
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
import openpyxl
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from fastapi import HTTPException, status, UploadFile

from app.core.security import get_password_hash
from app.models.user import User, UserRole, Role
from app.models.department import Department
from app.models.academic import (
    Semester,
    Subject,
    FacultyCourseAssignment,
    StudentSemesterRecord,
    SubjectResult,
    SubjectAttendance,
    StudentAssessment,
)
from app.models.profile import Student, Faculty, Mentor, StudentMentorAssignment
from app.models.student_intelligence import (
    Skill,
    StudentSkill,
    Certification,
    Project,
    Internship,
    Hackathon,
    ImportJob,
    ImportError,
    SkillCategory,
)
from app.models.audit import AuditLog
from app.schemas.student_intelligence import (
    StudentCreate,
    StudentUpdate,
    StudentProfileOut,
    StudentAnalyticsOut,
    FacultyAnalyticsOut,
    AdminAnalyticsOut,
    ImportPreviewResult,
    StudentSkillCreate,
    CertificationCreate,
    ProjectCreate,
    InternshipCreate,
    HackathonCreate,
)


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

        # Security scoping: if student, only view self
        if current_user.role == UserRole.STUDENT.value:
            query = query.filter(Student.user_id == current_user.id)
        # If faculty, can view students from their department or assigned sections
        elif current_user.role == UserRole.FACULTY.value:
            if current_user.department_id:
                query = query.filter(Student.department_id == current_user.department_id)
        # If mentor, can view their mentees or department
        elif current_user.role == UserRole.MENTOR.value:
            if current_user.mentor_profile:
                # Can view all mentees, or departmental students
                pass

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
        if current_user.role == UserRole.STUDENT.value:
            if student.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: Students are only authorized to view their own personal records."
                )

        return self._format_student_profile(student)

    # 3. Create Student Profile (Admin only)
    def create_student(self, data: StudentCreate, current_user: User) -> StudentProfileOut:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Only administrators can create student accounts.")

        # Check duplicate email
        existing_user = self.db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            raise HTTPException(status_code=400, detail=f"User with email '{data.email}' already exists.")

        # Check duplicate USN or Roll Number
        existing_student = self.db.query(Student).filter(
            or_(Student.usn == data.usn.upper(), Student.roll_number == data.roll_number.upper())
        ).first()
        if existing_student:
            raise HTTPException(status_code=400, detail=f"Student with USN '{data.usn}' or Roll Number '{data.roll_number}' already exists.")

        student_role = self.db.query(Role).filter(Role.name == UserRole.STUDENT.value).first()
        role_id = student_role.id if student_role else None

        user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password or "StudentPass123!"),
            full_name=data.full_name,
            role=UserRole.STUDENT.value,
            role_id=role_id,
            department_id=data.department_id,
            is_active=True,
            is_verified=True,
        )
        self.db.add(user)
        self.db.flush()

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
            details={"usn": student.usn, "email": user.email, "srn": student.srn}
        )

        return self._format_student_profile(student)

    # 4. Update Student Profile
    def update_student(self, student_id: int, data: StudentUpdate, current_user: User) -> StudentProfileOut:
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found.")

        # RBAC: Only Admin or student themselves for specific profile fields
        if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized to modify this student record.")

        update_dict = data.model_dump(exclude_unset=True)

        # If student themselves is updating, only allow personal contact info
        if current_user.role == UserRole.STUDENT.value:
            allowed_fields = {"phone", "address", "blood_group", "guardian_contact", "guardian_name"}
            for k in list(update_dict.keys()):
                if k not in allowed_fields:
                    del update_dict[k]

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
            details={"fields_updated": list(update_dict.keys())}
        )

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
        sem_records = self.db.query(StudentSemesterRecord).filter(
            StudentSemesterRecord.student_id == student.id
        ).order_by(StudentSemesterRecord.semester_number.asc()).all()

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
        results = self.db.query(SubjectResult).filter(
            SubjectResult.student_id == student.id
        ).all()

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
        att_records = self.db.query(SubjectAttendance).filter(
            SubjectAttendance.student_id == student.id
        ).all()

        attendance_breakdown = []
        total_classes_sum = 0
        attended_classes_sum = 0

        for a in att_records:
            total_classes_sum += a.total_classes
            attended_classes_sum += a.attended_classes
            pct = round((a.attended_classes / a.total_classes * 100.0), 1) if a.total_classes > 0 else 100.0
            attendance_breakdown.append({
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
            })

        calculated_overall_attendance = (
            round((attended_classes_sum / total_classes_sum * 100.0), 1)
            if total_classes_sum > 0
            else student.attendance_percentage
        )

        # 4. Continuous Assessments & CIA average
        assessments = self.db.query(StudentAssessment).filter(
            StudentAssessment.student_id == student.id
        ).order_by(StudentAssessment.created_at.desc()).all()

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
        student_skills = self.db.query(StudentSkill).filter(
            StudentSkill.student_id == student.id
        ).join(Skill).all()

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
            skills_by_category[cat].append({
                "id": sk.id,
                "skill_id": sk.skill_id,
                "skill_name": sk.skill.name if sk.skill else "Skill",
                "category": cat,
                "proficiency_level": sk.proficiency_level,
                "is_verified": sk.is_verified,
            })

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
        if current_user.role not in [UserRole.FACULTY.value, UserRole.ADMIN.value]:
            raise HTTPException(status_code=403, detail="Authorized to Faculty and Administrators only.")

        faculty = current_user.faculty_profile
        faculty_id = faculty.id if faculty else 1
        faculty_name = current_user.full_name
        dept_name = current_user.department.name if current_user.department else "Engineering"

        # Assigned subjects
        assignments = self.db.query(FacultyCourseAssignment).filter(
            FacultyCourseAssignment.faculty_id == faculty_id
        ).all()

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

        # Department cohort query
        dept_id = current_user.department_id or (faculty.department_id if faculty else 1)
        students = self.db.query(Student).filter(Student.department_id == dept_id).all()

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
            for s in students[:20]
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

        # Department-wise statistics
        depts = self.db.query(Department).all()
        dept_stats = []
        for d in depts:
            d_students = self.db.query(Student).filter(Student.department_id == d.id).all()
            d_count = len(d_students)
            d_avg_cgpa = sum(s.cgpa for s in d_students) / d_count if d_count > 0 else 0.0
            d_avg_att = sum(s.attendance_percentage for s in d_students) / d_count if d_count > 0 else 0.0
            at_risk = sum(1 for s in d_students if s.attendance_percentage < 75.0 or s.cgpa < 6.0)

            dept_stats.append({
                "department_code": d.code,
                "department_name": d.name,
                "total_students": d_count,
                "average_cgpa": round(d_avg_cgpa, 2),
                "average_attendance": round(d_avg_att, 1),
                "at_risk_count": at_risk,
                "hod_name": d.hod_name,
            })

        # Semester-wise statistics
        sem_stats = []
        for sem in [1, 3, 5, 7]:
            sem_students = self.db.query(Student).filter(Student.current_semester == sem).all()
            s_count = len(sem_students)
            s_cgpa = sum(s.cgpa for s in sem_students) / s_count if s_count > 0 else 0.0
            s_att = sum(s.attendance_percentage for s in sem_students) / s_count if s_count > 0 else 0.0
            sem_stats.append({
                "semester": f"Semester {sem}",
                "student_count": s_count,
                "average_cgpa": round(s_cgpa, 2),
                "average_attendance": round(s_att, 1),
            })

        # Attendance Distribution
        att_dist = {
            "above_85": self.db.query(Student).filter(Student.attendance_percentage >= 85.0).count(),
            "between_75_85": self.db.query(Student).filter(and_(Student.attendance_percentage >= 75.0, Student.attendance_percentage < 85.0)).count(),
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
            ]
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
        existing = self.db.query(StudentSkill).filter(
            StudentSkill.student_id == student.id,
            StudentSkill.skill_id == skill.id
        ).first()

        if existing:
            existing.proficiency_level = data.proficiency_level
            self.db.commit()
            return existing

        st_skill = StudentSkill(
            student_id=student.id,
            skill_id=skill.id,
            proficiency_level=data.proficiency_level,
            is_verified=False
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
            verification_status="Verified"
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
            semester_number=data.semester_number
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
            status=data.status
        )
        self.db.add(intern)
        self.db.commit()
        self.db.refresh(intern)
        return intern

    # 10. Data Import: Preview CSV/Excel
    async def preview_import_file(self, file: UploadFile, import_type: str, current_user: User) -> ImportPreviewResult:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Data import requires administrator privileges.")

        filename = file.filename or "uploaded_data.csv"
        is_excel = filename.endswith(".xlsx") or filename.endswith(".xls")

        content = await file.read()
        rows, columns = self._parse_file_rows(content, is_excel)

        # Validate rows
        valid_rows = []
        errors = []

        existing_usns = {s[0].upper() for s in self.db.query(Student.usn).all()}
        existing_emails = {u[0].lower() for u in self.db.query(User.email).all()}

        seen_in_batch_usn = set()
        seen_in_batch_email = set()

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

            elif import_type == "academic_records":
                usn = str(row.get("usn", "")).strip().upper()
                if not usn:
                    row_errors.append("Missing USN")
                elif usn not in existing_usns and usn not in seen_in_batch_usn:
                    row_errors.append(f"Student USN '{usn}' does not exist")

            elif import_type == "attendance":
                usn = str(row.get("usn", "")).strip().upper()
                if not usn:
                    row_errors.append("Missing USN")
                elif usn not in existing_usns:
                    row_errors.append(f"Student USN '{usn}' does not exist")

                total = row.get("total_classes")
                attended = row.get("attended_classes")
                try:
                    if int(attended) > int(total):
                        row_errors.append(f"Attended classes ({attended}) cannot exceed total classes ({total})")
                except (ValueError, TypeError):
                    row_errors.append("Classes counts must be valid integers")

            if row_errors:
                errors.append({
                    "row_number": idx,
                    "row_data": row,
                    "error_message": "; ".join(row_errors),
                })
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

    # 11. Execute Batch Import
    async def execute_import(self, file: UploadFile, import_type: str, current_user: User) -> ImportJob:
        if current_user.role != UserRole.ADMIN.value:
            raise HTTPException(status_code=403, detail="Administrator privileges required.")

        filename = file.filename or "import_data.csv"
        is_excel = filename.endswith(".xlsx") or filename.endswith(".xls")

        content = await file.read()
        rows, _ = self._parse_file_rows(content, is_excel)

        job = ImportJob(
            filename=filename,
            file_type="xlsx" if is_excel else "csv",
            import_type=import_type,
            status="processing",
            total_rows=len(rows),
            successful_rows=0,
            failed_rows=0,
            created_by=current_user.id
        )
        self.db.add(job)
        self.db.flush()

        student_role = self.db.query(Role).filter(Role.name == UserRole.STUDENT.value).first()
        role_id = student_role.id if student_role else 1
        default_dept = self.db.query(Department).first()
        dept_map = {d.code.upper(): d.id for d in self.db.query(Department).all()}

        successful = 0
        failed = 0

        for idx, row in enumerate(rows, start=1):
            try:
                if import_type == "students":
                    usn = str(row.get("usn", "")).strip().upper()
                    email = str(row.get("email", "")).strip().lower()
                    name = str(row.get("name", "")).strip() or str(row.get("full_name", "")).strip()
                    dept_code = str(row.get("department", "CSE")).strip().upper()
                    dept_id = dept_map.get(dept_code, default_dept.id if default_dept else 1)
                    sem = int(row.get("semester", 5))
                    sec = str(row.get("section", "A")).strip().upper()
                    roll = str(row.get("roll_number", f"R-{usn}")).strip().upper()
                    srn = str(row.get("srn", f"SRN-{usn}")).strip().upper()
                    cgpa = float(row.get("cgpa", 8.0))
                    att = float(row.get("attendance", 90.0))

                    # Check existence
                    if self.db.query(User).filter(User.email == email).first():
                        raise ValueError(f"User email '{email}' already registered.")
                    if self.db.query(Student).filter(Student.usn == usn).first():
                        raise ValueError(f"Student USN '{usn}' already exists.")

                    u = User(
                        email=email,
                        hashed_password=get_password_hash("StudentPass123!"),
                        full_name=name,
                        role=UserRole.STUDENT.value,
                        role_id=role_id,
                        department_id=dept_id,
                        is_active=True,
                        is_verified=True,
                    )
                    self.db.add(u)
                    self.db.flush()

                    s = Student(
                        user_id=u.id,
                        roll_number=roll,
                        usn=usn,
                        srn=srn,
                        department_id=dept_id,
                        current_semester=sem,
                        batch_year=2024,
                        admission_year=2022,
                        section=sec,
                        status="Active",
                        cgpa=cgpa,
                        attendance_percentage=att,
                        placement_status="Eligible" if (cgpa >= 7.0 and att >= 75.0) else "Ineligible"
                    )
                    self.db.add(s)
                    self.db.flush()
                    successful += 1

                elif import_type == "attendance":
                    usn = str(row.get("usn", "")).strip().upper()
                    st = self.db.query(Student).filter(Student.usn == usn).first()
                    if not st:
                        raise ValueError(f"Student USN '{usn}' not found.")
                    subj_code = str(row.get("subject_code", "CS501")).strip().upper()
                    subj = self.db.query(Subject).filter(Subject.code == subj_code).first()
                    if not subj:
                        raise ValueError(f"Subject '{subj_code}' not found.")

                    tot = int(row.get("total_classes", 45))
                    att = int(row.get("attended_classes", 40))
                    if att > tot:
                        raise ValueError(f"Attended ({att}) exceeds total ({tot})")

                    curr_sem = self.db.query(Semester).filter(Semester.is_current == True).first()
                    sem_id = curr_sem.id if curr_sem else 1

                    sa = SubjectAttendance(
                        student_id=st.id,
                        subject_id=subj.id,
                        semester_id=sem_id,
                        total_classes=tot,
                        attended_classes=att
                    )
                    self.db.add(sa)
                    successful += 1

            except Exception as e:
                failed += 1
                err = ImportError(
                    job_id=job.id,
                    row_number=idx,
                    raw_data=str(row),
                    error_message=str(e)
                )
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
            details={"type": import_type, "successful": successful, "failed": failed}
        )

        return job

    # 12. Generate Downloadable CSV Template
    def generate_csv_template(self, template_type: str) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        if template_type == "students":
            writer.writerow([
                "usn", "srn", "roll_number", "full_name", "email",
                "department", "program", "semester", "section",
                "batch_year", "admission_year", "cgpa", "attendance"
            ])
            writer.writerow([
                "1RV22CS099", "SRN-1RV22CS099", "CS22B099", "Sample Student",
                "sample.student@smartcampus.edu", "CSE",
                "B.Tech Computer Science & Engineering", "5", "A", "2024", "2022", "8.50", "92.0"
            ])
        elif template_type == "academic_records":
            writer.writerow([
                "usn", "semester_number", "subject_code", "internal_marks",
                "external_marks", "total_marks", "letter_grade", "grade_point"
            ])
            writer.writerow([
                "1RV22CS001", "5", "CS501", "42", "48", "90", "O", "10.0"
            ])
        elif template_type == "attendance":
            writer.writerow(["usn", "subject_code", "total_classes", "attended_classes"])
            writer.writerow(["1RV22CS001", "CS501", "45", "42"])
        else:
            writer.writerow(["usn", "data"])

        return output.getvalue()

    # Helpers
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
            email=u.email if u else "student@smartcampus.edu",
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

    def _log_audit(self, action: str, user_id: Optional[int], resource_type: str, resource_id: str, details: Dict[str, Any]):
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        self.db.add(audit)
        self.db.commit()
