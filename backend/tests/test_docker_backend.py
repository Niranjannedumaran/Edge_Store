import os
import shutil
import hashlib
import tempfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import settings, EnvironmentMode
from backend.app.hal.local_storage import LocalStorageProvider
from backend.app.hal.docker_hal import (
    DockerReplicationProvider,
    DockerEncryptionProvider,
    DockerHardwareAuthProvider,
    DockerPowerProvider,
    DockerSystemMonitorProvider
)
from backend.app.core.exceptions import StorageUnavailableException, ValidationException


@pytest.fixture
def temp_storage_dirs():
    """Create isolated temporary primary and replica directories for testing."""
    tmp_primary = Path(tempfile.mkdtemp(prefix="edgestore_test_primary_"))
    tmp_replica = Path(tempfile.mkdtemp(prefix="edgestore_test_replica_"))
    yield tmp_primary, tmp_replica
    shutil.rmtree(tmp_primary, ignore_errors=True)
    shutil.rmtree(tmp_replica, ignore_errors=True)


class TestLocalStorageProvider:
    def test_initialization_and_status(self, temp_storage_dirs):
        primary_dir, _ = temp_storage_dirs
        provider = LocalStorageProvider(primary_dir, label="TestPrimary")
        assert provider.initialize() is True
        assert provider.is_available() is True
        assert provider.is_mounted() is True

        status = provider.get_status()
        assert status["state"] == "healthy"
        assert status["mounted"] is True
        assert status["is_available"] is True
        assert status["is_simulated"] is False
        assert status["luks_active"] is False
        assert "Hardware encryption integration not active in Phase 1" in status["hardware_notice"]

    def test_atomic_write_and_read(self, temp_storage_dirs):
        primary_dir, _ = temp_storage_dirs
        provider = LocalStorageProvider(primary_dir, label="TestPrimary")
        provider.initialize()

        data = b"Real persistent storage payload test 123"
        rel_path = "test/subfolder/file.dat"

        assert provider.write(rel_path, data) is True
        assert provider.exists(rel_path) is True

        read_back = provider.read(rel_path)
        assert read_back == data
        assert hashlib.sha256(read_back).hexdigest() == hashlib.sha256(data).hexdigest()

    def test_path_traversal_prevention(self, temp_storage_dirs):
        primary_dir, _ = temp_storage_dirs
        provider = LocalStorageProvider(primary_dir, label="TestPrimary")
        provider.initialize()

        with pytest.raises(StorageUnavailableException):
            provider.write("../../../escape.txt", b"malicious")

        with pytest.raises(StorageUnavailableException):
            provider.read("../../../escape.txt")

    def test_deletion(self, temp_storage_dirs):
        primary_dir, _ = temp_storage_dirs
        provider = LocalStorageProvider(primary_dir, label="TestPrimary")
        provider.initialize()

        rel_path = "delete_me.txt"
        provider.write(rel_path, b"temporary data")
        assert provider.exists(rel_path) is True

        assert provider.delete(rel_path) is True
        assert provider.exists(rel_path) is False


class TestDockerReplication:
    def test_real_replication_and_sha256_verification(self, temp_storage_dirs):
        primary_dir, replica_dir = temp_storage_dirs
        p_provider = LocalStorageProvider(primary_dir, label="Primary")
        r_provider = LocalStorageProvider(replica_dir, label="Replica")
        p_provider.initialize()
        r_provider.initialize()

        engine = DockerReplicationProvider()
        test_file = "vault/doc.pdf"
        test_data = b"Encrypted document replica test payload"

        p_provider.write(test_file, test_data)
        assert r_provider.exists(test_file) is False

        # Execute real replication
        success = engine.replicate(test_file, p_provider, r_provider)
        assert success is True
        assert r_provider.exists(test_file) is True

        # Verify replica has exact matching SHA-256
        replica_data = r_provider.read(test_file)
        assert hashlib.sha256(replica_data).hexdigest() == hashlib.sha256(test_data).hexdigest()

        status = engine.get_status()
        assert status["state"] == "synced"
        assert status["is_simulated"] is False
        assert status["total_synced_files"] == 1
        assert len(status["failed_files"]) == 0

    def test_differential_recovery(self, temp_storage_dirs):
        primary_dir, replica_dir = temp_storage_dirs
        p_provider = LocalStorageProvider(primary_dir, label="Primary")
        r_provider = LocalStorageProvider(replica_dir, label="Replica")
        p_provider.initialize()
        r_provider.initialize()

        engine = DockerReplicationProvider()

        # Write 3 files to primary
        p_provider.write("file1.bin", b"file one data")
        p_provider.write("file2.bin", b"file two data")
        p_provider.write("file3.bin", b"file three data")

        # Manually sync file1 to replica
        r_provider.write("file1.bin", b"file one data")
        # Intentionally corrupt file2 on replica
        r_provider.write("file2.bin", b"corrupted data")
        # Leave file3 completely missing on replica

        # Run differential recovery
        result = engine.rebuild(p_provider, r_provider)
        assert result["success"] is True
        # Already synced: file1. Synced / recovered: file2 (corrupted) + file3 (missing) = 2
        assert result["already_synced_count"] == 1
        assert result["rebuilt_count"] == 2

        # Verify all 3 files now match primary checksums
        for f in ["file1.bin", "file2.bin", "file3.bin"]:
            assert r_provider.exists(f) is True
            assert r_provider.read(f) == p_provider.read(f)


