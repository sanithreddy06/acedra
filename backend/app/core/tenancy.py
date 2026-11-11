"""
ACEDRA multi-tenancy core.

Every university-owned table carries a ``university_id`` column (``TenantMixin``).
Isolation is enforced centrally at the ORM layer, so that every existing service
query is scoped without having to be rewritten individually:

* ``do_orm_execute`` adds ``WHERE university_id = :tenant`` to every SELECT /
  UPDATE / DELETE against a tenant-owned entity (including relationship loads).
* For students, faculty and mentors, an additional *student scope* limits every
  student-owned entity to the students that user is authorised to see.
* Platform (ACEDRA internal) sessions are denied confidential academic tables
  entirely unless code explicitly opts out with ``unscoped()`` for an audited,
  grant-checked operation.
* ``before_flush`` stamps new rows with the session tenant and rejects any
  attempt to write a row into, or move a row to, another tenant.

The scope lives in ``session.info`` for API requests. Scripts (seeding, CLI)
can use the ``tenant_context`` context manager instead.
"""
from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, Optional, Set

from sqlalchemy import Column, ForeignKey, Integer, event, false
from sqlalchemy.orm import Session, declared_attr, with_loader_criteria


class TenantMixin:
    """Marks a model as owned by exactly one university tenant."""

    @declared_attr
    def university_id(cls):
        return Column(
            Integer,
            ForeignKey("universities.id", ondelete="CASCADE"),
            index=True,
            nullable=True,  # nullable only for platform-level rows (users, audit, settings)
        )


# Tables whose rows may legitimately have university_id = NULL (platform-level rows).
PLATFORM_NULLABLE_TABLES = {"users", "audit_logs", "system_settings", "notifications", "notification_preferences"}


@dataclass
class TenantScope:
    tenant_id: Optional[int] = None
    # None = no student restriction inside the tenant; a set = only these student ids.
    student_ids: Optional[Set[int]] = None
    platform: bool = False
    bypass: bool = False
    user_id: Optional[int] = None
    role: Optional[str] = None
    extra: dict = field(default_factory=dict)


_script_scope: contextvars.ContextVar[Optional[TenantScope]] = contextvars.ContextVar("acedra_scope", default=None)


def set_session_scope(session: Session, scope: Optional[TenantScope]) -> None:
    session.info["acedra_scope"] = scope


def get_scope(session: Session) -> Optional[TenantScope]:
    scope = session.info.get("acedra_scope")
    if scope is None:
        scope = _script_scope.get()
    return scope


@contextmanager
def tenant_context(tenant_id: Optional[int], bypass: bool = False) -> Iterator[None]:
    """Scope for scripts: every session opened inside uses this tenant."""
    token = _script_scope.set(TenantScope(tenant_id=tenant_id, bypass=bypass))
    try:
        yield
    finally:
        _script_scope.reset(token)


@contextmanager
def unscoped(session: Session) -> Iterator[Session]:
    """Temporarily lift scoping on a session (platform operations, auth lookups)."""
    previous = session.info.get("acedra_scope")
    session.info["acedra_scope"] = TenantScope(bypass=True)
    try:
        yield session
    finally:
        session.info["acedra_scope"] = previous


def _confidential_classes():
    """Academic / personal records ACEDRA staff must never read without a grant."""
    from app.models import (
        Certification,
        Conversation,
        Hackathon,
        Internship,
        Intervention,
        InterventionFollowup,
        InterventionNote,
        Message,
        Project,
        Recommendation,
        RecommendationFeedback,
        RecommendationProgress,
        RiskAlert,
        RiskAlertHistory,
        RiskEvaluation,
        SkillEvidence,
        Student,
        StudentApplication,
        StudentAssessment,
        StudentSemesterRecord,
        StudentSkill,
        SubjectAttendance,
        SubjectResult,
    )
    return [
        Student, StudentSemesterRecord, SubjectResult, SubjectAttendance, StudentAssessment,
        StudentSkill, Certification, Project, Internship, Hackathon, RiskAlert, RiskEvaluation,
        RiskAlertHistory, Recommendation, RecommendationProgress, RecommendationFeedback,
        SkillEvidence, StudentApplication, Intervention, InterventionNote, InterventionFollowup,
        Conversation, Message,
    ]


