from typing import Any, Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.access import accessible_student_ids
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.core.tenancy import TenantScope, get_scope, set_session_scope
from app.models.platform import TenantStatus, University
from app.models.user import PLATFORM_ROLES, PlatformRole, User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

MODULE_PREFIXES = {
    "/risk": "risk_identification",
    "/recommendations": "recommendations",
    "/placement": "placement_readiness",
    "/ai": "ai_assistant",
    "/interventions": "interventions",
}


def get_client_ip(request: Request) -> str:
    """Client address for audit records.

    Never read X-Forwarded-For here: a caller can put anything in it. The API server is started with
    trusted proxy headers (see docker/Dockerfile.backend.prod), which rewrites ``request.client`` from the
    header only when the request really came through our reverse proxy.
    """
    return request.client.host if request.client else "unknown"


def _credentials_error(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


def resolve_user_from_token(db: Session, token: str) -> User:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access" or payload.get("sub") is None:
        raise _credentials_error()
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _credentials_error() from None
    set_session_scope(db, TenantScope(bypass=True))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _credentials_error()
    if payload.get("ver", 0) != (user.token_version or 0):
        raise _credentials_error("Session has ended. Please sign in again.")
    if payload.get("tid") != user.university_id:
        raise _credentials_error()
    return user


def _apply_scope(db: Session, user: User) -> None:
    if user.role in PLATFORM_ROLES:
        set_session_scope(db, TenantScope(platform=True, user_id=user.id, role=user.role))
        return
    student_ids = accessible_student_ids(db, user)
    set_session_scope(db, TenantScope(tenant_id=user.university_id, student_ids=student_ids,
                                      user_id=user.id, role=user.role))


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    user = resolve_user_from_token(db, token)
    if user.role not in PLATFORM_ROLES:
        university = db.query(University).filter(University.id == user.university_id).first()
        if university is None:
            raise _credentials_error()
        allowed = {TenantStatus.ACTIVE}
        if user.role == UserRole.ADMIN.value:
            allowed.add(TenantStatus.ONBOARDING)  # initial administrator configures before go-live
        if university.status not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="This university workspace is not currently active.")
    _apply_scope(db, user)
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")
    return current_user


def require_role(*roles: Any) -> Callable[..., User]:
    flattened = []
    for r in roles:
        if isinstance(r, (list, tuple, set)):
            flattened.extend(r)
        else:
            flattened.append(r)
    allowed_roles = {getattr(r, "value", r) for r in flattened}

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="You do not have permission to perform this action.")
        return current_user

    return role_checker


def get_university_user(request: Request, current_user: User = Depends(get_current_active_user),
                        db: Session = Depends(get_db)) -> User:
    """Guard for every university-workspace router.

    * rejects platform (ACEDRA internal) accounts — they use /platform
    * blocks modules the university has not enabled
    * verifies any student_id in the path or query is within the caller's authorised scope
    """
    if current_user.role in PLATFORM_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="ACEDRA platform accounts cannot use university workspaces.")
    _require_legal_acceptance(db, current_user)

    path = request.url.path.split("/api/v1", 1)[-1]
    for prefix, module in MODULE_PREFIXES.items():
        if path.startswith(prefix):
            university = db.query(University).filter(University.id == current_user.university_id).first()
            if university and module not in (university.enabled_modules or []):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail="This module is not enabled for your university.")
            break

    raw = request.path_params.get("student_id") or request.query_params.get("student_id")
    if raw not in (None, ""):
        try:
            sid = int(raw)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid student id") from None
        from app.models import Student
        in_tenant = db.query(Student.id).execution_options(acedra_unscoped=True).filter(
            Student.id == sid, Student.university_id == current_user.university_id).first()
        if not in_tenant:  # other universities' records are indistinguishable from missing ones
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
        # Reuse the student scope computed for this request in get_current_user instead of re-querying it.
        scope = get_scope(db)
        allowed = scope.student_ids if scope and scope.user_id == current_user.id else accessible_student_ids(
            db, current_user)
        if allowed is not None and sid not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Access forbidden: you are not authorised to view this student's records.")
    return current_user


def require_platform_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> User:
    if current_user.role not in PLATFORM_ROLES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_legal_acceptance(db, current_user)
    return current_user


def _require_legal_acceptance(db: Session, user: User) -> None:
    """With LEGAL_ACCEPTANCE_ENFORCED, refuse workspace calls until the current terms are accepted."""
    if not settings.LEGAL_ACCEPTANCE_ENFORCED:
        return
    from app.services.legal_service import pending_documents
    if pending_documents(db, user):
        raise HTTPException(status_code=428, detail="Please review and accept the current Terms and Privacy Policy.")


def require_platform_admin(current_user: User = Depends(require_platform_user)) -> User:
    if current_user.role != PlatformRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Platform super-administrator permission required.")
    return current_user


def require_university_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="University administrator permission required.")
    return current_user
