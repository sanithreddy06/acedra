"""
Configurable outbound email, delivered through an outbox.

EMAIL_PROVIDER=log  (default) — the message is stored in the email_messages outbox and never leaves the
                                 server. Platform administrators can preview it in development. This is
                                 NOT real delivery.
EMAIL_PROVIDER=smtp           — the message is stored as ``queued`` in the same transaction as the work that
                                 caused it, and delivered through the SMTP relay only after that transaction
                                 commits. A request that fails and rolls back therefore never sends an email,
                                 and a slow or unavailable relay never blocks a request.

Delivery runs on a small background thread pool straight after commit. Messages that fail are retried by
``deliver_queued`` (called periodically from the API process) with a growing delay, up to
``EMAIL_MAX_ATTEMPTS``; after that they stay ``failed`` and are visible in the platform email outbox.
"""
import logging
import smtplib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from email.message import EmailMessage as MimeMessage
from typing import Optional

from sqlalchemy import event, or_
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.models.platform import EmailMessage

log = logging.getLogger("acedra.email")

SIGNATURE = "\n\n—\nACEDRA · University Intelligence. Connected.\nThis is an automated message; replies are not monitored.\n"

_PENDING_FLAG = "acedra_email_pending"
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="acedra-email")


class EmailService:
    def __init__(self, db: Session):
        self.db = db

    def send(self, to_email: str, subject: str, body: str, template: str,
             university_id: Optional[int] = None) -> EmailMessage:
        body = body.rstrip() + SIGNATURE
        deliver = settings.EMAIL_PROVIDER == "smtp" and bool(settings.SMTP_HOST)
        record = EmailMessage(
            university_id=university_id, to_email=to_email.lower(), subject=subject,
            body_text=body, template=template, provider=settings.EMAIL_PROVIDER,
            status="queued" if deliver else "logged",
        )
        self.db.add(record)
        if deliver:
            self.db.info[_PENDING_FLAG] = True  # picked up by the after-commit hook below
        else:
            log.info("Email logged (not sent) template=%s", template)
        return record


@event.listens_for(Session, "after_commit")
def _deliver_after_commit(session: Session) -> None:
    if session.info.pop(_PENDING_FLAG, False):
        _executor.submit(_deliver_safely)


@event.listens_for(Session, "after_rollback")
def _forget_after_rollback(session: Session) -> None:
    session.info.pop(_PENDING_FLAG, None)


def _deliver_safely() -> None:
    try:
        deliver_queued()
    except Exception:  # background thread: log and let the periodic retry pick the messages up
        log.exception("Email delivery run failed")


def _smtp_send(message: EmailMessage) -> None:
    msg = MimeMessage()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = message.to_email
    msg["Subject"] = message.subject
    msg.set_content(message.body_text)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_STARTTLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        smtp.send_message(msg)


def deliver_queued(batch_size: int = 50) -> int:
    """Send queued messages and retry failed ones that are due. Returns how many were sent.

    Safe to run from several workers at once: on PostgreSQL each run locks the rows it takes
    (``FOR UPDATE SKIP LOCKED``), so no message is sent twice.
    """
    from app.core.database import SessionLocal
    from app.core.tenancy import TenantScope, set_session_scope

    if settings.EMAIL_PROVIDER != "smtp" or not settings.SMTP_HOST:
        return 0
    sent = 0
    db = SessionLocal()
    set_session_scope(db, TenantScope(bypass=True))
    try:
        now = utcnow()
        retry_before = now - timedelta(seconds=settings.EMAIL_RETRY_INTERVAL_SECONDS)
        query = db.query(EmailMessage).filter(
            EmailMessage.provider == "smtp",
            EmailMessage.attempts < settings.EMAIL_MAX_ATTEMPTS,
            or_(EmailMessage.status == "queued",
                (EmailMessage.status == "failed") & (EmailMessage.last_attempt_at < retry_before)),
        ).order_by(EmailMessage.id).limit(batch_size)
        if db.bind.dialect.name == "postgresql":
            query = query.with_for_update(skip_locked=True)
        for message in query.all():
            # Later retries wait longer: attempt n is retried no sooner than n × the retry interval.
            if message.status == "failed" and message.last_attempt_at and message.last_attempt_at > now - timedelta(
                    seconds=settings.EMAIL_RETRY_INTERVAL_SECONDS * (message.attempts or 1)):
                continue
            message.attempts = (message.attempts or 0) + 1
            message.last_attempt_at = utcnow()
            try:
                _smtp_send(message)
                message.status = "sent"
                message.sent_at = utcnow()
                message.error = None
                sent += 1
            except Exception as exc:  # noqa: BLE001 — external SMTP relay: any failure is recorded on the outbox row
                message.status = "failed"
                message.error = str(exc)[:480]
                log.warning("SMTP delivery failed for template=%s (attempt %s)", message.template, message.attempts)
        db.commit()
    finally:
        db.close()
    return sent
