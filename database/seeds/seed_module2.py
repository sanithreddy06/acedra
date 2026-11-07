#!/usr/bin/env python3
"""
Module 2 Seed Script: AI-Assisted Risk Identification & Early Warning System.
Populates canonical risk rules, executes initial rule evaluation across synthetic students,
and sets up demo alert workflow states (acknowledged, under review, resolved) for inspection.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Student, Mentor
from app.models.risk import RiskRule, RiskAlert, RiskAlertHistory, AlertAssignment, InAppNotification
from app.services.risk_service import RiskService


def seed_module2():
    db = SessionLocal()
    try:
        print("⚡ Seeding Module 2: Configurable Risk Rules...")
        admin = db.query(User).filter(User.role == "administrator").first()
        admin_id = admin.id if admin else None

        # 1. Seed Rules
        rules = RiskService.seed_default_rules_if_needed(db, user_id=admin_id)
        print(f"✅ {len(rules)} canonical risk rules seeded/verified.")

        # 2. Trigger Batch Evaluation across all students
        print("⚡ Executing initial rule evaluation across student population...")
        eval_run = RiskService.evaluate_risk(
            db=db,
            run_type="BATCH",
            user_id=admin_id
        )
        print(f"✅ Evaluation run #{eval_run.id} finished: {eval_run.evaluated_students_count} students evaluated, {eval_run.alerts_generated_count} alerts generated.")
        print(f"   Severity breakdown: Critical={eval_run.critical_count}, High={eval_run.high_count}, Moderate={eval_run.moderate_count}")

        # 3. Simulate workflow states on a few alerts to demonstrate lifecycle
        alerts = db.query(RiskAlert).all()
        mentor = db.query(Mentor).first()
        faculty_user = db.query(User).filter(User.role == "faculty").first()

        if alerts and mentor and faculty_user:
            print("⚡ Simulating alert review lifecycle (Acknowledge, Assign, Review, Resolve)...")
            # Alert 1: Under Review (Assigned to Mentor)
            if len(alerts) > 0:
                a1 = alerts[0]
                RiskService.acknowledge_alert(db, a1, faculty_user.id, "Acknowledged by course faculty; referred to mentor.")
                RiskService.assign_mentor(db, a1, mentor.id, faculty_user.id, "Please schedule weekly attendance check-in.")

            # Alert 2: Resolved
            if len(alerts) > 1:
                a2 = alerts[1]
                RiskService.acknowledge_alert(db, a2, admin_id or faculty_user.id, "Student provided medical documentation for missed classes.")
                RiskService.resolve_alert(
                    db=db,
                    alert=a2,
                    user_id=admin_id or faculty_user.id,
                    resolution_reason="Excused Medical Absence Approved",
                    review_notes="Verified hospitalization certificate. Make-up lab scheduled for Saturday."
                )

            # Alert 3: Note Added
            if len(alerts) > 2:
                a3 = alerts[2]
                RiskService.add_review_note(db, a3, faculty_user.id, "Student attended tutorial session 1; conceptual progress noted.")

        print("✅ Module 2 demo data and workflow state populated successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during Module 2 seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_module2()
