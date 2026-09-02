import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from backend.app.hal.interfaces import StorageProvider
from backend.app.config import DriveState
from backend.app.core.exceptions import StorageUnavailableException
from backend.app.core.logger import logger


class LinuxStorageProvider(StorageProvider):
    """
    Real Linux Storage Provider for physical Raspberry Pi 4 deployment.
    Interfaces directly with Linux mountpoints, mounted LUKS volumes (/dev/mapper/*),
    and validates filesystem status via statvfs / df / lsblk.
    """

    def __init__(self, device_path: str, mount_point: str, label: str = "LinuxDrive"):
        self.device_path = device_path
        self.mount_point = Path(mount_point).resolve()
        self.label = label
        self._drive_state = DriveState.HEALTHY

    def initialize(self) -> bool:
        try:
            self.mount_point.mkdir(parents=True, exist_ok=True)
            return self.is_available()
        except Exception as e:
            logger.error(f"[{self.label}] Linux storage initialization error: {e}")
            return False

    def is_mounted(self) -> bool:
        if not self.mount_point.exists():
            return False
        # On Linux, os.path.ismount checks if directory is a mount point
        return os.path.ismount(str(self.mount_point))

    def is_available(self) -> bool:
        return self.is_mounted() and os.access(str(self.mount_point), os.W_OK | os.R_OK)

    def mount(self) -> bool:
        if self.is_mounted():
            return True
        try:
            res = subprocess.run(
                ["mount", self.device_path, str(self.mount_point)],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                logger.info(f"[{self.label}] Mounted {self.device_path} to {self.mount_point}")
                return True
            else:
                logger.error(f"[{self.label}] Mount failed: {res.stderr}")
                return False
        except Exception as e:
            logger.error(f"[{self.label}] Mount exception: {e}")
            return False

    def unmount(self) -> bool:
        if not self.is_mounted():
            return True
        try:
            # Sync buffers before unmount
            subprocess.run(["sync"], check=False)
            res = subprocess.run(
                ["umount", str(self.mount_point)],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                logger.info(f"[{self.label}] Unmounted {self.mount_point}")
                return True
            else:
                logger.error(f"[{self.label}] Unmount failed: {res.stderr}")
                return False
        except Exception as e:
            logger.error(f"[{self.label}] Unmount exception: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        usage = self.get_usage()
        mounted = self.is_mounted()
        return {
            "label": self.label,
            "device": self.device_path,
            "mount_point": str(self.mount_point),
            "mounted": mounted,
            "is_available": self.is_available(),
            "capacity_bytes": usage["total"],
            "used_bytes": usage["used"],
            "free_bytes": usage["free"],
            "percent_used": usage["percent"],
            "is_simulated": False
        }

    def get_capacity(self) -> int:
        return self.get_usage()["total"]

    def get_usage(self) -> Dict[str, Any]:
        if not self.is_mounted():
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}
        try:
            usage = shutil.disk_usage(self.mount_point)
            pct = round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0.0
            return {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": pct
            }
        except Exception as e:
            logger.error(f"[{self.label}] Error calculating disk usage: {e}")
            return {"total": 0, "used": 0, "free": 0, "percent": 0.0}

    def write(self, relative_path: str, data: bytes) -> bool:
        if not self.is_available():
            raise StorageUnavailableException(f"Storage volume {self.label} is unmounted or read-only")
        target = (self.mount_point / relative_path).resolve()
        if not str(target).startswith(str(self.mount_point)):
            raise StorageUnavailableException("Path traversal attempt detected")

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        # Flush to physical storage
        f_dir = os.open(str(target.parent), os.O_RDONLY)
        try:
            os.fsync(f_dir)
        finally:
            os.close(f_dir)
        return True

    def read(self, relative_path: str) -> bytes:
        if not self.is_available():
            raise StorageUnavailableException(f"Storage volume {self.label} is unmounted or offline")
        target = (self.mount_point / relative_path).resolve()
        if not str(target).startswith(str(self.mount_point)):
            raise StorageUnavailableException("Path traversal attempt detected")
        if not target.exists():
            raise FileNotFoundError(f"File {relative_path} does not exist on {self.label}")

        with open(target, "rb") as f:
            return f.read()

    def delete(self, relative_path: str) -> bool:
        if not self.is_available():
            raise StorageUnavailableException(f"Storage volume {self.label} is unmounted or offline")
        target = (self.mount_point / relative_path).resolve()
        if not str(target).startswith(str(self.mount_point)):
            raise StorageUnavailableException("Path traversal attempt detected")
        if target.exists():
            target.unlink()
            return True
        return False

    def exists(self, relative_path: str) -> bool:
        if not self.is_available():
            return False
        target = (self.mount_point / relative_path).resolve()
        return target.exists() and str(target).startswith(str(self.mount_point))

    def list(self, subpath: str = "") -> List[str]:
        if not self.is_available():
            return []
        search_dir = (self.mount_point / subpath).resolve()
        if not search_dir.exists():
            return []
        rel_paths = []
        for p in search_dir.rglob("*"):
            if p.is_file() and p.name != ".gitkeep":
                rel_paths.append(str(p.relative_to(self.mount_point)).replace("\\", "/"))
        return rel_paths
