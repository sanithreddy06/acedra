from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., CSE, ECE, MECH, AI_DS
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    hod_name = Column(String(150), nullable=True)

    # Relationships
    users = relationship("User", back_populates="department")
    students = relationship("Student", back_populates="department")
    faculty_members = relationship("Faculty", back_populates="department")
    mentors = relationship("Mentor", back_populates="department")
    subjects = relationship("Subject", back_populates="department")
