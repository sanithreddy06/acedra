"""
Invitation-based provisioning. There is no public registration in ACEDRA:
every account is created by an authorised administrator and activated only when
the invitee proves control of the approved address by accepting the emailed link.
A matching email domain is a *precondition*, never a grant of access.
"""
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.core.security import generate_url_token, get_password_hash, hash_token
from app.models.platform import Invitation, University, UniversityDomain
from app.models.user import PLATFORM_ROLES, UNIVERSITY_ROLES, Role, User
from app.services.email_service import EmailService

ROLE_LABELS = {
    "student": "Student", "faculty": "Faculty", "mentor": "Mentor", "admin": "University Administrator",
    "placement_officer": "Placement Officer", "platform_admin": "ACEDRA Super Administrator",
    "platform_employee": "ACEDRA Employee",
}


def email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower().strip()


class InvitationService:
    def __init__(self, db: Session):
        self.db = db

    def check_domain(self, university: University, email: str, role: str) -> None:
        if not university.enforce_email_domains:
            return
        domains = self.db.query(UniversityDomain).filter(UniversityDomain.university_id == university.id).all()
        dom = email_domain(email)
        for d in domains:
            if d.domain == dom and (d.purpose == "all" or (d.purpose == "student") == (role == "student")):
                return
        approved = ", ".join(sorted(d.domain for d in domains)) or "none configured"
        raise HTTPException(status_code=422,
                            detail=f"{email} is not on an approved domain for {university.short_name} ({approved}).")

    def create_user_with_invitation(
        self, *, email: str, full_name: str, role: str, university: Optional[University],
        invited_by: Optional[User], department_id: Optional[int] = None, title: Optional[str] = None,
        phone: Optional[str] = None, send: bool = True,
    ) -> tuple[User, Invitation, str]:
        email = email.strip().lower()
        if university is None and role not in PLATFORM_ROLES:
            raise HTTPException(status_code=422, detail="University roles require a university.")
        if university is not None and role not in UNIVERSITY_ROLES:
            raise HTTPException(status_code=422, detail="Invalid university role.")
        if self.db.query(User).execution_options(acedra_unscoped=True).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        if university is not None:
            self.check_domain(university, email, role)

        role_obj = self.db.query(Role).filter(Role.name == role).first()
        user = User(
            email=email, full_name=full_name, role=role, role_id=role_obj.id if role_obj else None,
            department_id=department_id, title=title, phone=phone,
            hashed_password=get_password_hash(generate_url_token()),  # unusable until invitation accepted
            is_active=False, is_verified=False, invited_at=utcnow(),
            university_id=university.id if university else None,
        )
        self.db.add(user)
        self.db.flush()
        inv, token = self._issue(user, invited_by, send=send)
        return user, inv, token

    def _issue(self, user: User, invited_by: Optional[User], send: bool = True) -> tuple[Invitation, str]:
        token = generate_url_token()
        inv = Invitation(
            university_id=user.university_id, user_id=user.id, email=user.email, role=user.role,
            token_hash=hash_token(token), invited_by_id=invited_by.id if invited_by else None,
            expires_at=utcnow() + timedelta(hours=settings.INVITATION_TTL_HOURS),
        )
        self.db.add(inv)
        self.db.flush()
        if send:
            uni = self.db.query(University).filter(University.id == user.university_id).first() if user.university_id else None
            workspace = uni.name if uni else "the ACEDRA platform team"
            link = f"{settings.PUBLIC_APP_URL}/accept-invitation?token={token}"
            EmailService(self.db).send(
                user.email, f"You're invited to ACEDRA — {workspace}",
                f"Hello {user.full_name},\n\nYou have been invited to join {workspace} on ACEDRA as "
                f"{ROLE_LABELS.get(user.role, user.role)}.\n\nAccept the invitation and set your password "
                f"within {settings.INVITATION_TTL_HOURS} hours:\n{link}\n\n"
                "If you were not expecting this invitation, please ignore this email.",
                template="invitation", university_id=user.university_id,
            )
        return inv, token

    def resend(self, user: User, invited_by: Optional[User]) -> Invitation:
        if user.is_verified:
            raise HTTPException(status_code=409, detail="This user has already accepted their invitation.")
        for old in self.db.query(Invitation).filter(Invitation.user_id == user.id, Invitation.accepted_at.is_(None),
                                                    Invitation.revoked_at.is_(None)).all():
            old.revoked_at = utcnow()
        inv, _ = self._issue(user, invited_by)
        return inv