class TestHonestHardwareReporting:
    def test_docker_encryption_provider(self):
        enc = DockerEncryptionProvider()
        status = enc.get_status()
        assert status["unlocked"] is True
        assert status["luks_active"] is False
        assert status["is_simulated"] is False
        assert "Hardware encryption integration not active in Phase 1" in status["hardware_notice"]

    def test_docker_hardware_auth_provider(self):
        auth_prov = DockerHardwareAuthProvider()
        status = auth_prov.get_status()
        assert status["present"] is True
        assert status["is_simulated"] is False
        assert "Hardware authentication integration not active in Phase 1" in status["hardware_notice"]

    def test_docker_power_provider(self):
        power = DockerPowerProvider()
        telemetry = power.get_telemetry()
        assert telemetry["power_source"] == "AC/Mains (Docker Host)"
        assert telemetry["is_simulated"] is False
        assert telemetry["battery_level"] == 100
        assert "Hardware battery/UPS monitoring not active in Phase 1" in telemetry["hardware_notice"]

    def test_docker_system_monitor_provider(self):
        mon = DockerSystemMonitorProvider()
        metrics = mon.get_metrics()
        assert metrics["cpu_percent"] >= 0.0
        assert metrics["memory"]["total"] > 0
        assert metrics["temperature"] is None  # Honest: not available in standard container
        assert metrics["is_simulated"] is False


class TestSecurityAndIDORProtection:
    def test_idor_blocked_between_users(self, client: TestClient, admin_token: str):
        # 1. Login or create user
        reg_res = client.post("/api/admin/users", json={
            "username": "victim_user",
            "password": "Password123!",
            "display_name": "Victim User",
            "role": "file_manager"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert reg_res.status_code in (201, 400)

        # Login as victim
        victim_login = client.post("/api/auth/login", json={
            "username": "victim_user",
            "password": "Password123!"
        })
        victim_token = victim_login.json()["access_token"]

        # Create attacker
        client.post("/api/admin/users", json={
            "username": "attacker_user",
            "password": "Password123!",
            "display_name": "Attacker User",
            "role": "file_manager"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        attacker_login = client.post("/api/auth/login", json={
            "username": "attacker_user",
            "password": "Password123!"
        })
        attacker_token = attacker_login.json()["access_token"]

        # Victim uploads private file
        upload_res = client.post("/api/files/upload", files={
            "file": ("confidential.txt", b"Secret victim notes", "text/plain")
        }, headers={"Authorization": f"Bearer {victim_token}"})
        assert upload_res.status_code == 201
        file_id = upload_res.json()["file"]["id"]

        # Attacker attempts IDOR download
        idor_dl = client.get(f"/api/files/{file_id}/download", headers={
            "Authorization": f"Bearer {attacker_token}"
        })
        assert idor_dl.status_code == 403

        # Attacker attempts IDOR rename
        idor_rename = client.put(f"/api/files/{file_id}/rename", json={
            "new_filename": "hacked.txt"
        }, headers={"Authorization": f"Bearer {attacker_token}"})
        assert idor_rename.status_code == 403

        # Attacker attempts IDOR delete
        idor_del = client.delete(f"/api/files/{file_id}", headers={
            "Authorization": f"Bearer {attacker_token}"
        })
        assert idor_del.status_code == 403

        # Victim can legitimately download their own file
        legit_dl = client.get(f"/api/files/{file_id}/download", headers={
            "Authorization": f"Bearer {victim_token}"
        })
        assert legit_dl.status_code == 200
        assert legit_dl.content == b"Secret victim notes"
