from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.student_intelligence import (
    AdminAnalyticsOut,
    CertificationCreate,
    CertificationOut,
    FacultyAnalyticsOut,
    InternshipCreate,
    InternshipOut,
    ProjectCreate,
    ProjectOut,
    StudentAnalyticsOut,
    StudentCreate,
    StudentProfileOut,
    StudentSkillCreate,
    StudentSkillOut,
    StudentUpdate,
)
from app.services.student_service import StudentIntelligenceService

router = APIRouter(prefix="/students", tags=["Student Intelligence & Analytics"])


@router.get("/", response_model=List[StudentProfileOut])
def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """List and search students with filters. Students only see their own record."""
    service = StudentIntelligenceService(db)
    students, _ = service.list_students(
        current_user=current_user,
        skip=skip,
        limit=limit,
        search=search,
        department_id=department_id,
        semester=semester,
        section=section,
        status_filter=status,
    )
    return students


@router.get("/count")
def count_students(
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    semester: Optional[int] = None,
    section: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """How many students match the same filters as the list (for pagination)."""
    _, total = StudentIntelligenceService(db).list_students(
        current_user=current_user, skip=0, limit=1, search=search, department_id=department_id,
        semester=semester, section=section, status_filter=status,
    )
    return {"total": total}


@router.post("/", response_model=StudentProfileOut, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new student record (Administrator only)."""
    service = StudentIntelligenceService(db)
    return service.create_student(student_in, current_user)


@router.get("/analytics/faculty", response_model=FacultyAnalyticsOut)
def get_faculty_cohort_analytics(
    current_user: User = Depends(require_role(UserRole.FACULTY.value, UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Get aggregated cohort performance for assigned faculty courses."""
    service = StudentIntelligenceService(db)
    return service.get_faculty_analytics(current_user)


@router.get("/analytics/admin", response_model=AdminAnalyticsOut)
def get_admin_institutional_analytics(
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Get institutional academic distributions, department analytics, and attendance metrics."""
    service = StudentIntelligenceService(db)
    return service.get_admin_analytics(current_user)


@router.get("/{student_id}", response_model=StudentProfileOut)
def get_student_profile(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get full profile details for a student. Students are restricted to their own ID."""
    service = StudentIntelligenceService(db)
    return service.get_student_by_id(student_id, current_user)


@router.patch("/{student_id}", response_model=StudentProfileOut)
def update_student_profile(
    student_id: int,
    student_in: StudentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Edit student profile information."""
    service = StudentIntelligenceService(db)
    return service.update_student(student_id, student_in, current_user)


@router.get("/{student_id}/analytics", response_model=StudentAnalyticsOut)
def get_individual_student_analytics(
    student_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Consolidated Student Intelligence: SGPA trends, subjects, calculated attendance, assessments, skills, projects."""
    service = StudentIntelligenceService(db)
    return service.get_student_analytics(student_id, current_user)


@router.post("/{student_id}/skills", response_model=StudentSkillOut, status_code=status.HTTP_201_CREATED)
def add_student_skill(
    student_id: int,
    skill_in: StudentSkillCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add or update a technical / soft skill on the student profile."""
    service = StudentIntelligenceService(db)
    st_skill = service.add_student_skill(student_id, skill_in, current_user)
    return {
        "id": st_skill.id,
        "skill_id": st_skill.skill_id,
        "skill_name": st_skill.skill.name if st_skill.skill else skill_in.skill_name,
        "category": st_skill.skill.category if st_skill.skill else skill_in.category,
        "proficiency_level": st_skill.proficiency_level,
        "is_verified": st_skill.is_verified,
    }


@router.post("/{student_id}/certifications", response_model=CertificationOut, status_code=status.HTTP_201_CREATED)
def add_certification(
    student_id: int,
    cert_in: CertificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add a professional certification record."""
    service = StudentIntelligenceService(db)
    return service.add_certification(student_id, cert_in, current_user)


@router.post("/{student_id}/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def add_project(
    student_id: int,
    proj_in: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add an engineering / academic project record."""
    service = StudentIntelligenceService(db)
    return service.add_project(student_id, proj_in, current_user)


@router.post("/{student_id}/internships", response_model=InternshipOut, status_code=status.HTTP_201_CREATED)
def add_internship(
    student_id: int,
    intern_in: InternshipCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add an industry internship experience record."""
    service = StudentIntelligenceService(db)
    return service.add_internship(student_id, intern_in, current_user)
