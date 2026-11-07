from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
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
    semester_records = relationship("StudentSemesterRecord", back_populates="semester")


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
    subject_results = relationship("SubjectResult", back_populates="subject")
    attendance_records = relationship("SubjectAttendance", back_populates="subject")
    assessments = relationship("StudentAssessment", back_populates="subject")


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


# MODULE 1: Academic Records per Semester
class StudentSemesterRecord(Base, TimestampMixin):
    __tablename__ = "student_semester_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    semester_number = Column(Integer, nullable=False)
    sgpa = Column(Float, default=0.0, nullable=False)
    credits_registered = Column(Integer, default=24, nullable=False)
    credits_earned = Column(Integer, default=24, nullable=False)
    backlogs_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="Pass", nullable=False)  # Pass, Fail, Backlog

    student = relationship("Student", back_populates="semester_records")
    semester = relationship("Semester", back_populates="semester_records")


# MODULE 1: Subject-wise Examination Marks
class SubjectResult(Base, TimestampMixin):
    __tablename__ = "subject_results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    internal_marks = Column(Float, default=0.0, nullable=False)  # out of 40/50
    external_marks = Column(Float, default=0.0, nullable=False)  # out of 50/60
    total_marks = Column(Float, default=0.0, nullable=False)     # out of 100
    letter_grade = Column(String(5), default="A", nullable=False) # O, A+, A, B+, B, C, P, F
    grade_point = Column(Float, default=8.0, nullable=False)      # 10.0, 9.0, 8.0 etc
    is_backlog = Column(Boolean, default=False, nullable=False)

    student = relationship("Student", back_populates="subject_results")
    subject = relationship("Subject", back_populates="subject_results")
    semester = relationship("Semester")


# MODULE 1: Attendance Management (Computed from counts)
class SubjectAttendance(Base, TimestampMixin):
    __tablename__ = "subject_attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    total_classes = Column(Integer, default=45, nullable=False)
    attended_classes = Column(Integer, default=40, nullable=False)

    @hybrid_property
    def attendance_percentage(self) -> float:
        if self.total_classes <= 0:
            return 100.0
        return round((self.attended_classes / self.total_classes) * 100.0, 2)

    @hybrid_property
    def missed_classes(self) -> int:
        return max(0, self.total_classes - self.attended_classes)

    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")
    semester = relationship("Semester")


# MODULE 1: Continuous Assessments
class StudentAssessment(Base, TimestampMixin):
    __tablename__ = "student_assessments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, index=True)
    assessment_type = Column(String(100), nullable=False)  # Internal Assessment 1, IA 2, Quiz 1, Assignment, Lab Test
    max_marks = Column(Float, default=25.0, nullable=False)
    marks_obtained = Column(Float, default=20.0, nullable=False)
    remarks = Column(String(255), nullable=True)
    assessment_date = Column(Date, nullable=True)

    @hybrid_property
    def percentage(self) -> float:
        if self.max_marks <= 0:
            return 0.0
        return round((self.marks_obtained / self.max_marks) * 100.0, 2)

    student = relationship("Student", back_populates="assessments")
    subject = relationship("Subject", back_populates="assessments")
    semester = relationship("Semester")
