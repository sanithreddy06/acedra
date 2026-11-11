"""ACEDRA internal operations: enquiry workflow, tenant onboarding, employee assignment, data grants."""
import hashlib
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.tenancy import as_tenant
from app.models.platform import (
    ALL_MODULES,
    DEFAULT_ACADEMIC_STRUCTURE,
    AccountProvisioningRequest,
    EmployeeAssignment,
    EmployeeProfile,
    Enquiry,
    EnquiryActivity,
    EnquiryStatus,
    StudentDataAccessGrant,
    TenantStatus,
    University,
    UniversityDomain,
)
from app.models.user import PlatformRole, User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.services.email_service import EmailService
from app.services.invitation_service import InvitationService

DOMAIN_RE = re.compile(r"^(?=.{3,253}$)([a-z0-9](-?[a-z0-9])*\.)+[a-z]{2,63}$")
EMAIL_SERVICE_UNIT_COST_INR = 120.0  # documented estimate per account per year; configurable, not billed


def estimate_email_service(accounts: Optional[int]) -> Dict[str, Any]:
    n = max(0, int(accounts or 0))
    return {
        "accounts": n,
        "unit_cost_inr_per_year": EMAIL_SERVICE_UNIT_COST_INR,
        "estimated_total_inr_per_year": round(n * EMAIL_SERVICE_UNIT_COST_INR, 2),
        "note": "Indicative estimate for the optional ACEDRA-assisted email service. Not included in the standard "
                "service; final pricing is agreed in the service agreement. No mailboxes are created by this build.",
    }


def has_permission(user: User, perm: str) -> bool:
    if user.role == PlatformRole.SUPER_ADMIN.value:
        return True
    profile = getattr(user, "_employee_profile", None)
    return bool(profile and profile.is_active and perm in (profile.permissions or []))


