"""
Configurable outbound email.

EMAIL_PROVIDER=log  (default) — the message is stored in the email_messages outbox
                                 and never leaves the server. Platform administrators can
                                 preview it in development. This is NOT real delivery.
EMAIL_PROVIDER=smtp           — delivered through the configured SMTP relay and logged.
"""
import logging
import smtplib
from email.message import EmailMessage as MimeMessage
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.platform import EmailMessage

log = logging.getLogger("acedra.email")

SIGNATURE = "\n\n—\nACEDRA · University Intelligence. Connected.\nThis is an automated message; replies are not monitored.\n"


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    def send(self, to_email: str, subject: str, body: str, template: str,
             university_id: Optional[int] = None) -> EmailMessage:
        body = body.rstrip() + SIGNATURE
        record = EmailMessage(
            university_id=university_id, to_email=to_email.lower(), subject=subject,
            body_text=body, template=template, provider=settings.EMAIL_PROVIDER, status="logged",
        )
        if settings.EMAIL_PROVIDER == "smtp" and settings.SMTP_HOST:
            try:
                msg = MimeMessage()
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = to_email
                msg["Subject"] = subject
                msg.set_content(body)
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                    if settings.SMTP_STARTTLS:
                        smtp.starttls()
                    if settings.SMTP_USERNAME:
                        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
                    smtp.send_message(msg)
                record.status = "sent"
            except Exception as exc:  # noqa: BLE001 — external SMTP relay: any failure is recorded on the outbox row
                record.status = "failed"
                record.error = str(exc)[:480]
                log.warning("SMTP delivery failed for template=%s", template)
        else:
            log.info("Email logged (not sent) template=%s", template)
        self.db.add(record)
        return record
