from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.departments import router as departments_router
from app.api.v1.academics import router as academics_router
from app.api.v1.dashboards import router as dashboards_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.system_settings import router as settings_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(departments_router)
api_v1_router.include_router(academics_router)
api_v1_router.include_router(dashboards_router)
api_v1_router.include_router(audit_logs_router)
api_v1_router.include_router(settings_router)
