import enum

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    MENTOR = "mentor"
    ADMIN = "admin"  # University Administrator / HOD
    PLACEMENT_OFFICER = "placement_officer"


class PlatformRole(str, enum.Enum):
    """ACEDRA internal team roles. Platform users have university_id = NULL."""
    SUPER_ADMIN = "platform_admin"
    EMPLOYEE = "platform_employee"


UNIVERSITY_ROLES = {r.value for r in UserRole}
PLATFORM_ROLES = {r.value for r in PlatformRole}


class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, default=list, nullable=False)

    users = relationship("User", back_populates="role_rel")


class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(String(50), index=True, nullable=False)  # UserRole value
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=True, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    title = Column(String(150), nullable=True)  # job title / designation
    # Incremented on logout / password change so previously issued tokens stop working.
    token_version = Column(Integer, default=0, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    # Consecutive failed sign-ins; the account is locked until ``locked_until`` once the limit is reached.
    failed_login_count = Column(Integer, default=0, server_default="0", nullable=False)
    locked_until = Column(DateTime, nullable=True)
    invited_at = Column(DateTime, nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)

    # Relationships
    role_rel = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    faculty_profile = relationship("Faculty", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mentor_profile = relationship("Mentor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

