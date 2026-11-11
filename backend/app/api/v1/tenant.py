"""University workspace: profile/branding for every member; settings and staffing for administrators."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_university_user, require_university_admin
from app.core.database import get_db
from app.models import Department, Faculty, Mentor, Student, StudentMentorAssignment, User
from app.models.platform import (
    AccountProvisioningRequest,
    StaffStudentAccess,
    University,
)
from app.repositories.audit_repo import AuditRepository
from app.services.platform_service import estimate_email_service

router = APIRouter(prefix="/tenant", tags=["University Workspace"], dependencies=[Depends(get_university_user)])

# Settings a university administrator may change. Identity, domains, modules and the ACEDRA
# contact are configured by the ACEDRA team (platform) under the service agreement.
ADMIN_EDITABLE_STRUCTURE_KEYS = {"minimum_attendance_percent", "internal_assessment_max", "term_label"}


def _uni(db: Session, user: User) -> University:
    return db.query(University).filter(University.id == user.university_id).first()


@router.get("/profile")
def profile(user: User = Depends(get_university_user), db: Session = Depends(get_db)) -> Any:
    u = _uni(db, user)
    data = {
        "id": u.id, "name": u.name, "short_name": u.short_name, "logo_url": u.logo_url, "tagline": u.tagline,
        "brand_color": u.brand_color, "status": u.status, "is_synthetic": u.is_synthetic,
        "enabled_modules": u.enabled_modules or [], "academic_structure": u.academic_structure or {},
        "document_categories": u.document_categories or [],
    }
    if user.role == "admin":
        # ACEDRA employees are platform users (no tenant) — load explicitly, outside tenant scoping.
        pe = db.query(User).execution_options(acedra_unscoped=True).filter(User.id == u.primary_employee_id).first() \
            if u.primary_employee_id else None
        data.update({
            "official_website": u.official_website, "location": u.location, "institution_type": u.institution_type,
            "student_email_mode": u.student_email_mode, "enforce_email_domains": u.enforce_email_domains,
            "notification_settings": u.notification_settings or {},
            "domains": [{"domain": d.domain, "purpose": d.purpose, "is_primary": d.is_primary} for d in u.domains],
            "acedra_contact": {"full_name": pe.full_name, "email": pe.email, "phone": pe.phone, "title": pe.title} if pe else None,
            "agreement_reference": u.agreement_reference,
        })
    return data


class TenantSettingsIn(BaseModel):
    tagline: Optional[str] = Field(None, max_length=255)
    academic_structure: Optional[Dict[str, Any]] = None
    document_categories: Optional[List[str]] = None
    notification_settings: Optional[Dict[str, Any]] = None


@router.patch("/settings")
def update_settings(body: TenantSettingsIn, user: User = Depends(require_university_admin),
                    db: Session = Depends(get_db)) -> Any:
    u = _uni(db, user)
    data = body.model_dump(exclude_unset=True)
    if "academic_structure" in data:
        bad = set(data["academic_structure"]) - ADMIN_EDITABLE_STRUCTURE_KEYS
        if bad:
            raise HTTPException(status_code=403, detail=f"These settings are managed with your ACEDRA contact: {sorted(bad)}")
        att = data["academic_structure"].get("minimum_attendance_percent")
        if att is not None and not (40 <= float(att) <= 100):
            raise HTTPException(status_code=422, detail="Minimum attendance must be between 40 and 100.")
        u.academic_structure = dict(u.academic_structure or {}, **data["academic_structure"])
    if "document_categories" in data:
        u.document_categories = [c.strip()[:80] for c in data["document_categories"] if c.strip()][:30]
    if "notification_settings" in data:
        u.notification_settings = dict(u.notification_settings or {}, **data["notification_settings"])
    if "tagline" in data:
        u.tagline = data["tagline"]
    AuditRepository(db).log(action="UNIVERSITY_SETTINGS_UPDATED", user_id=user.id, resource_type="university",
                            resource_id=str(u.id), details={"fields": sorted(data)}, commit=False)
    db.commit()
    return profile(user, db)


# ---------------------------------------------------------------- departments
class DepartmentIn(BaseModel):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=150)
    hod_name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None


@router.get("/departments")
def departments(user: User = Depends(get_university_user), db: Session = Depends(get_db)) -> Any:
    counts = dict(db.query(Student.department_id, func.count(Student.id)).group_by(Student.department_id).all()) \
        if user.role in ("admin", "placement_officer") else {}
    fac = dict(db.query(Faculty.department_id, func.count(Faculty.id)).group_by(Faculty.department_id).all())
    return [{"id": d.id, "code": d.code, "name": d.name, "hod_name": d.hod_name, "description": d.description,
             "student_count": counts.get(d.id), "faculty_count": fac.get(d.id, 0)}
            for d in db.query(Department).order_by(Department.name).all()]


@router.post("/departments", status_code=201)
def create_department(body: DepartmentIn, user: User = Depends(require_university_admin),
                      db: Session = Depends(get_db)) -> Any:
    code = body.code.strip().upper()
    if db.query(Department).filter(Department.code == code).first():
        raise HTTPException(status_code=409, detail="A department with this code already exists.")
    d = Department(code=code, name=body.name, hod_name=body.hod_name, description=body.description)
    db.add(d)
    AuditRepository(db).log(action="DEPARTMENT_CREATED", user_id=user.id, resource_type="department",
                            resource_id=code, commit=False)
    db.commit()
    return {"id": d.id, "code": d.code, "name": d.name}


@router.patch("/departments/{department_id}")
def update_department(department_id: int, body: DepartmentIn, user: User = Depends(require_university_admin),
                      db: Session = Depends(get_db)) -> Any:
    d = db.query(Department).filter(Department.id == department_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Department not found")
    d.name, d.hod_name, d.description = body.name, body.hod_name, body.description
    db.commit()
    return {"id": d.id, "code": d.code, "name": d.name}


# ---------------------------------------------------------------- staffing
class MentorAssignIn(BaseModel):
    student_ids: List[int]
    mentor_id: int


@router.get("/mentors")
def mentors(user: User = Depends(require_university_admin), db: Session = Depends(get_db)) -> Any:
    mentee_counts = dict(db.query(Student.assigned_mentor_id, func.count(Student.id))
                         .group_by(Student.assigned_mentor_id).all())
    return [{"id": m.id, "user_id": m.user_id, "full_name": m.user.full_name, "email": m.user.email,
             "department": m.department.code if m.department else None, "designation": m.designation,
             "mentee_count": mentee_counts.get(m.id, 0), "max_mentees": m.max_mentees}
            for m in db.query(Mentor).all()]


@router.post("/mentor-assignments")
def assign_mentor(body: MentorAssignIn, user: User = Depends(require_university_admin),
                  db: Session = Depends(get_db)) -> Any:
    mentor = db.query(Mentor).filter(Mentor.id == body.mentor_id).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    students = db.query(Student).filter(Student.id.in_(body.student_ids)).all()
    if len(students) != len(set(body.student_ids)):
        raise HTTPException(status_code=404, detail="One or more students were not found.")
    for s in students:
        for a in db.query(StudentMentorAssignment).filter(StudentMentorAssignment.student_id == s.id,
                                                          StudentMentorAssignment.is_active.is_(True)).all():
            a.is_active = False
        s.assigned_mentor_id = mentor.id
        db.add(StudentMentorAssignment(student_id=s.id, mentor_id=mentor.id, academic_year="current",
                                       semester=s.current_semester, is_active=True))
    AuditRepository(db).log(action="MENTOR_ASSIGNED", user_id=user.id, resource_type="mentor",
                            resource_id=str(mentor.id), details={"students": body.student_ids}, commit=False)
    db.commit()
    return {"message": f"{len(students)} student(s) assigned to {mentor.user.full_name}."}


class StaffAccessIn(BaseModel):
    user_id: int
    student_id: int
    reason: str = Field(..., min_length=3, max_length=255)


@router.get("/staff-access")
def list_staff_access(user: User = Depends(require_university_admin), db: Session = Depends(get_db)) -> Any:
    rows = db.query(StaffStudentAccess).filter(StaffStudentAccess.university_id == user.university_id).all()
    staff = {u.id: u for u in db.query(User).filter(User.id.in_({r.user_id for r in rows})).all()} if rows else {}
    students = {s.id: s for s in db.query(Student).filter(Student.id.in_({r.student_id for r in rows})).all()} \
        if rows else {}
    out = []
    for r in rows:
        member, st = staff.get(r.user_id), students.get(r.student_id)
        out.append({"id": r.id, "staff": member.full_name if member else None,
                    "student": st.user.full_name if st else None, "student_id": r.student_id, "user_id": r.user_id,
                    "reason": r.reason, "created_at": r.created_at.isoformat()})
    return out


@router.post("/staff-access", status_code=201)
def grant_staff_access(body: StaffAccessIn, user: User = Depends(require_university_admin),
                       db: Session = Depends(get_db)) -> Any:
    staff = db.query(User).filter(User.id == body.user_id, User.role == "faculty").first()
    student = db.query(Student).filter(Student.id == body.student_id).first()
    if not staff or not student:
        raise HTTPException(status_code=404, detail="Faculty member or student not found in your university.")
    if db.query(StaffStudentAccess).filter(StaffStudentAccess.user_id == staff.id,
                                           StaffStudentAccess.student_id == student.id).first():
        raise HTTPException(status_code=409, detail="Access already granted.")
    db.add(StaffStudentAccess(university_id=user.university_id, user_id=staff.id, student_id=student.id,
                              reason=body.reason, granted_by_id=user.id))
    AuditRepository(db).log(action="STAFF_STUDENT_ACCESS_GRANTED", user_id=user.id, resource_type="student",
                            resource_id=str(student.id), details={"staff_user_id": staff.id}, commit=False)
    db.commit()
    return {"message": "Access granted"}


@router.delete("/staff-access/{access_id}")
def revoke_staff_access(access_id: int, user: User = Depends(require_university_admin), db: Session = Depends(get_db)) -> Any:
    r = db.query(StaffStudentAccess).filter(StaffStudentAccess.id == access_id,
                                            StaffStudentAccess.university_id == user.university_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(r)
    AuditRepository(db).log(action="STAFF_STUDENT_ACCESS_REVOKED", user_id=user.id, resource_type="student",
                            resource_id=str(r.student_id), commit=False)
    db.commit()
    return {"message": "Access revoked"}


# ---------------------------------------------------------------- account provisioning
class ProvisioningIn(BaseModel):
    method: str = Field(..., pattern="^(existing|rio_assisted)$")
    accounts_requested: int = Field(..., ge=1, le=500000)
    notes: Optional[str] = Field(None, max_length=2000)


@router.get("/provisioning")
def list_provisioning(user: User = Depends(require_university_admin), db: Session = Depends(get_db)) -> Any:
    rows = db.query(AccountProvisioningRequest).filter(
        AccountProvisioningRequest.university_id == user.university_id
    ).order_by(AccountProvisioningRequest.created_at.desc()).all()
    return [{"id": p.id, "method": p.method, "accounts_requested": p.accounts_requested,
             "accounts_completed": p.accounts_completed, "is_chargeable": p.is_chargeable,
             "estimated_cost": p.estimated_cost, "currency": p.currency, "status": p.status, "notes": p.notes,
             "created_at": p.created_at.isoformat()} for p in rows]


@router.post("/provisioning", status_code=201)
def request_provisioning(body: ProvisioningIn, user: User = Depends(require_university_admin),
                         db: Session = Depends(get_db)) -> Any:
    chargeable = body.method == "rio_assisted"
    est = estimate_email_service(body.accounts_requested) if chargeable else None
    p = AccountProvisioningRequest(
        university_id=user.university_id, method=body.method, accounts_requested=body.accounts_requested,
        is_chargeable=chargeable, estimated_cost=est["estimated_total_inr_per_year"] if est else None,
        status="estimated" if chargeable else "requested", notes=body.notes, requested_by_id=user.id)
    db.add(p)
    AuditRepository(db).log(action="PROVISIONING_REQUESTED", user_id=user.id, resource_type="provisioning",
                            details={"method": body.method, "accounts": body.accounts_requested}, commit=False)
    db.commit()
    return {"id": p.id, "status": p.status, "estimate": est}
