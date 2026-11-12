import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # registers every model with SQLAlchemy before routers import them
from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.database import Base, add_missing_columns, engine
from app.core.ratelimit import limiter
from app.core.tenancy import CrossTenantWriteError


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": self.formatTime(record), "level": record.levelname, "logger": record.name,
                   "msg": record.getMessage()}
        for key in ("request_id", "path", "status", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info and not settings.is_production:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


_handler = logging.StreamHandler()
_handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
log = logging.getLogger("acedra")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.AUTO_CREATE_SCHEMA:
        Base.metadata.create_all(bind=engine)
        added = add_missing_columns()
        if added:
            log.info("Development schema updated: added %s", ", ".join(added))
    log.info("ACEDRA API started (environment=%s, llm=%s, embeddings=%s, email=%s)", settings.ENVIRONMENT,
             settings.LLM_PROVIDER, settings.EMBEDDING_PROVIDER, settings.EMAIL_PROVIDER)
    retry_task = asyncio.create_task(_email_retry_loop()) if settings.EMAIL_PROVIDER == "smtp" else None
    yield
    if retry_task:
        retry_task.cancel()


async def _email_retry_loop() -> None:
    """Periodically deliver queued email and retry failed messages (see services/email_service.py)."""
    from app.services.email_service import deliver_queued
    while True:
        await asyncio.sleep(settings.EMAIL_RETRY_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(deliver_queued)
        except Exception:  # keep the loop alive; the next pass retries
            log.exception("Email retry pass failed")


app = FastAPI(
    title="ACEDRA API",
    version=settings.VERSION,
    description="ACEDRA — University Intelligence. Connected. Multi-tenant API for student analytics, early warning, "
                "recommendations, placement readiness, AI assistance and intervention tracking.",
    # The interactive docs and the machine-readable schema are development aids; neither is served in production.
    openapi_url=None if settings.is_production else f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Paths only — never query strings, bodies or tokens.
    log.info("request", extra={"request_id": request_id, "path": request.url.path,
                               "status": response.status_code, "duration_ms": duration})
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"status": "error", "status_code": exc.status_code, "detail": exc.detail,
                                 "message": exc.detail, "path": request.url.path},
                        headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": " → ".join(str(p) for p in e.get("loc", []) if p != "body"), "message": e.get("msg")}
              for e in exc.errors()]
    first = errors[0] if errors else {"field": "", "message": "Invalid input"}
    return JSONResponse(status_code=422, content={
        "status": "validation_error", "status_code": 422,
        "detail": f"{first['field']}: {first['message']}" if first["field"] else first["message"],
        "message": "Please check the highlighted fields.", "errors": errors, "path": request.url.path})


@app.exception_handler(CrossTenantWriteError)
async def cross_tenant_handler(request: Request, exc: CrossTenantWriteError):
    log.warning("Blocked cross-tenant write", extra={"path": request.url.path})
    return JSONResponse(status_code=403, content={"status": "error", "status_code": 403,
                                                  "detail": "Operation not permitted.", "path": request.url.path})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """A unique or foreign-key constraint rejected the write: a conflict with existing data, not a server fault."""
    log.warning("Constraint violation", extra={"path": request.url.path})
    detail = "This conflicts with an existing record (for example a duplicate code, number or email)."
    return JSONResponse(status_code=409, content={"status": "error", "status_code": 409, "detail": detail,
                                                  "message": detail, "path": request.url.path})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled error", exc_info=exc, extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"status": "server_error", "status_code": 500,
                                                  "detail": "An internal error occurred.", "path": request.url.path})


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/ready", tags=["Health"])
@app.get("/api/ready", tags=["Health"])
def readiness_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.warning("Readiness check failed: database unreachable")
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            content={"status": "not_ready", "database": "unavailable"})
    return {
        "status": "ready", "database": "connected", "version": settings.VERSION,
        "providers": {"llm": settings.LLM_PROVIDER, "embeddings": settings.EMBEDDING_PROVIDER,
                      "email": settings.EMAIL_PROVIDER},
    }


app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
