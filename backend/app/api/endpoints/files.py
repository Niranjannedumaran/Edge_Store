import io
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.core.dependencies import get_current_user, require_vault_unlocked
from backend.app.services.file_service import FileService

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    _vault: None = Depends(require_vault_unlocked),
    db: Session = Depends(get_db)
):
    content = await file.read()
    result = FileService.upload_file(
        db=db,
        current_user=current_user,
        filename=file.filename or "unnamed_file",
        data=content,
        content_type=file.content_type or "application/octet-stream"
    )
    return result


@router.get("")
def list_files(
    search: Optional[str] = Query(None, description="Search by filename"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by replica status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return FileService.list_files(db=db, current_user=current_user, search=search, replica_status=status_filter)


@router.get("/{file_id}")
def get_file_details(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_record = FileService.get_file(db, file_id, current_user)
    return file_record.to_dict()


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    _vault: None = Depends(require_vault_unlocked),
    db: Session = Depends(get_db)
):
    data, stored_file, is_degraded_fallback = FileService.download_file(db, file_id, current_user)

    headers = {
        "Content-Disposition": f'attachment; filename="{stored_file.filename}"',
        "X-EdgeStore-Degraded-Fallback": "true" if is_degraded_fallback else "false",
        "X-EdgeStore-SHA256": stored_file.sha256_hash
    }

    return StreamingResponse(
        io.BytesIO(data),
        media_type=stored_file.content_type or "application/octet-stream",
        headers=headers
    )


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    _vault: None = Depends(require_vault_unlocked),
    db: Session = Depends(get_db)
):
    return FileService.delete_file(db, file_id, current_user)


@router.get("/{file_id}/verify")
def verify_file_integrity(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return FileService.verify_file_integrity(db, file_id, current_user)
