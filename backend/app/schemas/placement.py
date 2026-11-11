from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# --- Skill Catalogue & Evidence Schemas ---
class SkillBase(BaseModel):
    name: str
    # programming, framework, database, cloud, data_science, artificial_intelligence,
    # cybersecurity, communication, teamwork, problem_solving
    category: str = "programming"
    description: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SkillEvidenceBase(BaseModel):
    evidence_type: str = "PROJECT"  # PROJECT, CERTIFICATION, GITHUB_REPO, LIVE_DEMO, PUBLICATION, OTHER
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[int] = None
    certification_id: Optional[int] = None


class SkillEvidenceCreate(SkillEvidenceBase):
    student_skill_id: int


class SkillEvidenceVerify(BaseModel):
    verification_status: str  # VERIFIED, REJECTED, PENDING_REVIEW
    verification_feedback: Optional[str] = None


class SkillEvidenceResponse(SkillEvidenceBase):
    id: int
    student_skill_id: int
    student_id: int
    verification_status: str
    verified_by_user_id: Optional[int] = None
    verified_at: Optional[datetime] = None
    verification_feedback: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentSkillDetailResponse(BaseModel):
    id: int
    student_id: int
    skill_id: int
    skill_name: str
    category: str
    proficiency_level: str
    is_verified: bool
    verified_by_name: Optional[str] = None
    evidence_count: int = 0
    evidences: List[SkillEvidenceResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentSkillCreateOrUpdate(BaseModel):
    skill_name: str
    category: str = "programming"
    proficiency_level: str = "Intermediate"  # Beginner, Intermediate, Advanced, Expert
    evidence: Optional[SkillEvidenceBase] = None


# --- Career Role Schemas ---
class RoleSkillItem(BaseModel):
    skill_id: Optional[int] = None
    skill_name: str
    category: Optional[str] = "programming"
    min_proficiency: str = "Intermediate"  # Beginner, Intermediate, Advanced, Expert
    importance: str = "CORE"  # CRITICAL, CORE, PREFERRED
    importance_weight: float = 2.0
    is_mandatory: bool = True


class RoleSkillResponse(RoleSkillItem):
    id: int
    role_id: int

    class Config:
        from_attributes = True


class CareerRoleBase(BaseModel):
    code: str
    title: str
    department_id: Optional[int] = None
    description: Optional[str] = None
    min_experience_level: str = "Entry Level"
    average_salary_range: str = "6-12 LPA"
    industry_demand: str = "High"
    is_active: bool = True


class CareerRoleCreate(CareerRoleBase):
    required_skills: List[RoleSkillItem] = []


class CareerRoleResponse(CareerRoleBase):
    id: int
    department_code: Optional[str] = None
    skills: List[RoleSkillResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Skill Gap Analysis & Readiness Engine Schemas ---
class SkillGapItem(BaseModel):
    skill_name: str
    category: str
    status: str  # MATCHED, BELOW_PROFICIENCY, MISSING, REQUIRES_VERIFICATION
    required_proficiency: str
    student_proficiency: Optional[str] = None
    required_level_val: int
    student_level_val: int
    importance: str
    importance_weight: float
    is_mandatory: bool
    is_verified: bool = False
    evidence_count: int = 0
    suggested_improvement: Optional[str] = None
    recommended_catalog_item_id: Optional[int] = None
    recommended_resource_url: Optional[str] = None


class PlacementReadinessResponse(BaseModel):
    student_id: int
    student_name: str
    srn: Optional[str] = None
    semester: int
    cgpa: float
    attendance_percentage: float
    active_backlogs: int
    target_role: CareerRoleResponse
    readiness_score: float  # 0.0 - 100.0%
    skill_coverage_percentage: float
    mandatory_skills_met: bool
    skills_matched_count: int
    skills_below_proficiency_count: int
    skills_missing_count: int
    skills_unverified_count: int
    total_role_skills_count: int
    skill_gaps: List[SkillGapItem]
    certification_progress: Dict[str, Any]
    project_experience: Dict[str, Any]
    readiness_tier: str  # READY, NEAR_READY, DEVELOPING, EARLY_STAGE
    disclaimer: str = "Internal prototype readiness indicator. Does not guarantee corporate hiring or selection."
    calculated_at: datetime


# --- Placement Opportunities & Applications Schemas ---
class OpportunityRequirementItem(BaseModel):
    skill_id: Optional[int] = None
    skill_name: str
    min_proficiency: str = "Intermediate"
    is_mandatory: bool = True


class PlacementOpportunityBase(BaseModel):
    company_name: str
    title: str
    opportunity_type: str = "JOB"  # JOB, INTERNSHIP
    role_id: Optional[int] = None
    location: str = "Bangalore"
    work_mode: str = "HYBRID"
    ctc_stipend: str
    min_cgpa: float = 6.5
    max_backlogs: int = 0
    min_attendance: float = 75.0
    eligible_departments: List[str] = ["CSE", "AI_DS", "ECE"]
    eligible_semesters: List[int] = [6, 7, 8]
    application_deadline: date
    open_positions: int = 5
    description: Optional[str] = None
    status: str = "OPEN"


class PlacementOpportunityCreate(PlacementOpportunityBase):
    requirements: List[OpportunityRequirementItem] = []


class PlacementOpportunityResponse(PlacementOpportunityBase):
    id: int
    role_title: Optional[str] = None
    requirements: List[Dict[str, Any]] = []
    application_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityMatchForStudent(PlacementOpportunityResponse):
    is_eligible: bool
    eligibility_breakdown: Dict[str, Any]
    readiness_score: float
    application_status: Optional[str] = None  # APPLIED, SHORTLISTED, etc. or None


class StudentApplicationCreate(BaseModel):
    opportunity_id: int
    resume_url: Optional[str] = None
    cover_notes: Optional[str] = None


class StudentApplicationStatusUpdate(BaseModel):
    status: str  # APPLIED, SHORTLISTED, INTERVIEW_SCHEDULED, OFFERED, REJECTED, WITHDRAWN
    reviewer_notes: Optional[str] = None


class StudentApplicationResponse(BaseModel):
    id: int
    opportunity_id: int
    opportunity_title: str
    company_name: str
    opportunity_type: str
    ctc_stipend: str
    location: str
    deadline: date
    student_id: int
    student_name: str
    student_srn: Optional[str] = None
    status: str
    applied_at: datetime
    resume_url: Optional[str] = None
    cover_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    readiness_score_at_application: float

    class Config:
        from_attributes = True