def _student_owned_classes():
    from app.models import (
        Certification,
        Hackathon,
        Internship,
        Intervention,
        Project,
        Recommendation,
        RiskAlert,
        RiskEvaluation,
        SkillEvidence,
        StudentApplication,
        StudentAssessment,
        StudentMentorAssignment,
        StudentSemesterRecord,
        StudentSkill,
        SubjectAttendance,
        SubjectResult,
    )
    return [
        StudentSemesterRecord, SubjectResult, SubjectAttendance, StudentAssessment, StudentSkill,
        Certification, Project, Internship, Hackathon, RiskAlert, RiskEvaluation, Recommendation,
        SkillEvidence, StudentApplication, Intervention, StudentMentorAssignment,
    ]


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_scope(state) -> None:
    if not (state.is_select or state.is_update or state.is_delete):
        return
    if state.execution_options.get("acedra_unscoped"):
        return
    scope = get_scope(state.session)
    if scope is None or scope.bypass:
        return

    options = []
    if scope.platform:
        for cls in _confidential_classes():
            options.append(with_loader_criteria(cls, false(), include_aliases=True))
    elif scope.tenant_id is not None:
        tid = scope.tenant_id
        options.append(
            with_loader_criteria(TenantMixin, lambda cls: cls.university_id == tid, include_aliases=True)
        )
        if scope.student_ids is not None:
            from app.models import Student
            ids = sorted(scope.student_ids) or [-1]
            options.append(with_loader_criteria(Student, Student.id.in_(ids), include_aliases=True))
            for cls in _student_owned_classes():
                if not hasattr(cls, "student_id"):
                    continue
                options.append(with_loader_criteria(cls, cls.student_id.in_(ids), include_aliases=True))
    else:
        # A non-platform session with no tenant must never see tenant data.
        options.append(with_loader_criteria(TenantMixin, lambda cls: cls.university_id == -1, include_aliases=True))

    if options:
        state.statement = state.statement.options(*options)


class CrossTenantWriteError(PermissionError):
    pass


@event.listens_for(Session, "before_flush")
def _stamp_and_guard_tenant(session: Session, flush_context, instances) -> None:
    scope = get_scope(session)
    if scope is None or scope.bypass:
        return
    for obj in list(session.new):
        if not isinstance(obj, TenantMixin):
            continue
        if scope.tenant_id is not None:
            if obj.university_id is None:
                obj.university_id = scope.tenant_id
            elif obj.university_id != scope.tenant_id:
                raise CrossTenantWriteError("Attempted to create a record in another university's workspace.")
        elif scope.platform and obj.__tablename__ not in PLATFORM_NULLABLE_TABLES and obj.university_id is None:
            raise CrossTenantWriteError("Platform sessions cannot create tenant records without an explicit tenant.")
    for obj in list(session.dirty):
        if not isinstance(obj, TenantMixin) or scope.tenant_id is None:
            continue
        if obj.university_id is not None and obj.university_id != scope.tenant_id:
            raise CrossTenantWriteError("Attempted to modify a record that belongs to another university.")
    for obj in list(session.deleted):
        if not isinstance(obj, TenantMixin) or scope.tenant_id is None:
            continue
        if obj.university_id is not None and obj.university_id != scope.tenant_id:
            raise CrossTenantWriteError("Attempted to delete a record that belongs to another university.")


@contextmanager
def as_tenant(session: Session, tenant_id: int) -> Iterator[Session]:
    """Run a block against a single tenant (used by platform provisioning and seeding)."""
    previous = session.info.get("acedra_scope")
    session.info["acedra_scope"] = TenantScope(tenant_id=tenant_id)
    try:
        yield session
    finally:
        session.info["acedra_scope"] = previous
