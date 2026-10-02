from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status

from backend.app.db.mongo import MongoDBManager
from backend.app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientListResponse
)
from backend.app.core.logger import logger


def _mongo_doc_to_client_response(doc: Dict[str, Any]) -> ClientResponse:
    """Helper to convert MongoDB document to Pydantic ClientResponse."""
    return ClientResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        phone=doc.get("phone"),
        company=doc.get("company"),
        address=doc.get("address"),
        notes=doc.get("notes"),
        metadata=doc.get("metadata", {}),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        created_by=doc.get("created_by")
    )


class ClientService:
    @staticmethod
    async def create_client(
        data: ClientCreate,
        current_username: Optional[str] = None
    ) -> ClientResponse:
        """Create and store new client details in MongoDB."""
        col = MongoDBManager.get_collection("clients")

        # Check existing email
        existing = await col.find_one({"email": data.email.lower().strip()})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A client with email '{data.email}' already exists"
            )

        now = datetime.now(timezone.utc)
        doc = {
            "name": data.name.strip(),
            "email": data.email.lower().strip(),
            "phone": data.phone.strip() if data.phone else None,
            "company": data.company.strip() if data.company else None,
            "address": data.address.strip() if data.address else None,
            "notes": data.notes.strip() if data.notes else None,
            "metadata": data.metadata or {},
            "created_at": now,
            "updated_at": now,
            "created_by": current_username
        }

        try:
            result = await col.insert_one(doc)
            doc["_id"] = result.inserted_id
            logger.info(f"Created client {doc['name']} ({doc['email']}) with ID {result.inserted_id}")
            return _mongo_doc_to_client_response(doc)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A client with email '{data.email}' already exists"
            )
        except Exception as e:
            logger.error(f"Failed to persist client in MongoDB: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database storage error: {str(e)}"
            )

    @staticmethod
    async def get_client_by_id(client_id: str) -> ClientResponse:
        """Fetch client document by its MongoDB ObjectId."""
        if not ObjectId.is_valid(client_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID format"
            )

        col = MongoDBManager.get_collection("clients")
        doc = await col.find_one({"_id": ObjectId(client_id)})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        return _mongo_doc_to_client_response(doc)

    @staticmethod
    async def list_clients(
        skip: int = 0,
        limit: int = 50,
        q: Optional[str] = None
    ) -> ClientListResponse:
        """List clients with optional search filter and pagination."""
        col = MongoDBManager.get_collection("clients")

        filter_query: Dict[str, Any] = {}
        if q and q.strip():
            query_str = q.strip()
            filter_query = {
                "$or": [
                    {"name": {"$regex": query_str, "$options": "i"}},
                    {"company": {"$regex": query_str, "$options": "i"}},
                    {"email": {"$regex": query_str, "$options": "i"}},
                    {"phone": {"$regex": query_str, "$options": "i"}},
                    {"address": {"$regex": query_str, "$options": "i"}},
                    {"notes": {"$regex": query_str, "$options": "i"}}
                ]
            }

        total = await col.count_documents(filter_query)
        cursor = col.find(filter_query).sort("created_at", -1).skip(skip).limit(limit)

        items: List[ClientResponse] = []
        async for doc in cursor:
            items.append(_mongo_doc_to_client_response(doc))

        page = (skip // limit) + 1 if limit > 0 else 1
        return ClientListResponse(
            total=total,
            page=page,
            limit=limit,
            items=items
        )

    @staticmethod
    async def update_client(
        client_id: str,
        data: ClientUpdate,
        current_username: Optional[str] = None
    ) -> ClientResponse:
        """Update existing client attributes in MongoDB."""
        if not ObjectId.is_valid(client_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID format"
            )

        col = MongoDBManager.get_collection("clients")
        oid = ObjectId(client_id)

        existing = await col.find_one({"_id": oid})
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )

        # Build update fields
        update_fields: Dict[str, Any] = {}
        if data.name is not None:
            update_fields["name"] = data.name.strip()
        if data.email is not None:
            new_email = data.email.lower().strip()
            # Check uniqueness against other clients
            conflict = await col.find_one({"email": new_email, "_id": {"$ne": oid}})
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{new_email}' is already in use by another client"
                )
            update_fields["email"] = new_email
        if data.phone is not None:
            update_fields["phone"] = data.phone.strip() if data.phone else None
        if data.company is not None:
            update_fields["company"] = data.company.strip() if data.company else None
        if data.address is not None:
            update_fields["address"] = data.address.strip() if data.address else None
        if data.notes is not None:
            update_fields["notes"] = data.notes.strip() if data.notes else None
        if data.metadata is not None:
            update_fields["metadata"] = data.metadata

        if not update_fields:
            return _mongo_doc_to_client_response(existing)

        update_fields["updated_at"] = datetime.now(timezone.utc)
        if current_username:
            update_fields["updated_by"] = current_username

        try:
            updated_doc = await col.find_one_and_update(
                {"_id": oid},
                {"$set": update_fields},
                return_document=True
            )
            return _mongo_doc_to_client_response(updated_doc)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already in use by another client"
            )

    @staticmethod
    async def delete_client(client_id: str) -> bool:
        """Delete client record from MongoDB."""
        if not ObjectId.is_valid(client_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid client ID format"
            )

        col = MongoDBManager.get_collection("clients")
        res = await col.delete_one({"_id": ObjectId(client_id)})
        if res.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        return True
