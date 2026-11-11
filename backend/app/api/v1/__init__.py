from fastapi import APIRouter, Depends

from app.api.deps import get_university_user
from app.api.v1.academics import router as academics_router
from app.api.v1.ai_assistant import router as ai_assistant_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.departments import router as departments_router
from app.api.v1.imports import router as imports_router
from app.api.v1.interventions import router as interventions_router
from app.api.v1.placement import router as placement_router
from app.api.v1.platform import router as platform_router
from app.api.v1.public import router as public_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.risk import router as risk_router
from app.api.v1.students import router as students_router
from app.api.v1.system_settings import router as settings_router
from app.api.v1.tenant import router as tenant_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter()

# Public and authentication endpoints
api_v1_router.include_router(public_router)
api_v1_router.include_router(auth_router)

# ACEDRA internal platform administration (platform accounts only)
api_v1_router.include_router(platform_router)

# University workspaces — every route is tenant-guarded, module-gated and student-scope checked
university_guard = [Depends(get_university_user)]
for r in (tenant_router, users_router, departments_router, academics_router, dashboards_router, audit_logs_router,
          settings_router, students_router, imports_router, risk_router, recommendations_router, placement_router,
          ai_assistant_router, interventions_router):
    api_v1_router.include_router(r, dependencies=university_guard)
