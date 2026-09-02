import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from backend.app.hal.interfaces import KeyDeviceProvider
from backend.app.config import KeySDState
from backend.app.core.logger import logger


class LinuxKeyProvider(KeyDeviceProvider):
    """
    Real Linux Key-SD Provider for Raspberry Pi 4.
    Identifies removable Key-SD via stable filesystem UUID (e.g. via blkid / lsblk),
    mounts it safely read-only, reads key material, and unmounts immediately.
    """

    def __init__(self, device_uuid: str, mount_point: str, key_file_name: str = "vault.key"):
        self.device_uuid = device_uuid
        self.mount_point = Path(mount_point).resolve()
        self.key_file_name = key_file_name

    def is_present(self) -> bool:
        """Check if device with target UUID exists in /dev/disk/by-uuid/."""
        uuid_path = Path(f"/dev/disk/by-uuid/{self.device_uuid}")
        return uuid_path.exists()

    def validate(self) -> bool:
        if not self.is_present():
            return False
        # Mount read-only temporarily to inspect key file
        mounted_by_us = False
        try:
            if not os.path.ismount(str(self.mount_point)):
                self.mount_point.mkdir(parents=True, exist_ok=True)
                res = subprocess.run(
                    ["mount", "-o", "ro", f"/dev/disk/by-uuid/{self.device_uuid}", str(self.mount_point)],
                    capture_output=True,
                    check=False
                )
                if res.returncode != 0:
                    return False
                mounted_by_us = True

            keyfile = self.mount_point / self.key_file_name
            valid = keyfile.exists() and keyfile.stat().st_size > 0
            return valid
        except Exception as e:
            logger.error(f"Linux Key-SD validation failed: {e}")
            return False
        finally:
            if mounted_by_us:
                subprocess.run(["umount", str(self.mount_point)], check=False)

    def get_key_material(self) -> Optional[bytes]:
        if not self.is_present():
            return None

        mounted_by_us = False
        try:
            if not os.path.ismount(str(self.mount_point)):
                self.mount_point.mkdir(parents=True, exist_ok=True)
                res = subprocess.run(
                    ["mount", "-o", "ro", f"/dev/disk/by-uuid/{self.device_uuid}", str(self.mount_point)],
                    capture_output=True,
                    check=False
                )
                if res.returncode != 0:
                    return None
                mounted_by_us = True

            keyfile = self.mount_point / self.key_file_name
            if not keyfile.exists():
                return None

            with open(keyfile, "rb") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading Linux Key-SD material: {e}")
            return None
        finally:
            if mounted_by_us:
                subprocess.run(["umount", str(self.mount_point)], check=False)

    def get_status(self) -> Dict[str, Any]:
        present = self.is_present()
        valid = self.validate() if present else False
        state = KeySDState.INSERTED if (present and valid) else (KeySDState.INVALID if present else KeySDState.REMOVED)
        return {
            "state": state.value,
            "present": present,
            "valid": valid,
            "uuid": self.device_uuid,
            "mount_path": str(self.mount_point),
            "key_file": self.key_file_name,
            "is_simulated": False
        }
