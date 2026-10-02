import io
from typing import Optional, List, Tuple
from fastapi import APIRouter, Depends, UploadFile, File, Query, Response, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from fastapi.security import HTTPAuthorizationCredentials
from backend.app.core.dependencies import get_current_user, require_permission, require_vault_unlocked, security
from backend.app.services.file_service import FileService
from backend.app.services.share_service import ShareService

router = APIRouter(prefix="/files", tags=["Files"])


def require_file_access_or_share(
    share_token: Optional[str] = Query(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Tuple[Optional[User], Optional[str]]:
    if share_token:
        return None, share_token

    if not credentials:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials or valid share token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_current_user(credentials=credentials, db=db)
    if not user.has_permission("files.download") and not user.has_permission("files.preview"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing required permission: 'files.download' or 'files.preview'"
        )
    return user, None


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permission("files.upload")),
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
    current_user: User = Depends(require_permission("files.read")),
    db: Session = Depends(get_db)
):
    return FileService.list_files(db=db, current_user=current_user, search=search, replica_status=status_filter)


@router.get("/{file_id}")
def get_file_details(
    file_id: str,
    share_token: Optional[str] = Query(None),
    current_user: User = Depends(require_permission("files.read")),
    db: Session = Depends(get_db)
):
    file_record = FileService.get_file(db, file_id, current_user, share_token=share_token)
    return file_record.to_dict()


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    share_token: Optional[str] = Query(None),
    auth_ctx: Tuple[Optional[User], Optional[str]] = Depends(require_file_access_or_share),
    _vault: None = Depends(require_vault_unlocked),
    db: Session = Depends(get_db)
):
    current_user, valid_share_token = auth_ctx
    effective_user = current_user or User(id=-1, username="anonymous_share_guest", role="guest", is_active=True)
    
    data, stored_file, is_degraded_fallback = FileService.download_file(
        db, file_id, effective_user, share_token=valid_share_token
    )

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


@router.put("/{file_id}/rename")
def rename_file(
    file_id: str,
    new_filename: str = Body(..., embed=True),
    current_user: User = Depends(require_permission("files.rename")),
    db: Session = Depends(get_db)
):
    return FileService.rename_file(db, file_id, new_filename, current_user)


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    current_user: User = Depends(require_permission("files.delete")),
    _vault: None = Depends(require_vault_unlocked),
    db: Session = Depends(get_db)
):
    return FileService.delete_file(db, file_id, current_user)


@router.get("/{file_id}/verify")
def verify_file_integrity(
    file_id: str,
    current_user: User = Depends(require_permission("files.read")),
    db: Session = Depends(get_db)
):
    return FileService.verify_file_integrity(db, file_id, current_user)


# --- TEMPORARY GUEST SHARING ENDPOINTS ---

@router.post("/{file_id}/share", status_code=status.HTTP_201_CREATED)
def create_file_share(
    file_id: str,
    expires_in_hours: int = Body(24, embed=True),
    allow_download: bool = Body(False, embed=True),
    max_uses: Optional[int] = Body(None, embed=True),
    current_user: User = Depends(require_permission("files.share")),
    db: Session = Depends(get_db)
):
    """Create a temporary, revocable guest share link for an authorized file."""
    share = ShareService.create_share(
        db=db,
        file_id=file_id,
        current_user=current_user,
        expires_in_hours=expires_in_hours,
        allow_download=allow_download,
        max_uses=max_uses
    )
    return {
        "success": True,
        "message": "Temporary share token generated successfully",
        "share": share.to_dict()
    }


@router.get("/{file_id}/shares")
def list_file_shares(
    file_id: str,
    current_user: User = Depends(require_permission("files.share")),
    db: Session = Depends(get_db)
):
    return ShareService.list_shares_for_file(db, file_id, current_user)


@router.delete("/shares/{share_id}")
def revoke_file_share(
    share_id: str,
    current_user: User = Depends(require_permission("files.share")),
    db: Session = Depends(get_db)
):
    return ShareService.revoke_share(db, share_id, current_user)


@router.get("/shared/{share_token}")
def get_shared_file_info(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Public inspection of a shared file metadata using temporary token."""
    share = ShareService.get_valid_share(db, share_token)
    return {
        "share_id": share.id,
        "file": share.file.to_dict(),
        "expires_at": share.expires_at.isoformat() if share.expires_at else None,
        "allow_download": share.allow_download,
        "access_count": share.access_count
    }
