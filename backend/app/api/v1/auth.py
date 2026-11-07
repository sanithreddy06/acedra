from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_active_user, get_client_ip
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.schemas.user import PasswordResetRequest, PasswordResetConfirm
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login_json(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Login with JSON payload containing email and password."""
    ip = get_client_ip(request)
    ua = request.headers.get("User-Agent")
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password,
        ip_address=ip,
        user_agent=ua
    )
    return auth_service.generate_tokens(user)


@router.post("/token", response_model=Token, include_in_schema=False)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
) -> Any:
    """OAuth2 compatible token login for Swagger UI."""
    ip = get_client_ip(request) if request else "unknown"
    ua = request.headers.get("User-Agent") if request else "swagger"
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password,
        ip_address=ip,
        user_agent=ua
    )
    return auth_service.generate_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Obtain a new access token using a valid refresh token."""
    auth_service = AuthService(db)
    return auth_service.refresh_access_token(payload.refresh_token)


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve full profile details of the currently authenticated user."""
    auth_service = AuthService(db)
    return auth_service.generate_tokens(current_user)["user"]


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
) -> Any:
    """Invalidate session / register audit event for logout."""
    auth_service = AuthService(db)
    ip = get_client_ip(request) if request else None
    auth_service.audit_repo.log(
        action="LOGOUT",
        user_id=current_user.id,
        resource_type="auth",
        ip_address=ip,
        details={"email": current_user.email}
    )
    return {"message": "Logged out successfully"}


@router.post("/password-reset-request")
def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Request a password reset link/token."""
    ip = get_client_ip(request)
    auth_service = AuthService(db)
    token = auth_service.request_password_reset(body.email, ip_address=ip)
    return {
        "message": "If the account exists, instructions have been generated.",
        "reset_token": token if "reset:" in token else None
    }


@router.post("/password-reset-confirm")
def confirm_password_reset(
    body: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """Set new password using a valid reset token."""
    ip = get_client_ip(request)
    auth_service = AuthService(db)
    auth_service.confirm_password_reset(body.token, body.new_password, ip_address=ip)
    return {"message": "Password has been successfully updated. You may now login."}
