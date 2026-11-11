"""ACEDRA internal platform administration. Never reachable by university accounts (404)."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin, require_platform_user
from app.core.access import active_data_grant
from app.core.clock import utcnow
from app.core.config import settings
from app.core.database import get_db
from app.core.tenancy import unscoped
from app.models import AuditLog, Department, Student
from app.models.legal import LEGAL_DOCUMENT_TYPES, ContactMessage, LegalDocument
from app.models.platform import (
    ALL_MODULES,
    AccountProvisioningRequest,
    EmailMessage,
    EmployeeAssignment,
    EmployeeProfile,
    Enquiry,
    EnquiryStatus,
    ProvisioningStatus,
    StudentDataAccessGrant,
    TenantStatus,
    University,
    UniversityDomain,
)
from app.models.user import PlatformRole, User
from app.schemas.legal import (
    ContactMessageOut,
    ContactStatusIn,
    LegalApproval,
    LegalDocumentAdminOut,
    LegalDraftCreate,
    LegalDraftUpdate,
    LegalPublish,
)
from app.services import legal_service
from app.services.invitation_service import InvitationService
from app.services.legal_service import LegalDocumentAdmin
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platform", tags=["Platform Administration"], dependencies=[Depends(require_platform_user)])


# ------------------------------------------------------------------ serializers
def _dt(v):
    return v.isoformat() if v else None


def _user_brief(u: Optional[User]) -> Optional[dict]:
    if not u:
        return None
    return {"id": u.id, "full_name": u.full_name, "email": u.email, "phone": u.phone, "title": u.title, "role": u.role}


def _enquiry_out(e: Enquiry, full: bool = False) -> dict:
    out = {
        "id": e.id, "reference": e.reference, "status": e.status, "status_label": EnquiryStatus.LABELS.get(e.status),
        "university_name": e.university_name, "institution_type": e.institution_type, "location": e.location,
        "student_population": e.student_population, "contact_name": e.contact_name,
        "contact_designation": e.contact_designation, "contact_email": e.contact_email,
        "requested_modules": e.requested_modules or [], "email_provisioning": e.email_provisioning,
        "owner": _user_brief(e.owner), "university_id": e.university_id,
        "created_at": _dt(e.created_at), "updated_at": _dt(e.updated_at),
    }
    if full:
        out.update({
            "official_website": e.official_website, "department_count": e.department_count,
            "campus_count": e.campus_count, "contact_phone": e.contact_phone,
            "preferred_contact_method": e.preferred_contact_method, "existing_sis": e.existing_sis,
            "existing_academic_systems": e.existing_academic_systems, "has_student_emails": e.has_student_emails,
            "accounts_required": e.accounts_required, "institutional_requirements": e.institutional_requirements,
            "expected_outcomes": e.expected_outcomes, "additional_information": e.additional_information,
            "finalized_requirements": e.finalized_requirements, "agreement_reference": e.agreement_reference,
            "agreement_recorded_at": _dt(e.agreement_recorded_at), "agreed_modules": e.agreed_modules or [],
            "email_service_estimate": e.email_service_estimate,
            "activities": [{
                "id": a.id, "kind": a.kind, "from_status": a.from_status, "to_status": a.to_status, "body": a.body,
                "meeting_at": _dt(a.meeting_at), "author": _user_brief(a.author), "created_at": _dt(a.created_at),
            } for a in e.activities],
        })
    return out


def _university_out(db: Session, u: University, full: bool = False) -> dict:
    out = {
        "id": u.id, "name": u.name, "short_name": u.short_name, "slug": u.slug, "status": u.status,
        "location": u.location, "institution_type": u.institution_type, "is_synthetic": u.is_synthetic,
        "brand_color": u.brand_color, "logo_url": u.logo_url, "enabled_modules": u.enabled_modules or [],
        "primary_employee": _user_brief(u.primary_employee), "activated_at": _dt(u.activated_at),
        "created_at": _dt(u.created_at), "domains": [{"id": d.id, "domain": d.domain, "purpose": d.purpose,
                                                      "is_primary": d.is_primary} for d in u.domains],
    }
    if full:
        svc = PlatformService(db)
        out.update({
            "official_website": u.official_website, "tagline": u.tagline,
            "academic_structure": u.academic_structure, "document_categories": u.document_categories,
            "notification_settings": u.notification_settings, "enforce_email_domains": u.enforce_email_domains,
            "student_email_mode": u.student_email_mode, "agreement_reference": u.agreement_reference,
            "enquiry_id": u.enquiry_id, "user_counts": svc.tenant_counts(u.id),
            "readiness": svc.readiness(u),
            "assignments": [{
                "id": a.id, "employee": _user_brief(a.employee), "assignment_role": a.assignment_role,
                "is_active": a.is_active, "started_at": _dt(a.started_at), "ended_at": _dt(a.ended_at), "notes": a.notes,
            } for a in sorted(u.assignments, key=lambda a: a.started_at, reverse=True)],
            "admins": [_user_brief(x) | {"is_verified": x.is_verified, "is_active": x.is_active}
                       for x in db.query(User).filter(User.university_id == u.id, User.role == "admin").all()],
        })
    return out


# ------------------------------------------------------------------ overview
@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(require_platform_user)) -> Any:
    enquiries = dict(db.query(Enquiry.status, func.count(Enquiry.id)).group_by(Enquiry.status).all())
    tenants = dict(db.query(University.status, func.count(University.id)).group_by(University.status).all())
    my = db.query(EmployeeAssignment).filter(EmployeeAssignment.employee_user_id == user.id,
                                             EmployeeAssignment.is_active.is_(True)).all()
    recent = db.query(Enquiry).order_by(Enquiry.created_at.desc()).limit(6).all()
    pending_prov = db.query(AccountProvisioningRequest).filter(
        AccountProvisioningRequest.status.in_(["requested", "estimated", "approved", "in_progress"])).count()
    return {
        "enquiries_by_status": enquiries,
        "open_enquiries": sum(v for k, v in enquiries.items() if k not in ("active", "rejected", "closed")),
        "tenants_by_status": tenants,
        "my_universities": [_university_out(db, a.university) for a in my],
        "recent_enquiries": [_enquiry_out(e) for e in recent],
        "pending_provisioning": pending_prov,
        "email_provider": settings.EMAIL_PROVIDER,
    }


# ------------------------------------------------------------------ enquiries
class EnquiryStatusIn(BaseModel):
    status: str
    note: Optional[str] = Field(None, max_length=4000)


class EnquiryActivityIn(BaseModel):
    kind: str
    body: str = Field(..., min_length=2, max_length=8000)
    meeting_at: Optional[datetime] = None


class AgreementIn(BaseModel):
    reference: str = Field(..., min_length=3, max_length=120)
    agreed_modules: List[str]
    notes: Optional[str] = Field(None, max_length=4000)


class OwnerIn(BaseModel):
    owner_id: Optional[int] = None


class CreateTenantFromEnquiry(BaseModel):
    name: Optional[str] = None
    short_name: str = Field(..., min_length=2, max_length=50)
    slug: str = Field(..., min_length=2, max_length=80)
    domains: List[str] = []
    primary_employee_id: int


def _get_enquiry(db: Session, enquiry_id: int) -> Enquiry:
    e = db.query(Enquiry).filter(Enquiry.id == enquiry_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Enquiry not found")
    return e


@router.get("/enquiries")
def list_enquiries(status: Optional[str] = None, search: Optional[str] = None,
                   skip: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100),
                   db: Session = Depends(get_db)) -> Any:
    q = db.query(Enquiry)
    if status == "open":
        q = q.filter(Enquiry.status.notin_(["active", "rejected", "closed"]))
    elif status:
        q = q.filter(Enquiry.status == status)
    if search:
        t = f"%{search.lower()}%"
        q = q.filter(or_(func.lower(Enquiry.university_name).like(t), func.lower(Enquiry.reference).like(t),
                         func.lower(Enquiry.contact_name).like(t)))
    total = q.count()
    items = q.order_by(Enquiry.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [_enquiry_out(e) for e in items], "total": total, "statuses": EnquiryStatus.LABELS}


@router.get("/enquiries/{enquiry_id}")
def get_enquiry(enquiry_id: int, db: Session = Depends(get_db)) -> Any:
    return _enquiry_out(_get_enquiry(db, enquiry_id), full=True)


@router.post("/enquiries/{enquiry_id}/status")
def set_enquiry_status(enquiry_id: int, body: EnquiryStatusIn, db: Session = Depends(get_db),
                       user: User = Depends(require_platform_user)) -> Any:
    e = PlatformService(db, user).change_enquiry_status(_get_enquiry(db, enquiry_id), body.status, body.note)
    db.commit()
    return _enquiry_out(e, full=True)


@router.post("/enquiries/{enquiry_id}/activities", status_code=201)
def add_activity(enquiry_id: int, body: EnquiryActivityIn, db: Session = Depends(get_db),
                 user: User = Depends(require_platform_user)) -> Any:
    e = _get_enquiry(db, enquiry_id)
    PlatformService(db, user).add_enquiry_activity(e, body.kind, body.body, body.meeting_at)
    db.commit()
    db.refresh(e)
    return _enquiry_out(e, full=True)


@router.post("/enquiries/{enquiry_id}/owner")
def set_owner(enquiry_id: int, body: OwnerIn, db: Session = Depends(get_db),
              user: User = Depends(require_platform_user)) -> Any:
    e = _get_enquiry(db, enquiry_id)
    svc = PlatformService(db, user)
    svc.require("tenant.coordinate")
    if body.owner_id:
        svc._get_employee(body.owner_id)
    e.owner_id = body.owner_id
    svc.log("ENQUIRY_OWNER_SET", "enquiry", e.id, {"owner_id": body.owner_id})
    db.commit()
    return _enquiry_out(e, full=True)


@router.post("/enquiries/{enquiry_id}/agreement")
def record_agreement(enquiry_id: int, body: AgreementIn, db: Session = Depends(get_db),
                     user: User = Depends(require_platform_user)) -> Any:
    e = PlatformService(db, user).record_agreement(_get_enquiry(db, enquiry_id), body.reference,
                                                   body.agreed_modules, body.notes)
    db.commit()
    return _enquiry_out(e, full=True)


@router.post("/enquiries/{enquiry_id}/create-tenant", status_code=201)
def create_tenant_from_enquiry(enquiry_id: int, body: CreateTenantFromEnquiry, db: Session = Depends(get_db),
                               user: User = Depends(require_platform_admin)) -> Any:
    uni = PlatformService(db, user).create_tenant_from_enquiry(_get_enquiry(db, enquiry_id), body.model_dump())
    db.commit()
    return _university_out(db, uni, full=True)


# ------------------------------------------------------------------ universities
class DomainIn(BaseModel):
    domain: str = Field(..., max_length=255)
    purpose: str = "all"
    is_primary: bool = False


class TenantConfigIn(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    official_website: Optional[str] = Field(None, max_length=255)
    institution_type: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    brand_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    tagline: Optional[str] = Field(None, max_length=255)
    enabled_modules: Optional[List[str]] = None
    academic_structure: Optional[Dict[str, Any]] = None
    document_categories: Optional[List[str]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    enforce_email_domains: Optional[bool] = None
    student_email_mode: Optional[str] = Field(None, pattern="^(existing|rio_assisted)$")


class AssignEmployeeIn(BaseModel):
    employee_id: int
    notes: Optional[str] = Field(None, max_length=1000)


class AdminIn(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    title: Optional[str] = Field(None, max_length=150)


class StatusIn(BaseModel):
    status: str
    reason: Optional[str] = Field(None, max_length=1000)


class GrantIn(BaseModel):
    employee_id: int
    reason: str = Field(..., min_length=10, max_length=2000)
    university_authorised_by: str = Field(..., min_length=3, max_length=255)
    days: int = 7


class ProvisioningIn(BaseModel):
    status: Optional[str] = None
    accounts_completed: Optional[int] = Field(None, ge=0)
    estimated_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=2000)


@router.get("/universities")
def list_universities(status: Optional[str] = None, db: Session = Depends(get_db)) -> Any:
    q = db.query(University)
    if status:
        q = q.filter(University.status == status)
    return [_university_out(db, u) for u in q.order_by(University.name).all()]


@router.get("/universities/{university_id}")
def get_university(university_id: int, db: Session = Depends(get_db)) -> Any:
    return _university_out(db, PlatformService(db).get_university(university_id), full=True)


@router.patch("/universities/{university_id}")
def configure_university(university_id: int, body: TenantConfigIn, db: Session = Depends(get_db),
                         user: User = Depends(require_platform_user)) -> Any:
    svc = PlatformService(db, user)
    uni = svc.update_configuration(svc.get_university(university_id), body.model_dump(exclude_unset=True))
    db.commit()
    return _university_out(db, uni, full=True)


@router.post("/universities/{university_id}/domains", status_code=201)
def add_domain(university_id: int, body: DomainIn, db: Session = Depends(get_db),
               user: User = Depends(require_platform_user)) -> Any:
    svc = PlatformService(db, user)
    uni = svc.get_university(university_id)
    svc.add_domain(uni, body.domain, body.purpose, body.is_primary)
    db.commit()
    db.refresh(uni)
    return _university_out(db, uni, full=True)


@router.delete("/universities/{university_id}/domains/{domain_id}")
def remove_domain(university_id: int, domain_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_platform_user)) -> Any:
    svc = PlatformService(db, user)
    uni = svc.get_university(university_id)
    svc.require_tenant_config(uni)
    d = db.query(UniversityDomain).filter(UniversityDomain.id == domain_id,
                                          UniversityDomain.university_id == uni.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Domain not found")
    db.delete(d)
    svc.log("DOMAIN_REMOVED", "university", uni.id, {"domain": d.domain}, university_id=uni.id)
    db.commit()
    db.refresh(uni)
    return _university_out(db, uni, full=True)


@router.post("/universities/{university_id}/primary-employee")
def assign_primary(university_id: int, body: AssignEmployeeIn, db: Session = Depends(get_db),
                   user: User = Depends(require_platform_admin)) -> Any:
    svc = PlatformService(db, user)
    uni = svc.assign_primary_employee(svc.get_university(university_id), body.employee_id, body.notes)
    db.commit()
    db.refresh(uni)
    return _university_out(db, uni, full=True)


@router.post("/universities/{university_id}/admins", status_code=201)
def provision_admin(university_id: int, body: AdminIn, db: Session = Depends(get_db),
                    user: User = Depends(require_platform_user)) -> Any:
    svc = PlatformService(db, user)
    uni = svc.get_university(university_id)
    svc.provision_initial_admin(uni, body.email, body.full_name, body.title)
    db.commit()
    return _university_out(db, uni, full=True)


@router.post("/universities/{university_id}/status")
def set_university_status(university_id: int, body: StatusIn, db: Session = Depends(get_db),
                          user: User = Depends(require_platform_admin)) -> Any:
    svc = PlatformService(db, user)
    uni = svc.set_status(svc.get_university(university_id), body.status, body.reason)
    db.commit()
    return _university_out(db, uni, full=True)


@router.get("/universities/{university_id}/grants")
def list_grants(university_id: int, db: Session = Depends(get_db)) -> Any:
    grants = db.query(StudentDataAccessGrant).filter(StudentDataAccessGrant.university_id == university_id) \
        .order_by(StudentDataAccessGrant.created_at.desc()).all()
    now = utcnow()
    return [{
        "id": g.id, "employee": _user_brief(g.employee), "scope": g.scope, "reason": g.reason,
        "university_authorised_by": g.university_authorised_by, "starts_at": _dt(g.starts_at),
        "expires_at": _dt(g.expires_at), "revoked_at": _dt(g.revoked_at),
        "is_active": g.revoked_at is None and g.starts_at <= now < g.expires_at,
    } for g in grants]


@router.post("/universities/{university_id}/grants", status_code=201)
def create_grant(university_id: int, body: GrantIn, db: Session = Depends(get_db),
                 user: User = Depends(require_platform_admin)) -> Any:
    svc = PlatformService(db, user)
    g = svc.create_grant(svc.get_university(university_id), body.employee_id, body.reason,
                         body.university_authorised_by, body.days)
    db.commit()
    return {"id": g.id}


@router.post("/grants/{grant_id}/revoke")
def revoke_grant(grant_id: int, db: Session = Depends(get_db), user: User = Depends(require_platform_admin)) -> Any:
    g = db.query(StudentDataAccessGrant).filter(StudentDataAccessGrant.id == grant_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grant not found")
    PlatformService(db, user).revoke_grant(g)
    db.commit()
    return {"message": "Grant revoked"}


@router.get("/universities/{university_id}/student-directory")
def granted_student_directory(university_id: int, db: Session = Depends(get_db),
                              user: User = Depends(require_platform_user)) -> Any:
    """Read-only, minimal student directory — only with an active, explicit grant. Every read is audited."""
    grant = active_data_grant(db, user, university_id)
    if not grant:
        raise HTTPException(status_code=403, detail="No active student-data access grant for this university. "
                                                    "Configuration access does not include student records.")
    with unscoped(db):
        rows = db.query(Student, User, Department).join(User, User.id == Student.user_id) \
            .join(Department, Department.id == Student.department_id) \
            .filter(Student.university_id == university_id).order_by(User.full_name).limit(500).all()
        data = [{"id": s.id, "full_name": u.full_name, "usn": s.usn, "department": d.code,
                 "semester": s.current_semester, "status": s.status} for s, u, d in rows]
    PlatformService(db, user).log("STUDENT_DATA_ACCESSED", "student_data_grant", grant.id,
                                  {"records": len(data)}, university_id=university_id)
    db.commit()
    return {"grant_expires_at": _dt(grant.expires_at), "students": data}


@router.get("/universities/{university_id}/provisioning")
def list_provisioning(university_id: int, db: Session = Depends(get_db)) -> Any:
    rows = db.query(AccountProvisioningRequest).filter(AccountProvisioningRequest.university_id == university_id) \
        .order_by(AccountProvisioningRequest.created_at.desc()).all()
    return [_prov_out(p) for p in rows]


def _prov_out(p: AccountProvisioningRequest) -> dict:
    return {"id": p.id, "university_id": p.university_id, "method": p.method,
            "accounts_requested": p.accounts_requested, "accounts_completed": p.accounts_completed,
            "is_chargeable": p.is_chargeable, "estimated_cost": p.estimated_cost, "currency": p.currency,
            "status": p.status, "notes": p.notes, "created_at": _dt(p.created_at)}


@router.patch("/provisioning/{request_id}")
def update_provisioning(request_id: int, body: ProvisioningIn, db: Session = Depends(get_db),
                        user: User = Depends(require_platform_user)) -> Any:
    p = db.query(AccountProvisioningRequest).filter(AccountProvisioningRequest.id == request_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Request not found")
    svc = PlatformService(db, user)
    svc.require("tenant.coordinate")
    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in ProvisioningStatus.ALL:
        raise HTTPException(status_code=422, detail="Invalid status")
    for k, v in data.items():
        setattr(p, k, v)
    svc.log("PROVISIONING_UPDATED", "provisioning", p.id, data, university_id=p.university_id)
    db.commit()
    return _prov_out(p)


# ------------------------------------------------------------------ employees
class EmployeeIn(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    title: Optional[str] = Field(None, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = PlatformRole.EMPLOYEE.value
    permissions: List[str] = ["tenant.configure", "tenant.coordinate"]


class EmployeeUpdate(BaseModel):
    title: Optional[str] = None
    phone: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


VALID_PERMS = {"tenant.configure", "tenant.coordinate"}


def _employee_out(db: Session, u: User) -> dict:
    p = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == u.id).first()
    assigns = db.query(EmployeeAssignment).filter(EmployeeAssignment.employee_user_id == u.id,
                                                  EmployeeAssignment.is_active.is_(True)).all()
    return {**_user_brief(u), "is_active": u.is_active, "is_verified": u.is_verified,
            "employee_code": p.employee_code if p else None,
            "permissions": (p.permissions if p else []) if u.role == PlatformRole.EMPLOYEE.value else ["all"],
            "assignments": [{"university_id": a.university_id, "university": a.university.short_name,
                             "assignment_role": a.assignment_role} for a in assigns]}


@router.get("/employees")
def list_employees(db: Session = Depends(get_db)) -> Any:
    users = db.query(User).filter(User.role.in_([PlatformRole.EMPLOYEE.value, PlatformRole.SUPER_ADMIN.value])) \
        .order_by(User.full_name).all()
    return [_employee_out(db, u) for u in users]


@router.post("/employees", status_code=201)
def create_employee(body: EmployeeIn, db: Session = Depends(get_db), user: User = Depends(require_platform_admin)) -> Any:
    if body.role not in (PlatformRole.EMPLOYEE.value, PlatformRole.SUPER_ADMIN.value):
        raise HTTPException(status_code=422, detail="Invalid platform role")
    perms = [p for p in body.permissions if p in VALID_PERMS]
    new_user, _, _ = InvitationService(db).create_user_with_invitation(
        email=body.email, full_name=body.full_name, role=body.role, university=None, invited_by=user,
        title=body.title, phone=body.phone)
    count = db.query(EmployeeProfile).count() + 1
    db.add(EmployeeProfile(user_id=new_user.id, employee_code=f"ACD-{count:04d}", title=body.title,
                           phone=body.phone, permissions=perms))
    PlatformService(db, user).log("EMPLOYEE_INVITED", "user", new_user.id, {"role": body.role})
    db.commit()
    return _employee_out(db, new_user)


@router.patch("/employees/{user_id}")
def update_employee(user_id: int, body: EmployeeUpdate, db: Session = Depends(get_db),
                    user: User = Depends(require_platform_admin)) -> Any:
    emp = db.query(User).filter(User.id == user_id, User.role.in_(
        [PlatformRole.EMPLOYEE.value, PlatformRole.SUPER_ADMIN.value])).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    data = body.model_dump(exclude_unset=True)
    p = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == emp.id).first()
    if "permissions" in data and p:
        p.permissions = [x for x in data["permissions"] if x in VALID_PERMS]
    if "is_active" in data:
        if emp.id == user.id:
            raise HTTPException(status_code=422, detail="You cannot deactivate yourself.")
        emp.is_active = data["is_active"]
        emp.token_version = (emp.token_version or 0) + 1
    for k in ("title", "phone"):
        if k in data:
            setattr(emp, k, data[k])
            if p:
                setattr(p, k, data[k])
    PlatformService(db, user).log("EMPLOYEE_UPDATED", "user", emp.id, {"fields": sorted(data.keys())})
    db.commit()
    return _employee_out(db, emp)


# ------------------------------------------------------------------ audit & email
@router.get("/audit-logs")
def platform_audit(university_id: Optional[int] = None, action: Optional[str] = None,
                   skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                   db: Session = Depends(get_db)) -> Any:
    q = db.query(AuditLog)
    if university_id:
        q = q.filter(AuditLog.university_id == university_id)
    if action:
        q = q.filter(AuditLog.action == action)
    total = q.count()
    rows = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    unis = {u.id: u.short_name for u in db.query(University).all()}
    return {"total": total, "items": [{
        "id": a.id, "action": a.action, "resource_type": a.resource_type, "resource_id": a.resource_id,
        "university": unis.get(a.university_id), "actor": a.user.full_name if a.user else None,
        "ip_address": a.ip_address, "details": a.details, "created_at": _dt(a.created_at),
    } for a in rows]}


@router.get("/email-outbox")
def email_outbox(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db),
                 user: User = Depends(require_platform_admin)) -> Any:
    """Development preview of logged emails. Bodies (which contain single-use links) are hidden in production."""
    rows = db.query(EmailMessage).order_by(EmailMessage.created_at.desc()).limit(limit).all()
    show_body = not settings.is_production
    return {"provider": settings.EMAIL_PROVIDER, "bodies_visible": show_body, "items": [{
        "id": m.id, "to_email": m.to_email, "subject": m.subject, "template": m.template, "status": m.status,
        "provider": m.provider, "body_text": m.body_text if show_body else None, "created_at": _dt(m.created_at),
    } for m in rows]}


@router.get("/meta")
def platform_meta(user: User = Depends(require_platform_user)) -> Any:
    return {"modules": ALL_MODULES, "enquiry_statuses": EnquiryStatus.LABELS, "tenant_statuses": TenantStatus.ALL,
            "provisioning_statuses": ProvisioningStatus.ALL, "role": user.role}


# ------------------------------------------------------------------ legal documents (global ACEDRA terms)
def _legal_out(doc: LegalDocument, current_ids: set) -> LegalDocumentAdminOut:
    out = LegalDocumentAdminOut.model_validate(doc)
    out.approved_by_name = doc.approved_by.full_name if doc.approved_by else None
    out.published_by_name = doc.published_by.full_name if doc.published_by else None
    out.is_current = doc.id in current_ids
    return out


@router.get("/legal-documents", response_model=List[LegalDocumentAdminOut])
def list_legal_documents(db: Session = Depends(get_db)) -> Any:
    """Every version of every legal document, newest first. Visible to the whole ACEDRA team."""
    current = {legal_service.current_document(db, t).id for t in LEGAL_DOCUMENT_TYPES}
    docs = db.query(LegalDocument).order_by(LegalDocument.doc_type, LegalDocument.created_at.desc()).all()
    return [_legal_out(d, current) for d in docs]


@router.post("/legal-documents", response_model=LegalDocumentAdminOut, status_code=201)
def create_legal_draft(body: LegalDraftCreate, db: Session = Depends(get_db),
                       user: User = Depends(require_platform_admin)) -> Any:
    doc = LegalDocumentAdmin(db, user).create_draft(body.doc_type, body.version, body.title, body.body,
                                                    body.change_summary)
    return _legal_out(doc, set())


@router.patch("/legal-documents/{doc_id}", response_model=LegalDocumentAdminOut)
def update_legal_draft(doc_id: int, body: LegalDraftUpdate, db: Session = Depends(get_db),
                       user: User = Depends(require_platform_admin)) -> Any:
    doc = LegalDocumentAdmin(db, user).update_draft(doc_id, body.model_dump(exclude_unset=True))
    return _legal_out(doc, set())


@router.post("/legal-documents/{doc_id}/approve", response_model=LegalDocumentAdminOut)
def approve_legal_version(doc_id: int, body: LegalApproval, db: Session = Depends(get_db),
                          user: User = Depends(require_platform_admin)) -> Any:
    return _legal_out(LegalDocumentAdmin(db, user).approve(doc_id, body.approval_note), set())


@router.post("/legal-documents/{doc_id}/reopen", response_model=LegalDocumentAdminOut)
def reopen_legal_version(doc_id: int, db: Session = Depends(get_db),
                         user: User = Depends(require_platform_admin)) -> Any:
    return _legal_out(LegalDocumentAdmin(db, user).return_to_draft(doc_id), set())


@router.post("/legal-documents/{doc_id}/publish", response_model=LegalDocumentAdminOut)
def publish_legal_version(doc_id: int, body: LegalPublish, db: Session = Depends(get_db),
                          user: User = Depends(require_platform_admin)) -> Any:
    doc = LegalDocumentAdmin(db, user).publish(doc_id, body.effective_date)
    current = {legal_service.current_document(db, t).id for t in LEGAL_DOCUMENT_TYPES}
    return _legal_out(doc, current)


# ------------------------------------------------------------------ contact messages
@router.get("/contact-messages", response_model=List[ContactMessageOut])
def list_contact_messages(status: Optional[str] = None, db: Session = Depends(get_db)) -> Any:
    q = db.query(ContactMessage)
    if status:
        q = q.filter(ContactMessage.status == status)
    return q.order_by(ContactMessage.created_at.desc()).limit(200).all()


@router.patch("/contact-messages/{message_id}", response_model=ContactMessageOut)
def update_contact_message(message_id: int, body: ContactStatusIn, db: Session = Depends(get_db),
                           user: User = Depends(require_platform_user)) -> Any:
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.status, msg.handled_by_id = body.status, user.id
    PlatformService(db, user).log("CONTACT_MESSAGE_UPDATED", "contact_message", msg.id, {"status": body.status})
    db.commit()
    db.refresh(msg)
    return msg

