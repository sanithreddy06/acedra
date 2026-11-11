from sqlalchemy import JSON, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class SystemSetting(Base, TimestampMixin, TenantMixin):
    __tablename__ = "system_settings"
    __table_args__ = (UniqueConstraint("university_id", "key", name="uq_system_settings_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), index=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(String(255), nullable=True)
    category = Column(String(50), default="general", index=True, nullable=False)  # general, security, academic, notifications
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    updater = relationship("User")
