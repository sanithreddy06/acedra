from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.profile import Student
from app.models.recommendation import (
    Recommendation,
    RecommendationCatalogue,
)
from app.models.user import User, UserRole
from app.schemas.recommendation import (
    CatalogueItemCreate,
    CatalogueItemOut,
    CatalogueItemUpdate,
    MentorSuggestionCreate,
    RecommendationFeedbackCreate,
    RecommendationFeedbackOut,
    RecommendationGuidanceRequest,
    RecommendationOut,
    RecommendationProgressCreate,
    RecommendationRejectRequest,
    StudentCareerProfileUpdate,
    StudentLearningPathOut,
)
from app.services.recommendation_service import RecommendationService, recommendation_to_out

router = APIRouter(prefix="/recommendations", tags=["Personalized Recommendation Engine"])


def _get_student_for_caller(db: Session, student_id: int, current_user: User, denied_detail: str) -> Student:
    """Load a student (tenant-scoped) and stop students from acting on anyone but themselves."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
    if current_user.role == UserRole.STUDENT.value and student.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=denied_detail)
    return student


def _get_recommendation_for_caller(db: Session, recommendation_id: int, current_user: User) -> Recommendation:
    """Load a recommendation (tenant- and student-scoped); students may only act on their own."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    if current_user.role == UserRole.STUDENT.value and rec.student.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return rec


