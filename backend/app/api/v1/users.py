"""University user management — invitation based. Platform roles can never be assigned here."""
from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_university_admin
from app.core.database import get_db
from app.models import Department, Faculty, Mentor, Student
from app.models.platform import University
from app.models.user import UNIVERSITY_ROLES, Role, User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.schemas.user import RoleOut
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/users", tags=["University Users"])


class InviteUser(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str
    department_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    # role-specific identifiers
    employee_id: Optional[str] = Field(None, max_length=50)
    roll_number: Optional[str] = Field(None, max_length=50)
    usn: Optional[str] = Field(None, max_length=50)
    current_semester: Optional[int] = Field(None, ge=1, le=12)
    section: Optional[str] = Field(None, max_length=10)
    batch_year: Optional[int] = None
    program: Optional[str] = Field(None, max_length=100)


class UpdateUser(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=150)
    department_id: Optional[int] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


def _user_out(u: User) -> dict:
    return {
        "id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "title": u.title,
        "phone": u.phone, "department_id": u.department_id,
        "department_name": u.department.name if u.department else None,
        "is_active": u.is_active, "is_verified": u.is_verified,
        "status": "active" if (u.is_active and u.is_verified) else ("invited" if not u.is_verified else "disabled"),
        "invited_at": u.invited_at.isoformat() if u.invited_at else None,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "is_synthetic": u.is_synthetic,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("/")
def list_users(
    role: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None,
    skip: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=200),
    current_user: User = Depends(require_university_admin), db: Session = Depends(get_db),
) -> Any:
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if status == "invited":
        q = q.filter(User.is_verified.is_(False))
    elif status == "active":
        q = q.filter(User.is_verified.is_(True), User.is_active.is_(True))
    elif status == "disabled":
        q = q.filter(User.is_verified.is_(True), User.is_active.is_(False))
    if search:
        term = f"%{search.lower()}%"
        q = q.filter(or_(func.lower(User.full_name).like(term), func.lower(User.email).like(term)))
    total = q.count()
    items = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    counts = dict(db.query(User.role, func.count(User.id)).group_by(User.role).all())
    return {"items": [_user_out(u) for u in items], "total": total, "role_counts": counts}


@router.get("/roles", response_model=List[RoleOut])
def get_roles(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> Any:
    return db.query(Role).filter(Role.name.in_(UNIVERSITY_ROLES)).all()


@router.post("/invite", status_code=201)
def invite_user(body: InviteUser, current_user: User = Depends(require_university_admin),
                db: Session = Depends(get_db)) -> Any:
    if body.role not in UNIVERSITY_ROLES:
        raise HTTPException(status_code=422, detail="Role must be one of the university roles.")
    university = db.query(University).filter(University.id == current_user.university_id).first()
    dept = None
    if body.department_id:
        dept = db.query(Department).filter(Department.id == body.department_id).first()
        if not dept:
            raise HTTPException(status_code=422, detail="Department not found in your university.")
    if body.role in ("student", "faculty", "mentor") and not dept:
        raise HTTPException(status_code=422, detail="A department is required for this role.")

    svc = InvitationService(db)
    user, inv, _ = svc.create_user_with_invitation(
        email=body.email, full_name=body.full_name, role=body.role, university=university,
        invited_by=current_user, department_id=body.department_id, title=body.title, phone=body.phone,
    )
    if body.role == UserRole.STUDENT.value:
        if not body.usn:
            raise HTTPException(status_code=422, detail="USN / registration number is required for students.")
        db.add(Student(
            user_id=user.id, roll_number=body.roll_number or body.usn, usn=body.usn,
            department_id=dept.id, current_semester=body.current_semester or 1,
            section=(body.section or "A").upper(), batch_year=body.batch_year or date.today().year,
            admission_year=body.batch_year or date.today().year,
            program=body.program or dept.name, cgpa=0.0, attendance_percentage=0.0,
        ))
    elif body.role == UserRole.FACULTY.value:
        db.add(Faculty(user_id=user.id, employee_id=body.employee_id or f"FAC-{user.id:05d}",
                       department_id=dept.id, designation=body.title or "Assistant Professor"))
    elif body.role == UserRole.MENTOR.value:
        db.add(Mentor(user_id=user.id, employee_id=body.employee_id or f"MNT-{user.id:05d}",
                      department_id=dept.id, designation=body.title or "Faculty Mentor"))
    AuditRepository(db).log(action="USER_INVITED", user_id=current_user.id, resource_type="user",
                            resource_id=str(user.id), details={"role": body.role}, commit=False)
    db.commit()
    return _user_out(user)


@router.post("/{user_id}/resend-invitation")
def resend_invitation(user_id: int, current_user: User = Depends(require_university_admin),
                      db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    InvitationService(db).resend(user, current_user)
    db.commit()
    return {"message": f"A new invitation was sent to {user.email}."}


@router.get("/{user_id}")
def get_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> Any:
    if current_user.role != UserRole.ADMIN.value and current_user.id != user_id:
        raise HTTPException(status_code=404, detail="User not found")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_out(user)


@router.patch("/{user_id}")
def update_user(user_id: int, body: UpdateUser, current_user: User = Depends(require_university_admin),
                db: Session = Depends(get_db)) -> Any:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = body.model_dump(exclude_unset=True)
    if "role" in data:
        if data["role"] not in UNIVERSITY_ROLES:
            raise HTTPException(status_code=422, detail="Platform roles cannot be assigned by a university.")
        if user.id == current_user.id and data["role"] != user.role:
            raise HTTPException(status_code=422, detail="You cannot change your own role.")
        if data["role"] != user.role and user.role in ("student",) or data["role"] == "student" and user.role != "student":
            raise HTTPException(status_code=422, detail="Student accounts cannot be converted to or from staff roles.")
        role_obj = db.query(Role).filter(Role.name == data["role"]).first()
        user.role_id = role_obj.id if role_obj else None
    if data.get("is_active") is False and user.id == current_user.id:
        raise HTTPException(status_code=422, detail="You cannot disable your own account.")
    if data.get("department_id") is not None and not db.query(Department).filter(
            Department.id == data["department_id"]).first():
        raise HTTPException(status_code=422, detail="Department not found in your university.")
    for k, v in data.items():
        setattr(user, k, v)
    if data.get("is_active") is False or "role" in data:
        user.token_version = (user.token_version or 0) + 1  # end existing sessions
    AuditRepository(db).log(action="USER_UPDATED", user_id=current_user.id, resource_type="user",
                            resource_id=str(user.id), details={"fields": sorted(data.keys())}, commit=False)
    db.commit()
    return _user_out(user)
