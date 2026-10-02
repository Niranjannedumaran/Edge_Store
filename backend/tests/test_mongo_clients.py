import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime, timezone
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.client import ClientCreate, ClientUpdate
from backend.app.services.client_service import ClientService
from backend.app.core.security import create_access_token


@pytest.fixture
def mock_clients_col():
    """Mock MongoDB async collection for unit testing without live daemon."""
    col = MagicMock()
    col.find_one = AsyncMock()
    col.insert_one = AsyncMock()
    col.count_documents = AsyncMock()
    col.find = MagicMock()
    col.find_one_and_update = AsyncMock()
    col.delete_one = AsyncMock()
    return col


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "admin", "role": "super_admin"})
    return {"Authorization": f"Bearer {token}"}


class TestClientService:
    @pytest.mark.asyncio
    async def test_create_client_success(self, mock_clients_col):
        mock_clients_col.find_one.return_value = None
        fake_id = ObjectId()
        mock_clients_col.insert_one.return_value = MagicMock(inserted_id=fake_id)

        with patch("backend.app.db.mongo.MongoDBManager.get_collection", return_value=mock_clients_col):
            req = ClientCreate(
                name="Acme Corp",
                email="contact@acme.com",
                phone="+1-555-0199",
                company="Acme Global",
                address="100 Enterprise Way",
                notes="Primary partner"
            )
            client = await ClientService.create_client(req, current_username="admin")

            assert client.name == "Acme Corp"
            assert client.email == "contact@acme.com"
            assert client.id == str(fake_id)
            assert client.created_by == "admin"
            assert mock_clients_col.insert_one.called

    @pytest.mark.asyncio
    async def test_create_client_duplicate_email(self, mock_clients_col):
        mock_clients_col.find_one.return_value = {"_id": ObjectId(), "email": "exists@domain.com"}

        with patch("backend.app.db.mongo.MongoDBManager.get_collection", return_value=mock_clients_col):
            req = ClientCreate(
                name="Duplicate User",
                email="exists@domain.com"
            )
            with pytest.raises(HTTPException) as exc:
                await ClientService.create_client(req)
            assert exc.value.status_code == 409
            assert "already exists" in exc.value.detail

    @pytest.mark.asyncio
    async def test_get_client_by_id_not_found(self, mock_clients_col):
        fake_id = str(ObjectId())
        mock_clients_col.find_one.return_value = None

        with patch("backend.app.db.mongo.MongoDBManager.get_collection", return_value=mock_clients_col):
            with pytest.raises(HTTPException) as exc:
                await ClientService.get_client_by_id(fake_id)
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_client_invalid_id_format(self):
        with pytest.raises(HTTPException) as exc:
            await ClientService.get_client_by_id("invalid-not-an-oid")
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_client_success(self, mock_clients_col):
        oid = ObjectId()
        now = datetime.now(timezone.utc)
        mock_clients_col.find_one.side_effect = [
            {"_id": oid, "name": "Old Name", "email": "old@test.com", "created_at": now, "updated_at": now},  # existence check
            None  # email conflict check
        ]
        mock_clients_col.find_one_and_update.return_value = {
            "_id": oid,
            "name": "New Name",
            "email": "new@test.com",
            "phone": "+1-111-2222",
            "created_at": now,
            "updated_at": now,
            "created_by": "admin"
        }

        with patch("backend.app.db.mongo.MongoDBManager.get_collection", return_value=mock_clients_col):
            update_req = ClientUpdate(name="New Name", email="new@test.com", phone="+1-111-2222")
            res = await ClientService.update_client(str(oid), update_req, current_username="editor")
            assert res.name == "New Name"
            assert res.email == "new@test.com"
            assert mock_clients_col.find_one_and_update.called

    @pytest.mark.asyncio
    async def test_delete_client_success(self, mock_clients_col):
        mock_clients_col.delete_one.return_value = MagicMock(deleted_count=1)

        with patch("backend.app.db.mongo.MongoDBManager.get_collection", return_value=mock_clients_col):
            res = await ClientService.delete_client(str(ObjectId()))
            assert res is True

    @pytest.mark.asyncio
    async def test_delete_client_not_found(self, mock_clients_col):
        mock_clients_col.delete_one.return_value = MagicMock(deleted_count=0)

        with patch("backend.app.db.mongo.MongoDBManager.get_collection", return_value=mock_clients_col):
            with pytest.raises(HTTPException) as exc:
                await ClientService.delete_client(str(ObjectId()))
            assert exc.value.status_code == 404


class TestClientEndpoints:
    def test_unauthorized_access_on_protected_delete(self):
        client = TestClient(app)
        # DELETE requires authenticated operator
        response = client.delete("/api/clients/507f1f77bcf86cd799439011")
        assert response.status_code == 401
