"""
REVA University tenant — day-to-day activity on top of the core records and module seeds.

A university that has been using the workspace for a few weeks does not have every alert sitting untouched.
This step makes the sample data look like that: alerts raised over the past three weeks and at different
review stages, support cases opened by mentors for the students who need them (with notes and follow-ups),
recommendations issued to every student and partly acted on, and a placement season in progress with
applications at every stage. Everything goes through the same services the application uses, so the audit
history, notifications and counts stay consistent with what the screens show.

Run through seed_all.py (after the module seeders); expects the tenant context to be set by the caller.
"""
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from app.core.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Department, Faculty, FacultyCourseAssignment, Intervention, InterventionFollowup, InterventionNote, Mentor,
    PlacementOpportunity, Recommendation, RiskAlert, RiskRule, Student, StudentApplication,
    StudentSemesterRecord, Subject, User,
)
from app.services.placement_service import PlacementService  # noqa: E402
from app.services.recommendation_service import RecommendationService  # noqa: E402
from app.services.risk_service import RiskService  # noqa: E402

EXTRA_OPPORTUNITIES = [
    dict(company_name="Infosys", title="InStep Summer Internship", opportunity_type="INTERNSHIP", location="Mysuru",
         work_mode="ONSITE", ctc_stipend="20,000 / month", min_cgpa=7.0, max_backlogs=0, min_attendance=75.0,
         eligible_departments=["CSE", "AI_DS", "ECE", "MECH"], eligible_semesters=[5, 6], open_positions=25,
         description="Eight-week summer internship on a live project with a mentor from a delivery unit.", days=20),
    dict(company_name="Infosys", title="Systems Engineer", opportunity_type="JOB", location="Bengaluru",
         work_mode="ONSITE", ctc_stipend="6.5 LPA", min_cgpa=6.0, max_backlogs=0, min_attendance=75.0,
         eligible_departments=["CSE", "AI_DS", "ECE", "MECH"], eligible_semesters=[7, 8], open_positions=40,
         description="Campus hiring for the Systems Engineer role across delivery units.", days=24),
    dict(company_name="Bosch Global Software Technologies", title="Associate Embedded Engineer",
         opportunity_type="JOB", location="Bengaluru", work_mode="HYBRID", ctc_stipend="8.0 LPA", min_cgpa=7.0,
         max_backlogs=0, min_attendance=75.0, eligible_departments=["ECE", "MECH", "CSE"], eligible_semesters=[7, 8],
         open_positions=12, description="Embedded software and mechatronics roles for the mobility business.", days=31),
    dict(company_name="Toyota Kirloskar Motor", title="Graduate Engineer Trainee", opportunity_type="JOB",
         location="Bidadi", work_mode="ONSITE", ctc_stipend="6.0 LPA", min_cgpa=6.5, max_backlogs=0,
         min_attendance=75.0, eligible_departments=["MECH", "ECE"], eligible_semesters=[7, 8], open_positions=8,
         description="Manufacturing, quality and production engineering trainee programme.", days=38),
]

