import json
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    require_role,
)
from app.core.config import settings
from app.core.database import get_db
from app.models.ai_assistant import (
    AssistantMode,
    Conversation,
    Document,
    DocumentAccessPermission,
    DocumentCategory,
)
from app.models.user import User
from app.schemas.ai_assistant import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationFeedbackCreate,
    ConversationFeedbackResponse,
    ConversationResponse,
    DocumentCreate,
    DocumentDetailResponse,
    DocumentResponse,
    MessageCreate,
    MessageResponse,
    SuggestedQuestion,
)
from app.services.ai_assistant_service import AIAssistantService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/ai", tags=["Conversational AI Assistant & RAG"])


# =============================================================================
# 1. Suggested Exploration Questions
# =============================================================================

@router.get("/status")
def assistant_status(current_user: User = Depends(get_current_active_user)):
    """Tell the interface exactly what is powering the assistant, so it can label answers honestly."""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL if settings.LLM_PROVIDER != "none" else None,
        "llm_configured": settings.LLM_PROVIDER != "none",
        "retrieval": EmbeddingService.provider_label(),
        "semantic_retrieval": settings.EMBEDDING_PROVIDER != "lexical",
        "personal_mode_available": True,
    }


@router.get("/suggested-questions", response_model=List[SuggestedQuestion])
def get_suggested_questions(
    mode: str = Query("PUBLIC_MODE_A", description="PUBLIC_MODE_A or PERSONAL_MODE_B")
):
    """Retrieve categorized quick-launch prompts based on the assistant mode."""
    return AIAssistantService.get_suggested_questions(mode)


# =============================================================================
# 2. Conversation Lifecycle (Public & Authenticated)
# =============================================================================

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Start or join a conversation session.
    Mode A is public. Mode B requires an authenticated user.
    """
    if payload.mode not in (AssistantMode.PUBLIC_MODE_A.value, AssistantMode.PERSONAL_MODE_B.value):
        raise HTTPException(status_code=422, detail="Unknown assistant mode")

    conv = AIAssistantService.get_or_create_conversation(
        db=db,
        session_id=payload.session_id,
        mode=payload.mode,
        user=current_user,
        title=payload.title,
    )
    return conv


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List recent conversations belonging to the user or session."""
    return AIAssistantService.list_user_conversations(
        db=db,
        user=current_user,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve conversation messages and citations."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id,
                                         Conversation.user_id == current_user.id).first()
    if not conv:  # other users' conversations are indistinguishable from missing ones
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation history."""
    AIAssistantService.delete_conversation(db, conversation_id, current_user)
    return {"message": "Conversation deleted successfully", "id": conversation_id}


# =============================================================================
# 3. Message Dispatch & Streaming Response
# =============================================================================

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI Assistant.
    Retrieves grounded passages and returns the assistant response with source citations.
    """
    _, assistant_msg = AIAssistantService.send_message(
        db=db,
        conversation_id=conversation_id,
        user_message=payload.content,
        current_user=current_user,
        target_student_id=payload.student_id,
    )
    return assistant_msg


@router.post("/conversations/{conversation_id}/messages/stream")
def stream_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Yields chunks incrementally, followed by citations metadata event.
    """
    _, assistant_msg = AIAssistantService.send_message(
        db=db,
        conversation_id=conversation_id,
        user_message=payload.content,
        current_user=current_user,
        target_student_id=payload.student_id,
    )

    async def event_generator():
        # Stream text chunks
        async for chunk in LLMService.stream_response_tokens(assistant_msg.content):
            data = json.dumps({"type": "chunk", "content": chunk})
            yield f"data: {data}\n\n"

        # Final event containing full message payload and citations
        final_payload = {
            "type": "done",
            "message_id": assistant_msg.id,
            "citations": assistant_msg.sources_json or [],
            "processing_time_ms": assistant_msg.processing_time_ms,
        }
        yield f"data: {json.dumps(final_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/messages/{message_id}/feedback", response_model=ConversationFeedbackResponse)
def submit_message_feedback(
    message_id: int,
    payload: ConversationFeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Record user satisfaction feedback (Helpful / Unhelpful) for a message."""
    return AIAssistantService.record_feedback(
        db=db,
        message_id=message_id,
        is_helpful=payload.is_helpful,
        feedback_text=payload.feedback_text,
        user=current_user,
    )