# -----------------------------------------------------------------------------
# 1. RECOMMENDATION CATALOGUE MANAGEMENT
# -----------------------------------------------------------------------------
@router.get("/catalogue", response_model=List[CatalogueItemOut])
def list_catalogue(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    status_filter: Optional[str] = Query("Active", alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve learning resources from the approved recommendation catalogue."""
    # Ensure default canonical resources are seeded
    RecommendationService.seed_default_catalogue_if_needed(db, current_user.id)
    return RecommendationService.get_catalogue(db, category=category, difficulty=difficulty, status=status_filter)


@router.post("/catalogue", response_model=CatalogueItemOut, status_code=status.HTTP_201_CREATED)
def create_catalogue_item(
    item_in: CatalogueItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "faculty")),
):
    """Administrator or faculty adds an approved resource to the catalogue."""
    data = item_in.model_dump()
    return RecommendationService.create_catalogue_item(db, data, user_id=current_user.id)


@router.put("/catalogue/{item_id}", response_model=CatalogueItemOut)
def update_catalogue_item(
    item_id: int,
    item_in: CatalogueItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Administrator modifies catalogue resource details."""
    item = db.query(RecommendationCatalogue).filter(RecommendationCatalogue.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalogue item not found.")
    return RecommendationService.update_catalogue_item(db, item, item_in.model_dump(exclude_unset=True))


@router.delete("/catalogue/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_catalogue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Administrator removes an item from the learning catalogue."""
    item = db.query(RecommendationCatalogue).filter(RecommendationCatalogue.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalogue item not found.")
    RecommendationService.delete_catalogue_item(db, item)
    return None


# -----------------------------------------------------------------------------
# 2. RECOMMENDATION GENERATION & RETRIEVAL
# -----------------------------------------------------------------------------
@router.post("/generate/{student_id}", response_model=List[RecommendationOut])
def generate_recommendations(
    student_id: int,
    force_regenerate: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Evaluates student academic results, skills, career goals, and interests to
    generate personalized, fact-grounded recommendations.
    """
    student = _get_student_for_caller(db, student_id, current_user, "Access denied: Students can only generate recommendations for themselves.")

    recs = RecommendationService.generate_recommendations_for_student(
        db, student_id=student.id, force_regenerate=force_regenerate
    )
    return [recommendation_to_out(r) for r in recs]


@router.get("/", response_model=List[RecommendationOut])
def list_recommendations(
    student_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List recommendations with filtering and role-based security scoping."""
    return RecommendationService.list_recommendations(
        db, current_user, student_id=student_id, category=category, status=status_filter,
        priority=priority, skip=skip, limit=limit,
    )


# -----------------------------------------------------------------------------
# 3. STUDENT LEARNING PATH & ROADMAP
# -----------------------------------------------------------------------------
@router.get("/students/{student_id}/learning-path", response_model=StudentLearningPathOut)
def get_student_learning_path(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve comprehensive categorized learning path (Academic vs Career)."""
    _get_student_for_caller(db, student_id, current_user,
                            "Access denied: Students can only view their own learning roadmap.")
    return RecommendationService.get_student_learning_path(db, student_id)


# -----------------------------------------------------------------------------
# 4. CAREER PROFILE & INTERESTS
# -----------------------------------------------------------------------------
@router.put("/students/{student_id}/career-profile")
def update_student_career_profile(
    student_id: int,
    profile_in: StudentCareerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Student or mentor updates career aspirations and technical interests."""
    student = _get_student_for_caller(db, student_id, current_user, "Access denied: Students can only edit their personal career profile.")

    student.career_goals = profile_in.career_goals
    student.interests = profile_in.interests
    db.commit()
    db.refresh(student)

    # Automatically trigger recommendation refresh with new goals
    RecommendationService.generate_recommendations_for_student(db, student_id=student.id, force_regenerate=True)

    return {
        "message": "Career profile updated and recommendations regenerated.",
        "career_goals": student.career_goals,
        "interests": student.interests,
    }


# -----------------------------------------------------------------------------
# 5. STUDENT ACTIONS (ACCEPT, REJECT, PROGRESS, FEEDBACK)
# -----------------------------------------------------------------------------
@router.post("/{recommendation_id}/accept")
def accept_recommendation(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Student accepts a recommended activity into their active learning roadmap."""
    _get_recommendation_for_caller(db, recommendation_id, current_user)

    updated = RecommendationService.accept_recommendation(db, recommendation_id, current_user.id)
    return {"message": "Recommendation accepted successfully.", "status": updated.status}


@router.post("/{recommendation_id}/reject")
def reject_recommendation(
    recommendation_id: int,
    req: RecommendationRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Student declines a recommendation with documented reason."""
    _get_recommendation_for_caller(db, recommendation_id, current_user)

    updated = RecommendationService.reject_recommendation(db, recommendation_id, req.rejection_reason)
    return {"message": "Recommendation rejected.", "status": updated.status}


@router.post("/{recommendation_id}/progress")
def update_progress(
    recommendation_id: int,
    progress_in: RecommendationProgressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Record completion progress and logged hours towards a recommendation."""
    _get_recommendation_for_caller(db, recommendation_id, current_user)

    updated = RecommendationService.update_progress(
        db=db,
        recommendation_id=recommendation_id,
        status=progress_in.status,
        percent_complete=progress_in.percent_complete,
        notes=progress_in.notes,
        hours_spent=progress_in.hours_spent,
        user_id=current_user.id,
    )
    return {"message": "Progress recorded.", "status": updated.status, "completed_at": updated.completed_at}


@router.post("/{recommendation_id}/feedback", response_model=RecommendationFeedbackOut)
def submit_feedback(
    recommendation_id: int,
    feedback_in: RecommendationFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Student submits feedback rating and review on recommendation utility."""
    rec = _get_recommendation_for_caller(db, recommendation_id, current_user)

    return RecommendationService.submit_feedback(
        db=db,
        recommendation_id=recommendation_id,
        student_id=rec.student_id,
        rating=feedback_in.rating,
        helpful=feedback_in.helpful,
        relevance_score=feedback_in.relevance_score,
        comments=feedback_in.comments,
        outcome_achieved=feedback_in.outcome_achieved,
    )


# -----------------------------------------------------------------------------
# 6. FACULTY & MENTOR ACTIONS
# -----------------------------------------------------------------------------
@router.post("/suggest", status_code=status.HTTP_201_CREATED)
def mentor_suggest_resource(
    suggestion_in: MentorSuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mentor", "faculty", "admin")),
):
    """Faculty or mentor proposes a targeted learning resource for a student."""
    rec = RecommendationService.create_mentor_suggestion(
        db=db,
        data=suggestion_in.model_dump(),
        mentor_user_id=current_user.id,
    )
    return {"message": "Recommendation proposed to student.", "recommendation_id": rec.id}


@router.post("/{recommendation_id}/guidance")
def add_guidance_notes(
    recommendation_id: int,
    req: RecommendationGuidanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mentor", "faculty", "admin")),
):
    """Mentor adds customized coaching notes to a recommendation."""
    rec = RecommendationService.add_guidance_notes(db, recommendation_id, req.guidance_notes)
    return {"message": "Mentor guidance notes documented.", "guidance_notes": rec.mentor_guidance_notes}
