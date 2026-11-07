from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import RoleDashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.get("/me", response_model=RoleDashboardResponse)
def get_my_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Get dynamic, role-tailored dashboard metrics and stats for the authenticated user."""
    dashboard_service = DashboardService(db)
    return dashboard_service.get_dashboard_for_user(current_user)
