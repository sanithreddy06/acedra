import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.ai_assistant import (
    Document,
    DocumentChunk,
    DocumentAccessRule,
    Conversation,
    Message,
    ConversationFeedback,
    DocumentCategory,
    DocumentAccessPermission,
    AssistantMode,
    MessageRole,
)
from app.models.user import User
from app.models.profile import Student
from app.schemas.ai_assistant import (
    DocumentCreate,
    ConversationCreate,
    MessageCreate,
    ConversationFeedbackCreate,
    SourceCitation,
    SuggestedQuestion,
)
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.student_context_service import StudentContextService


class AIAssistantService:
    """
    Core conversational AI orchestration service.
    Manages RAG document indexing, access control, conversations, and dual-mode generation.
    """

    # -------------------------------------------------------------
    # Document RAG Indexing & Management
    # -------------------------------------------------------------

    @staticmethod
    def process_and_index_document(
        db: Session,
        title: str,
        category: str,
        file_bytes: bytes,
        file_name: str,
        file_type: str,
        description: Optional[str] = None,
        access_permission: str = DocumentAccessPermission.PUBLIC.value,
        created_by_user_id: Optional[int] = None,
    ) -> Document:
        """
        Full RAG pipeline:
        File bytes -> Text extraction -> Chunking -> Embedding generation -> DB persistence.
        """
        # Calculate SHA-256 hash to prevent identical duplicate uploads
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Extract text pages/sections
        sections = EmbeddingService.extract_text(file_bytes, file_type, file_name)
        all_raw_text = file_bytes.decode("utf-8", errors="ignore") if file_type in ["md", "txt", "markdown"] else "\n\n".join(s["text"] for s in sections)

        # Chunk text
        chunks_data = EmbeddingService.chunk_text(sections, target_chunk_size=550, overlap=80)

        # Create Document record
        doc = Document(
            title=title,
            category=category,
            description=description,
            file_name=file_name,
            file_type=file_type.lower().replace(".", ""),
            file_size_bytes=len(file_bytes),
            file_hash=file_hash,
            content_raw=all_raw_text,
            chunk_count=len(chunks_data),
            access_permission=access_permission,
            is_active=True,
            indexed_at=datetime.utcnow(),
            created_by=created_by_user_id,
        )
        db.add(doc)
        db.flush()

        # Add default access rules based on permission
        if access_permission == DocumentAccessPermission.PUBLIC.value:
            for role in ["public", "student", "faculty", "mentor", "admin", "placement_officer"]:
                db.add(DocumentAccessRule(document_id=doc.id, role_name=role, can_read=True))
        elif access_permission == DocumentAccessPermission.AUTHENTICATED_STUDENT.value:
            for role in ["student", "faculty", "mentor", "admin", "placement_officer"]:
                db.add(DocumentAccessRule(document_id=doc.id, role_name=role, can_read=True))
        elif access_permission == DocumentAccessPermission.FACULTY_ONLY.value:
            for role in ["faculty", "admin"]:
                db.add(DocumentAccessRule(document_id=doc.id, role_name=role, can_read=True))
        else:
            db.add(DocumentAccessRule(document_id=doc.id, role_name="admin", can_read=True, can_edit=True))

        # Generate embeddings and store chunks
        for c in chunks_data:
            text_to_embed = f"{c.get('section_heading', '')} {c['content']}".strip()
            emb = EmbeddingService.generate_embedding(text_to_embed)
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                token_count=c["token_count"],
                section_heading=c.get("section_heading"),
                page_number=c.get("page_number", 1),
                metadata_json={
                    "document_title": title,
                    "category": category,
                    "access_permission": access_permission,
                },
                embedding_vector=emb,
            )
            db.add(chunk)

        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def reindex_document(db: Session, document_id: int) -> Document:
        """Re-chunks and re-generates embeddings for an existing document."""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete old chunks
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

        # Re-extract and re-chunk from raw content
        raw = doc.content_raw or ""
        sections = EmbeddingService.extract_text(raw.encode("utf-8"), doc.file_type, doc.file_name)
        chunks_data = EmbeddingService.chunk_text(sections, target_chunk_size=550, overlap=80)

        for c in chunks_data:
            text_to_embed = f"{c.get('section_heading', '')} {c['content']}".strip()
            emb = EmbeddingService.generate_embedding(text_to_embed)
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                token_count=c["token_count"],
                section_heading=c.get("section_heading"),
                page_number=c.get("page_number", 1),
                metadata_json={
                    "document_title": doc.title,
                    "category": doc.category,
                    "access_permission": doc.access_permission,
                },
                embedding_vector=emb,
            )
            db.add(chunk)

        doc.chunk_count = len(chunks_data)
        doc.indexed_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def delete_document(db: Session, document_id: int) -> bool:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        db.delete(doc)
        db.commit()
        return True

    @staticmethod
    def list_documents(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Document]:
        query = db.query(Document).filter(Document.is_active == True)
        if category:
            query = query.filter(Document.category == category)
        if search:
            query = query.filter(Document.title.ilike(f"%{search}%"))
        return query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def search_relevant_passages(
        db: Session,
        query: str,
        user_role: str = "public",
        top_k: int = 4,
        min_threshold: float = 0.28,
    ) -> List[Dict[str, Any]]:
        """
        RAG similarity search:
        1. Query chunks joining Document with access permission filtering.
        2. Score via EmbeddingService.rank_chunks.
        3. Return top-k passages with scores and metadata.
        """
        # Role-based access permission filter
        allowed_permissions = [DocumentAccessPermission.PUBLIC.value]
        if user_role in ["student", "faculty", "mentor", "admin", "placement_officer"]:
            allowed_permissions.append(DocumentAccessPermission.AUTHENTICATED_STUDENT.value)
        if user_role in ["faculty", "admin"]:
            allowed_permissions.append(DocumentAccessPermission.FACULTY_ONLY.value)
        if user_role == "admin":
            allowed_permissions.append(DocumentAccessPermission.ADMIN_ONLY.value)

        chunks = (
            db.query(DocumentChunk, Document.title, Document.category)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(
                Document.is_active == True,
                Document.access_permission.in_(allowed_permissions),
            )
            .all()
        )

        if not chunks:
            return []

        # Convert to dictionary representation for ranking
        items_to_rank: List[Dict[str, Any]] = []
        for chunk, doc_title, category in chunks:
            items_to_rank.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "document_title": doc_title,
                "category": category,
                "content": chunk.content,
                "section_heading": chunk.section_heading,
                "page_number": chunk.page_number,
                "embedding_vector": chunk.embedding_vector,
            })

        ranked = EmbeddingService.rank_chunks(
            query=query,
            chunks_with_embeddings=items_to_rank,
            top_k=top_k,
            min_threshold=min_threshold,
        )

        results = []
        for item, score in ranked:
            results.append({
                "chunk": item,
                "score": score,
                "document_title": item["document_title"],
                "category": item["category"],
            })
        return results

    # -------------------------------------------------------------
    # Conversation Management
    # -------------------------------------------------------------

    @staticmethod
    def get_or_create_conversation(
        db: Session,
        session_id: Optional[str] = None,
        mode: str = AssistantMode.PUBLIC_MODE_A.value,
        user: Optional[User] = None,
        title: Optional[str] = "New Conversation",
    ) -> Conversation:
        if session_id:
            conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if conv:
                return conv

        new_session_id = session_id or str(uuid.uuid4())
        conv = Conversation(
            session_id=new_session_id,
            user_id=user.id if user else None,
            mode=mode,
            title=title or ("Personal Assistant" if mode == AssistantMode.PERSONAL_MODE_B.value else "Campus Assistant"),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @staticmethod
    def list_user_conversations(
        db: Session,
        user: Optional[User] = None,
        session_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Conversation]:
        query = db.query(Conversation)
        if user:
            query = query.filter(Conversation.user_id == user.id)
        elif session_id:
            query = query.filter(Conversation.session_id == session_id)
        else:
            return []

        conversations = query.order_by(desc(Conversation.updated_at)).limit(limit).all()
        # Annotate with message count and latest message preview
        for c in conversations:
            msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
            latest = db.query(Message).filter(Message.conversation_id == c.id).order_by(desc(Message.created_at)).first()
            setattr(c, "messages_count", msg_count)
            setattr(c, "latest_message", latest.content[:60] if latest else None)
        return conversations

    @staticmethod
    def delete_conversation(db: Session, conversation_id: int, user: Optional[User] = None) -> bool:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if user and conv.user_id and conv.user_id != user.id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Unauthorized to delete this conversation")
        db.delete(conv)
        db.commit()
        return True

    # -------------------------------------------------------------
    # Message Dispatch & Generation
    # -------------------------------------------------------------

    @staticmethod
    def send_message(
        db: Session,
        conversation_id: int,
        user_message: str,
        current_user: Optional[User] = None,
        target_student_id: Optional[int] = None,
    ) -> Tuple[Message, Message]:
        """
        Processes user query, conducts RAG / personal context grounding,
        invokes LLMService, and persists both User and Assistant messages.
        """
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 1. Save User Message
        user_msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER.value,
            content=user_message,
            token_count=len(user_message.split()),
        )
        db.add(user_msg)
        db.flush()

        # Update conversation title if still default
        if conv.title == "New Conversation" or conv.title == "Campus Assistant" or conv.title == "Personal Assistant":
            clean_title = user_message[:45].strip()
            if len(user_message) > 45:
                clean_title += "..."
            conv.title = clean_title

        conv.updated_at = datetime.utcnow()

        # 2. Gather Grounding Context
        user_role = current_user.role if current_user else "public"
        retrieved_passages = AIAssistantService.search_relevant_passages(
            db=db,
            query=user_message,
            user_role=user_role,
            top_k=4,
            min_threshold=0.28,
        )

        student_context: Optional[Dict[str, Any]] = None
        if conv.mode == AssistantMode.PERSONAL_MODE_B.value:
            # Mode B requires verified student context
            student_context = StudentContextService.get_authorized_student_context(
                db=db,
                current_user=current_user,
                target_student_id=target_student_id,
            )

        # 3. Invoke LLM Service
        history = [
            {"role": m.role, "content": m.content}
            for m in conv.messages[-6:]
        ]

        llm_result = LLMService.generate_response(
            user_message=user_message,
            mode=conv.mode,
            retrieved_passages=retrieved_passages,
            student_context=student_context,
            conversation_history=history,
        )

        # 4. Save Assistant Message
        assistant_msg = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT.value,
            content=llm_result["content"],
            sources_json=llm_result.get("citations", []),
            token_count=llm_result.get("token_count", 0),
            processing_time_ms=llm_result.get("processing_time_ms", 0.0),
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return user_msg, assistant_msg

    # -------------------------------------------------------------
    # Feedback & Suggested Questions
    # -------------------------------------------------------------

    @staticmethod
    def record_feedback(
        db: Session,
        message_id: int,
        is_helpful: bool,
        feedback_text: Optional[str] = None,
        user: Optional[User] = None,
    ) -> ConversationFeedback:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")

        feedback = ConversationFeedback(
            conversation_id=msg.conversation_id,
            message_id=msg.id,
            user_id=user.id if user else None,
            is_helpful=is_helpful,
            feedback_text=feedback_text,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def get_suggested_questions(mode: str) -> List[SuggestedQuestion]:
        """Provides quick-launch exploration prompts for both modes."""
        if mode == AssistantMode.PERSONAL_MODE_B.value:
            return [
                SuggestedQuestion(
                    category="Attendance",
                    prompt="What is my attendance breakdown across all subjects?",
                    mode="PERSONAL_MODE_B",
                ),
                SuggestedQuestion(
                    category="Academic Progress",
                    prompt="Summarize my CGPA, CIA test average, and backlog status.",
                    mode="PERSONAL_MODE_B",
                ),
                SuggestedQuestion(
                    category="Career Readiness",
                    prompt="What skills am I missing for my target Software Developer role?",
                    mode="PERSONAL_MODE_B",
                ),
                SuggestedQuestion(
                    category="Study Plan",
                    prompt="Generate a personalized weekly study schedule based on my current academic metrics.",
                    mode="PERSONAL_MODE_B",
                ),
            ]
        else:
            return [
                SuggestedQuestion(
                    category="Campus Policy",
                    prompt="What are the official REVA University attendance requirements and condonation rules?",
                    mode="PUBLIC_MODE_A",
                ),
                SuggestedQuestion(
                    category="Examinations",
                    prompt="What is the continuous internal assessment (CIA) passing threshold?",
                    mode="PUBLIC_MODE_A",
                ),
                SuggestedQuestion(
                    category="Placements",
                    prompt="What are the eligibility criteria and backlog rules for campus recruitment drives?",
                    mode="PUBLIC_MODE_A",
                ),
                SuggestedQuestion(
                    category="Programming Help",
                    prompt="How do I implement binary search in Python with optimal time complexity?",
                    mode="PUBLIC_MODE_A",
                ),
                SuggestedQuestion(
                    category="Interview Prep",
                    prompt="Give me key preparation advice for full-stack engineering technical interviews.",
                    mode="PUBLIC_MODE_A",
                ),
            ]
