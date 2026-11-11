from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import RoleDashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.get("/me", response_model=RoleDashboardResponse)
def get_my_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get integrated, dynamic, role-tailored dashboard metrics and stats for the authenticated user."""
    integration_service = DashboardService(db)
    return integration_service.get_role_dashboard(current_user)


@router.get("/student", response_model=RoleDashboardResponse)
def get_student_dashboard(
    current_user: User = Depends(require_role(["student", "faculty", "mentor", "admin"])),
    db: Session = Depends(get_db)
) -> Any:
    """Direct route for Student Dashboard."""
    return DashboardService(db).get_student_dashboard(current_user)


@router.get("/faculty", response_model=RoleDashboardResponse)
def get_faculty_dashboard(
    current_user: User = Depends(require_role(["faculty", "admin"])),
    db: Session = Depends(get_db)
) -> Any:
    """Direct route for Faculty Cohort Dashboard."""
    return DashboardService(db).get_faculty_dashboard(current_user)


@router.get("/mentor", response_model=RoleDashboardResponse)
def get_mentor_dashboard(
    current_user: User = Depends(require_role(["mentor", "admin"])),
    db: Session = Depends(get_db)
) -> Any:
    """Direct route for Mentor Dashboard."""
    return DashboardService(db).get_mentor_dashboard(current_user)


@router.get("/admin", response_model=RoleDashboardResponse)
def get_admin_dashboard(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
) -> Any:
    """Direct route for Administrator / HOD Executive Dashboard."""
    return DashboardService(db).get_admin_dashboard(current_user)


@router.get("/placement", response_model=RoleDashboardResponse)
def get_placement_dashboard(
    current_user: User = Depends(require_role(["placement_officer", "admin"])),
    db: Session = Depends(get_db)
) -> Any:
    """Direct route for Placement Officer Dashboard."""
    return DashboardService(db).get_placement_dashboard(current_user)
