from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
import time
from sqlalchemy import text
from app.core.database import Base, engine, SessionLocal
from app.api.v1 import api_v1_router
# Import all models to ensure they are registered with Base.metadata
import app.models  # noqa: F401


# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables are created
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Smart Campus Intelligence — AI-Powered Student Success & Institutional Intelligence Platform",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    import json
    try:
        origins = json.loads(origins)
    except Exception:
        origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security and Performance Middleware
@app.middleware("http")
async def add_security_headers_and_timing(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    # Performance metric header
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    
    # Production security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
    return response


# Centralized error handling
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " -> ".join([str(loc) for loc in error.get("loc", [])])
        errors.append({
            "field": field,
            "message": error.get("msg"),
            "type": error.get("type")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "validation_error",
            "status_code": 422,
            "message": "Input validation failed. Please check the submitted fields.",
            "errors": errors,
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "server_error",
            "status_code": 500,
            "message": "An internal server error occurred.",
            "path": request.url.path
        }
    )


# Health and Readiness check endpoints
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/ready", tags=["Health"])
@app.get("/api/ready", tags=["Health"])
def readiness_check():
    """Readiness probe to verify database connectivity."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": db_status}
        )

    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "database": db_status,
        "version": settings.VERSION
    }


# Include V1 API
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
