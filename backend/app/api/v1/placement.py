from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.access import own_student_record
from app.core.database import get_db
from app.models.profile import Student
from app.models.student_intelligence import Skill
from app.models.user import User, UserRole
from app.schemas.placement import (
    CareerRoleCreate,
    CareerRoleResponse,
    OpportunityMatchForStudent,
    PlacementOpportunityCreate,
    PlacementOpportunityResponse,
    PlacementReadinessResponse,
    SkillCreate,
    SkillEvidenceCreate,
    SkillEvidenceResponse,
    SkillEvidenceVerify,
    SkillResponse,
    StudentApplicationCreate,
    StudentApplicationResponse,
    StudentApplicationStatusUpdate,
    StudentSkillCreateOrUpdate,
    StudentSkillDetailResponse,
)
from app.services.placement_service import (
    APPLICATION_STATUSES,
    InvalidApplicationStatus,
    PlacementService,
    application_to_response,
    career_role_to_response,
    default_role_code_for_student,
    opportunity_to_response,
)

router = APIRouter(prefix="/placement", tags=["Skill Gap & Placement Readiness"])

PLACEMENT_MANAGERS = {UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value}
CATALOGUE_EDITORS = PLACEMENT_MANAGERS | {UserRole.FACULTY.value}
EVIDENCE_VERIFIERS = CATALOGUE_EDITORS | {UserRole.MENTOR.value}


def verify_student_access(student_id: int, current_user: User, db: Session):
    """Ensure students can only access their own profile; faculty/admins/placement officers have institutional access."""
    if current_user.role == UserRole.STUDENT.value:
        student = own_student_record(db, current_user)
        if not student or student.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students can only access their own placement and skill records."
            )


