from datetime import date, datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LegalDocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_type: str
    version: str
    title: str
    status: str
    effective_date: Optional[date] = None
    change_summary: Optional[str] = None
    published_at: Optional[datetime] = None


class LegalDocumentOut(LegalDocumentSummary):
    body: str


class LegalDocumentAdminOut(LegalDocumentOut):
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    approved_by_name: Optional[str] = None
    published_by_name: Optional[str] = None
    is_current: bool = False


class LegalDraftCreate(BaseModel):
    doc_type: str
    version: str = Field(..., min_length=1, max_length=40, pattern=r"^[A-Za-z0-9.\-]+$")
    title: Optional[str] = Field(None, max_length=200)
    body: Optional[str] = Field(None, max_length=200_000)
    change_summary: Optional[str] = Field(None, max_length=500)


class LegalDraftUpdate(BaseModel):
    version: Optional[str] = Field(None, min_length=1, max_length=40, pattern=r"^[A-Za-z0-9.\-]+$")
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    body: Optional[str] = Field(None, min_length=20, max_length=200_000)
    change_summary: Optional[str] = Field(None, max_length=500)
    effective_date: Optional[date] = None


class LegalApproval(BaseModel):
    approval_note: str = Field(..., min_length=10, max_length=500,
                               description="Who reviewed the text and on what basis, e.g. counsel's sign-off.")


class LegalPublish(BaseModel):
    effective_date: date


class LegalStatusOut(BaseModel):
    pending: list[LegalDocumentSummary]
    accepted: list[Dict[str, str]]


class LegalAcceptanceIn(BaseModel):
    accepted_versions: Dict[str, str] = Field(..., description="Document type -> version the person reviewed.")


FREE_MAIL_DOMAINS = {"gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "outlook.com", "hotmail.com",
                     "live.com", "rediffmail.com", "icloud.com", "aol.com", "proton.me", "protonmail.com",
                     "zoho.com", "yandex.com", "gmx.com", "mail.com"}


class ContactIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    institution: str = Field(..., min_length=2, max_length=255)
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=20, max_length=5000)
    website: Optional[str] = Field(None, max_length=200)  # honeypot: must stay empty

    @field_validator("email")
    @classmethod
    def institutional(cls, v: str) -> str:
        if v.split("@")[-1].lower() in FREE_MAIL_DOMAINS:
            raise ValueError("Please use your institution's email address.")
        return v

    @field_validator("message")
    @classmethod
    def not_link_spam(cls, v: str) -> str:
        if v.lower().count("http://") + v.lower().count("https://") > 3:
            raise ValueError("Please remove some links from your message.")
        return v


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    institution: str
    subject: str
    message: str
    status: str
    created_at: datetime
    updated_at: datetime


class ContactStatusIn(BaseModel):
    status: str = Field(..., pattern="^(new|in_progress|closed)$")
