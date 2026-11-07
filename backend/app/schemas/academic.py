from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SemesterBase(BaseModel):
    name: str
    academic_year: str
    semester_number: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False


class SemesterCreate(SemesterBase):
    pass


class SemesterOut(SemesterBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class SubjectBase(BaseModel):
    code: str
    name: str
    department_id: int
    semester_number: int
    credits: int = 3
    subject_type: str = "Theory"


class SubjectCreate(SubjectBase):
    pass


class SubjectOut(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class FacultyCourseAssignmentBase(BaseModel):
    faculty_id: int
    subject_id: int
    semester_id: int
    section: str = "A"
    academic_year: str


class FacultyCourseAssignmentCreate(FacultyCourseAssignmentBase):
    pass


class FacultyCourseAssignmentOut(FacultyCourseAssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty_name: Optional[str] = None
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