# --- 1. Skill Catalogue ---
@router.get("/skills", response_model=List[SkillResponse])
def get_skills_catalogue(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve skill catalogue across programming, frameworks, cloud, data science, soft skills, etc."""
    q = db.query(Skill)
    if category:
        q = q.filter(Skill.category == category.lower())
    return q.order_by(Skill.name).all()


@router.post("/skills", response_model=SkillResponse)
def create_skill(
    skill_in: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a new skill to the institutional catalogue (Admin or Placement Officer)."""
    if current_user.role not in CATALOGUE_EDITORS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to add catalogue skills.")
    return PlacementService.get_or_create_skill(db, skill_in.name, skill_in.category, skill_in.description)


# --- 2. Student Skill Profiles & Evidence ---
@router.get("/students/{student_id}/skills", response_model=List[StudentSkillDetailResponse])
def get_student_skills(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all skills for a student, distinguishing self-reported vs. verified with supporting evidences."""
    verify_student_access(student_id, current_user, db)
    return PlacementService.get_student_skills_detail(db, student_id)


@router.post("/students/{student_id}/skills", response_model=StudentSkillDetailResponse)
def add_or_update_student_skill(
    student_id: int,
    payload: StudentSkillCreateOrUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add or update proficiency of a student skill, optionally attaching initial evidence."""
    verify_student_access(student_id, current_user, db)
    student_skill = PlacementService.add_or_update_student_skill(
        db,
        student_id=student_id,
        skill_name=payload.skill_name,
        category=payload.category,
        proficiency_level=payload.proficiency_level,
        evidence=payload.evidence
    )
    details = PlacementService.get_student_skills_detail(db, student_id)
    match = next((s for s in details if s["id"] == student_skill.id), None)
    if not match:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated skill")
    return match


@router.post("/students/{student_id}/evidence", response_model=SkillEvidenceResponse)
def submit_skill_evidence(
    student_id: int,
    payload: SkillEvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit project, certification, or repo evidence to back a self-reported skill."""
    verify_student_access(student_id, current_user, db)
    return PlacementService.submit_skill_evidence(
        db,
        student_id=student_id,
        student_skill_id=payload.student_skill_id,
        evidence=payload
    )


@router.post("/evidence/{evidence_id}/verify", response_model=SkillEvidenceResponse)
def verify_skill_evidence(
    evidence_id: int,
    payload: SkillEvidenceVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Faculty, Admins, or Placement Officers verify or reject student skill evidence."""
    if current_user.role not in EVIDENCE_VERIFIERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only faculty and placement officers can verify skill evidence.")
    try:
        return PlacementService.verify_skill_evidence(
            db,
            evidence_id=evidence_id,
            verifier_user_id=current_user.id,
            verification_status=payload.verification_status,
            feedback=payload.verification_feedback
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# --- 3. Career Role Catalogue ---
@router.get("/roles", response_model=List[CareerRoleResponse])
def get_career_roles(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List configurable career roles with required skills and salary benchmarks."""
    roles = PlacementService.get_career_roles(db, is_active)
    if not roles:
        roles = PlacementService.seed_canonical_career_roles(db)

    return [career_role_to_response(r) for r in roles]


@router.post("/roles", response_model=CareerRoleResponse)
def create_career_role(
    payload: CareerRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Placement Officers and Admins configure a new career role with skill benchmarks."""
    if current_user.role not in PLACEMENT_MANAGERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only placement officers and administrators can configure career roles.")

    try:
        role = PlacementService.create_career_role(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return career_role_to_response(role)


# --- 4. Skill Gap & Placement Readiness Engine ---
@router.get("/readiness/{student_id}", response_model=PlacementReadinessResponse)
def get_student_placement_readiness(
    student_id: int,
    role: Optional[str] = Query(None, description="Career role code (e.g. SOFTWARE_DEVELOPER) or integer ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Evaluates student skills against a target career role.
    Computes readiness score (0-100%), skill coverage, missing skills, below-proficiency gaps, and recommended actions.
    """
    verify_student_access(student_id, current_user, db)
    try:
        if not role:
            role = default_role_code_for_student(db.query(Student).filter(Student.id == student_id).first())
        return PlacementService.calculate_placement_readiness(db, student_id, role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# --- 5. Placement Opportunities ---
@router.get("/opportunities", response_model=List[PlacementOpportunityResponse])
def get_opportunities(
    opportunity_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List job and internship opportunities with eligibility criteria."""
    opps = PlacementService.list_opportunities(db, opportunity_type, status_filter, search)
    if not opps:
        opps = PlacementService.seed_canonical_opportunities(db)

    return [opportunity_to_response(o) for o in opps]


@router.post("/opportunities", response_model=PlacementOpportunityResponse)
def create_placement_opportunity(
    payload: PlacementOpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Placement Officer creates a corporate recruitment drive or internship."""
    if current_user.role not in PLACEMENT_MANAGERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only placement officers can post opportunities.")

    return opportunity_to_response(PlacementService.create_opportunity(db, payload, current_user.id))


@router.get("/students/{student_id}/matching-opportunities", response_model=List[OpportunityMatchForStudent])
def get_student_matching_opportunities(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Checks eligibility and computes skill readiness match for all active opportunities for this student."""
    verify_student_access(student_id, current_user, db)
    try:
        return PlacementService.get_matching_opportunities_for_student(db, student_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# --- 6. Applications Tracking ---
@router.post("/applications", response_model=StudentApplicationResponse)
def submit_student_application(
    payload: StudentApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Student submits an application to an eligible placement or internship opportunity."""
    student = own_student_record(db, current_user)
    if not student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only registered students can apply for opportunities.")

    try:
        app = PlacementService.apply_to_opportunity(
            db,
            student_id=student.id,
            opportunity_id=payload.opportunity_id,
            resume_url=payload.resume_url,
            cover_notes=payload.cover_notes,
        )
        return application_to_response(app)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/applications", response_model=List[StudentApplicationResponse])
def list_student_applications(
    student_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List applications, newest first, optionally filtered by status and paged. Students only see their
    own applications; Placement Officers and Admins see all across the institution.
    """
    if current_user.role == UserRole.STUDENT.value:  # students see only their own applications
        student = own_student_record(db, current_user)
        if not student:
            return []
        student_id, opportunity_id = student.id, None
    apps = PlacementService.list_applications(db, student_id=student_id, opportunity_id=opportunity_id,
                                              status=status, skip=skip, limit=limit)
    return [application_to_response(a) for a in apps]


@router.get("/applications/count")
def count_student_applications(
    student_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """How many applications match the same filters as the list (for pagination)."""
    if current_user.role == UserRole.STUDENT.value:
        student = own_student_record(db, current_user)
        if not student:
            return {"total": 0}
        student_id, opportunity_id = student.id, None
    return {"total": PlacementService.count_applications(db, student_id=student_id, opportunity_id=opportunity_id,
                                                         status=status)}


@router.put("/applications/{application_id}/status", response_model=StudentApplicationResponse)
def update_application_status(
    application_id: int,
    payload: StudentApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Placement officer moves an application through the workflow (see APPLICATION_STATUSES).
    Marking it PLACED records the accepted offer and sets the student's placement status to Placed."""
    if current_user.role not in PLACEMENT_MANAGERS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only placement officers can update application statuses.")
    try:
        app = PlacementService.update_application_status(db, application_id, payload.status, payload.reviewer_notes)
        return application_to_response(app)
    except InvalidApplicationStatus:
        raise HTTPException(status_code=422, detail="Status must be one of: " + ", ".join(APPLICATION_STATUSES)) from None
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
