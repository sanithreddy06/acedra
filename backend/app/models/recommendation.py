from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class RecommendationCatalogue(Base, TimestampMixin):
    __tablename__ = "recommendation_catalogue"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    # Categories: SUBJECT_IMPROVEMENT, STUDY_RESOURCES, LEARNING_COURSES, PROGRAMMING_PRACTICE,
    # TECHNICAL_CERTIFICATIONS, SOFT_SKILLS, EXAMINATION_PREPARATION, PROJECT_SUGGESTIONS,
    # INTERNSHIP_PREPARATION, PLACEMENT_PREPARATION, HACKATHON_PARTICIPATION
    description = Column(Text, nullable=False)
    required_skill = Column(String(100), nullable=True, index=True)
    target_audience = Column(String(150), nullable=True)
    difficulty_level = Column(String(30), default="Intermediate", nullable=False)  # Beginner, Intermediate, Advanced
    resource_url = Column(String(500), nullable=True)
    provider = Column(String(100), nullable=True)  # Coursera, LeetCode, NPTEL, AWS Academy, Internal Academic Portal
    estimated_duration = Column(String(50), nullable=True)  # e.g., "4 Weeks", "20 Hours"
    eligibility_conditions = Column(JSON, nullable=True)  # e.g., {"target_skills": ["Python"], "career_goals": ["AI/ML Engineer"]}
    expected_learning_outcome = Column(Text, nullable=True)
    status = Column(String(30), default="Active", nullable=False)  # Active, Inactive, Archived
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    resources = relationship("RecommendationResource", back_populates="catalogue", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="catalogue")


class RecommendationResource(Base, TimestampMixin):
    __tablename__ = "recommendation_resources"

    id = Column(Integer, primary_key=True, index=True)
    catalogue_id = Column(Integer, ForeignKey("recommendation_catalogue.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)  # Course, Practice, Documentation, Video, Template, Exam
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    platform = Column(String(100), nullable=True)
    is_free = Column(Boolean, default=True, nullable=False)
    duration_minutes = Column(Integer, nullable=True)

    # Relationships
    catalogue = relationship("RecommendationCatalogue", back_populates="resources")


class Recommendation(Base, TimestampMixin):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    catalogue_id = Column(Integer, ForeignKey("recommendation_catalogue.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    reason = Column(Text, nullable=False)  # Why it is recommended
    gap_type = Column(String(50), nullable=False, index=True)  # ACADEMIC_WEAKNESS, SKILL_DEFICIT, CAREER_ALIGNMENT, ATTENDANCE_SUPPORT, INTEREST_EXPLORATION
    gap_detail = Column(String(255), nullable=True)  # Related academic or skill gap
    expected_outcome = Column(Text, nullable=True)
    priority = Column(String(20), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    resource_url = Column(String(500), nullable=True)
    suggested_completion_time = Column(String(50), nullable=True)
    status = Column(String(30), default="SUGGESTED", nullable=False, index=True)
    # Statuses: SUGGESTED, ACCEPTED, IN_PROGRESS, COMPLETED, REJECTED, EXPIRED
    source = Column(String(30), default="SYSTEM", nullable=False)  # SYSTEM, MENTOR, FACULTY
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    mentor_approval_status = Column(String(30), default="APPROVED", nullable=False)  # PENDING, APPROVED, REJECTED
    mentor_guidance_notes = Column(Text, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(255), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="recommendations")
    catalogue = relationship("RecommendationCatalogue", back_populates="recommendations")
    created_by = relationship("User", foreign_keys=[created_by_id])
    progress_logs = relationship("RecommendationProgress", back_populates="recommendation", cascade="all, delete-orphan", order_by="desc(RecommendationProgress.created_at)")
    feedback = relationship("RecommendationFeedback", back_populates="recommendation", cascade="all, delete-orphan", uselist=False)


class RecommendationProgress(Base, TimestampMixin):
    __tablename__ = "recommendation_progress"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False)  # ACCEPTED, IN_PROGRESS, COMPLETED
    percent_complete = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    hours_spent = Column(Float, default=0.0, nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="progress_logs")
    updated_by = relationship("User", foreign_keys=[updated_by_id])


class RecommendationFeedback(Base, TimestampMixin):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1 to 5
    helpful = Column(Boolean, default=True, nullable=False)
    relevance_score = Column(Integer, default=5, nullable=False)  # 1 to 5
    comments = Column(Text, nullable=True)
    outcome_achieved = Column(Boolean, default=False, nullable=False)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="feedback")
    student = relationship("Student")
