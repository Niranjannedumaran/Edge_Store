import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from backend.app.hal.interfaces import StorageProvider
from backend.app.config import DriveState
from backend.app.core.exceptions import StorageUnavailableException
from backend.app.core.logger import logger


class SimulationStorageProvider(StorageProvider):
    """
    Simulation Storage Provider for laptop development.
    Interacts with an authentic local folder on the file system, but encapsulates
    simulated drive hardware and mount states (connected, disconnected, healthy, failed).
    """

    def __init__(self, root_path: str, label: str = "Drive"):
        self.root_path = Path(root_path).resolve()
        self.label = label
        self._drive_state: DriveState = DriveState.HEALTHY
        self._mounted: bool = True
        self._simulated_capacity: int = 500 * 1024 * 1024 * 1024  # 500 GB simulated volume

    def initialize(self) -> bool:
        """Create root directory if missing and ensure writable."""
        try:
            self.root_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialized simulation storage for {self.label} at {self.root_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize simulation storage for {self.label}: {e}")
            self._drive_state = DriveState.FAILED
            return False

    def is_available(self) -> bool:
        """Available only if connected, healthy, and mounted."""
        return (
            self._drive_state in (DriveState.HEALTHY, DriveState.DEGRADED)
            and self._mounted
            and self.root_path.exists()
        )

    def is_mounted(self) -> bool:
        return self._mounted

    def mount(self) -> bool:
        if self._drive_state == DriveState.DISCONNECTED:
            logger.warning(f"Cannot mount {self.label}: device is disconnected")
            return False
        self._mounted = True
        logger.info(f"Mounted simulated volume {self.label}")
        return True

    def unmount(self) -> bool:
        self._mounted = False
        logger.info(f"Unmounted simulated volume {self.label}")
        return True

    def get_status(self) -> Dict[str, Any]:
        usage = self.get_usage()
        return {
            "label": self.label,
            "path": str(self.root_path),
            "state": self._drive_state.value,
            "mounted": self._mounted,
            "is_available": self.is_available(),
            "capacity_bytes": self._simulated_capacity,
            "used_bytes": usage["used"],
            "free_bytes": usage["free"],
            "percent_used": usage["percent"],
            "is_simulated": True,
        }

    def get_capacity(self) -> int:
        return self._simulated_capacity

    def get_usage(self) -> Dict[str, Any]:
        """Calculates actual files size inside the simulated directory against the simulated quota."""
        total_used = 0
        if self.root_path.exists() and self._mounted:
            for dirpath, _, filenames in os.walk(self.root_path):
                for f in filenames:
                    if f != ".gitkeep":
                        fp = os.path.join(dirpath, f)
                        if os.path.isfile(fp):
                            total_used += os.path.getsize(fp)

        free = max(0, self._simulated_capacity - total_used)
        pct = round((total_used / self._simulated_capacity) * 100, 2) if self._simulated_capacity > 0 else 0.0
        return {
            "total": self._simulated_capacity,
            "used": total_used,
            "free": free,
            "percent": pct
        }

    def write(self, relative_path: str, data: bytes) -> bool:
        self._check_io_allowed("write")
        target = (self.root_path / relative_path).resolve()
        # Security: Prevent path traversal
        if not str(target).startswith(str(self.root_path)):
            raise StorageUnavailableException("Path traversal attempt detected")

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        logger.info(f"[{self.label}] Written {len(data)} bytes to {relative_path}")
        return True

    def read(self, relative_path: str) -> bytes:
        self._check_io_allowed("read")
        target = (self.root_path / relative_path).resolve()
        if not str(target).startswith(str(self.root_path)):
            raise StorageUnavailableException("Path traversal attempt detected")

        if not target.exists():
            raise FileNotFoundError(f"File {relative_path} does not exist on {self.label}")

        with open(target, "rb") as f:
            return f.read()

    def delete(self, relative_path: str) -> bool:
        self._check_io_allowed("delete")
        target = (self.root_path / relative_path).resolve()
        if not str(target).startswith(str(self.root_path)):
            raise StorageUnavailableException("Path traversal attempt detected")

        if target.exists():
            target.unlink()
            logger.info(f"[{self.label}] Deleted {relative_path}")
            return True
        return False

    def exists(self, relative_path: str) -> bool:
        if not self.is_available():
            return False
        target = (self.root_path / relative_path).resolve()
        return target.exists() and str(target).startswith(str(self.root_path))

    def list(self, subpath: str = "") -> List[str]:
        self._check_io_allowed("list")
        search_dir = (self.root_path / subpath).resolve()
        if not search_dir.exists():
            return []

        rel_paths = []
        for p in search_dir.rglob("*"):
            if p.is_file() and p.name != ".gitkeep":
                rel_paths.append(str(p.relative_to(self.root_path)).replace("\\", "/"))
        return rel_paths

    def _check_io_allowed(self, operation: str):
        if not self._mounted:
            raise StorageUnavailableException(f"Cannot perform {operation} on {self.label}: Volume is unmounted")
        if self._drive_state == DriveState.DISCONNECTED:
            raise StorageUnavailableException(f"Cannot perform {operation} on {self.label}: Drive is disconnected")
        if self._drive_state == DriveState.FAILED:
            raise StorageUnavailableException(f"Hardware I/O error on {self.label}: Drive has failed")

    # Fault injection controls for simulation testing
    def set_drive_state(self, state: DriveState):
        logger.warning(f"Hardware simulation: Changing {self.label} state from {self._drive_state.value} to {state.value}")
        self._drive_state = state

    def simulate_failure(self):
        self.set_drive_state(DriveState.FAILED)

    def simulate_disconnect(self):
        self.set_drive_state(DriveState.DISCONNECTED)
        self._mounted = False

    def simulate_connect(self):
        self.set_drive_state(DriveState.HEALTHY)
        self._mounted = True

    def simulate_recovery(self):
        self.set_drive_state(DriveState.HEALTHY)
        self._mounted = True
