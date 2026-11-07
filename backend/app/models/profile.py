from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Date, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    usn = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    current_semester = Column(Integer, default=1, nullable=False)
    batch_year = Column(Integer, nullable=False)  # e.g., 2024
    section = Column(String(10), default="A", nullable=False)
    cgpa = Column(Float, default=0.0, nullable=False)
    attendance_percentage = Column(Float, default=100.0, nullable=False)
    placement_status = Column(String(50), default="Eligible", nullable=False)  # Eligible, Placed, Ineligible
    assigned_mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    mentor = relationship("Mentor", back_populates="mentees", foreign_keys=[assigned_mentor_id])
    mentor_assignments = relationship("StudentMentorAssignment", back_populates="student", cascade="all, delete-orphan")


class Faculty(Base, TimestampMixin):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100), default="Assistant Professor", nullable=False)
    specialization = Column(String(200), nullable=True)
    qualification = Column(String(100), default="Ph.D.", nullable=True)

    # Relationships
    user = relationship("User", back_populates="faculty_profile")
    department = relationship("Department", back_populates="faculty_members")
    course_assignments = relationship("FacultyCourseAssignment", back_populates="faculty")


class Mentor(Base, TimestampMixin):
    __tablename__ = "mentors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    designation = Column(String(100), default="Senior Faculty Mentor", nullable=False)
    max_mentees = Column(Integer, default=30, nullable=False)

    # Relationships
    user = relationship("User", back_populates="mentor_profile")
    department = relationship("Department", back_populates="mentors")
    mentees = relationship("Student", back_populates="mentor", foreign_keys=[Student.assigned_mentor_id])
    assignments = relationship("StudentMentorAssignment", back_populates="mentor")


class StudentMentorAssignment(Base, TimestampMixin):
    __tablename__ = "student_mentor_assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=False)
    academic_year = Column(String(50), nullable=False)  # e.g., 2026-2027
    semester = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    assigned_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    student = relationship("Student", back_populates="mentor_assignments")
    mentor = relationship("Mentor", back_populates="assignments")
