from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class SystemSettingBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    category: str = "general"


class SystemSettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None


class SystemSettingOut(SystemSettingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_by: Optional[int] = None
    updated_at: datetime
