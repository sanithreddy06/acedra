"""
Server-side access policy for student records.

* student            — only their own record
* faculty            — students in sections they teach (department + semester + section of a
                       FacultyCourseAssignment) plus students explicitly authorised via
                       StaffStudentAccess
* mentor             — assigned mentees (Student.assigned_mentor_id or active StudentMentorAssignment)
* admin              — every student in their own university
* placement_officer  — every student in their own university (placement data)
* platform roles     — no student data, unless an active StudentDataAccessGrant exists and
                       the specific grant-checked endpoint is used

How it is enforced: ``accessible_student_ids`` is computed once per request in
``api.deps.get_current_user`` and stored on the session's ``TenantScope``. The ORM hook in
``core.tenancy`` then filters every student-owned query to that set, and the university route guard
(``api.deps.get_university_user``) returns 404/403 for any ``student_id`` outside it. Route handlers add
explicit checks only where a rule is narrower than the scope (e.g. students acting on their own records).
"""
from typing import Optional, Set

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.user import PLATFORM_ROLES, User, UserRole


def _q(db: Session, *entities):
    return db.query(*entities).execution_options(acedra_unscoped=True)


def accessible_student_ids(db: Session, user: User) -> Optional[Set[int]]:
    """Return the set of student ids the user may see, or None for "all in tenant"."""
    from app.models import Faculty, Mentor, Student, StudentMentorAssignment

    tid = user.university_id
    role = user.role
    if role in PLATFORM_ROLES:
        return set()
    if role in (UserRole.ADMIN.value, UserRole.PLACEMENT_OFFICER.value):
        return None
    if role == UserRole.STUDENT.value:
        rows = _q(db, Student.id).filter(Student.user_id == user.id, Student.university_id == tid).all()
        return {r[0] for r in rows}
    if role == UserRole.MENTOR.value:
        mentor = _q(db, Mentor).filter(Mentor.user_id == user.id, Mentor.university_id == tid).first()
        if not mentor:
            return set()
        ids = {r[0] for r in _q(db, Student.id).filter(
            Student.assigned_mentor_id == mentor.id, Student.university_id == tid).all()}
        ids |= {r[0] for r in _q(db, StudentMentorAssignment.student_id).filter(
            StudentMentorAssignment.mentor_id == mentor.id, StudentMentorAssignment.is_active.is_(True),
            StudentMentorAssignment.university_id == tid).all()}
        return ids
    if role == UserRole.FACULTY.value:
        faculty = _q(db, Faculty).filter(Faculty.user_id == user.id, Faculty.university_id == tid).first()
        return faculty_student_ids(db, user, faculty)
    return set()


def faculty_student_ids(db: Session, user: User, faculty) -> Set[int]:
    """Students a faculty member may see: every student in a section they teach (department + semester +
    section of a teaching assignment, in any department) plus students an administrator explicitly shared
    with them through StaffStudentAccess. Department membership alone grants nothing.

    The same set drives list views, direct record access and faculty analytics, so they always agree.
    """
    from app.models import FacultyCourseAssignment, Student, Subject
    from app.models.platform import StaffStudentAccess

    tid = user.university_id
    ids: Set[int] = set()
    if faculty is not None:
        sections = _q(db, Subject.department_id, Subject.semester_number, FacultyCourseAssignment.section).join(
            Subject, Subject.id == FacultyCourseAssignment.subject_id
        ).filter(FacultyCourseAssignment.faculty_id == faculty.id,
                 FacultyCourseAssignment.university_id == tid).distinct().all()
        if sections:
            conds = [
                (Student.department_id == d) & (Student.current_semester == s) & (Student.section == sec)
                for d, s, sec in sections
            ]
            ids |= {r[0] for r in _q(db, Student.id).filter(Student.university_id == tid, or_(*conds)).all()}
    ids |= {r[0] for r in _q(db, StaffStudentAccess.student_id).filter(
        StaffStudentAccess.user_id == user.id, StaffStudentAccess.university_id == tid).all()}
    return ids


def own_student_record(db: Session, user: User):
    """The Student profile behind a student account, or None (staff accounts, or no profile yet).

    Uses the caller's tenant-scoped session, so it can never return another university's record.
    """
    from app.models import Student
    if user.role != UserRole.STUDENT.value:
        return None
    return db.query(Student).filter(Student.user_id == user.id).first()


def active_data_grant(db: Session, employee: User, university_id: int, scope: str = "student_directory_read"):
    from app.models.platform import StudentDataAccessGrant
    now = utcnow()
    return (
        db.query(StudentDataAccessGrant)
        .filter(
            StudentDataAccessGrant.employee_user_id == employee.id,
            StudentDataAccessGrant.university_id == university_id,
            StudentDataAccessGrant.scope == scope,
            StudentDataAccessGrant.revoked_at.is_(None),
            StudentDataAccessGrant.starts_at <= now,
            StudentDataAccessGrant.expires_at > now,
        )
        .first()
    )
