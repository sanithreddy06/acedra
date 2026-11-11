"""Global legal documents: versions, approval and publication, and users' recorded acceptances.

Lifecycle of a document version: ``draft`` (editable) → ``approved`` (content frozen; the approver and
an approval note are recorded) → ``published``. The version *in force* for a type is the newest published
version whose effective date has arrived. Only ACEDRA super administrators can approve or publish;
university administrators have no access to these records.

Acceptance is explicit: a person accepts specific versions (on invitation acceptance or when prompted
after signing in), and each acceptance is stored with user, tenant, document type, version and time.
Signing in never counts as acceptance.

On first use, if a type has no published version at all, the provisional text bundled in
``app/legal_content`` is published as version ``BASELINE_VERSION`` so that the site is never without
terms; that text states plainly that it is a draft awaiting legal review.
"""
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.tenancy import TenantScope, set_session_scope, unscoped
from app.models.legal import (
    ACCEPTANCE_REQUIRED_TYPES,
    LEGAL_DOCUMENT_TYPES,
    LegalAcceptance,
    LegalDocument,
    LegalDocumentStatus,
)
from app.models.user import User
from app.repositories.audit_repo import AuditRepository

CONTENT_DIR = Path(__file__).resolve().parent.parent / "legal_content"
BASELINE_VERSION = "0.1-draft"
TITLES = {"terms": "Terms and Conditions", "privacy": "Privacy Policy", "cookies": "Cookie Policy"}


def _check_type(doc_type: str) -> None:
    if doc_type not in LEGAL_DOCUMENT_TYPES:
        raise HTTPException(status_code=404, detail="Unknown legal document.")


def _published_types(db: Session) -> set:
    with unscoped(db):
        rows = db.query(LegalDocument.doc_type).filter(LegalDocument.status == LegalDocumentStatus.PUBLISHED).distinct()
        return {r[0] for r in rows}


def ensure_baseline_documents(db: Session) -> None:
    """Publish the bundled provisional text for any document type that has never been published.

    Runs in its own short session so that it never commits or rolls back the caller's work, and so that two
    first requests arriving together cannot fail: if another request inserted the baseline first, the unique
    (doc_type, version) constraint rejects the duplicate and this call simply carries on.
    """
    missing = [t for t in LEGAL_DOCUMENT_TYPES if t not in _published_types(db)]
    if not missing:
        return
    seed = Session(bind=db.get_bind())
    set_session_scope(seed, TenantScope(bypass=True))
    try:
        for doc_type in missing:
            now = utcnow()
            seed.add(LegalDocument(
                doc_type=doc_type, version=BASELINE_VERSION, title=TITLES[doc_type],
                body=(CONTENT_DIR / f"{doc_type}.md").read_text(encoding="utf-8"),
                change_summary="Provisional text bundled with the application.",
                status=LegalDocumentStatus.PUBLISHED, effective_date=now.date(),
                approval_note="Bundled provisional draft. Not yet reviewed by a lawyer or approved by a university.",
                approved_at=now, published_at=now,
            ))
            try:
                seed.commit()
            except IntegrityError:
                seed.rollback()  # created concurrently by another request
    finally:
        seed.close()


def current_document(db: Session, doc_type: str, today: Optional[date] = None) -> LegalDocument:
    """The published version in force today (newest effective date that has arrived)."""
    _check_type(doc_type)
    ensure_baseline_documents(db)
    today = today or utcnow().date()
    with unscoped(db):
        doc = (db.query(LegalDocument)
               .filter(LegalDocument.doc_type == doc_type, LegalDocument.status == LegalDocumentStatus.PUBLISHED,
                       LegalDocument.effective_date <= today)
               .order_by(LegalDocument.effective_date.desc(), LegalDocument.published_at.desc())
               .first())
    if doc is None:
        raise HTTPException(status_code=404, detail="No version of this document is in force yet.")
    return doc


def published_history(db: Session, doc_type: str) -> List[LegalDocument]:
    _check_type(doc_type)
    ensure_baseline_documents(db)
    with unscoped(db):
        return (db.query(LegalDocument)
                .filter(LegalDocument.doc_type == doc_type, LegalDocument.status == LegalDocumentStatus.PUBLISHED)
                .order_by(LegalDocument.effective_date.desc(), LegalDocument.published_at.desc()).all())


def required_documents(db: Session) -> List[LegalDocument]:
    return [current_document(db, t) for t in ACCEPTANCE_REQUIRED_TYPES]


def pending_documents(db: Session, user: User) -> List[LegalDocument]:
    """Required documents whose current version this user has not accepted."""
    required = required_documents(db)
    with unscoped(db):
        accepted = {row[0] for row in db.query(LegalAcceptance.document_id).filter(
            LegalAcceptance.user_id == user.id, LegalAcceptance.document_id.in_([d.id for d in required])).all()}
    return [d for d in required if d.id not in accepted]


