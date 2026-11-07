from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Semester(Base, TimestampMixin):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Fall 2026", "Semester 5"
    academic_year = Column(String(50), nullable=False)  # e.g., "2026-2027"
    semester_number = Column(Integer, nullable=False)  # 1 to 8
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)

    course_assignments = relationship("FacultyCourseAssignment", back_populates="semester")


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(30), unique=True, index=True, nullable=False)  # e.g., "CS501"
    name = Column(String(200), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    semester_number = Column(Integer, nullable=False)
    credits = Column(Integer, default=3, nullable=False)
    subject_type = Column(String(50), default="Theory", nullable=False)  # Theory, Lab, Project, Elective

    department = relationship("Department", back_populates="subjects")
    course_assignments = relationship("FacultyCourseAssignment", back_populates="subject")


class FacultyCourseAssignment(Base, TimestampMixin):
    __tablename__ = "faculty_course_assignments"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False)
    section = Column(String(10), default="A", nullable=False)
    academic_year = Column(String(50), nullable=False)

    faculty = relationship("Faculty", back_populates="course_assignments")
    subject = relationship("Subject", back_populates="course_assignments")
    semester = relationship("Semester", back_populates="course_assignments")
