from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.academic import FacultyCourseAssignment, Semester, Subject
from app.models.department import Department
from app.models.profile import Faculty
from app.models.user import User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.schemas.academic import (
    FacultyCourseAssignmentOut,
    SemesterCreate,
    SemesterOut,
    SubjectCreate,
    SubjectOut,
    TeachingAssignmentCreate,
)

router = APIRouter(prefix="/academics", tags=["Academic Structure"])


@router.get("/semesters", response_model=List[SemesterOut])
def list_semesters(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all configured academic semesters."""
    return db.query(Semester).order_by(Semester.semester_number.asc()).all()


@router.post("/semesters", response_model=SemesterOut, status_code=status.HTTP_201_CREATED)
def create_semester(
    sem_in: SemesterCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
) -> Any:
    """Create a term (Admin only). Marking it current un-marks any previous current term."""
    if db.query(Semester).filter(Semester.semester_number == sem_in.semester_number,
                                 Semester.academic_year == sem_in.academic_year).first():
        raise HTTPException(status_code=400, detail="This term already exists for that academic year.")
    if sem_in.is_current:
        db.query(Semester).filter(Semester.is_current.is_(True)).update({"is_current": False})
    semester = Semester(**sem_in.model_dump())
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.get("/subjects", response_model=List[SubjectOut])
def list_subjects(
    department_id: int = None,
    semester_number: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List all subjects with optional filters."""
    query = db.query(Subject)
    if department_id:
        query = query.filter(Subject.department_id == department_id)
    if semester_number:
        query = query.filter(Subject.semester_number == semester_number)
    return query.all()


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    sub_in: SubjectCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
) -> Any:
    """Register a new subject curriculum (Admin only)."""
    existing = db.query(Subject).filter(Subject.code == sub_in.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject with this code already exists")
    # The session is tenant-scoped, so another university's department is indistinguishable from a missing one.
    if not db.query(Department).filter(Department.id == sub_in.department_id).first():
        raise HTTPException(status_code=422, detail="Department not found in your university.")

    subject = Subject(**sub_in.model_dump())
    subject.code = subject.code.upper()
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/assignments", response_model=List[FacultyCourseAssignmentOut])
def list_course_assignments(
    faculty_id: int = None,
    semester_id: int = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """List faculty course assignments."""
    query = db.query(FacultyCourseAssignment)
    if faculty_id:
        query = query.filter(FacultyCourseAssignment.faculty_id == faculty_id)
    if semester_id:
        query = query.filter(FacultyCourseAssignment.semester_id == semester_id)

    assignments = query.all()
    results = []
    for a in assignments:
        item = FacultyCourseAssignmentOut(
            id=a.id,
            faculty_id=a.faculty_id,
            subject_id=a.subject_id,
            semester_id=a.semester_id,
            section=a.section,
            academic_year=a.academic_year,
            faculty_name=a.faculty.user.full_name if a.faculty and a.faculty.user else "Faculty",
            subject_name=a.subject.name if a.subject else "Subject",
            subject_code=a.subject.code if a.subject else "N/A"
        )
        results.append(item)
    return results


@router.post("/assignments", response_model=FacultyCourseAssignmentOut, status_code=status.HTTP_201_CREATED)
def create_course_assignment(
    body: TeachingAssignmentCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Assign a faculty member to a subject section (Admin only). This decides which students they can see."""
    faculty = db.query(Faculty).filter(Faculty.user_id == body.faculty_user_id).first()
    if not faculty:
        raise HTTPException(status_code=422, detail="That person has no faculty profile in your university.")
    subject = db.query(Subject).filter(Subject.id == body.subject_id).first()
    term = db.query(Semester).filter(Semester.id == body.semester_id).first()
    if not subject or not term:
        raise HTTPException(status_code=422, detail="Subject or term not found in your university.")
    section = body.section.strip().upper()
    duplicate = db.query(FacultyCourseAssignment).filter(
        FacultyCourseAssignment.faculty_id == faculty.id, FacultyCourseAssignment.subject_id == subject.id,
        FacultyCourseAssignment.semester_id == term.id, FacultyCourseAssignment.section == section).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="This teaching assignment already exists.")
    assignment = FacultyCourseAssignment(faculty_id=faculty.id, subject_id=subject.id, semester_id=term.id,
                                         section=section, academic_year=body.academic_year.strip())
    db.add(assignment)
    AuditRepository(db).log(action="TEACHING_ASSIGNMENT_CREATED", user_id=current_user.id,
                            resource_type="teaching_assignment", resource_id=f"{faculty.id}:{subject.id}:{section}",
                            details={"faculty_user_id": body.faculty_user_id, "subject": subject.code,
                                     "term_id": term.id, "section": section}, commit=False)
    db.commit()
    db.refresh(assignment)
    return FacultyCourseAssignmentOut(
        id=assignment.id, faculty_id=faculty.id, subject_id=subject.id, semester_id=term.id, section=section,
        academic_year=assignment.academic_year, faculty_name=faculty.user.full_name if faculty.user else None,
        subject_name=subject.name, subject_code=subject.code,
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_assignment(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> None:
    """Remove a teaching assignment; the faculty member loses access to that section's students."""
    assignment = db.query(FacultyCourseAssignment).filter(FacultyCourseAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Teaching assignment not found.")
    db.delete(assignment)
    AuditRepository(db).log(action="TEACHING_ASSIGNMENT_REMOVED", user_id=current_user.id,
                            resource_type="teaching_assignment", resource_id=str(assignment_id), commit=False)
    db.commit()
