from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class Department(Base, TimestampMixin, TenantMixin):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("university_id", "code", name="uq_departments_tenant_code"),)

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), index=True, nullable=False)  # e.g., CSE, ECE, MECH, AI_DS
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    hod_name = Column(String(150), nullable=True)

    # Relationships
    users = relationship("User", back_populates="department")
    students = relationship("Student", back_populates="department")
    faculty_members = relationship("Faculty", back_populates="department")
    mentors = relationship("Mentor", back_populates="department")
    subjects = relationship("Subject", back_populates="department")