# Support-case templates keyed by the indicator that raised the alert.
CASES = {
    "attendance_percentage": [
        ("Attendance recovery plan", "ATTENDANCE_CONDONATION_COUNSELING",
         "Attendance has fallen below the requirement. Agree a week-by-week recovery plan and review eligibility for condonation.",
         "Met the student; absences were mostly first-hour classes because of a long commute. Agreed a recovery target.",
         "Subject teachers informed. Attendance to be reviewed every Friday until it is back above the requirement."),
    ],
    "assessment_percentage": [
        ("Internal assessment remedial coaching", "ACADEMIC_REMEDIAL",
         "Internal assessment scores are below the pass mark in more than one course. Arrange remedial sessions before the next internal.",
         "Went through the answer scripts with the student. Gaps are in problem-solving practice rather than attendance.",
         "Two remedial sessions a week arranged with the course teacher; practice sheets shared."),
    ],
    "backlog_count": [
        ("Backlog clearance plan", "EXAMINATION_PREPARATION",
         "Student carries arrears from the previous semester. Plan preparation for the supplementary examination alongside current courses.",
         "Drew up a timetable that keeps two evenings a week for the arrear subject. Previous papers shared.",
         "Registered for the supplementary examination; revision test scheduled two weeks before it."),
    ],
    "sgpa_drop": [
        ("Wellbeing and study-habits check-in", "BEHAVIORAL_WELLBEING",
         "Sharp drop in SGPA last semester after consistent results. Check for personal or workload reasons before it repeats.",
         "Student reports taking on too many club commitments last semester. Agreed to step back from one of them.",
         "Introduced the student to the counselling cell; follow-up after the first internal assessment."),
    ],
    "missing_assessments": [
        ("Missed internal assessments follow-up", "ACADEMIC_REMEDIAL",
         "No internal assessment marks are recorded this semester. Confirm whether the student sat the tests and arrange a make-up.",
         "Student was on medical leave during the first internal. Documents collected.",
         "Make-up test requested from the course teachers through the department office."),
    ],
    "composite": [
        ("Combined attendance and performance support", "ACADEMIC_REMEDIAL",
         "Low attendance and weak internal scores together. Needs a joint plan with the subject teachers and the guardian informed.",
         "Spoke to the student and the guardian. Hostel move planned to cut travel time.",
         "Weekly review set up with two subject teachers."),
    ],
}
CAREER_CASES = [
    ("Placement interview preparation", "PLACEMENT_INTERVIEW_PREPARATION",
     "Shortlisted for interviews. Two mock technical interviews and one HR round before the drive.",
     "First mock interview done: strong on fundamentals, needs to structure answers on projects.",
     "Second mock scheduled with an alumni volunteer."),
    ("Career role alignment and skills plan", "CAREER_SKILL_COACHING",
     "Target role identified but two core skills are below the level recruiters ask for. Agree a certification and project plan.",
     "Reviewed the skill-gap report together and picked one certification to complete this semester.",
     "Project idea approved; progress check in three weeks."),
]
RESOLUTIONS = {
    "attendance_percentage": "Attendance is back above the requirement for three consecutive weeks.",
    "assessment_percentage": "Scored above the pass mark in the second internal assessment in every course.",
    "backlog_count": "Cleared the arrear subject in the supplementary examination.",
    "sgpa_drop": "First internal results are back in line with earlier semesters.",
    "missing_assessments": "Make-up assessments completed and marks recorded.",
    "composite": "Attendance and internal scores both recovered; plan closed with the guardian informed.",
}
ACK_NOTES = ["Seen in the weekly review. Speaking to the student this week.",
             "Acknowledged. Checking attendance registers with the class teacher.",
             "Noted; will raise it at the department mentor meeting."]
ASSIGN_NOTES = ["Please meet the student this week and record a plan.",
                "Referred to the mentor for a one-to-one discussion.",
                "Mentor to follow up and report back at the next review."]


