"""
Module 6 Database Seeder:
Seeds canonical interventions, case notes, follow-up sessions, in-app notifications,
notification preferences, and initial institutional compliance report exports.
"""
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.models.profile import Student, Mentor, Faculty
from app.models.risk import RiskAlert
from app.models.intervention import (
    Intervention,
    InterventionNote,
    InterventionFollowup,
    Notification,
    NotificationPreference,
    ReportExport,
    InterventionStatus,
    InterventionType,
    NotificationType,
    ReportType,
)
from app.services.report_service import ReportService
from app.core.clock import utcnow  # noqa: E402


def seed_module6():
    db = SessionLocal()
    try:
        print(">>> [Module 6 Seeder] Starting Module 6 seeding...")

        students = db.query(Student).all()
        mentors = db.query(Mentor).all()
        admin_user = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        faculty_user = db.query(User).filter(User.role == UserRole.FACULTY.value).first()
        mentor_user = db.query(User).filter(User.role == UserRole.MENTOR.value).first()
        student_user = db.query(User).filter(User.role == UserRole.STUDENT.value).first()

        if not students or not mentors:
            print("⚠️ Insufficient student or mentor records found. Please run earlier seeders first.")
            return

        lead_mentor = mentors[0]
        primary_student = students[0]
        second_student = students[1] if len(students) > 1 else students[0]

        # -------------------------------------------------------------------------
        # 1. SEED CANONICAL INTERVENTIONS
        # -------------------------------------------------------------------------
        existing_interventions = db.query(Intervention).count()
        if existing_interventions == 0:
            print(">>> Seeding canonical student interventions...")

            # Find active risk alert if any
            first_alert = db.query(RiskAlert).filter(RiskAlert.student_id == primary_student.id).first()
            alert_id = first_alert.id if first_alert else None

            # Case 1: Attendance & Remedial Intervention (IN_PROGRESS)
            it1 = Intervention(
                student_id=primary_student.id,
                mentor_id=lead_mentor.id,
                assigned_by=faculty_user.id if faculty_user else (admin_user.id if admin_user else 1),
                risk_alert_id=alert_id,
                title="Academic Remedial & Attendance Coaching Plan",
                intervention_type=InterventionType.ACADEMIC_REMEDIAL.value,
                priority="HIGH",
                status=InterventionStatus.IN_PROGRESS.value,
                initial_notes="Student attendance dropped below 75% threshold in 2 core computer science courses. Recommended supplementary tutoring.",
                target_resolution_date=date.today() + timedelta(days=21),
                created_at=utcnow() - timedelta(days=12),
                updated_at=utcnow() - timedelta(days=2),
            )
            db.add(it1)
            db.flush()

            # Notes for Case 1
            db.add(InterventionNote(
                intervention_id=it1.id,
                author_id=mentor_user.id if mentor_user else 1,
                note_text="Conducted initial 1-on-1 counseling session. Identified commuting challenges and lab scheduling conflict.",
                note_type="OBSERVATION",
                created_at=utcnow() - timedelta(days=11),
            ))
            db.add(InterventionNote(
                intervention_id=it1.id,
                author_id=mentor_user.id if mentor_user else 1,
                note_text="Formulated remedial study schedule: 4 hours weekly guided lab time and peer tutoring for Operating Systems.",
                note_type="ACTION_ITEM",
                created_at=utcnow() - timedelta(days=9),
            ))
            db.add(InterventionNote(
                intervention_id=it1.id,
                author_id=mentor_user.id if mentor_user else 1,
                note_text="Communicated attendance recovery criteria and expectations with student's guardian via official academic portal.",
                note_type="PARENT_COMMUNICATION",
                created_at=utcnow() - timedelta(days=4),
            ))

            # Followups for Case 1
            db.add(InterventionFollowup(
                intervention_id=it1.id,
                mentor_id=lead_mentor.id,
                scheduled_date=date.today() - timedelta(days=5),
                conducted_date=utcnow() - timedelta(days=5),
                followup_status="COMPLETED",
                outcome_notes="Student attended all peer study group sessions this week. Subject attendance climbed from 71% to 76%.",
                student_feedback="Found the peer explanation on memory paging very helpful. Confident for upcoming mid-term re-test.",
                next_review_date=date.today() + timedelta(days=7),
                created_at=utcnow() - timedelta(days=10),
            ))
            db.add(InterventionFollowup(
                intervention_id=it1.id,
                mentor_id=lead_mentor.id,
                scheduled_date=date.today() + timedelta(days=7),
                followup_status="SCHEDULED",
                outcome_notes="Scheduled check-in on midterm 2 test scores and final attendance margin.",
                created_at=utcnow() - timedelta(days=5),
            ))

            # Case 2: Career Readiness & Placement Mentoring (ASSIGNED)
            it2 = Intervention(
                student_id=second_student.id,
                mentor_id=lead_mentor.id,
                assigned_by=admin_user.id if admin_user else 1,
                title="Career Role Alignment & Cloud Certifications Track",
                intervention_type=InterventionType.CAREER_SKILL_COACHING.value,
                priority="MEDIUM",
                status=InterventionStatus.ASSIGNED.value,
                initial_notes="Mentee target role is Cloud Engineer. Identified gap in AWS/Docker containerization skills before Day 1 recruitment drives.",
                target_resolution_date=date.today() + timedelta(days=30),
                created_at=utcnow() - timedelta(days=5),
                updated_at=utcnow() - timedelta(days=1),
            )
            db.add(it2)
            db.flush()

            db.add(InterventionNote(
                intervention_id=it2.id,
                author_id=mentor_user.id if mentor_user else 1,
                note_text="Curated AWS Certified Solutions Architect module and recommended Docker hands-on lab sandbox.",
                note_type="ACTION_ITEM",
                created_at=utcnow() - timedelta(days=3),
            ))

            db.add(InterventionFollowup(
                intervention_id=it2.id,
                mentor_id=lead_mentor.id,
                scheduled_date=date.today() + timedelta(days=4),
                followup_status="SCHEDULED",
                outcome_notes="Review project repository demonstrating microservices deployment on Docker/Kubernetes.",
                created_at=utcnow() - timedelta(days=2),
            ))

            # Case 3: Attendance Condonation & Wellness Counseling (RESOLVED)
            it3 = Intervention(
                student_id=primary_student.id,
                mentor_id=lead_mentor.id,
                assigned_by=faculty_user.id if faculty_user else 1,
                title="Medical Leave Attendance Condonation Review",
                intervention_type=InterventionType.ATTENDANCE_CONDONATION_COUNSELING.value,
                priority="MEDIUM",
                status=InterventionStatus.RESOLVED.value,
                initial_notes="Review valid medical certificate submitted for 6 days of absence during viral infection.",
                target_resolution_date=date.today() - timedelta(days=2),
                resolved_at=utcnow() - timedelta(days=2),
                resolution_summary="Medical certificate verified by university health clinic. Attendance condonation of 5% approved by Dean Academics. Overall attendance restored to 82%.",
                created_at=utcnow() - timedelta(days=20),
                updated_at=utcnow() - timedelta(days=2),
            )
            db.add(it3)
            db.flush()

            db.add(InterventionNote(
                intervention_id=it3.id,
                author_id=mentor_user.id if mentor_user else 1,
                note_text="Received official hospital discharge slip. Forwarded to Academic Registrar for condonation waiver.",
                note_type="COUNSELING",
                created_at=utcnow() - timedelta(days=18),
            ))
            db.add(InterventionNote(
                intervention_id=it3.id,
                author_id=mentor_user.id if mentor_user else 1,
                note_text="Condonation approval confirmed in institutional ERP. Case closed successfully.",
                note_type="ACTION_ITEM",
                created_at=utcnow() - timedelta(days=2),
            ))

            db.commit()
            print("✅ Seeded canonical interventions, notes, and scheduled follow-ups.")
        else:
            print(f"ℹ️ {existing_interventions} interventions already present. Skipping intervention creation.")

        # -------------------------------------------------------------------------
        # 2. SEED IN-APP NOTIFICATIONS
        # -------------------------------------------------------------------------
        existing_notifs = db.query(Notification).count()
        if existing_notifs == 0:
            print(">>> Seeding rich multi-channel in-app notifications...")
            users = db.query(User).all()

            for u in users:
                # Welcome & System notification
                db.add(Notification(
                    user_id=u.id,
                    title="Smart Campus Intelligence System Active",
                    message="Welcome to Smart Campus Intelligence Platform. All role dashboards and AI analytics are fully operational.",
                    notification_type=NotificationType.ADMINISTRATIVE_ANNOUNCEMENT.value,
                    severity="INFO",
                    is_read=True,
                    read_at=utcnow() - timedelta(days=1),
                    created_at=utcnow() - timedelta(days=3),
                ))

                if u.role == UserRole.STUDENT.value:
                    db.add(Notification(
                        user_id=u.id,
                        title="New Personalized Learning Recommendations",
                        message="Your profile has been matched with 3 high-relevance algorithmic skill modules and study plans.",
                        notification_type=NotificationType.NEW_RECOMMENDATION.value,
                        severity="INFO",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=4),
                    ))
                    db.add(Notification(
                        user_id=u.id,
                        title="Mentorship Follow-Up Scheduled",
                        message="Your mentor has scheduled a progress review session for next week. Please review your target items.",
                        notification_type=NotificationType.INTERVENTION_FOLLOWUP.value,
                        severity="WARNING",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=1),
                    ))

                elif u.role == UserRole.MENTOR.value:
                    db.add(Notification(
                        user_id=u.id,
                        title="New Mentee Intervention Assigned",
                        message="A new academic remedial intervention case has been allocated to you for student Alex Mercer.",
                        notification_type=NotificationType.MENTOR_ASSIGNMENT.value,
                        severity="WARNING",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=2),
                    ))
                    db.add(Notification(
                        user_id=u.id,
                        title="Mentee Risk Threshold Triggered",
                        message="Biometric sync flagged 2 assigned mentees with attendance below 75% for this fortnight.",
                        notification_type=NotificationType.RISK_ALERT.value,
                        severity="ERROR",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=5),
                    ))

                elif u.role == UserRole.FACULTY.value:
                    db.add(Notification(
                        user_id=u.id,
                        title="Midterm Assessment Grades Audited",
                        message="Internal assessment results for CS501 Data Structures have been locked and synced with student dossiers.",
                        notification_type=NotificationType.STATUS_UPDATE.value,
                        severity="SUCCESS",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=6),
                    ))

                elif u.role == UserRole.PLACEMENT_OFFICER.value:
                    db.add(Notification(
                        user_id=u.id,
                        title="New Campus Recruitment Drive Published",
                        message="Google Cloud Software Engineer 2026 drive published. 38 students meet the minimum CGPA and skill criteria.",
                        notification_type=NotificationType.ADMINISTRATIVE_ANNOUNCEMENT.value,
                        severity="SUCCESS",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=3),
                    ))

                elif u.role == UserRole.ADMIN.value:
                    db.add(Notification(
                        user_id=u.id,
                        title="Weekly Institutional Intelligence Digest",
                        message="Department KPIs and risk alert distributions for all 4 engineering faculties are compiled and ready for review.",
                        notification_type=NotificationType.ADMINISTRATIVE_ANNOUNCEMENT.value,
                        severity="INFO",
                        is_read=False,
                        created_at=utcnow() - timedelta(hours=1),
                    ))

                # Default Notification Preferences
                pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == u.id).first()
                if not pref:
                    db.add(NotificationPreference(
                        user_id=u.id,
                        email_alerts_enabled=True,
                        risk_notifications=True,
                        recommendation_notifications=True,
                        intervention_notifications=True,
                        placement_notifications=True,
                        announcement_notifications=True,
                    ))

            db.commit()
            print("✅ Seeded in-app notifications and user alert preferences.")
        else:
            print(f"ℹ️ {existing_notifs} notifications already present.")

        # -------------------------------------------------------------------------
        # 3. SEED INITIAL COMPLIANCE & PROGRESS REPORTS
        # -------------------------------------------------------------------------
        existing_reports = db.query(ReportExport).count()
        if existing_reports == 0:
            print(">>> Seeding canonical institutional compliance reports...")
            ReportService.generate_report(
                db=db,
                report_type=ReportType.STUDENT_PROGRESS.value,
                file_format="CSV",
                current_user=admin_user,
            )
            ReportService.generate_report(
                db=db,
                report_type=ReportType.MENTOR_INTERVENTIONS.value,
                file_format="CSV",
                current_user=admin_user,
            )
            ReportService.generate_report(
                db=db,
                report_type=ReportType.DEPARTMENT_SUMMARY.value,
                file_format="CSV",
                current_user=admin_user,
            )
            ReportService.generate_report(
                db=db,
                report_type=ReportType.RISK_SUMMARY.value,
                file_format="CSV",
                current_user=admin_user,
            )
            ReportService.generate_report(
                db=db,
                report_type=ReportType.PLACEMENT_READINESS.value,
                file_format="CSV",
                current_user=admin_user,
            )
            print("✅ Seeded 5 institutional CSV reports (Student Progress, Interventions, Department, Risk, Placement).")
        else:
            print(f"ℹ️ {existing_reports} reports already present.")

        print(">>> [Module 6 Seeder] Module 6 seeding complete!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_module6()
