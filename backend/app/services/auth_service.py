from datetime import timedelta, datetime, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.repositories.audit_repo import AuditRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        user = self.user_repo.get_by_email(email)
        if not user:
            self.audit_repo.log(
                action="LOGIN_FAILED",
                resource_type="auth",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": email, "reason": "User not found"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(password, user.hashed_password):
            self.audit_repo.log(
                action="LOGIN_FAILED",
                user_id=user.id,
                resource_type="auth",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"email": email, "reason": "Invalid password"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive or disabled. Contact administrator.",
            )

        self.audit_repo.log(
            action="LOGIN_SUCCESS",
            user_id=user.id,
            resource_type="auth",
            resource_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
            details={"role": user.role}
        )
        return user

    def generate_tokens(self, user: User) -> Dict[str, Any]:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id,
            expires_delta=access_token_expires,
            role=user.role
        )
        refresh_token = create_refresh_token(subject=user.id)

        user_info = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else None,
            "avatar_url": user.avatar_url,
        }

        # Add profile-specific IDs
        if user.student_profile:
            user_info["student_id"] = user.student_profile.id
            user_info["roll_number"] = user.student_profile.roll_number
            user_info["usn"] = user.student_profile.usn
            user_info["cgpa"] = user.student_profile.cgpa
            user_info["current_semester"] = user.student_profile.current_semester
        elif user.faculty_profile:
            user_info["faculty_id"] = user.faculty_profile.id
            user_info["employee_id"] = user.faculty_profile.employee_id
            user_info["designation"] = user.faculty_profile.designation
        elif user.mentor_profile:
            user_info["mentor_id"] = user.mentor_profile.id
            user_info["employee_id"] = user.mentor_profile.employee_id
            user_info["designation"] = user.mentor_profile.designation

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": user_info
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        user = self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or not found",
            )

        return self.generate_tokens(user)

    def request_password_reset(self, email: str, ip_address: Optional[str] = None) -> str:
        user = self.user_repo.get_by_email(email)
        # Even if user not found, don't leak user existence in generic message
        if not user:
            return "If that account exists, a password reset token has been issued."

        # Create temporary reset token (expires in 30 mins)
        reset_token = create_access_token(
            subject=f"reset:{user.id}",
            expires_delta=timedelta(minutes=30)
        )

        self.audit_repo.log(
            action="PASSWORD_RESET_REQUESTED",
            user_id=user.id,
            resource_type="auth",
            ip_address=ip_address,
            details={"email": email}
        )
        return reset_token

    def confirm_password_reset(self, token: str, new_password: str, ip_address: Optional[str] = None) -> bool:
        payload = decode_token(token)
        if not payload or not str(payload.get("sub", "")).startswith("reset:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )

        user_id = int(payload["sub"].split("reset:")[1])
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.hashed_password = get_password_hash(new_password)
        self.db.commit()

        self.audit_repo.log(
            action="PASSWORD_RESET_SUCCESS",
            user_id=user.id,
            resource_type="auth",
            ip_address=ip_address,
            details={"email": user.email}
        )
        return True
