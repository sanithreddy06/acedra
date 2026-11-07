from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.user import User, Role, UserRole
from app.models.department import Department
from app.models.academic import (
    Semester,
    Subject,
    FacultyCourseAssignment,
    StudentSemesterRecord,
    SubjectResult,
    SubjectAttendance,
    StudentAssessment,
)
from app.models.profile import Student, Faculty, Mentor, StudentMentorAssignment
from app.models.audit import AuditLog
from app.models.system import SystemSetting
from app.models.student_intelligence import (
    Skill,
    StudentSkill,
    Certification,
    Project,
    Internship,
    Hackathon,
    ImportJob,
    ImportError,
    SkillCategory,
)
from app.models.risk import (
    RiskRule,
    RiskAlert,
    RiskEvaluation,
    RiskAlertHistory,
    AlertAssignment,
    InAppNotification,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Role",
    "UserRole",
    "Department",
    "Semester",
    "Subject",
    "FacultyCourseAssignment",
    "StudentSemesterRecord",
    "SubjectResult",
    "SubjectAttendance",
    "StudentAssessment",
    "Student",
    "Faculty",
    "Mentor",
    "StudentMentorAssignment",
    "AuditLog",
    "SystemSetting",
    "Skill",
    "StudentSkill",
    "Certification",
    "Project",
    "Internship",
    "Hackathon",
    "ImportJob",
    "ImportError",
    "SkillCategory",
    "RiskRule",
    "RiskAlert",
    "RiskEvaluation",
    "RiskAlertHistory",
    "AlertAssignment",
    "InAppNotification",
]