# =============================================================================
# 4. RAG Document Knowledge Base (Admin & Institutional Management)
# =============================================================================

@router.get("/documents", response_model=List[DocumentResponse])
def list_documents(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List university documents the caller's role may read."""
    docs = AIAssistantService.list_documents(db=db, category=category, search=search, limit=200)
    allowed = AIAssistantService.allowed_permissions(current_user.role)
    return [d for d in docs if d.access_permission in allowed]


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def get_document_details(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """View document details including its indexed text chunks (permission-checked)."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or doc.access_permission not in AIAssistantService.allowed_permissions(current_user.role):
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(DocumentCategory.GENERAL_POLICY.value),
    description: Optional[str] = Form(None),
    access_permission: str = Form(DocumentAccessPermission.PUBLIC.value),
    current_user: User = Depends(require_role("admin", "placement_officer")),
    db: Session = Depends(get_db),
):
    """
    Upload and index a campus document (PDF, DOCX, TXT, MD) into pgvector / semantic embeddings.
    Accessible to Administrators and authorized campus officers.
    """
    filename = file.filename or "uploaded_document.txt"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_exts = {"pdf", "docx", "txt", "md"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Only PDF, DOCX, TXT, and Markdown files are accepted.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Document exceeds the {settings.MAX_UPLOAD_MB} MB limit.")
    # Verify content matches the declared type (magic bytes) — never trust the filename alone.
    if ext == "pdf" and not file_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File content is not a valid PDF.")
    if ext == "docx" and not file_bytes.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="File content is not a valid DOCX document.")
    if ext in ("txt", "md"):
        try:
            file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Text documents must be UTF-8 encoded.") from None
    if category not in {c.value for c in DocumentCategory}:
        raise HTTPException(status_code=422, detail="Unknown document category")
    if access_permission not in {p.value for p in DocumentAccessPermission}:
        raise HTTPException(status_code=422, detail="Unknown access level")

    return AIAssistantService.process_and_index_document(
        db=db,
        title=title,
        category=category,
        file_bytes=file_bytes,
        file_name=filename,
        file_type=ext,
        description=description,
        access_permission=access_permission,
        created_by_user_id=current_user.id,
    )


@router.post("/documents/text", response_model=DocumentResponse)
def create_text_document(
    payload: DocumentCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Add a raw markdown or policy text document directly into the knowledge base."""
    text_bytes = (payload.content_raw or "").encode("utf-8")
    return AIAssistantService.process_and_index_document(
        db=db,
        title=payload.title,
        category=payload.category,
        file_bytes=text_bytes,
        file_name=f"{payload.title.lower().replace(' ', '_')}.md",
        file_type="md",
        description=payload.description,
        access_permission=payload.access_permission,
        created_by_user_id=current_user.id,
    )


@router.post("/documents/{document_id}/reindex", response_model=DocumentResponse)
def reindex_document(
    document_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Re-chunk and regenerate vector embeddings for an indexed document."""
    return AIAssistantService.reindex_document(db=db, document_id=document_id)


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Delete a document and its associated vector chunks from the RAG store."""
    AIAssistantService.delete_document(db, document_id)
    return {"message": "Document and chunks successfully deleted", "id": document_id}


@router.get("/rag/search")
def test_rag_search(
    q: str = Query(..., description="Query string to search in RAG knowledge base"),
    top_k: int = Query(4, ge=1, le=10),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Directly test vector semantic retrieval and view relevance scores and chunks."""
    user_role = current_user.role
    passages = AIAssistantService.search_relevant_passages(
        db=db,
        query=q,
        user_role=user_role,
        top_k=top_k,
        min_threshold=0.25,
    )
    return {
        "query": q,
        "role_evaluated": user_role,
        "results_count": len(passages),
        "results": passages,
    }
