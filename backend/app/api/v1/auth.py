from typing import Any, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip, get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import limiter
from app.core.tenancy import unscoped
from app.models.legal import LegalAcceptance
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, Token
from app.schemas.legal import LegalAcceptanceIn, LegalStatusOut
from app.services import legal_service
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)
    new_password: str = Field(..., max_length=128)


class AcceptInvitation(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)
    password: str = Field(..., max_length=128)
    # Document type -> version of the Terms and Privacy Policy the person reviewed and accepted.
    accepted_versions: Dict[str, str]


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., max_length=128)


@router.post("/login", response_model=Token)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def login_json(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Any:
    svc = AuthService(db)
    user = svc.authenticate_user(credentials.email, credentials.password, get_client_ip(request),
                                 request.headers.get("User-Agent"))
    return svc.generate_tokens(user)


@router.post("/token", response_model=Token, include_in_schema=False)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def login_form(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Any:
    svc = AuthService(db)
    user = svc.authenticate_user(form_data.username, form_data.password, get_client_ip(request), "swagger")
    return svc.generate_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> Any:
    return AuthService(db).refresh_access_token(payload.refresh_token)


@router.get("/me")
def me(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> Any:
    return AuthService(db).build_user_info(current_user)


@router.post("/logout")
def logout(request: Request, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> Any:
    svc = AuthService(db)
    svc.logout(current_user, get_client_ip(request))
    db.commit()
    return {"message": "Signed out. All active sessions for this account have ended."}


@router.get("/invitations/{token}")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def describe_invitation(token: str, request: Request, db: Session = Depends(get_db)) -> Any:
    return AuthService(db).describe_invitation(token)


@router.post("/invitations/accept", response_model=Token)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def accept_invitation(body: AcceptInvitation, request: Request, db: Session = Depends(get_db)) -> Any:
    svc = AuthService(db)
    invitation = svc.get_invitation(body.token)
    legal_service.record_acceptance(db, invitation.user, body.accepted_versions, context="invitation", commit=False)
    result = svc.accept_invitation(body.token, body.password, get_client_ip(request))
    db.commit()
    return result


@router.get("/legal-status", response_model=LegalStatusOut)
def legal_status(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> Any:
    """Which current legal documents this person still needs to accept, and what they have accepted."""
    with unscoped(db):
        accepted = db.query(LegalAcceptance).filter(LegalAcceptance.user_id == current_user.id) \
            .order_by(LegalAcceptance.accepted_at.desc()).all()
        history = [{"doc_type": a.doc_type, "version": a.version, "accepted_at": a.accepted_at.isoformat()}
                   for a in accepted]
    return {"pending": legal_service.pending_documents(db, current_user), "accepted": history}


@router.post("/legal-acceptances", response_model=LegalStatusOut)
def accept_legal_documents(body: LegalAcceptanceIn, current_user: User = Depends(get_current_active_user),
                           db: Session = Depends(get_db)) -> Any:
    """Record that the signed-in person accepted the current Terms and Privacy Policy."""
    legal_service.record_acceptance(db, current_user, body.accepted_versions, context="sign_in")
    return legal_status(current_user, db)


@router.post("/password-reset-request")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def request_password_reset(body: PasswordResetRequest, request: Request, db: Session = Depends(get_db)) -> Any:
    AuthService(db).request_password_reset(body.email, get_client_ip(request))
    db.commit()
    return {"message": "If an active account exists for that email, a reset link has been sent."}


@router.post("/password-reset-confirm")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def confirm_password_reset(body: PasswordResetConfirm, request: Request, db: Session = Depends(get_db)) -> Any:
    AuthService(db).confirm_password_reset(body.token, body.new_password, get_client_ip(request))
    db.commit()
    return {"message": "Your password has been updated. You can now sign in."}


@router.post("/change-password")
def change_password(body: ChangePassword, current_user: User = Depends(get_current_active_user),
                    db: Session = Depends(get_db)) -> Any:
    AuthService(db).change_password(current_user, body.old_password, body.new_password)
    db.commit()
    return {"message": "Password changed. Please sign in again."}