def _naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_reva_activity() -> None:
    rng = random.Random(20261101)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").order_by(User.id).first()
        placement_officer = db.query(User).filter(User.role == "placement_officer").order_by(User.id).first()
        mentors = {m.id: m for m in db.query(Mentor).all()}
        students = {s.id: s for s in db.query(Student).all()}
        rules = {r.id: r for r in db.query(RiskRule).all()}
        today = date.today()
        now = _naive_now()

        # A teacher of each student's section acknowledges alerts; fall back to the administrator.
        teacher_user = {}
        rows = db.query(Subject.department_id, Subject.semester_number, FacultyCourseAssignment.section, Faculty.user_id) \
            .join(FacultyCourseAssignment, FacultyCourseAssignment.subject_id == Subject.id) \
            .join(Faculty, Faculty.id == FacultyCourseAssignment.faculty_id).all()
        for dept_id, semester, section, user_id in rows:
            teacher_user.setdefault((dept_id, semester, section), user_id)

        def teacher_of(student):
            return teacher_user.get((student.department_id, student.current_semester, student.section), admin.id)

        # ------------------------------------------------------------------ alerts were raised over three weeks
        alerts = db.query(RiskAlert).order_by(RiskAlert.id).all()
        for alert in alerts:
            raised = now - timedelta(days=rng.randint(2, 21), hours=rng.randint(0, 8))
            alert.detected_date = raised
            alert.created_at = raised
        db.commit()

        # ------------------------------------------------------------------ support cases
        with_case = {i.student_id for i in db.query(Intervention).all()}
        severity_rank = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
        candidates = {}
        for alert in sorted(alerts, key=lambda a: (severity_rank.get(a.severity, 3), a.id)):
            if alert.status == "FLAGGED" and alert.student_id not in with_case:
                candidates.setdefault(alert.student_id, alert)  # the most severe open alert per student
        chosen = list(candidates.values())[:32]
        statuses = (["IN_PROGRESS"] * 13 + ["ASSIGNED"] * 7 + ["RESOLVED"] * 8 + ["OPEN"] * 3 + ["CLOSED"] * 1)
        handled = set()
        for alert, status in zip(chosen, statuses):
            student = students[alert.student_id]
            mentor = mentors.get(student.assigned_mentor_id)
            indicator = rules[alert.rule_id].indicator_type
            title, kind, brief, observation, action = rng.choice(CASES.get(indicator, CASES["attendance_percentage"]))
            opened = alert.detected_date + timedelta(days=rng.randint(1, 3))
            if opened > now:
                opened = now - timedelta(hours=6)
            closed = status in ("RESOLVED", "CLOSED")
            case = Intervention(
                student_id=student.id, mentor_id=mentor.id if mentor and status != "OPEN" else None,
                assigned_by=teacher_of(student), risk_alert_id=alert.id, title=title, intervention_type=kind,
                priority={"CRITICAL": "URGENT", "HIGH": "HIGH"}.get(alert.severity, "MEDIUM"), status=status,
                initial_notes=brief, target_resolution_date=(opened + timedelta(days=28)).date(),
                resolved_at=now - timedelta(days=rng.randint(0, 2)) if closed else None,
                resolution_summary=RESOLUTIONS.get(indicator) if closed else None,
                created_at=opened, updated_at=now - timedelta(days=rng.randint(0, 3), hours=rng.randint(1, 9)),
            )
            db.add(case)
            db.flush()
            if mentor and status in ("IN_PROGRESS", "RESOLVED", "CLOSED"):
                db.add(InterventionNote(intervention_id=case.id, author_id=mentor.user_id, note_text=observation,
                                        note_type="OBSERVATION", created_at=opened + timedelta(days=1)))
                db.add(InterventionNote(intervention_id=case.id, author_id=mentor.user_id, note_text=action,
                                        note_type="ACTION_ITEM", created_at=opened + timedelta(days=2)))
                done = (opened + timedelta(days=7)).date()
                if done < today:
                    db.add(InterventionFollowup(
                        intervention_id=case.id, mentor_id=mentor.id, scheduled_date=done,
                        conducted_date=datetime.combine(done, datetime.min.time()) + timedelta(hours=11),
                        followup_status="COMPLETED", outcome_notes="Reviewed progress against the agreed plan.",
                        next_review_date=done + timedelta(days=7), created_at=opened + timedelta(days=2)))
            if mentor and status in ("IN_PROGRESS", "ASSIGNED"):
                db.add(InterventionFollowup(
                    intervention_id=case.id, mentor_id=mentor.id, scheduled_date=today + timedelta(days=rng.randint(1, 12)),
                    followup_status="SCHEDULED", outcome_notes="Progress review with the student.", created_at=now))
            db.commit()

            # Keep the alert in step with its case.
            actor = teacher_of(student)
            if status != "OPEN":
                RiskService.acknowledge_alert(db, alert, actor, rng.choice(ACK_NOTES))
                if mentor:
                    RiskService.assign_mentor(db, alert, mentor.id, actor, rng.choice(ASSIGN_NOTES))
            if closed:
                RiskService.resolve_alert(db=db, alert=alert, user_id=mentor.user_id if mentor else admin.id,
                                          resolution_reason="Support plan completed",
                                          review_notes=RESOLUTIONS.get(indicator, "Plan completed."))
            handled.add(alert.id)

        # Remaining alerts: some acknowledged, some referred to the mentor, the newest still waiting.
        for alert in alerts:
            if alert.id in handled or alert.status != "FLAGGED":
                continue
            student = students[alert.student_id]
            roll = rng.random()
            if roll < 0.40:
                continue
            RiskService.acknowledge_alert(db, alert, teacher_of(student), rng.choice(ACK_NOTES))
            mentor = mentors.get(student.assigned_mentor_id)
            if roll > 0.72 and mentor:
                RiskService.assign_mentor(db, alert, mentor.id, teacher_of(student), rng.choice(ASSIGN_NOTES))

        # ------------------------------------------------------------------ recommendations for everyone
        have = {sid for (sid,) in db.query(Recommendation.student_id).distinct().all()}
        for student in students.values():
            if student.id not in have:
                RecommendationService.generate_recommendations_for_student(db, student_id=student.id)
        for rec in db.query(Recommendation).filter(Recommendation.status == "SUGGESTED").order_by(Recommendation.id).all():
            student = students[rec.student_id]
            if student.id == min(students):  # the demo student's plan is set up by the recommendations seeder
                continue
            roll = rng.random()
            if roll < 0.45:
                continue
            RecommendationService.accept_recommendation(db, rec.id, student.user_id)
            if roll > 0.88:
                RecommendationService.update_progress(db, rec.id, "COMPLETED", 100, "Completed.",
                                                      float(rng.randint(8, 30)), student.user_id)
            elif roll > 0.62:
                RecommendationService.update_progress(db, rec.id, "IN_PROGRESS", rng.choice([25, 40, 50, 60, 75]),
                                                      "Working through it.", float(rng.randint(2, 14)), student.user_id)

        # ------------------------------------------------------------------ placement season
        for spec in EXTRA_OPPORTUNITIES:
            spec = dict(spec)
            deadline = today + timedelta(days=spec.pop("days"))
            if not db.query(PlacementOpportunity).filter(PlacementOpportunity.company_name == spec["company_name"],
                                                         PlacementOpportunity.title == spec["title"]).first():
                db.add(PlacementOpportunity(**spec, application_deadline=deadline, status="OPEN",
                                            created_by_user_id=placement_officer.id if placement_officer else None))
        db.commit()

        dept_code = {d.id: d.code for d in db.query(Department).all()}
        backlogs = {}
        for record in db.query(StudentSemesterRecord).all():
            backlogs[record.student_id] = backlogs.get(record.student_id, 0) + (record.backlogs_count or 0)
        opportunities = db.query(PlacementOpportunity).filter(PlacementOpportunity.status == "OPEN").all()

        def eligible(student, opp):
            return (dept_code[student.department_id] in (opp.eligible_departments or [])
                    and student.current_semester in (opp.eligible_semesters or [])
                    and (student.cgpa or 0) >= opp.min_cgpa
                    and (student.attendance_percentage or 0) >= opp.min_attendance
                    and backlogs.get(student.id, 0) <= opp.max_backlogs)

        def apply(student, opp, status, days_ago):
            if db.query(StudentApplication).filter(StudentApplication.student_id == student.id,
                                                   StudentApplication.opportunity_id == opp.id).first():
                return
            try:
                readiness = PlacementService.calculate_placement_readiness(db, student.id, opp.role_id or 1).readiness_score
            except Exception:  # noqa: BLE001 — sample data only: a missing role must not stop the seed
                readiness = 0.0
            notes = {"SHORTLISTED": "Cleared résumé screening.", "INTERVIEW_SCHEDULED": "Cleared the online assessment.",
                     "OFFERED": "Offer letter issued; awaiting acceptance.", "PLACED": "Offer accepted.",
                     "REJECTED": "Not shortlisted after the online assessment."}.get(status)
            db.add(StudentApplication(opportunity_id=opp.id, student_id=student.id, status=status,
                                      applied_at=now - timedelta(days=days_ago), reviewer_notes=notes,
                                      cover_notes=None, readiness_score_at_application=readiness))

        jobs = [o for o in opportunities if o.opportunity_type == "JOB"]
        internships = [o for o in opportunities if o.opportunity_type == "INTERNSHIP"]
        for student in sorted(students.values(), key=lambda s: s.id):
            if student.placement_status == "Placed" and student.current_semester != 7:
                student.placement_status = "Eligible"  # only final-year students hold accepted offers
            if student.current_semester == 7:
                options = [o for o in jobs if eligible(student, o)]
                if student.placement_status == "Placed":
                    if not options:  # every placed student has an accepted offer on record
                        student.placement_status = "Eligible"
                        continue
                    apply(student, rng.choice(options), "PLACED", rng.randint(12, 20))
                    continue
                if not options or rng.random() < 0.25:
                    continue
                for opp in rng.sample(options, k=min(len(options), rng.choice([1, 1, 2]))):
                    status = rng.choices(["APPLIED", "SHORTLISTED", "INTERVIEW_SCHEDULED", "OFFERED", "REJECTED"],
                                         weights=[34, 24, 20, 8, 14])[0]
                    apply(student, opp, status, rng.randint(1, 14))
            elif student.current_semester == 5:
                options = [o for o in internships if eligible(student, o)]
                if options and rng.random() < 0.35:
                    apply(student, rng.choice(options), rng.choice(["APPLIED", "APPLIED", "SHORTLISTED"]), rng.randint(1, 10))
        db.commit()

        # Mentors of students with interviews coming up open a preparation case.
        with_case = {i.student_id for i in db.query(Intervention).all()}
        upcoming = db.query(StudentApplication).filter(StudentApplication.status == "INTERVIEW_SCHEDULED") \
            .order_by(StudentApplication.id).all()
        for application, template in zip([a for a in upcoming if a.student_id not in with_case][:6], CAREER_CASES * 3):
            student = students[application.student_id]
            mentor = mentors.get(student.assigned_mentor_id)
            if not mentor:
                continue
            title, kind, brief, observation, action = template
            opened = now - timedelta(days=rng.randint(3, 9))
            case = Intervention(student_id=student.id, mentor_id=mentor.id, assigned_by=mentor.user_id, title=title,
                                intervention_type=kind, priority="MEDIUM", status="IN_PROGRESS", initial_notes=brief,
                                target_resolution_date=today + timedelta(days=rng.randint(10, 21)),
                                created_at=opened, updated_at=now - timedelta(days=rng.randint(0, 2)))
            db.add(case)
            db.flush()
            db.add(InterventionNote(intervention_id=case.id, author_id=mentor.user_id, note_text=observation,
                                    note_type="OBSERVATION", created_at=opened + timedelta(days=1)))
            db.add(InterventionNote(intervention_id=case.id, author_id=mentor.user_id, note_text=action,
                                    note_type="ACTION_ITEM", created_at=opened + timedelta(days=2)))
            db.add(InterventionFollowup(intervention_id=case.id, mentor_id=mentor.id,
                                        scheduled_date=today + timedelta(days=rng.randint(2, 9)),
                                        followup_status="SCHEDULED", outcome_notes="Mock interview and feedback.",
                                        created_at=now))
            with_case.add(student.id)
        db.commit()

        print(f">>> REVA activity: {db.query(Intervention).count()} support cases, "
              f"{db.query(Recommendation).count()} recommendations, "
              f"{db.query(StudentApplication).count()} applications, "
              f"{db.query(RiskAlert).filter(RiskAlert.status == 'FLAGGED').count()} alerts awaiting review")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_reva_activity()
