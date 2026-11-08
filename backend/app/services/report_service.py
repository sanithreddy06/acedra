import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.intervention import ReportExport, ReportType, Intervention
from app.models.profile import Student, Mentor
from app.models.department import Department
from app.models.risk import RiskAlert
from app.models.placement import StudentApplication
from app.models.user import User


class ReportService:
    """Generates institutional compliance, student progress, and intervention reports."""

    @staticmethod
    def generate_report(
        db: Session,
        report_type: str,
        file_format: str = "CSV",
        department_id: Optional[int] = None,
        student_id: Optional[int] = None,
        current_user: Optional[User] = None,
    ) -> ReportExport:
        """Assembles data rows, formats CSV/JSON output, and creates ReportExport."""
        report_type = report_type.upper()
        file_format = file_format.upper()
        now_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        output_io = io.StringIO()
        report_title = ""
        file_name = ""

        if report_type == ReportType.STUDENT_PROGRESS.value:
            report_title = "Student Academic Progress & Intelligence Dossier"
            file_name = f"Student_Progress_Report_{now_str}.csv"
            writer = csv.writer(output_io)
            writer.writerow(["Student ID", "USN", "SRN", "Full Name", "Department", "Semester", "CGPA", "Attendance %", "Backlogs", "Placement Readiness %", "Status"])

            query = db.query(Student)
            if student_id:
                query = query.filter(Student.id == student_id)
            elif department_id:
                query = query.filter(Student.department_id == department_id)

            for s in query.limit(100).all():
                dept_name = s.department.name if s.department else "N/A"
                st_name = s.user.full_name if s.user else "Student"
                writer.writerow([
                    s.id,
                    s.usn,
                    s.srn,
                    st_name,
                    dept_name,
                    s.current_semester,
                    f"{s.cgpa:.2f}" if s.cgpa else "0.00",
                    f"{s.attendance_percentage:.1f}%" if s.attendance_percentage else "0.0%",
                    getattr(s, "total_backlogs", 0),
                    f"{s.readiness_score:.1f}%" if hasattr(s, "readiness_score") and s.readiness_score else "N/A",
                    s.status,
                ])

        elif report_type == ReportType.MENTOR_INTERVENTIONS.value:
            report_title = "Mentor Interventions & Student Support Audit"
            file_name = f"Mentor_Interventions_Report_{now_str}.csv"
            writer = csv.writer(output_io)
            writer.writerow(["Intervention ID", "Student USN", "Student Name", "Department", "Mentor Name", "Type", "Priority", "Status", "Created Date", "Target Date", "Followups Count", "Resolution Summary"])

            query = db.query(Intervention)
            if department_id:
                query = query.join(Student).filter(Student.department_id == department_id)

            for it in query.order_by(Intervention.created_at.desc()).limit(150).all():
                s = it.student
                m = it.mentor
                st_name = s.user.full_name if s and s.user else "Student"
                writer.writerow([
                    it.id,
                    s.usn if s else "N/A",
                    st_name,
                    s.department.code if s and s.department else "N/A",
                    m.user.full_name if m and m.user else "Unassigned",
                    it.intervention_type,
                    it.priority,
                    it.status,
                    it.created_at.strftime("%Y-%m-%d"),
                    it.target_resolution_date.strftime("%Y-%m-%d") if it.target_resolution_date else "N/A",
                    len(it.followups),
                    (it.resolution_summary or "").replace("\n", " "),
                ])

        elif report_type == ReportType.DEPARTMENT_SUMMARY.value:
            report_title = "Institutional Departmental Performance Summary"
            file_name = f"Department_Summary_Report_{now_str}.csv"
            writer = csv.writer(output_io)
            writer.writerow(["Dept Code", "Department Name", "HOD", "Total Students", "Average CGPA", "Average Attendance %", "Total Backlogs Count"])

            departments = db.query(Department).all()
            for d in departments:
                students = db.query(Student).filter(Student.department_id == d.id).all()
                count = len(students)
                avg_cgpa = sum(s.cgpa or 0.0 for s in students) / count if count > 0 else 0.0
                avg_att = sum(s.attendance_percentage or 0.0 for s in students) / count if count > 0 else 0.0
                backlogs = sum(getattr(s, "total_backlogs", 0) for s in students)
                writer.writerow([
                    d.code,
                    d.name,
                    getattr(d, "hod_name", "Appointed HOD"),
                    count,
                    f"{avg_cgpa:.2f}",
                    f"{avg_att:.1f}%",
                    backlogs,
                ])

        elif report_type == ReportType.RISK_SUMMARY.value:
            report_title = "Early-Warning Academic Risk Distribution"
            file_name = f"Risk_Early_Warning_Report_{now_str}.csv"
            writer = csv.writer(output_io)
            writer.writerow(["Alert ID", "Student USN", "Student Name", "Department", "Rule Name", "Severity", "Observed Value", "Threshold", "Detected Date", "Status"])

            alerts = db.query(RiskAlert).order_by(RiskAlert.detected_date.desc()).limit(150).all()
            for a in alerts:
                s = a.student
                st_name = s.user.full_name if s and s.user else "Student"
                writer.writerow([
                    a.id,
                    s.usn if s else "N/A",
                    st_name,
                    s.department.code if s and s.department else "N/A",
                    a.rule.name if a.rule else "Policy Trigger",
                    a.severity,
                    a.observed_value,
                    a.threshold_value,
                    a.detected_date.strftime("%Y-%m-%d") if a.detected_date else "N/A",
                    a.status,
                ])

        elif report_type == ReportType.PLACEMENT_READINESS.value:
            report_title = "Campus Placement Readiness & Career Benchmark Summary"
            file_name = f"Placement_Readiness_Report_{now_str}.csv"
            writer = csv.writer(output_io)
            writer.writerow(["Student ID", "USN", "Name", "Department", "Semester", "CGPA", "Placement Status", "Total Applications"])

            students = db.query(Student).filter(Student.current_semester >= 5).limit(100).all()
            for s in students:
                app_count = db.query(StudentApplication).filter(StudentApplication.student_id == s.id).count()
                st_name = s.user.full_name if s.user else "Student"
                writer.writerow([
                    s.id,
                    s.usn,
                    st_name,
                    s.department.code if s.department else "N/A",
                    s.current_semester,
                    f"{s.cgpa:.2f}" if s.cgpa else "0.00",
                    s.placement_status or "Eligible",
                    app_count,
                ])

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported report type '{report_type}'")

        content = output_io.getvalue()
        file_size = len(content.encode("utf-8"))

        export = ReportExport(
            report_type=report_type,
            title=report_title,
            generated_by=current_user.id if current_user else None,
            department_id=department_id,
            student_id=student_id,
            file_format=file_format,
            file_name=file_name,
            file_size_bytes=file_size,
            content_payload=content,
            created_at=datetime.utcnow(),
        )
        db.add(export)
        db.commit()
        db.refresh(export)
        return export

    @staticmethod
    def list_reports(db: Session, limit: int = 30) -> List[ReportExport]:
        """List recent generated report downloads."""
        return db.query(ReportExport).order_by(ReportExport.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_report_download(db: Session, report_id: int) -> Tuple[ReportExport, str]:
        """Retrieve report record and payload for file download."""
        report = db.query(ReportExport).filter(ReportExport.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report, report.content_payload or ""
