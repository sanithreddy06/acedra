from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_active_user, require_role
from app.models.user import User, Role, UserRole
from app.schemas.user import UserOut, UserCreate, UserUpdate, ChangePassword, RoleOut
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
) -> Any:
    """List registered users (Administrator only)."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.offset(skip).limit(limit).all()


@router.get("/roles", response_model=List[RoleOut])
def get_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get all configured platform roles."""
    return db.query(Role).all()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
) -> Any:
    """Create a new user account (Administrator only)."""
    user_service = UserService(db)
    return user_service.create_user(user_in, creator_id=current_user.id)


@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get user details by ID. Non-admins can only fetch their own profile."""
    if current_user.role != UserRole.ADMIN.value and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user profile.")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update user information."""
    if current_user.role != UserRole.ADMIN.value and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user profile.")

    user_service = UserService(db)
    return user_service.update_user(user_id, user_in, actor_id=current_user.id)


@router.post("/me/change-password")
def change_my_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update password for the current user."""
    user_service = UserService(db)
    user_service.change_password(current_user.id, payload.old_password, payload.new_password)
    return {"message": "Password changed successfully"}
