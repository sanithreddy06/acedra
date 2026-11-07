from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.academic import Semester, Subject, FacultyCourseAssignment
from app.models.department import Department
from app.models.profile import Student, Faculty, Mentor, StudentMentorAssignment
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, db: Session):
        super().__init__(Department, db)

    def get_by_code(self, code: str) -> Optional[Department]:
        return self.db.query(Department).filter(Department.code == code.upper()).first()


class AcademicRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_current_semester(self) -> Optional[Semester]:
        return self.db.query(Semester).filter(Semester.is_current == True).first()

    def get_all_semesters(self) -> List[Semester]:
        return self.db.query(Semester).order_by(Semester.semester_number.asc()).all()

    def get_subjects_by_department(self, dept_id: int) -> List[Subject]:
        return self.db.query(Subject).filter(Subject.department_id == dept_id).all()

    def get_all_subjects(self) -> List[Subject]:
        return self.db.query(Subject).all()

    def get_faculty_assignments(self, faculty_id: int) -> List[FacultyCourseAssignment]:
        return self.db.query(FacultyCourseAssignment).filter(
            FacultyCourseAssignment.faculty_id == faculty_id
        ).all()