class PlatformService:
    def __init__(self, db: Session, actor: Optional[User] = None):
        self.db = db
        self.actor = actor
        self.audit = AuditRepository(db)
        if actor is not None and actor.role == PlatformRole.EMPLOYEE.value:
            actor._employee_profile = db.query(EmployeeProfile).filter(EmployeeProfile.user_id == actor.id).first()

    # ------------------------------------------------------------ helpers
    def log(self, action: str, resource_type: str, resource_id: Any, details: Optional[dict] = None,
            university_id: Optional[int] = None):
        self.audit.log(action=action, user_id=self.actor.id if self.actor else None, resource_type=resource_type,
                       resource_id=str(resource_id), details=details or {}, university_id=university_id, commit=False)

    def require(self, perm: str):
        if not has_permission(self.actor, perm):
            raise HTTPException(status_code=403, detail="Your ACEDRA role does not include this permission.")

    def is_assigned(self, university_id: int) -> bool:
        return self.db.query(EmployeeAssignment).filter(
            EmployeeAssignment.university_id == university_id,
            EmployeeAssignment.employee_user_id == self.actor.id,
            EmployeeAssignment.is_active.is_(True)).first() is not None

    def require_tenant_config(self, university: University):
        self.require("tenant.configure")
        if self.actor.role != PlatformRole.SUPER_ADMIN.value and not self.is_assigned(university.id):
            raise HTTPException(status_code=403, detail="Only employees assigned to this university can configure it.")

    def get_university(self, university_id: int) -> University:
        uni = self.db.query(University).filter(University.id == university_id).first()
        if not uni:
            raise HTTPException(status_code=404, detail="University not found")
        return uni

    # ------------------------------------------------------------ enquiries
    def submit_enquiry(self, data: Dict[str, Any], client_ip: str) -> Enquiry:
        ref = f"ENQ-{utcnow():%y%m}-{secrets.token_hex(3).upper()}"
        if data.get("email_provisioning") == "rio_assisted":
            data["email_service_estimate"] = estimate_email_service(data.get("accounts_required"))
        enquiry = Enquiry(reference=ref, status=EnquiryStatus.NEW,
                          source_ip_hash=hashlib.sha256(client_ip.encode()).hexdigest(), **data)
        self.db.add(enquiry)
        self.db.flush()
        self.db.add(EnquiryActivity(enquiry_id=enquiry.id, kind="system", to_status=EnquiryStatus.NEW,
                                    body="Enquiry submitted through the public ACEDRA website."))
        # Notify the platform team (logged in development).
        for admin in self.db.query(User).filter(User.role == PlatformRole.SUPER_ADMIN.value, User.is_active.is_(True)).all():
            EmailService(self.db).send(
                admin.email, f"New university enquiry {ref}: {enquiry.university_name}",
                f"A new institutional enquiry was submitted.\n\nUniversity: {enquiry.university_name}\n"
                f"Contact: {enquiry.contact_name} ({enquiry.contact_designation})\nReference: {ref}\n",
                template="enquiry_internal")
        EmailService(self.db).send(
            enquiry.contact_email, f"We received your enquiry ({ref})",
            f"Dear {enquiry.contact_name},\n\nThank you for your interest in ACEDRA. Our team will review the "
            f"details for {enquiry.university_name} and contact you by your preferred method.\n\nReference: {ref}\n",
            template="enquiry_ack")
        return enquiry

    def change_enquiry_status(self, enquiry: Enquiry, to_status: str, note: Optional[str]) -> Enquiry:
        self.require("tenant.coordinate")
        if to_status not in EnquiryStatus.ALL:
            raise HTTPException(status_code=422, detail="Unknown status")
        if enquiry.status in EnquiryStatus.TERMINAL and to_status not in (EnquiryStatus.UNDER_REVIEW,):
            raise HTTPException(status_code=422, detail="Closed or rejected enquiries can only be reopened to Under Review.")
        if to_status in (EnquiryStatus.ONBOARDING, EnquiryStatus.ACTIVE):
            raise HTTPException(status_code=422, detail="Onboarding and Active are set automatically by tenant creation and activation.")
        if to_status == EnquiryStatus.APPROVED and not enquiry.agreement_reference:
            raise HTTPException(status_code=422, detail="Record the service agreement before approving.")
        frm = enquiry.status
        enquiry.status = to_status
        self.db.add(EnquiryActivity(enquiry_id=enquiry.id, kind="status_change", from_status=frm,
                                    to_status=to_status, body=note, author_id=self.actor.id))
        self.log("ENQUIRY_STATUS_CHANGED", "enquiry", enquiry.id, {"from": frm, "to": to_status})
        return enquiry

    def add_enquiry_activity(self, enquiry: Enquiry, kind: str, body: str, meeting_at: Optional[datetime]) -> EnquiryActivity:
        self.require("tenant.coordinate")
        if kind not in ("note", "meeting", "requirements", "contact"):
            raise HTTPException(status_code=422, detail="Invalid activity type")
        act = EnquiryActivity(enquiry_id=enquiry.id, kind=kind, body=body, meeting_at=meeting_at, author_id=self.actor.id)
        self.db.add(act)
        if kind == "requirements":
            enquiry.finalized_requirements = body
        if kind == "meeting" and enquiry.status in (EnquiryStatus.NEW, EnquiryStatus.UNDER_REVIEW, EnquiryStatus.CONTACTED):
            self.change_enquiry_status(enquiry, EnquiryStatus.MEETING_SCHEDULED, "Meeting recorded")
        return act

    def record_agreement(self, enquiry: Enquiry, reference: str, agreed_modules: List[str], notes: Optional[str]) -> Enquiry:
        self.require("tenant.coordinate")
        bad = [m for m in agreed_modules if m not in ALL_MODULES]
        if bad or not agreed_modules:
            raise HTTPException(status_code=422, detail="Select at least one valid module for the agreement.")
        enquiry.agreement_reference = reference
        enquiry.agreed_modules = agreed_modules
        enquiry.agreement_recorded_at = utcnow()
        if enquiry.status in EnquiryStatus.ORDER[:6]:
            frm = enquiry.status
            enquiry.status = EnquiryStatus.PROPOSAL
            self.db.add(EnquiryActivity(enquiry_id=enquiry.id, kind="status_change", from_status=frm,
                                        to_status=EnquiryStatus.PROPOSAL, author_id=self.actor.id))
        self.db.add(EnquiryActivity(enquiry_id=enquiry.id, kind="agreement", author_id=self.actor.id,
                                    body=f"Service agreement {reference} recorded. Modules: {', '.join(agreed_modules)}."
                                         + (f"\n{notes}" if notes else "")))
        self.log("AGREEMENT_RECORDED", "enquiry", enquiry.id, {"reference": reference})
        return enquiry

    # -------------------------------------------------------------- tenants
    def create_tenant_from_enquiry(self, enquiry: Enquiry, data: Dict[str, Any]) -> University:
        if self.actor.role != PlatformRole.SUPER_ADMIN.value:
            raise HTTPException(status_code=403, detail="Only a super administrator can create university tenants.")
        if enquiry.status != EnquiryStatus.APPROVED:
            raise HTTPException(status_code=422, detail="The enquiry must be Approved before a tenant is created.")
        if enquiry.university_id:
            raise HTTPException(status_code=409, detail="A tenant already exists for this enquiry.")
        uni = self.create_tenant({
            "name": data.get("name") or enquiry.university_name,
            "short_name": data["short_name"],
            "slug": data["slug"],
            "official_website": enquiry.official_website,
            "institution_type": enquiry.institution_type,
            "location": enquiry.location,
            "enabled_modules": enquiry.agreed_modules or enquiry.requested_modules or list(ALL_MODULES),
            "student_email_mode": enquiry.email_provisioning,
            "agreement_reference": enquiry.agreement_reference,
            "domains": data.get("domains") or [],
            "primary_employee_id": data["primary_employee_id"],
        }, enquiry=enquiry)
        enquiry.university_id = uni.id
        frm = enquiry.status
        enquiry.status = EnquiryStatus.ONBOARDING
        self.db.add(EnquiryActivity(enquiry_id=enquiry.id, kind="status_change", from_status=frm,
                                    to_status=EnquiryStatus.ONBOARDING, author_id=self.actor.id,
                                    body=f"University tenant '{uni.name}' created."))
        if enquiry.email_provisioning == "rio_assisted" and enquiry.accounts_required:
            est = estimate_email_service(enquiry.accounts_required)
            self.db.add(AccountProvisioningRequest(
                university_id=uni.id, method="rio_assisted", accounts_requested=enquiry.accounts_required,
                is_chargeable=True, estimated_cost=est["estimated_total_inr_per_year"], status="estimated",
                notes="Recorded from the institutional enquiry. Additional chargeable service.",
                requested_by_id=self.actor.id))
        return uni

    def create_tenant(self, data: Dict[str, Any], enquiry: Optional[Enquiry] = None) -> University:
        slug = data["slug"].strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,78}", slug):
            raise HTTPException(status_code=422, detail="Slug may contain lowercase letters, digits and hyphens.")
        if self.db.query(University).filter(University.slug == slug).first():
            raise HTTPException(status_code=409, detail="That workspace slug is already in use.")
        employee = self._get_employee(data["primary_employee_id"])
        modules = [m for m in data.get("enabled_modules") or ALL_MODULES if m in ALL_MODULES]
        uni = University(
            name=data["name"], short_name=data["short_name"], slug=slug,
            official_website=data.get("official_website"), institution_type=data.get("institution_type"),
            location=data.get("location"), status=TenantStatus.ONBOARDING,
            academic_structure=dict(DEFAULT_ACADEMIC_STRUCTURE, **(data.get("academic_structure") or {})),
            enabled_modules=modules,
            document_categories=data.get("document_categories") or [
                "Academic Regulations", "Attendance Policy", "Examination", "Placement", "Student Handbook"],
            student_email_mode=data.get("student_email_mode", "existing"),
            agreement_reference=data.get("agreement_reference"),
            is_synthetic=bool(data.get("is_synthetic")),
            brand_color=data.get("brand_color") or "#3F5A40",
            created_by_id=self.actor.id if self.actor else None,
            enquiry_id=enquiry.id if enquiry else None,
        )
        self.db.add(uni)
        self.db.flush()
        for i, d in enumerate(data.get("domains") or []):
            self.add_domain(uni, d, is_primary=(i == 0), check_perm=False)
        self._assign_primary(uni, employee)
        with as_tenant(self.db, uni.id):
            from app.services.recommendation_service import RecommendationService
            from app.services.risk_service import RiskService
            RiskService.seed_default_rules_if_needed(self.db)
            RecommendationService.seed_default_catalogue_if_needed(self.db)
        self.log("TENANT_CREATED", "university", uni.id, {"slug": slug}, university_id=uni.id)
        return uni

    def _get_employee(self, user_id: int) -> User:
        emp = self.db.query(User).filter(User.id == user_id,
                                         User.role.in_([PlatformRole.EMPLOYEE.value, PlatformRole.SUPER_ADMIN.value]),
                                         User.is_active.is_(True)).first()
        if not emp:
            raise HTTPException(status_code=422, detail="Primary contact must be an active ACEDRA employee.")
        return emp

    def _assign_primary(self, uni: University, employee: User, notes: Optional[str] = None):
        for a in self.db.query(EmployeeAssignment).filter(EmployeeAssignment.university_id == uni.id,
                                                          EmployeeAssignment.assignment_role == "primary",
                                                          EmployeeAssignment.is_active.is_(True)).all():
            a.is_active = False
            a.ended_at = utcnow()
        self.db.add(EmployeeAssignment(university_id=uni.id, employee_user_id=employee.id, assignment_role="primary",
                                       assigned_by_id=self.actor.id if self.actor else None, notes=notes))
        uni.primary_employee_id = employee.id

    def assign_primary_employee(self, uni: University, employee_id: int, notes: Optional[str]) -> University:
        if self.actor.role != PlatformRole.SUPER_ADMIN.value:
            raise HTTPException(status_code=403, detail="Only a super administrator can change the primary ACEDRA employee.")
        emp = self._get_employee(employee_id)
        self._assign_primary(uni, emp, notes)
        self.log("PRIMARY_EMPLOYEE_ASSIGNED", "university", uni.id, {"employee_id": emp.id}, university_id=uni.id)
        return uni

    def add_domain(self, uni: University, domain: str, purpose: str = "all", is_primary: bool = False,
                   check_perm: bool = True) -> UniversityDomain:
        if check_perm:
            self.require_tenant_config(uni)
        domain = domain.strip().lower().lstrip("@")
        if not DOMAIN_RE.match(domain):
            raise HTTPException(status_code=422, detail=f"'{domain}' is not a valid domain.")
        if purpose not in ("all", "staff", "student"):
            raise HTTPException(status_code=422, detail="Invalid domain purpose")
        if self.db.query(UniversityDomain).filter(UniversityDomain.domain == domain).first():
            raise HTTPException(status_code=409, detail="That domain is already registered to a university.")
        d = UniversityDomain(university_id=uni.id, domain=domain, purpose=purpose, is_primary=is_primary)
        self.db.add(d)
        self.log("DOMAIN_ADDED", "university", uni.id, {"domain": domain}, university_id=uni.id)
        return d

    def update_configuration(self, uni: University, data: Dict[str, Any]) -> University:
        self.require_tenant_config(uni)
        allowed = {"name", "short_name", "official_website", "institution_type", "location", "logo_url",
                   "brand_color", "tagline", "enabled_modules", "academic_structure", "document_categories",
                   "notification_settings", "enforce_email_domains", "student_email_mode", "workflow_settings"}
        for k, v in data.items():
            if k not in allowed or v is None:
                continue
            if k == "enabled_modules":
                v = [m for m in v if m in ALL_MODULES]
            if k == "academic_structure":
                v = dict(uni.academic_structure or {}, **v)
            setattr(uni, k, v)
        self.log("TENANT_CONFIGURED", "university", uni.id, {"fields": sorted(data.keys())}, university_id=uni.id)
        return uni

    def provision_initial_admin(self, uni: University, email: str, full_name: str, title: Optional[str]) -> User:
        self.require_tenant_config(uni)
        user, _, _ = InvitationService(self.db).create_user_with_invitation(
            email=email, full_name=full_name, role=UserRole.ADMIN.value, university=uni, invited_by=self.actor,
            title=title)
        self.log("TENANT_ADMIN_PROVISIONED", "university", uni.id, {"user_id": user.id}, university_id=uni.id)
        return user

    def readiness(self, uni: University) -> Dict[str, Any]:
        domains = self.db.query(UniversityDomain).filter(UniversityDomain.university_id == uni.id).count()
        admins = self.db.query(User).filter(User.university_id == uni.id, User.role == UserRole.ADMIN.value).count()
        checks = [
            {"key": "primary_employee", "label": "Dedicated ACEDRA employee assigned", "done": uni.primary_employee_id is not None},
            {"key": "domains", "label": "Institutional email domain configured", "done": domains > 0},
            {"key": "modules", "label": "At least one module enabled", "done": bool(uni.enabled_modules)},
            {"key": "admin", "label": "Initial university administrator provisioned", "done": admins > 0},
        ]
        return {"checks": checks, "ready": all(c["done"] for c in checks)}

    def set_status(self, uni: University, status: str, reason: Optional[str]) -> University:
        if self.actor.role != PlatformRole.SUPER_ADMIN.value:
            raise HTTPException(status_code=403, detail="Only a super administrator can activate or deactivate workspaces.")
        if status not in TenantStatus.ALL:
            raise HTTPException(status_code=422, detail="Invalid status")
        if status == TenantStatus.ACTIVE and not self.readiness(uni)["ready"]:
            raise HTTPException(status_code=422, detail="Complete the onboarding checklist before activation.")
        prev = uni.status
        uni.status = status
        if status == TenantStatus.ACTIVE and not uni.activated_at:
            uni.activated_at = utcnow()
        if uni.enquiry_id and status == TenantStatus.ACTIVE:
            enq = self.db.query(Enquiry).filter(Enquiry.id == uni.enquiry_id).first()
            if enq and enq.status != EnquiryStatus.ACTIVE:
                self.db.add(EnquiryActivity(enquiry_id=enq.id, kind="status_change", from_status=enq.status,
                                            to_status=EnquiryStatus.ACTIVE, author_id=self.actor.id,
                                            body="University workspace activated."))
                enq.status = EnquiryStatus.ACTIVE
        self.log("TENANT_STATUS_CHANGED", "university", uni.id, {"from": prev, "to": status, "reason": reason},
                 university_id=uni.id)
        return uni

    # --------------------------------------------------- student-data grants
    def create_grant(self, uni: University, employee_id: int, reason: str, authorised_by: str, days: int) -> StudentDataAccessGrant:
        if self.actor.role != PlatformRole.SUPER_ADMIN.value:
            raise HTTPException(status_code=403, detail="Only a super administrator can record student-data access grants.")
        if not 1 <= days <= 30:
            raise HTTPException(status_code=422, detail="Grants may last between 1 and 30 days.")
        emp = self._get_employee(employee_id)
        g = StudentDataAccessGrant(university_id=uni.id, employee_user_id=emp.id, reason=reason,
                                   university_authorised_by=authorised_by, approved_by_id=self.actor.id,
                                   starts_at=utcnow(), expires_at=utcnow() + timedelta(days=days))
        self.db.add(g)
        self.db.flush()
        self.log("STUDENT_DATA_GRANT_CREATED", "student_data_grant", g.id,
                 {"employee_id": emp.id, "days": days, "authorised_by": authorised_by}, university_id=uni.id)
        return g

    def revoke_grant(self, grant: StudentDataAccessGrant) -> StudentDataAccessGrant:
        if self.actor.role != PlatformRole.SUPER_ADMIN.value:
            raise HTTPException(status_code=403, detail="Only a super administrator can revoke grants.")
        grant.revoked_at = utcnow()
        grant.revoked_by_id = self.actor.id
        self.log("STUDENT_DATA_GRANT_REVOKED", "student_data_grant", grant.id, university_id=grant.university_id)
        return grant

    def tenant_counts(self, uni_id: int) -> Dict[str, int]:
        rows = self.db.query(User.role, func.count(User.id)).filter(User.university_id == uni_id).group_by(User.role).all()
        return {r: c for r, c in rows}
