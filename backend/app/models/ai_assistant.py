import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.clock import utcnow
from app.core.database import Base
from app.core.tenancy import TenantMixin
from app.models.base import TimestampMixin


class DocumentCategory(str, enum.Enum):
    ACADEMIC_REGULATIONS = "ACADEMIC_REGULATIONS"
    ATTENDANCE_GUIDELINES = "ATTENDANCE_GUIDELINES"
    EXAMINATION_GUIDELINES = "EXAMINATION_GUIDELINES"
    DEPARTMENT_INFO = "DEPARTMENT_INFO"
    COURSE_INFO = "COURSE_INFO"
    INTERNSHIP_GUIDELINES = "INTERNSHIP_GUIDELINES"
    PLACEMENT_GUIDELINES = "PLACEMENT_GUIDELINES"
    CAMPUS_HANDBOOK = "CAMPUS_HANDBOOK"
    GENERAL_POLICY = "GENERAL_POLICY"


class DocumentAccessPermission(str, enum.Enum):
    PUBLIC = "PUBLIC"
    AUTHENTICATED_STUDENT = "AUTHENTICATED_STUDENT"
    FACULTY_ONLY = "FACULTY_ONLY"
    ADMIN_ONLY = "ADMIN_ONLY"


class AssistantMode(str, enum.Enum):
    PUBLIC_MODE_A = "PUBLIC_MODE_A"
    PERSONAL_MODE_B = "PERSONAL_MODE_B"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Document(Base, TimestampMixin, TenantMixin):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, default=DocumentCategory.GENERAL_POLICY.value, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, md
    file_size_bytes = Column(Integer, default=0)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    content_raw = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    access_permission = Column(String(50), nullable=False, default=DocumentAccessPermission.PUBLIC.value, index=True)
    is_active = Column(Boolean, default=True, index=True)
    indexed_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan", order_by="DocumentChunk.chunk_index")
    access_rules = relationship("DocumentAccessRule", back_populates="document", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class DocumentChunk(Base, TenantMixin):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    section_heading = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    metadata_json = Column(JSON, default=dict)
    embedding_vector = Column(JSON, nullable=True)  # List of floats for cosine similarity
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")


class DocumentAccessRule(Base, TimestampMixin, TenantMixin):
    __tablename__ = "document_access_rules"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    role_name = Column(String(50), nullable=False)  # student, faculty, mentor, admin, placement_officer, public
    can_read = Column(Boolean, default=True)
    can_edit = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="access_rules")
    department = relationship("Department")


class Conversation(Base, TimestampMixin, TenantMixin):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    mode = Column(String(50), nullable=False, default=AssistantMode.PUBLIC_MODE_A.value, index=True)
    title = Column(String(255), nullable=False, default="New Conversation")
    is_pinned = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    feedback_entries = relationship("ConversationFeedback", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, TenantMixin):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default=MessageRole.USER.value)
    content = Column(Text, nullable=False)
    sources_json = Column(JSON, default=list)  # Citations list: [{"document_id", "document_title", "section", "page", "score"}]
    token_count = Column(Integer, default=0)
    processing_time_ms = Column(Float, default=0.0)
    # "llm" when produced by the configured model, "offline_fallback" for extractive/template output
    generation_mode = Column(String(30), default="offline_fallback", nullable=False)
    created_at = Column(DateTime, default=utcnow, index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    feedbacks = relationship("ConversationFeedback", back_populates="message", cascade="all, delete-orphan")


class ConversationFeedback(Base, TenantMixin):
    __tablename__ = "conversation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_helpful = Column(Boolean, nullable=False)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="feedback_entries")
    message = relationship("Message", back_populates="feedbacks")
    user = relationship("User")
