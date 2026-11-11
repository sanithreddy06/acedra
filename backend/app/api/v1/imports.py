import json
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.database import get_db
from app.models.student_intelligence import ImportJob
from app.models.user import User, UserRole
from app.schemas.student_intelligence import ImportJobOut, ImportPreviewResult
from app.services.student_service import StudentIntelligenceService

router = APIRouter(prefix="/imports", tags=["Data Import Center"])


def _mapping(raw: Optional[str]):
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="column_mapping must be a JSON object of source → field names.")
    return {str(k)[:100]: str(v)[:100] for k, v in data.items()}


@router.post("/preview", response_model=ImportPreviewResult)
def preview_data_import(
    file: UploadFile = File(...),
    import_type: str = Form("students"),
    column_mapping: Optional[str] = Form(None),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Upload CSV or Excel file to preview data, detect duplicates, and catch errors before committing."""
    service = StudentIntelligenceService(db)
    return service.preview_import_file(file, import_type, current_user, _mapping(column_mapping))


@router.post("/execute", response_model=ImportJobOut, status_code=status.HTTP_201_CREATED)
def execute_data_import(
    file: UploadFile = File(...),
    import_type: str = Form("students"),
    column_mapping: Optional[str] = Form(None),
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Commit batch import into institutional database with row-level validation."""
    service = StudentIntelligenceService(db)
    job = service.execute_import(file, import_type, current_user, _mapping(column_mapping))
    return {
        "id": job.id,
        "filename": job.filename,
        "file_type": job.file_type,
        "import_type": job.import_type,
        "status": job.status,
        "total_rows": job.total_rows,
        "successful_rows": job.successful_rows,
        "failed_rows": job.failed_rows,
        "created_at": job.created_at,
        "error_count": len(job.errors),
    }


@router.get("/template/{template_type}")
def download_import_template(
    template_type: str,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Download standardized CSV template for bulk data imports."""
    service = StudentIntelligenceService(db)
    csv_content = service.generate_csv_template(template_type)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=template_{template_type}.csv"},
    )


@router.get("/jobs", response_model=List[ImportJobOut])
def list_import_jobs(
    limit: int = 20,
    current_user: User = Depends(require_role(UserRole.ADMIN.value)),
    db: Session = Depends(get_db),
) -> Any:
    """Retrieve historical data import jobs and results."""
    jobs = db.query(ImportJob).order_by(ImportJob.created_at.desc()).limit(limit).all()
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "file_type": j.file_type,
            "import_type": j.import_type,
            "status": j.status,
            "total_rows": j.total_rows,
            "successful_rows": j.successful_rows,
            "failed_rows": j.failed_rows,
            "created_at": j.created_at,
            "error_count": len(j.errors),
        }
        for j in jobs
    ]
