from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Student schemas
class StudentBase(BaseModel):
    roll_number: str
    usn: str
    srn: Optional[str] = None
    department_id: int
    program: str = "B.Tech Computer Science & Engineering"
    current_semester: int = Field(1, ge=1, le=8)
    batch_year: int = 2024
    admission_year: int = 2022
    section: str = "A"
    status: str = "Active"
    placement_status: str = "Eligible"
    assigned_mentor_id: Optional[int] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    blood_group: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    address: Optional[str] = None


class StudentCreate(StudentBase):
    full_name: str
    email: EmailStr
    password: Optional[str] = None  # ignored: accounts are activated by invitation


class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    program: Optional[str] = None
    current_semester: Optional[int] = None
    section: Optional[str] = None
    status: Optional[str] = None
    placement_status: Optional[str] = None
    assigned_mentor_id: Optional[int] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    blood_group: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    address: Optional[str] = None


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    roll_number: str
    usn: str
    srn: Optional[str] = None
    department_id: int
    department_code: Optional[str] = None
    department_name: Optional[str] = None
    program: str
    current_semester: int
    batch_year: int
    admission_year: int
    section: str
    status: str
    cgpa: float
    attendance_percentage: float
    placement_status: str
    assigned_mentor_id: Optional[int] = None
    mentor_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[date] = None
    blood_group: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Academic records schemas


# Attendance schemas
class SubjectAttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    subject_id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    semester_id: int
    total_classes: int
    attended_classes: int
    missed_classes: int
    attendance_percentage: float


# Assessment schemas
class StudentAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    subject_id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    semester_id: int
    assessment_type: str
    max_marks: float
    marks_obtained: float
    percentage: float
    remarks: Optional[str] = None
    assessment_date: Optional[date] = None


# Skills schemas


class StudentSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: int
    skill_name: str
    category: str
    proficiency_level: str
    is_verified: bool


class StudentSkillCreate(BaseModel):
    skill_name: str
    category: str = "programming"
    proficiency_level: str = "Intermediate"


# Certification, Project, Internship, Hackathon schemas
class CertificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    title: str
    issuing_organization: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    verification_status: str


class CertificationCreate(BaseModel):
    title: str
    issuing_organization: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    title: str
    description: str
    tech_stack: str
    role: str
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    semester_number: int


class ProjectCreate(BaseModel):
    title: str
    description: str
    tech_stack: str
    role: str = "Developer"
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    semester_number: int = 5


class InternshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    company_name: str
    role: str
    start_date: date
    end_date: Optional[date] = None
    stipend: Optional[str] = None
    description: Optional[str] = None
    status: str


class InternshipCreate(BaseModel):
    company_name: str
    role: str
    start_date: date
    end_date: Optional[date] = None
    stipend: Optional[str] = None
    description: Optional[str] = None
    status: str = "Completed"


class HackathonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    event_name: str
    organizer: str
    year: int
    achievement: str
    project_title: Optional[str] = None


# Comprehensive Individual Student Analytics Output
class StudentMetricsOut(BaseModel):
    """Headline indicators for one student, derived from their recorded results and attendance."""

    cgpa: Optional[float] = None
    calculated_attendance_percentage: Optional[float] = None
    internal_assessment_average: Optional[float] = None
    total_credits_earned: Optional[int] = None
    total_backlogs: int = 0
    total_skills_count: int = 0
    certifications_count: int = 0
    projects_count: int = 0
    internships_count: int = 0
    hackathons_count: int = 0


class SgpaTrendPoint(BaseModel):
    semester: str
    semester_number: int
    sgpa: float
    credits_registered: int
    credits_earned: int
    backlogs: int
    status: str


class SubjectPerformanceOut(BaseModel):
    subject_code: str
    subject_name: str
    internal_marks: float
    external_marks: float
    total_marks: float
    letter_grade: str
    grade_point: float
    is_backlog: bool


class StudentAnalyticsOut(BaseModel):
    student_profile: StudentProfileOut
    metrics: StudentMetricsOut
    sgpa_trend: List[SgpaTrendPoint]
    subject_performance: List[SubjectPerformanceOut]
    attendance_breakdown: List[SubjectAttendanceOut]
    assessment_history: List[StudentAssessmentOut]
    skills_by_category: Dict[str, List[StudentSkillOut]]
    certifications: List[CertificationOut]
    projects: List[ProjectOut]
    internships: List[InternshipOut]
    hackathons: List[HackathonOut]


# Faculty & Admin Analytics Outputs
class AssignedCourseOut(BaseModel):
    assignment_id: int
    subject_code: str
    subject_name: str
    section: str
    academic_year: Optional[str] = None


class CohortStudentOut(BaseModel):
    id: int
    name: str
    usn: str
    roll_number: str
    semester: int
    section: str
    cgpa: float
    attendance: float
    status: str


class FacultyAnalyticsOut(BaseModel):
    faculty_id: Optional[int] = None
    faculty_name: str
    department_name: Optional[str] = None
    assigned_courses: List[AssignedCourseOut]
    total_assigned_students: int
    average_cohort_attendance: float
    average_cohort_marks: float
    students_summary: List[CohortStudentOut]
    # False when the caller has no faculty profile yet: nothing is taught, so the lists are empty.
    profile_configured: bool = True


class InstitutionalStatsOut(BaseModel):
    total_students: int
    active_students: int
    total_faculty: int
    total_departments: int
    campus_average_cgpa: float
    campus_average_attendance: float


class DepartmentStatsOut(BaseModel):
    department_code: str
    department_name: str
    total_students: int
    average_cgpa: float
    average_attendance: float
    at_risk_count: int
    hod_name: Optional[str] = None


class SemesterStatsOut(BaseModel):
    semester: str  # label from the tenant's academic structure, e.g. "Term 4"
    semester_number: int
    student_count: int
    average_cgpa: float
    average_attendance: float


class ImportBatchOut(BaseModel):
    id: int
    filename: str
    type: str
    status: str
    success: int
    failed: int
    date: str


class ImportStatsOut(BaseModel):
    total_import_batches: int
    recent_batches: List[ImportBatchOut]


class AdminAnalyticsOut(BaseModel):
    institutional_stats: InstitutionalStatsOut
    department_wise_stats: List[DepartmentStatsOut]
    semester_wise_performance: List[SemesterStatsOut]
    attendance_distribution: Dict[str, int]
    cgpa_distribution: Dict[str, int]
    import_stats: ImportStatsOut


# Data Import schemas
class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    import_type: str
    status: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    created_at: datetime
    error_count: Optional[int] = 0


class ImportRowError(BaseModel):
    row_number: int
    row_data: Dict[str, Any]
    error_message: str


class ImportPreviewResult(BaseModel):
    filename: str
    import_type: str
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    columns_detected: List[str]
    preview_rows: List[Dict[str, Any]]
    errors: List[ImportRowError]
