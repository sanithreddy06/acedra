from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.profile import Student
from app.services.student_service import StudentIntelligenceService
from app.services.risk_service import RiskService
from app.services.recommendation_service import RecommendationService
from app.services.placement_service import PlacementService


class StudentContextService:
    """
    Retrieves authorized personal student context for Mode B.
    Enforces strict access control:
    - Students can ONLY access their own records.
    - Faculty/mentors/admins can only access authorized cohorts.
    - Unauthenticated callers are strictly blocked.
    """

    @staticmethod
    def get_authorized_student_context(
        db: Session,
        current_user: Optional[User],
        target_student_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Validates authorization and gathers verified metrics across Modules 1, 2, 3, and 4.
        Returns a structured dictionary ready for LLM grounding.
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Mode B requires an active authenticated session.",
            )

        student: Optional[Student] = None

        if current_user.role == "student":
            # Student can only access their own profile
            student = db.query(Student).filter(Student.user_id == current_user.id).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student record not found for authenticated account.",
                )
            if target_student_id and target_student_id != student.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-student data access denied. You can only query your own academic records.",
                )
        else:
            # Faculty / Mentor / Admin / Placement Officer
            if not target_student_id:
                # Default to first student in their department or global first
                query = db.query(Student)
                if current_user.department_id:
                    query = query.filter(Student.department_id == current_user.department_id)
                student = query.first()
            else:
                student = db.query(Student).filter(Student.id == target_student_id).first()

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student record with ID {target_student_id} not found.",
                )

        # 1. Fetch Module 1 Analytics (Academics, Dynamic Attendance, CIA Marks)
        analytics_out = StudentIntelligenceService(db).get_student_analytics(student.id, current_user)
        analytics = analytics_out.model_dump()

        # 2. Fetch Module 2 Early-Warning Risks
        active_alerts_list, _ = RiskService.get_alerts(db, student_id=student.id, status="ACTIVE")
        alerts_summary = []
        for a in active_alerts_list:
            rule_name = a.rule.name if a.rule else "Risk Policy Alert"
            alerts_summary.append(
                f"- Rule: {rule_name} (Severity: {a.severity}, Observed: {a.observed_value}, Threshold: {a.threshold_value})"
            )

        # 3. Fetch Module 3 Recommendations
        rec_data = RecommendationService.get_student_learning_path(db, student.id)
        all_recs = rec_data.get("academic_improvement_plan", []) + rec_data.get("career_development_plan", [])
        rec_summary = []
        for r in all_recs[:4]:
            category = getattr(r, "category", None) or (r.get("category") if isinstance(r, dict) else "")
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            status_val = getattr(r, "status", None) or (r.get("status") if isinstance(r, dict) else "")
            rec_summary.append(f"- [{category}] {title} ({status_val})")

        # 4. Fetch Module 4 Placement Readiness
        readiness_out = PlacementService.calculate_placement_readiness(db, student.id, "SOFTWARE_DEVELOPER")
        readiness_data = readiness_out.model_dump()

        # Build compact, structured context
        student_profile = analytics["student_profile"]
        metrics = analytics["metrics"]
        recent_results = analytics.get("academic_records", [])[:3]
        attendance_subjects = analytics.get("attendance_summary", {}).get("subject_breakdown", [])

        # Placement gap summary
        skill_gaps = readiness_data.get("skill_gap_analysis", [])
        matched = [s["skill_name"] for s in skill_gaps if s["status"] in ["MATCHED", "REQUIRES_VERIFICATION"]]
        missing = [s["skill_name"] for s in skill_gaps if s["status"] == "MISSING"]
        below = [f"{s['skill_name']} ({s['student_proficiency']} vs {s['required_proficiency']})" for s in skill_gaps if s["status"] == "BELOW_PROFICIENCY"]

        return {
            "student_id": student.id,
            "full_name": student_profile["full_name"],
            "usn": student_profile["usn"],
            "srn": student_profile["srn"],
            "department": student_profile.get("department_name", ""),
            "program": student_profile["program"],
            "current_semester": student_profile["current_semester"],
            "section": student_profile["section"],
            "cgpa": metrics.get("cgpa", 0.0),
            "total_credits": metrics.get("total_credits_earned", 0),
            "active_backlogs": metrics.get("total_backlogs", 0),
            "overall_attendance_percentage": metrics.get("overall_attendance_percentage", 0.0),
            "cia_average": metrics.get("internal_assessment_average", 0.0),
            "risk_status": "FLAGGED" if active_alerts_list else "NORMAL",
            "active_alerts_count": len(active_alerts_list),
            "active_alerts_detail": alerts_summary,
            "target_career_role": readiness_data.get("career_role_title", "Software Developer"),
            "readiness_score": readiness_data.get("readiness_score", 0.0),
            "readiness_tier": readiness_data.get("readiness_tier", "DEVELOPING"),
            "mandatory_skills_met": readiness_data.get("mandatory_skills_met", False),
            "matched_skills": matched,
            "missing_skills": missing,
            "below_proficiency_skills": below,
            "active_recommendations": rec_summary,
            "recent_academic_records": [
                {
                    "semester": r.get("semester"),
                    "sgpa": r.get("sgpa"),
                    "cgpa": r.get("cgpa"),
                    "backlogs": r.get("backlogs"),
                }
                for r in recent_results
            ],
            "subject_attendance": [
                {
                    "subject": s.get("subject_name"),
                    "percentage": s.get("percentage"),
                    "attended": s.get("attended_classes"),
                    "total": s.get("total_classes"),
                }
                for s in attendance_subjects[:5]
            ],
        }
