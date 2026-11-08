#!/usr/bin/env python3
"""
Module 3 Seed Script: Personalized Recommendation Engine.
Populates approved recommendation catalogue, sets career goals and interests for synthetic students,
generates personalized recommendations, and simulates acceptance, progress, and feedback lifecycles.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.profile import Student, Mentor
from app.models.recommendation import (
    RecommendationCatalogue,
    Recommendation,
    RecommendationProgress,
    RecommendationFeedback,
)
from app.services.recommendation_service import RecommendationService


def seed_module3():
    db = SessionLocal()
    try:
        print("⚡ Seeding Module 3: Approved Recommendation Catalogue...")
        admin = db.query(User).filter(User.role == "admin").first()
        admin_id = admin.id if admin else None

        # 1. Seed Catalogue
        catalogue = RecommendationService.seed_default_catalogue_if_needed(db, user_id=admin_id)
        print(f"✅ {len(catalogue)} approved learning catalogue items verified across 11 categories.")

        # 2. Assign Career Goals and Interests to Students
        print("⚡ Configuring career goals and technical interests for demo students...")
        students = db.query(Student).all()
        career_presets = [
            (["Full Stack Developer", "Cloud Architect"], ["Distributed Systems", "Web Performance", "Cloud Native"]),
            (["AI/ML Engineer"], ["Deep Learning", "Natural Language Processing", "Computer Vision"]),
            (["Data Engineer"], ["Big Data", "Data Warehousing", "Stream Processing"]),
            (["Cybersecurity Analyst"], ["Network Security", "Cryptography", "Ethical Hacking"]),
            (["Cloud Architect"], ["DevOps", "Kubernetes", "Microservices"]),
        ]

        for i, s in enumerate(students):
            preset = career_presets[i % len(career_presets)]
            s.career_goals = preset[0]
            s.interests = preset[1]
        db.commit()
        print(f"✅ Configured career profiles for {len(students)} students.")

        # 3. Generate Personalized Recommendations for the first 10 students
        print("⚡ Running recommendation engine for student population...")
        total_gen = 0
        for s in students[:10]:
            recs = RecommendationService.generate_recommendations_for_student(db, student_id=s.id, force_regenerate=True)
            total_gen += len(recs)
        print(f"✅ Generated {total_gen} personalized recommendations for initial student cohort.")

        # 4. Simulate Student 1 (Alex Mercer) Lifecycle: Accept, Progress, Complete, Feedback
        student1 = students[0]
        s1_recs = db.query(Recommendation).filter(Recommendation.student_id == student1.id).all()
        mentor = db.query(Mentor).first()
        mentor_user_id = mentor.user_id if mentor and mentor.user_id else (admin_id or 1)

        if s1_recs:
            print("⚡ Simulating student learning lifecycle (Accept, In Progress, Complete, Feedback)...")
            # Rec 0: Completed with Feedback
            r0 = s1_recs[0]
            RecommendationService.accept_recommendation(db, r0.id, student1.user_id)
            RecommendationService.update_progress(
                db, r0.id, "COMPLETED", 100, "Finished all modules and submitted final project repository.", 18.5, student1.user_id
            )
            RecommendationService.submit_feedback(
                db, r0.id, student1.id, rating=5, helpful=True, relevance_score=5,
                comments="Exceptional practical course. Helped me build a fully functional full stack SaaS with automated tests.",
                outcome_achieved=True
            )

            # Rec 1: In Progress
            if len(s1_recs) > 1:
                r1 = s1_recs[1]
                RecommendationService.accept_recommendation(db, r1.id, student1.user_id)
                RecommendationService.update_progress(
                    db, r1.id, "IN_PROGRESS", 65, "Completed 45 out of 75 Blind LeetCode problems. Focusing on DP next.", 12.0, student1.user_id
                )

            # Rec 2: Mentor Proposes Personalized Suggestion with Guidance
            mentor_rec = RecommendationService.create_mentor_suggestion(
                db=db,
                data={
                    "student_id": student1.id,
                    "title": "System Design Primer & Scalable Architecture Review",
                    "category": "PLACEMENT_PREPARATION",
                    "reason": "Mentor Dr. Sterling identified strong coding skills and recommends focusing on high-level system design for tier-1 campus interviews.",
                    "gap_type": "CAREER_ALIGNMENT",
                    "gap_detail": "Distributed system design interview preparation",
                    "expected_outcome": "Design high-throughput, low-latency microservices with caching strategies.",
                    "priority": "HIGH",
                    "resource_url": "https://github.com/donnemartin/system-design-primer",
                    "suggested_completion_time": "3 Weeks",
                    "mentor_guidance_notes": "Alex, review the sections on CAP theorem, database sharding, and Redis caching before our mentorship meeting.",
                },
                mentor_user_id=mentor_user_id,
            )
            print(f"✅ Created mentor-directed suggestion #{mentor_rec.id} for {student1.roll_number}.")

        print("✅ Module 3 seed data and learning paths populated successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error during Module 3 seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_module3()
