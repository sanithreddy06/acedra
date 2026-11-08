from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------
# Catalogue Resource Schemas
# ----------------------------------------------------
class RecommendationResourceBase(BaseModel):
    resource_type: str = Field(..., description="Course, Practice, Documentation, Video, Template, Exam")
    title: str = Field(..., max_length=200)
    url: str = Field(..., max_length=500)
    platform: Optional[str] = None
    is_free: bool = True
    duration_minutes: Optional[int] = None


class RecommendationResourceCreate(RecommendationResourceBase):
    pass


class RecommendationResourceOut(RecommendationResourceBase):
    id: int
    catalogue_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Recommendation Catalogue Schemas
# ----------------------------------------------------
class CatalogueItemBase(BaseModel):
    title: str = Field(..., max_length=200)
    category: str = Field(..., description="SUBJECT_IMPROVEMENT, STUDY_RESOURCES, LEARNING_COURSES, PROGRAMMING_PRACTICE, TECHNICAL_CERTIFICATIONS, SOFT_SKILLS, EXAMINATION_PREPARATION, PROJECT_SUGGESTIONS, INTERNSHIP_PREPARATION, PLACEMENT_PREPARATION, HACKATHON_PARTICIPATION")
    description: str
    required_skill: Optional[str] = None
    target_audience: Optional[str] = None
    difficulty_level: str = "Intermediate"
    resource_url: Optional[str] = None
    provider: Optional[str] = None
    estimated_duration: Optional[str] = None
    eligibility_conditions: Optional[Dict[str, Any]] = None
    expected_learning_outcome: Optional[str] = None
    status: str = "Active"


class CatalogueItemCreate(CatalogueItemBase):
    resources: Optional[List[RecommendationResourceCreate]] = None


class CatalogueItemUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    required_skill: Optional[str] = None
    target_audience: Optional[str] = None
    difficulty_level: Optional[str] = None
    resource_url: Optional[str] = None
    provider: Optional[str] = None
    estimated_duration: Optional[str] = None
    eligibility_conditions: Optional[Dict[str, Any]] = None
    expected_learning_outcome: Optional[str] = None
    status: Optional[str] = None


class CatalogueItemOut(CatalogueItemBase):
    id: int
    created_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resources: List[RecommendationResourceOut] = []

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Progress & Feedback Schemas
# ----------------------------------------------------
class RecommendationProgressCreate(BaseModel):
    status: str = Field("IN_PROGRESS", description="ACCEPTED, IN_PROGRESS, COMPLETED")
    percent_complete: int = Field(0, ge=0, le=100)
    notes: Optional[str] = None
    hours_spent: float = 0.0


class RecommendationProgressOut(BaseModel):
    id: int
    recommendation_id: int
    status: str
    percent_complete: int
    notes: Optional[str] = None
    hours_spent: float
    updated_by_id: int
    updated_by_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationFeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    helpful: bool = True
    relevance_score: int = Field(5, ge=1, le=5)
    comments: Optional[str] = None
    outcome_achieved: bool = False


class RecommendationFeedbackOut(BaseModel):
    id: int
    recommendation_id: int
    student_id: int
    rating: int
    helpful: bool
    relevance_score: int
    comments: Optional[str] = None
    outcome_achieved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Personalized Recommendation Schemas
# ----------------------------------------------------
class MentorSuggestionCreate(BaseModel):
    student_id: int
    catalogue_id: Optional[int] = None
    title: str = Field(..., max_length=200)
    category: str
    reason: str
    gap_type: str = "CAREER_ALIGNMENT"
    gap_detail: Optional[str] = None
    expected_outcome: Optional[str] = None
    priority: str = "HIGH"
    resource_url: Optional[str] = None
    suggested_completion_time: Optional[str] = None
    mentor_guidance_notes: Optional[str] = None


class RecommendationRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=2)


class RecommendationGuidanceRequest(BaseModel):
    guidance_notes: str = Field(..., min_length=2)


class RecommendationOut(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    student_department: Optional[str] = None
    catalogue_id: Optional[int] = None
    title: str
    category: str
    reason: str
    gap_type: str
    gap_detail: Optional[str] = None
    expected_outcome: Optional[str] = None
    priority: str
    resource_url: Optional[str] = None
    suggested_completion_time: Optional[str] = None
    status: str
    source: str
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    mentor_approval_status: str
    mentor_guidance_notes: Optional[str] = None
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    progress_logs: List[RecommendationProgressOut] = []
    feedback: Optional[RecommendationFeedbackOut] = None

    model_config = ConfigDict(from_attributes=True)


# ----------------------------------------------------
# Student Learning Path & Plans
# ----------------------------------------------------
class StudentCareerProfileUpdate(BaseModel):
    career_goals: List[str]
    interests: List[str]


class StudentLearningPathOut(BaseModel):
    student_id: int
    student_name: str
    roll_number: str
    department: str
    current_semester: int
    career_goals: List[str]
    interests: List[str]
    academic_improvement_plan: List[RecommendationOut]
    career_development_plan: List[RecommendationOut]
    total_recommendations: int
    accepted_count: int
    in_progress_count: int
    completed_count: int
    summary_explanation: str
