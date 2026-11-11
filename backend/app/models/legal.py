"""Global ACEDRA legal documents, users' acceptances of them, and public contact messages.

These are platform-level records (no tenant scoping): legal terms are written and published by the
ACEDRA team only, and university administrators cannot change them.
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.clock import utcnow
from app.core.database import Base

LEGAL_DOCUMENT_TYPES = ("terms", "privacy", "cookies")
# Documents a person must accept before using a workspace.
ACCEPTANCE_REQUIRED_TYPES = ("terms", "privacy")


class LegalDocumentStatus:
    DRAFT = "draft"          # editable
    APPROVED = "approved"    # content frozen, approval recorded, awaiting publication
    PUBLISHED = "published"  # visible to the public; the newest one in force is current
    ALL = (DRAFT, APPROVED, PUBLISHED)


class LegalDocument(Base):
    __tablename__ = "legal_documents"
    __table_args__ = (UniqueConstraint("doc_type", "version", name="uq_legal_documents_type_version"),)

    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String(30), nullable=False, index=True)
    version = Column(String(40), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    change_summary = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default=LegalDocumentStatus.DRAFT, index=True)
    effective_date = Column(Date, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_note = Column(String(500), nullable=True)
    published_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    approved_by = relationship("User", foreign_keys=[approved_by_id])
    published_by = relationship("User", foreign_keys=[published_by_id])


class LegalAcceptance(Base):
    """One person's acceptance of one published document version (never inferred from signing in)."""

    __tablename__ = "legal_acceptances"
    __table_args__ = (UniqueConstraint("user_id", "document_id", name="uq_legal_acceptances_user_document"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    university_id = Column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("legal_documents.id", ondelete="RESTRICT"), nullable=False)
    doc_type = Column(String(30), nullable=False)
    version = Column(String(40), nullable=False)
    context = Column(String(30), nullable=False)  # invitation | sign_in
    accepted_at = Column(DateTime, default=utcnow, nullable=False)

    document = relationship("LegalDocument")


class ContactMessage(Base):
    """A message sent through the public contact form. Read by the ACEDRA team in the platform workspace."""

    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    institution = Column(String(255), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="new", index=True)  # new | in_progress | closed
    handled_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
