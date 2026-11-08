from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.profile import Student
from app.models.student_intelligence import Skill
from app.models.placement import (
    CareerRole,
    RoleSkill,
    PlacementOpportunity,
    OpportunityRequirement,
    StudentApplication,
    SkillEvidence,
)
from app.schemas.placement import (
    SkillResponse,
    SkillCreate,
    SkillEvidenceCreate,
    SkillEvidenceVerify,
    SkillEvidenceResponse,
    StudentSkillDetailResponse,
    StudentSkillCreateOrUpdate,
    CareerRoleCreate,
    CareerRoleUpdate,
    CareerRoleResponse,
    RoleSkillResponse,
    PlacementReadinessResponse,
    PlacementOpportunityCreate,
    PlacementOpportunityResponse,
    OpportunityMatchForStudent,
    StudentApplicationCreate,
    StudentApplicationStatusUpdate,
    StudentApplicationResponse,
)
from app.services.placement_service import PlacementService

router = APIRouter(prefix="/placement", tags=["Skill Gap & Placement Readiness"])


def verify_student_access(student_id: int, current_user: User, db: Session):
    """Ensure students can only access their own profile; faculty/admins/placement officers have institutional access."""
    if current_user.role in [UserRole.STUDENT.value, "student"]:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
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
    if current_user.role not in [UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value, UserRole.FACULTY.value, "admin", "placement_officer", "faculty"]:
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
    if current_user.role not in [UserRole.FACULTY.value, UserRole.MENTOR.value, UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value, "faculty", "mentor", "admin", "placement_officer"]:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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
    
    results = []
    for r in roles:
        skills_res = []
        for rs in r.role_skills:
            skills_res.append(RoleSkillResponse(
                id=rs.id,
                role_id=rs.role_id,
                skill_id=rs.skill_id,
                skill_name=rs.skill.name if rs.skill else "",
                category=rs.skill.category if rs.skill else "programming",
                min_proficiency=rs.min_proficiency,
                importance=rs.importance,
                importance_weight=rs.importance_weight,
                is_mandatory=rs.is_mandatory,
            ))
        results.append(CareerRoleResponse(
            id=r.id,
            code=r.code,
            title=r.title,
            department_id=r.department_id,
            department_code=r.department.code if r.department else None,
            description=r.description,
            min_experience_level=r.min_experience_level,
            average_salary_range=r.average_salary_range,
            industry_demand=r.industry_demand,
            is_active=r.is_active,
            skills=skills_res,
            created_at=r.created_at,
        ))
    return results


