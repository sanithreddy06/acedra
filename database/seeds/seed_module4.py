"""
Module 4 Database Seeder:
Seeds canonical career roles, role skills, corporate placement & internship opportunities,
student skill evidences, and sample placement applications.
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, date

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.append(str(backend_path))

from app.core.database import SessionLocal
from app.models.profile import Student, Faculty
from app.models.student_intelligence import Skill, StudentSkill, Project, Certification
from app.models.placement import (
    CareerRole,
    RoleSkill,
    PlacementOpportunity,
    OpportunityRequirement,
    StudentApplication,
    SkillEvidence,
)
from app.services.placement_service import PlacementService


def seed_module4():
    db = SessionLocal()
    try:
        print(">>> [Module 4 Seeder] Initializing Career Roles and Skill Matrices...")
        roles = PlacementService.seed_canonical_career_roles(db)
        print(f"✅ Seeded/Verified {len(roles)} canonical career roles.")

        print(">>> [Module 4 Seeder] Initializing Corporate Placement & Internship Opportunities...")
        opps = PlacementService.seed_canonical_opportunities(db)
        print(f"✅ Seeded/Verified {len(opps)} placement opportunities.")

        print(">>> [Module 4 Seeder] Enhancing Student Skills & Creating Skill Evidences...")
        students = db.query(Student).all()
        print(f"Found {len(students)} students to enhance with skill profiles.")

        # Skills matrix presets
        core_tech_skills = [
            ("Python", "programming", "Advanced"),
            ("Java", "programming", "Intermediate"),
            ("Data Structures", "problem_solving", "Advanced"),
            ("Algorithms", "problem_solving", "Advanced"),
            ("React", "framework", "Intermediate"),
            ("SQL", "database", "Advanced"),
            ("PostgreSQL", "database", "Intermediate"),
            ("Docker", "cloud", "Intermediate"),
            ("Machine Learning", "artificial_intelligence", "Intermediate"),
            ("Git Collaboration", "teamwork", "Advanced"),
            ("Technical Writing", "communication", "Intermediate"),
        ]

        for idx, student in enumerate(students):
            # Seed 5-8 skills per student
            assigned_skills = core_tech_skills[: 5 + (idx % 6)]
            for sname, scat, sprof in assigned_skills:
                # Add or update
                ss = PlacementService.add_or_update_student_skill(
                    db,
                    student_id=student.id,
                    skill_name=sname,
                    category=scat,
                    proficiency_level=sprof
                )

                # Add evidence if not existing
                existing_ev = db.query(SkillEvidence).filter(
                    SkillEvidence.student_skill_id == ss.id
                ).first()

                if not existing_ev:
                    # Provide realistic evidence for demonstration
                    ev_status = "VERIFIED" if (idx % 2 == 0) else "SELF_REPORTED"
                    ev_type = "PROJECT" if (idx % 3 == 0) else "GITHUB_REPO" if (idx % 3 == 1) else "CERTIFICATION"
                    ev_title = f"{sname} Capstone Implementation & Benchmark Suite"

                    ev = SkillEvidence(
                        student_skill_id=ss.id,
                        student_id=student.id,
                        evidence_type=ev_type,
                        title=ev_title,
                        url=f"https://github.com/smartcampus-lab/{student.usn.lower()}-{sname.lower().replace(' ', '-')}",
                        description=f"Demonstrated {sprof} proficiency in {sname} via autonomous laboratory assignment and system benchmarking.",
                        verification_status=ev_status,
                        verified_by_user_id=2 if ev_status == "VERIFIED" else None,
                        verified_at=datetime.now(timezone.utc) if ev_status == "VERIFIED" else None,
                        verification_feedback="Faculty code review completed. Coding conventions and algorithmic complexity verified." if ev_status == "VERIFIED" else None,
                    )
                    db.add(ev)
                    if ev_status == "VERIFIED":
                        ss.is_verified = True
            db.commit()

        # Seed sample student applications
        print(">>> [Module 4 Seeder] Creating Sample Placement Applications...")
        # First 3 students apply to Google, Amazon, Microsoft
        if len(students) >= 3 and len(opps) >= 3:
            sample_apps = [
                (students[0].id, opps[0].id, "SHORTLISTED", "https://campus-drive.edu/resumes/1RV22SYN001.pdf", "Strong competitive programming track record. High CGPA.", 92.5),
                (students[0].id, opps[2].id, "INTERVIEW_SCHEDULED", "https://campus-drive.edu/resumes/1RV22SYN001.pdf", "Cleared online technical assessment round. Technical interview scheduled.", 88.0),
                (students[1].id, opps[1].id, "APPLIED", "https://campus-drive.edu/resumes/1RV22SYN002.pdf", "Passionate about Azure AI and deep learning research.", 78.5),
                (students[2].id, opps[2].id, "APPLIED", "https://campus-drive.edu/resumes/1RV22SYN003.pdf", "Full stack developer with 3 production React projects.", 84.0),
            ]

            for st_id, op_id, st_status, r_url, notes, r_score in sample_apps:
                existing_app = db.query(StudentApplication).filter(
                    StudentApplication.student_id == st_id,
                    StudentApplication.opportunity_id == op_id
                ).first()
                if not existing_app:
                    app = StudentApplication(
                        opportunity_id=op_id,
                        student_id=st_id,
                        status=st_status,
                        applied_at=datetime.now(timezone.utc),
                        resume_url=r_url,
                        cover_notes=notes,
                        reviewer_notes="Profile screening completed by placement cell coordinator." if st_status != "APPLIED" else None,
                        readiness_score_at_application=r_score,
                    )
                    db.add(app)
            db.commit()
            print("✅ Seeded sample student applications.")

        print("🎉 [Module 4 Seeder] Placement readiness and skill gap data seeded successfully!")

    except Exception as e:
        print(f"❌ [Module 4 Seeder] Error during seeding: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_module4()
