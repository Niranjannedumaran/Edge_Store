from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Request
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.core.dependencies import get_current_user, get_optional_current_user
from backend.app.models.user import User
from backend.app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse
)
from backend.app.services.client_service import ClientService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/clients", tags=["Clients (MongoDB)"])


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    req: ClientCreate,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Store new client details in MongoDB."""
    operator_name = current_user.username if current_user else "client_frontend"
    client = await ClientService.create_client(req, current_username=operator_name)
    
    # Audit log
    AuditService.log_event(
        db=db,
        event_type="CLIENT_CREATE",
        description=f"Created client '{client.name}' ({client.email}) with MongoDB ID {client.id}",
        user_id=current_user.id if current_user else None,
        username=operator_name,
        ip_address=request.client.host if request.client else "127.0.0.1",
        severity="INFO"
    )
    return client


@router.get("", response_model=ClientListResponse)
async def list_clients(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Page size limit"),
    q: Optional[str] = Query(None, description="Search query across name, company, email, and phone"),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """List and search clients stored in MongoDB."""
    return await ClientService.list_clients(skip=skip, limit=limit, q=q)


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Retrieve details for a single client by MongoDB ObjectId."""
    return await ClientService.get_client_by_id(client_id)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    req: ClientUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update details for an existing client in MongoDB."""
    updated = await ClientService.update_client(client_id, req, current_username=current_user.username)

    # Audit log
    AuditService.log_event(
        db=db,
        event_type="CLIENT_UPDATE",
        description=f"Updated client '{updated.name}' ({updated.id}) in MongoDB",
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else "127.0.0.1",
        severity="INFO"
    )
    return updated


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete client record from MongoDB."""
    await ClientService.delete_client(client_id)

    # Audit log
    AuditService.log_event(
        db=db,
        event_type="CLIENT_DELETE",
        description=f"Deleted client with MongoDB ID {client_id}",
        user_id=current_user.id,
        username=current_user.username,
        ip_address=request.client.host if request.client else "127.0.0.1",
        severity="WARNING"
    )
    return None
