from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SemesterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    academic_year: str = Field(..., min_length=4, max_length=50)
    semester_number: int = Field(..., ge=1, le=24)
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
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    department_id: int
    semester_number: int = Field(..., ge=1, le=24)
    credits: int = Field(3, ge=0, le=30)
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


class TeachingAssignmentCreate(BaseModel):
    """Assign a faculty member (by user account) to teach a subject's section in a term."""

    faculty_user_id: int
    subject_id: int
    semester_id: int
    section: str = Field("A", min_length=1, max_length=10)
    academic_year: str = Field(..., min_length=4, max_length=50)


class FacultyCourseAssignmentOut(FacultyCourseAssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty_name: Optional[str] = None
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