def record_acceptance(db: Session, user: User, accepted_versions: Dict[str, str], context: str,
                      commit: bool = True) -> List[LegalAcceptance]:
    """Record acceptance of the *current* version of every required document.

    ``accepted_versions`` maps document type to the version the person was shown. If any differs from
    the version now in force (it was updated while they were reading), nothing is recorded and the
    caller gets 409 so the person can review the new text.
    """
    rows = []
    for doc in required_documents(db):
        shown = accepted_versions.get(doc.doc_type)
        if shown is None:
            raise HTTPException(status_code=422, detail=f"Please review and accept the {doc.title}.")
        if shown != doc.version:
            raise HTTPException(status_code=409, detail=f"The {doc.title} has been updated. Please review the "
                                                        "current version before accepting.")
    with unscoped(db):
        for doc in required_documents(db):
            existing = db.query(LegalAcceptance).filter(LegalAcceptance.user_id == user.id,
                                                        LegalAcceptance.document_id == doc.id).first()
            if existing:
                rows.append(existing)
                continue
            row = LegalAcceptance(user_id=user.id, university_id=user.university_id, document_id=doc.id,
                                  doc_type=doc.doc_type, version=doc.version, context=context, accepted_at=utcnow())
            db.add(row)
            rows.append(row)
        AuditRepository(db).log(action="LEGAL_TERMS_ACCEPTED", user_id=user.id, resource_type="legal_document",
                                resource_id=",".join(f"{d.doc_type}:{d.version}" for d in required_documents(db)),
                                details={"context": context}, university_id=user.university_id, commit=False)
        if commit:
            db.commit()
    return rows


# ---------------------------------------------------------------------- administration
class LegalDocumentAdmin:
    """Draft, approve and publish document versions. Callers must already be platform super administrators
    (enforced by the route dependency); every action is audited."""

    def __init__(self, db: Session, actor: User):
        self.db, self.actor = db, actor

    def _get(self, doc_id: int) -> LegalDocument:
        doc = self.db.query(LegalDocument).filter(LegalDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document version not found.")
        return doc

    def _log(self, action: str, doc: LegalDocument, **details) -> None:
        AuditRepository(self.db).log(action=action, user_id=self.actor.id, resource_type="legal_document",
                                     resource_id=f"{doc.doc_type}:{doc.version}", details=details, commit=False)

    def _version_taken(self, doc_type: str, version: str, exclude_id: Optional[int] = None) -> bool:
        q = self.db.query(LegalDocument.id).filter(LegalDocument.doc_type == doc_type, LegalDocument.version == version)
        if exclude_id:
            q = q.filter(LegalDocument.id != exclude_id)
        return q.first() is not None

    def create_draft(self, doc_type: str, version: str, title: Optional[str], body: Optional[str],
                     change_summary: Optional[str]) -> LegalDocument:
        _check_type(doc_type)
        if self._version_taken(doc_type, version):
            raise HTTPException(status_code=409, detail=f"Version {version} already exists for this document.")
        base = current_document(self.db, doc_type)
        doc = LegalDocument(doc_type=doc_type, version=version, title=title or base.title, body=body or base.body,
                            change_summary=change_summary, status=LegalDocumentStatus.DRAFT,
                            created_by_id=self.actor.id, updated_by_id=self.actor.id)
        self.db.add(doc)
        self.db.flush()
        self._log("LEGAL_DRAFT_CREATED", doc)
        self.db.commit()
        return doc

    def update_draft(self, doc_id: int, changes: Dict[str, object]) -> LegalDocument:
        doc = self._get(doc_id)
        if doc.status != LegalDocumentStatus.DRAFT:
            raise HTTPException(status_code=409, detail="Only drafts can be edited. Create a new version instead.")
        if "version" in changes and changes["version"] and self._version_taken(doc.doc_type, changes["version"], doc.id):
            raise HTTPException(status_code=409, detail="That version number is already used.")
        for key in ("version", "title", "body", "change_summary", "effective_date"):
            if key in changes:
                setattr(doc, key, changes[key])
        doc.updated_by_id = self.actor.id
        self._log("LEGAL_DRAFT_UPDATED", doc, fields=sorted(changes))
        self.db.commit()
        return doc

    def approve(self, doc_id: int, approval_note: str) -> LegalDocument:
        doc = self._get(doc_id)
        if doc.status != LegalDocumentStatus.DRAFT:
            raise HTTPException(status_code=409, detail="Only drafts can be approved.")
        doc.status = LegalDocumentStatus.APPROVED
        doc.approved_by_id, doc.approved_at, doc.approval_note = self.actor.id, utcnow(), approval_note
        self._log("LEGAL_VERSION_APPROVED", doc, note=approval_note)
        self.db.commit()
        return doc

    def return_to_draft(self, doc_id: int) -> LegalDocument:
        doc = self._get(doc_id)
        if doc.status != LegalDocumentStatus.APPROVED:
            raise HTTPException(status_code=409, detail="Only approved, unpublished versions can be reopened.")
        doc.status = LegalDocumentStatus.DRAFT
        doc.approved_by_id = doc.approved_at = doc.approval_note = None
        self._log("LEGAL_VERSION_REOPENED", doc)
        self.db.commit()
        return doc

    def publish(self, doc_id: int, effective_date: date) -> LegalDocument:
        doc = self._get(doc_id)
        if doc.status != LegalDocumentStatus.APPROVED:
            raise HTTPException(status_code=409, detail="A version must be approved before it can be published.")
        doc.status = LegalDocumentStatus.PUBLISHED
        doc.effective_date = effective_date
        doc.published_by_id, doc.published_at = self.actor.id, utcnow()
        self._log("LEGAL_VERSION_PUBLISHED", doc, effective_date=effective_date.isoformat())
        self.db.commit()
        return doc
