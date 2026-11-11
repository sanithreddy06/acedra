from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    roll_number: str
    usn: str
    department_id: int
    current_semester: int
    batch_year: int
    section: str
    cgpa: float
    attendance_percentage: float
    placement_status: str
    assigned_mentor_id: Optional[int] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    department_name: Optional[str] = None


class FacultyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    employee_id: str
    department_id: int
    designation: str
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    department_name: Optional[str] = None


class MentorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    employee_id: str
    department_id: int
    designation: str
    max_mentees: int
    mentee_count: Optional[int] = 0
    full_name: Optional[str] = None
    email: Optional[str] = None
    department_name: Optional[str] = None


class StudentMentorAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    mentor_id: int
    academic_year: str
    semester: int
    is_active: bool
    assigned_date: Optional[date] = None
    notes: Optional[str] = None
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    mentor_name: Optional[str] = None
