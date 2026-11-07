from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import User, UserRole
from app.models.system import SystemSetting
from app.schemas.system import SystemSettingOut, SystemSettingUpdate

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("/", response_model=List[SystemSettingOut])
def list_settings(
    category: str = None,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
) -> Any:
    """List system settings (Admin only)."""
    query = db.query(SystemSetting)
    if category:
        query = query.filter(SystemSetting.category == category)
    return query.all()


@router.patch("/{key}", response_model=SystemSettingOut)
def update_setting(
    key: str,
    setting_in: SystemSettingUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db)
) -> Any:
    """Update a system configuration setting (Admin only)."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found.")

    setting.value = setting_in.value
    if setting_in.description:
        setting.description = setting_in.description
    setting.updated_by = current_user.id
    db.commit()
    db.refresh(setting)
    return setting
