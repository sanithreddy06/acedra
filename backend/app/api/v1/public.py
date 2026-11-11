"""Public, unauthenticated endpoints for the ACEDRA website. No student data, no chatbot."""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_client_ip
from app.core.config import settings
from app.core.database import get_db
from app.core.ratelimit import limiter
from app.core.tenancy import TenantScope, set_session_scope
from app.models.legal import ContactMessage
from app.models.platform import ALL_MODULES
from app.schemas.legal import ContactIn, LegalDocumentOut, LegalDocumentSummary
from app.services import legal_service
from app.services.email_service import EmailService
from app.services.platform_service import PlatformService, estimate_email_service

router = APIRouter(prefix="/public", tags=["Public Website"])

INSTITUTION_TYPES = ["Public university", "Private university", "Deemed university", "Autonomous college",
                     "Affiliated college", "Institute of national importance", "Other"]
POPULATION_BANDS = ["Under 2,000", "2,000 – 5,000", "5,000 – 15,000", "15,000 – 30,000", "Over 30,000"]


class EnquiryIn(BaseModel):
    university_name: str = Field(..., min_length=3, max_length=255)
    official_website: Optional[str] = Field(None, max_length=255)
    institution_type: str
    location: str = Field(..., min_length=2, max_length=255)
    student_population: str
    department_count: Optional[int] = Field(None, ge=1, le=500)
    campus_count: Optional[int] = Field(None, ge=1, le=100)
    contact_name: str = Field(..., min_length=2, max_length=255)
    contact_designation: str = Field(..., min_length=2, max_length=150)
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(None, max_length=40)
    preferred_contact_method: str = Field("email", pattern="^(email|phone|video_call)$")
    requested_modules: List[str] = Field(..., min_length=1)
    existing_sis: Optional[str] = Field(None, max_length=255)
    existing_academic_systems: Optional[str] = Field(None, max_length=255)
    has_student_emails: bool = True
    email_provisioning: str = Field("existing", pattern="^(existing|rio_assisted)$")
    accounts_required: Optional[int] = Field(None, ge=0, le=500000)
    institutional_requirements: Optional[str] = Field(None, max_length=5000)
    expected_outcomes: Optional[str] = Field(None, max_length=5000)
    additional_information: Optional[str] = Field(None, max_length=5000)
    consent_to_contact: bool
    website: Optional[str] = Field(None, max_length=200)  # honeypot: must stay empty

    @field_validator("requested_modules")
    @classmethod
    def valid_modules(cls, v):
        bad = [m for m in v if m not in ALL_MODULES]
        if bad:
            raise ValueError(f"Unknown modules: {bad}")
        return v

    @field_validator("institution_type")
    @classmethod
    def valid_type(cls, v):
        if v not in INSTITUTION_TYPES:
            raise ValueError("Invalid institution type")
        return v

    @field_validator("student_population")
    @classmethod
    def valid_population(cls, v):
        if v not in POPULATION_BANDS:
            raise ValueError("Invalid population band")
        return v


@router.get("/enquiry-options")
def enquiry_options() -> Any:
    return {"institution_types": INSTITUTION_TYPES, "population_bands": POPULATION_BANDS, "modules": ALL_MODULES,
            "email_service_unit_cost_inr": estimate_email_service(1)["unit_cost_inr_per_year"]}


@router.post("/enquiries", status_code=201)
@limiter.limit(settings.ENQUIRY_RATE_LIMIT)
def submit_enquiry(body: EnquiryIn, request: Request, db: Session = Depends(get_db)) -> Any:
    if not body.consent_to_contact:
        raise HTTPException(status_code=422, detail="Please confirm that ACEDRA may contact you about this enquiry.")
    set_session_scope(db, TenantScope(bypass=True))
    data = body.model_dump(exclude={"website"})
    if body.website:  # bot filled the hidden field: accept silently, store nothing
        return {"reference": "ENQ-RECEIVED", "message": "Thank you. Your enquiry has been received."}
    if data["email_provisioning"] == "existing":
        data["accounts_required"] = data.get("accounts_required")
    enquiry = PlatformService(db).submit_enquiry(data, get_client_ip(request))
    db.commit()
    return {"reference": enquiry.reference,
            "message": "Thank you. Your enquiry has been received and the ACEDRA team will be in touch.",
            "email_service_estimate": enquiry.email_service_estimate}


# ------------------------------------------------------------------ legal documents
@router.get("/legal", response_model=List[LegalDocumentSummary])
def legal_documents(db: Session = Depends(get_db)) -> Any:
    """The version of each legal document currently in force."""
    from app.models.legal import LEGAL_DOCUMENT_TYPES
    return [legal_service.current_document(db, t) for t in LEGAL_DOCUMENT_TYPES]


@router.get("/legal/{doc_type}", response_model=LegalDocumentOut)
def legal_document(doc_type: str, version: Optional[str] = None, db: Session = Depends(get_db)) -> Any:
    """A document's current text, or a specific earlier published version."""
    if version is None:
        return legal_service.current_document(db, doc_type)
    doc = next((d for d in legal_service.published_history(db, doc_type) if d.version == version), None)
    if doc is None:
        raise HTTPException(status_code=404, detail="That version has not been published.")
    return doc


@router.get("/legal/{doc_type}/history", response_model=List[LegalDocumentSummary])
def legal_history(doc_type: str, db: Session = Depends(get_db)) -> Any:
    return legal_service.published_history(db, doc_type)


# ------------------------------------------------------------------ contact
@router.post("/contact", status_code=201)
@limiter.limit(settings.CONTACT_RATE_LIMIT)
def submit_contact(body: ContactIn, request: Request, db: Session = Depends(get_db)) -> Any:
    """Store a contact-form message for the ACEDRA team and acknowledge it by email."""
    received = {"message": "Thank you. Your message has been received and the ACEDRA team will reply by email."}
    if body.website:  # bot filled the hidden field: accept silently, store nothing
        return received
    set_session_scope(db, TenantScope(bypass=True))
    msg = ContactMessage(name=body.name.strip(), email=body.email.lower(), institution=body.institution.strip(),
                         subject=body.subject.strip(), message=body.message.strip())
    db.add(msg)
    EmailService(db).send(
        to_email=body.email, template="contact_acknowledgement", subject="We received your message",
        body=f"Dear {msg.name},\n\nThank you for contacting ACEDRA about \"{msg.subject}\". A member of the team "
             "will reply to this address.\n\nThis acknowledgement does not create any agreement or account.",
    )
    db.commit()
    return received

