import os
import shutil
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any, List
from backend.app.hal.interfaces import StorageProvider
from backend.app.config import settings
from backend.app.core.exceptions import StorageUnavailableException
from backend.app.core.logger import logger


class LocalStorageProvider(StorageProvider):
    """
    Production-oriented Local / Docker Persistent Storage Provider.
    Works directly with local filesystem directories and Docker volume bind mounts.
    Provides:
    - Path traversal containment
    - Atomic writes (temp write -> verify checksum -> atomic rename)
    - Real disk capacity monitoring and disk-exhaustion rejection
    """

    def __init__(self, root_path: str | Path, label: str = "Volume"):
        self.root_path = Path(root_path).resolve()
        self.label = label
        self._mounted: bool = True
        self._tmp_dir = self.root_path / ".tmp"

    def initialize(self) -> bool:
        """Create root storage directory and temporary scratch folder if missing."""
        try:
            self.root_path.mkdir(parents=True, exist_ok=True)
            self._tmp_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialized persistent storage for {self.label} at {self.root_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize persistent storage for {self.label}: {e}")
            return False

    def is_available(self) -> bool:
        return self._mounted and self.root_path.exists() and os.access(self.root_path, os.W_OK)

    def is_mounted(self) -> bool:
        return self._mounted

    def mount(self) -> bool:
        self._mounted = True
        logger.info(f"Mounted persistent volume {self.label}")
        return True

    def unmount(self) -> bool:
        self._mounted = False
        logger.info(f"Unmounted persistent volume {self.label}")
        return True

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Strictly resolve and contain relative path within root_path."""
        if not relative_path:
            raise StorageUnavailableException("Empty path rejected")

        # Sanitize slashes
        clean_rel = relative_path.replace("\\", "/").lstrip("/")
        target = (self.root_path / clean_rel).resolve()

        # Path traversal guard
        try:
            target.relative_to(self.root_path)
        except ValueError:
            logger.warning(f"Path traversal attempt blocked: '{relative_path}' outside '{self.root_path}'")
            raise StorageUnavailableException("Path traversal attempt detected")

        return target

    def get_capacity(self) -> int:
        return self.get_usage()["total"]

    def get_usage(self) -> Dict[str, Any]:
        """Calculates real filesystem disk usage using shutil.disk_usage."""
        if not self.root_path.exists():
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        try:
            usage = shutil.disk_usage(self.root_path)
            pct = round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0.0
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": pct
            }
        except Exception as e:
            logger.error(f"Failed to read disk usage for {self.label}: {e}")
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}

    def get_status(self) -> Dict[str, Any]:
        usage = self.get_usage()
        if not self.root_path.exists():
            drive_state = "disconnected"
        elif not self._mounted:
            drive_state = "unmounted"
        elif not os.access(self.root_path, os.W_OK):
            drive_state = "degraded"
        else:
            drive_state = "healthy"

        return {
            "label": self.label,
            "path": str(self.root_path),
            "state": drive_state,
            "mounted": self._mounted,
            "is_available": self.is_available(),
            "capacity_bytes": usage["total"],
            "used_bytes": usage["used"],
            "free_bytes": usage["free"],
            "percent_used": usage["percent"],
            "is_simulated": False,
            "luks_active": False,  # Truthful reporting in Phase 1 Docker / Local
            "hardware_notice": "Hardware encryption integration not active in Phase 1 (Docker Mode)"
        }

    def write(self, relative_path: str, data: bytes) -> bool:
        """
        Safe Atomic File Write:
        1. Check disk capacity headroom to prevent disk exhaustion.
        2. Write to temporary file in .tmp.
        3. Flush and sync to disk.
        4. Validate written checksum.
        5. Atomically replace target file.
        """
        if not self.is_available():
            raise StorageUnavailableException(f"Cannot write to {self.label}: volume is offline or unmounted")

        target = self._resolve_safe_path(relative_path)
        data_len = len(data)

        # Disk-full protection check
        usage = self.get_usage()
        if usage["free"] < (data_len + settings.MIN_FREE_DISK_BYTES):
            logger.error(f"Disk full guard on {self.label}: required {data_len} + {settings.MIN_FREE_DISK_BYTES}, free: {usage['free']}")
            raise StorageUnavailableException("Insufficient storage capacity on device. Write operation aborted.")

        target.parent.mkdir(parents=True, exist_ok=True)
        self._tmp_dir.mkdir(parents=True, exist_ok=True)

        tmp_path = self._tmp_dir / f"{uuid.uuid4().hex}.tmp"
        try:
            with open(tmp_path, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            # Verify written checksum
            written_hash = hashlib.sha256(tmp_path.read_bytes()).hexdigest()
            expected_hash = hashlib.sha256(data).hexdigest()
            if written_hash != expected_hash:
                raise StorageUnavailableException("Data verification failed during atomic write")

            # Atomic move / replace
            os.replace(tmp_path, target)
            logger.info(f"[{self.label}] Atomically written {data_len} bytes to {relative_path}")
            return True
        except Exception as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            logger.error(f"Write failure on {self.label} for {relative_path}: {e}")
            raise
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def read(self, relative_path: str) -> bytes:
        if not self.is_available():
            raise StorageUnavailableException(f"Cannot read from {self.label}: volume is offline or unmounted")

        target = self._resolve_safe_path(relative_path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File '{relative_path}' not found on {self.label}")

        with open(target, "rb") as f:
            return f.read()

    def delete(self, relative_path: str) -> bool:
        if not self.is_available():
            raise StorageUnavailableException(f"Cannot delete from {self.label}: volume is offline or unmounted")

        target = self._resolve_safe_path(relative_path)
        if target.exists() and target.is_file():
            target.unlink()
            logger.info(f"[{self.label}] Deleted {relative_path}")
            return True
        return False

    def exists(self, relative_path: str) -> bool:
        if not self.is_available():
            return False
        try:
            target = self._resolve_safe_path(relative_path)
            return target.exists() and target.is_file()
        except Exception:
            return False

    def list(self, subpath: str = "") -> List[str]:
        if not self.is_available():
            return []

        search_dir = self._resolve_safe_path(subpath) if subpath else self.root_path
        if not search_dir.exists():
            return []

        rel_paths = []
        for p in search_dir.rglob("*"):
            # Exclude scratch .tmp directory and hidden files
            if p.is_file() and not str(p).startswith(str(self._tmp_dir)) and p.name != ".gitkeep":
                rel_paths.append(str(p.relative_to(self.root_path)).replace("\\", "/"))
        return rel_paths
