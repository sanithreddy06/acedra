from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.ai_assistant import (
    AssistantMode,
    DocumentAccessPermission,
    DocumentCategory,
)


class SourceCitation(BaseModel):
    document_id: int
    document_title: str
    category: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[int] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    snippet: str


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    chunk_index: int
    content: str
    token_count: int
    section_heading: Optional[str] = None
    page_number: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime


class DocumentAccessRuleItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    role_name: str
    can_read: bool = True
    can_edit: bool = False
    department_id: Optional[int] = None


class DocumentBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    category: str = DocumentCategory.GENERAL_POLICY.value
    description: Optional[str] = None
    access_permission: str = DocumentAccessPermission.PUBLIC.value


class DocumentCreate(DocumentBase):
    content_raw: Optional[str] = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    is_active: bool
    indexed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []
    access_rules: List[DocumentAccessRuleItem] = []


class ConversationCreate(BaseModel):
    mode: str = AssistantMode.PUBLIC_MODE_A.value
    title: Optional[str] = "New Conversation"
    session_id: Optional[str] = None


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    student_id: Optional[int] = None  # For Mode B context if mentor/admin or authenticated student


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    sources_json: List[SourceCitation] = []
    generation_mode: str = "offline_fallback"
    token_count: int
    processing_time_ms: float
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    user_id: Optional[int] = None
    mode: str
    title: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    messages_count: Optional[int] = 0
    latest_message: Optional[str] = None


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []


class ConversationFeedbackCreate(BaseModel):
    is_helpful: bool
    feedback_text: Optional[str] = None


class ConversationFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    message_id: int
    user_id: Optional[int] = None
    is_helpful: bool
    feedback_text: Optional[str] = None
    created_at: datetime


class SuggestedQuestion(BaseModel):
    category: str
    prompt: str
    mode: str  # PUBLIC_MODE_A or PERSONAL_MODE_B
