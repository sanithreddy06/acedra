"""Authentication: sign-in, JWT issue/refresh, logout, invitation acceptance and password reset.

Tokens embed the user's ``token_version``; bumping it (logout, password change/reset) revokes every
outstanding token. Invitation and reset tokens are stored hashed and are single use.
"""
from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_url_token,
    get_password_hash,
    hash_token,
    validate_password_strength,
    verify_password,
)
from app.core.tenancy import TenantScope, set_session_scope
from app.models.platform import AuthToken, Invitation, TenantStatus, University
from app.models.user import PLATFORM_ROLES, User, UserRole
from app.repositories.audit_repo import AuditRepository
from app.services.email_service import EmailService

GENERIC_LOGIN_ERROR = "Incorrect email or password"


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        set_session_scope(db, TenantScope(bypass=True))  # auth lookups span tenants by email
        self.audit_repo = AuditRepository(db)

    # ------------------------------------------------------------------ login
    def _get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.strip().lower()).first()

    def authenticate_user(self, email: str, password: str, ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None) -> User:
        user = self._get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            self.audit_repo.log(
                action="LOGIN_FAILED", user_id=user.id if user else None, resource_type="auth",
                ip_address=ip_address, user_agent=(user_agent or "")[:250],
                university_id=user.university_id if user else None,
                details={"reason": "invalid_credentials"},
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_LOGIN_ERROR,
                                headers={"WWW-Authenticate": "Bearer"})
        if not user.is_verified:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Please accept your invitation and verify your email before signing in.")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="This account is disabled. Contact your administrator.")
        if user.role not in PLATFORM_ROLES:
            uni = self.db.query(University).filter(University.id == user.university_id).first()
            allowed = {TenantStatus.ACTIVE} | ({TenantStatus.ONBOARDING} if user.role == UserRole.ADMIN.value else set())
            if not uni or uni.status not in allowed:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="Your university workspace is not active yet.")
        user.last_login_at = utcnow()
        self.audit_repo.log(
            action="LOGIN_SUCCESS", user_id=user.id, resource_type="auth", resource_id=str(user.id),
            ip_address=ip_address, user_agent=(user_agent or "")[:250], university_id=user.university_id,
            details={"role": user.role},
        )
        return user

    def build_user_info(self, user: User) -> Dict[str, Any]:
        info: Dict[str, Any] = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "title": user.title,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else None,
            "avatar_url": user.avatar_url,
            "is_platform": user.role in PLATFORM_ROLES,
            "university": None,
        }
        if user.university_id:
            uni = self.db.query(University).filter(University.id == user.university_id).first()
            if uni:
                info["university"] = {
                    "id": uni.id, "name": uni.name, "short_name": uni.short_name, "slug": uni.slug,
                    "logo_url": uni.logo_url, "brand_color": uni.brand_color, "status": uni.status,
                    "is_synthetic": uni.is_synthetic, "enabled_modules": uni.enabled_modules or [],
                    "academic_structure": uni.academic_structure or {},
                }
        if user.student_profile:
            sp = user.student_profile
            info.update(student_id=sp.id, roll_number=sp.roll_number, usn=sp.usn, cgpa=sp.cgpa,
                        current_semester=sp.current_semester)
        elif user.faculty_profile:
            info.update(faculty_id=user.faculty_profile.id, employee_id=user.faculty_profile.employee_id,
                        designation=user.faculty_profile.designation)
        elif user.mentor_profile:
            info.update(mentor_id=user.mentor_profile.id, employee_id=user.mentor_profile.employee_id,
                        designation=user.mentor_profile.designation)
        return info

    def generate_tokens(self, user: User) -> Dict[str, Any]:
        access_token = create_access_token(
            subject=user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            role=user.role, tenant_id=user.university_id, token_version=user.token_version or 0,
        )
        refresh_token = create_refresh_token(subject=user.id, token_version=user.token_version or 0)
        self.db.commit()
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": self.build_user_info(user),
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        user = self.db.query(User).filter(User.id == int(payload.get("sub", 0))).first()
        if not user or not user.is_active or payload.get("ver", 0) != (user.token_version or 0):
            raise HTTPException(status_code=401, detail="Session has ended. Please sign in again.")
        return self.generate_tokens(user)

    def logout(self, user: User, ip_address: Optional[str] = None) -> None:
        user.token_version = (user.token_version or 0) + 1  # revoke every issued token
        self.audit_repo.log(action="LOGOUT", user_id=user.id, resource_type="auth", ip_address=ip_address,
                            university_id=user.university_id)

    # ---------------------------------------------------------- invitations
    def get_invitation(self, token: str) -> Invitation:
        inv = self.db.query(Invitation).filter(Invitation.token_hash == hash_token(token)).first()
        if not inv or inv.revoked_at or inv.accepted_at or inv.expires_at < utcnow():
            raise HTTPException(status_code=400, detail="This invitation is invalid or has expired.")
        return inv

    def describe_invitation(self, token: str) -> Dict[str, Any]:
        inv = self.get_invitation(token)
        uni = self.db.query(University).filter(University.id == inv.university_id).first() if inv.university_id else None
        return {
            "email": inv.email,
            "full_name": inv.user.full_name if inv.user else None,
            "role": inv.role,
            "university_name": uni.name if uni else "ACEDRA",
            "expires_at": inv.expires_at.isoformat(),
        }

    def accept_invitation(self, token: str, password: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        inv = self.get_invitation(token)
        problem = validate_password_strength(password)
        if problem:
            raise HTTPException(status_code=422, detail=problem)
        user = inv.user
        user.hashed_password = get_password_hash(password)
        user.is_verified = True  # possession of the emailed token verifies the approved address
        user.is_active = True
        user.token_version = (user.token_version or 0) + 1
        inv.accepted_at = utcnow()
        self.audit_repo.log(action="INVITATION_ACCEPTED", user_id=user.id, resource_type="invitation",
                            resource_id=str(inv.id), ip_address=ip_address, university_id=inv.university_id)
        return self.generate_tokens(user)

    # ------------------------------------------------------- password reset
    def request_password_reset(self, email: str, ip_address: Optional[str] = None) -> None:
        user = self._get_by_email(email)
        if not user or not user.is_active or not user.is_verified:
            return  # never reveal whether an account exists
        token = generate_url_token()
        self.db.add(AuthToken(user_id=user.id, purpose="password_reset", token_hash=hash_token(token),
                              expires_at=utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TTL_MINUTES)))
        link = f"{settings.PUBLIC_APP_URL}/reset-password?token={token}"
        EmailService(self.db).send(
            user.email, "Reset your ACEDRA password",
            f"Hello {user.full_name},\n\nA password reset was requested for your ACEDRA account.\n"
            f"Use this link within {settings.PASSWORD_RESET_TTL_MINUTES} minutes:\n{link}\n\n"
            "If you did not request this, you can ignore this email.",
            template="password_reset", university_id=user.university_id,
        )
        self.audit_repo.log(action="PASSWORD_RESET_REQUESTED", user_id=user.id, resource_type="auth",
                            ip_address=ip_address, university_id=user.university_id)

    def confirm_password_reset(self, token: str, new_password: str, ip_address: Optional[str] = None) -> None:
        record = self.db.query(AuthToken).filter(AuthToken.token_hash == hash_token(token),
                                                 AuthToken.purpose == "password_reset").first()
        if not record or record.used_at or record.expires_at < utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired password reset link.")
        problem = validate_password_strength(new_password)
        if problem:
            raise HTTPException(status_code=422, detail=problem)
        user = self.db.query(User).filter(User.id == record.user_id).first()
        user.hashed_password = get_password_hash(new_password)
        user.token_version = (user.token_version or 0) + 1
        record.used_at = utcnow()
        self.audit_repo.log(action="PASSWORD_RESET_SUCCESS", user_id=user.id, resource_type="auth",
                            ip_address=ip_address, university_id=user.university_id)

    def change_password(self, user: User, old_password: str, new_password: str) -> None:
        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        problem = validate_password_strength(new_password)
        if problem:
            raise HTTPException(status_code=422, detail=problem)
        user.hashed_password = get_password_hash(new_password)
        user.token_version = (user.token_version or 0) + 1
        self.audit_repo.log(action="PASSWORD_CHANGED", user_id=user.id, resource_type="auth",
                            university_id=user.university_id)