@router.post("/roles", response_model=CareerRoleResponse)
def create_career_role(
    payload: CareerRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Placement Officers and Admins configure a new career role with skill benchmarks."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value, "admin", "placement_officer"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only placement officers and administrators can configure career roles.")
    
    existing = db.query(CareerRole).filter(CareerRole.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Career role code '{payload.code}' already exists.")

    role = CareerRole(
        code=payload.code.upper(),
        title=payload.title,
        department_id=payload.department_id,
        description=payload.description,
        min_experience_level=payload.min_experience_level,
        average_salary_range=payload.average_salary_range,
        industry_demand=payload.industry_demand,
        is_active=payload.is_active,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    for item in payload.required_skills:
        skill = PlacementService.get_or_create_skill(db, item.skill_name, item.category or "programming")
        rs = RoleSkill(
            role_id=role.id,
            skill_id=skill.id,
            min_proficiency=item.min_proficiency,
            importance=item.importance,
            importance_weight=item.importance_weight,
            is_mandatory=item.is_mandatory,
        )
        db.add(rs)
    db.commit()

    return PlacementService.get_career_role_by_id_or_code(db, role.id)


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
        # If no role specified, try student's declared first career goal or default
        if not role:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student and student.career_goals and len(student.career_goals) > 0:
                first_goal = student.career_goals[0].replace(" ", "_").upper()
                role = first_goal
            else:
                role = "SOFTWARE_DEVELOPER"
        return PlacementService.calculate_placement_readiness(db, student_id, role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- 5. Placement Opportunities ---
@router.get("/opportunities", response_model=List[PlacementOpportunityResponse])
def get_opportunities(
    opportunity_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List job and internship opportunities with eligibility criteria."""
    opps = PlacementService.list_opportunities(db, opportunity_type, status, search)
    if not opps:
        opps = PlacementService.seed_canonical_opportunities(db)
    
    results = []
    for o in opps:
        req_list = []
        for r in o.requirements:
            req_list.append({
                "skill_name": r.skill.name if r.skill else "",
                "min_proficiency": r.min_proficiency,
                "is_mandatory": r.is_mandatory,
            })
        results.append(PlacementOpportunityResponse(
            id=o.id,
            company_name=o.company_name,
            title=o.title,
            opportunity_type=o.opportunity_type,
            role_id=o.role_id,
            role_title=o.role.title if o.role else None,
            location=o.location,
            work_mode=o.work_mode,
            ctc_stipend=o.ctc_stipend,
            min_cgpa=o.min_cgpa,
            max_backlogs=o.max_backlogs,
            min_attendance=o.min_attendance,
            eligible_departments=o.eligible_departments,
            eligible_semesters=o.eligible_semesters,
            application_deadline=o.application_deadline,
            open_positions=o.open_positions,
            description=o.description,
            status=o.status,
            requirements=req_list,
            application_count=len(o.applications),
            created_at=o.created_at,
        ))
    return results


@router.post("/opportunities", response_model=PlacementOpportunityResponse)
def create_placement_opportunity(
    payload: PlacementOpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Placement Officer creates a corporate recruitment drive or internship."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value, "admin", "placement_officer"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only placement officers can post opportunities.")
    
    opp = PlacementOpportunity(
        company_name=payload.company_name,
        title=payload.title,
        opportunity_type=payload.opportunity_type,
        role_id=payload.role_id,
        location=payload.location,
        work_mode=payload.work_mode,
        ctc_stipend=payload.ctc_stipend,
        min_cgpa=payload.min_cgpa,
        max_backlogs=payload.max_backlogs,
        min_attendance=payload.min_attendance,
        eligible_departments=payload.eligible_departments,
        eligible_semesters=payload.eligible_semesters,
        application_deadline=payload.application_deadline,
        open_positions=payload.open_positions,
        description=payload.description,
        status=payload.status,
        created_by_user_id=current_user.id,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)

    for req_in in payload.requirements:
        skill = PlacementService.get_or_create_skill(db, req_in.skill_name)
        req = OpportunityRequirement(
            opportunity_id=opp.id,
            skill_id=skill.id,
            min_proficiency=req_in.min_proficiency,
            is_mandatory=req_in.is_mandatory,
        )
        db.add(req)
    db.commit()

    return opp


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# --- 6. Applications Tracking ---
@router.post("/applications", response_model=StudentApplicationResponse)
def submit_student_application(
    payload: StudentApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Student submits an application to an eligible placement or internship opportunity."""
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
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
        user_name = student.user.full_name if (student.user and student.user.full_name) else "Student"
        return StudentApplicationResponse(
            id=app.id,
            opportunity_id=app.opportunity_id,
            opportunity_title=app.opportunity.title if app.opportunity else "",
            company_name=app.opportunity.company_name if app.opportunity else "",
            opportunity_type=app.opportunity.opportunity_type if app.opportunity else "JOB",
            ctc_stipend=app.opportunity.ctc_stipend if app.opportunity else "",
            location=app.opportunity.location if app.opportunity else "",
            deadline=app.opportunity.application_deadline if app.opportunity else datetime.now(timezone.utc).date(),
            student_id=student.id,
            student_name=user_name,
            student_srn=student.srn or student.usn,
            status=app.status,
            applied_at=app.applied_at,
            resume_url=app.resume_url,
            cover_notes=app.cover_notes,
            reviewer_notes=app.reviewer_notes,
            readiness_score_at_application=app.readiness_score_at_application,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/applications", response_model=List[StudentApplicationResponse])
def list_student_applications(
    student_id: Optional[int] = None,
    opportunity_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List applications. Students only see their own applications;
    Placement Officers and Admins see all across the institution.
    """
    q = db.query(StudentApplication)
    if current_user.role in [UserRole.STUDENT.value, "student"]:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not student:
            return []
        q = q.filter(StudentApplication.student_id == student.id)
    else:
        if student_id:
            q = q.filter(StudentApplication.student_id == student_id)
        if opportunity_id:
            q = q.filter(StudentApplication.opportunity_id == opportunity_id)

    apps = q.order_by(StudentApplication.applied_at.desc()).all()
    results = []
    for a in apps:
        st_name = a.student.user.full_name if (a.student and a.student.user and a.student.user.full_name) else "Student"
        results.append(StudentApplicationResponse(
            id=a.id,
            opportunity_id=a.opportunity_id,
            opportunity_title=a.opportunity.title if a.opportunity else "",
            company_name=a.opportunity.company_name if a.opportunity else "",
            opportunity_type=a.opportunity.opportunity_type if a.opportunity else "JOB",
            ctc_stipend=a.opportunity.ctc_stipend if a.opportunity else "",
            location=a.opportunity.location if a.opportunity else "",
            deadline=a.opportunity.application_deadline if a.opportunity else datetime.now(timezone.utc).date(),
            student_id=a.student_id,
            student_name=st_name,
            student_srn=a.student.srn or a.student.usn if a.student else None,
            status=a.status,
            applied_at=a.applied_at,
            resume_url=a.resume_url,
            cover_notes=a.cover_notes,
            reviewer_notes=a.reviewer_notes,
            readiness_score_at_application=a.readiness_score_at_application,
        ))
    return results


@router.put("/applications/{application_id}/status", response_model=StudentApplicationResponse)
def update_application_status(
    application_id: int,
    payload: StudentApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Placement Officer updates application status (SHORTLISTED, INTERVIEW_SCHEDULED, OFFERED, REJECTED)."""
    if current_user.role not in [UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value, "admin", "placement_officer"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only placement officers can update application statuses.")
    try:
        app = PlacementService.update_application_status(db, application_id, payload.status, payload.reviewer_notes)
        st_name = app.student.user.full_name if (app.student and app.student.user and app.student.user.full_name) else "Student"
        return StudentApplicationResponse(
            id=app.id,
            opportunity_id=app.opportunity_id,
            opportunity_title=app.opportunity.title if app.opportunity else "",
            company_name=app.opportunity.company_name if app.opportunity else "",
            opportunity_type=app.opportunity.opportunity_type if app.opportunity else "JOB",
            ctc_stipend=app.opportunity.ctc_stipend if app.opportunity else "",
            location=app.opportunity.location if app.opportunity else "",
            deadline=app.opportunity.application_deadline if app.opportunity else datetime.now(timezone.utc).date(),
            student_id=app.student_id,
            student_name=st_name,
            student_srn=app.student.srn or app.student.usn if app.student else None,
            status=app.status,
            applied_at=app.applied_at,
            resume_url=app.resume_url,
            cover_notes=app.cover_notes,
            reviewer_notes=app.reviewer_notes,
            readiness_score_at_application=app.readiness_score_at_application,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
