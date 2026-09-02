import subprocess
from pathlib import Path
from typing import Dict, Any
from backend.app.hal.interfaces import EncryptionProvider
from backend.app.config import VaultState
from backend.app.core.logger import logger


class LinuxEncryptionProvider(EncryptionProvider):
    """
    Real Linux LUKS2 Encryption Provider.
    Interfaces directly with Linux cryptsetup and dm-crypt kernel subsystem.
    Executes 'cryptsetup luksOpen' using piped key material to avoid disk exposure,
    and 'cryptsetup luksClose' for safe locking.
    """

    def __init__(self, raw_device_path: str, mapper_name: str):
        self.raw_device_path = raw_device_path
        self.mapper_name = mapper_name
        self.mapper_path = Path(f"/dev/mapper/{mapper_name}")

    def is_unlocked(self) -> bool:
        """Check if mapped block device exists and crypt status is active."""
        if not self.mapper_path.exists():
            return False
        try:
            res = subprocess.run(
                ["cryptsetup", "status", self.mapper_name],
                capture_output=True,
                text=True,
                check=False
            )
            return res.returncode == 0 and "is active" in res.stdout
        except Exception:
            return False

    def unlock(self, key_material: bytes) -> bool:
        if self.is_unlocked():
            return True
        try:
            # Safely pipe key material via stdin into cryptsetup
            proc = subprocess.Popen(
                ["cryptsetup", "luksOpen", self.raw_device_path, self.mapper_name, "--key-file", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = proc.communicate(input=key_material)
            if proc.returncode == 0:
                logger.info(f"[LUKS2] Successfully unlocked {self.raw_device_path} -> /dev/mapper/{self.mapper_name}")
                return True
            else:
                logger.error(f"[LUKS2] luksOpen failed: {stderr.decode('utf-8', errors='ignore')}")
                return False
        except Exception as e:
            logger.error(f"[LUKS2] Unlock exception: {e}")
            return False

    def lock(self) -> bool:
        if not self.is_unlocked():
            return True
        try:
            # Sync filesystem before closing mapper
            subprocess.run(["sync"], check=False)
            res = subprocess.run(
                ["cryptsetup", "luksClose", self.mapper_name],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                logger.info(f"[LUKS2] Closed and locked /dev/mapper/{self.mapper_name}")
                return True
            else:
                logger.error(f"[LUKS2] luksClose failed: {res.stderr}")
                return False
        except Exception as e:
            logger.error(f"[LUKS2] Lock exception: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        unlocked = self.is_unlocked()
        state = VaultState.UNLOCKED if unlocked else VaultState.LOCKED
        details = {}
        if unlocked:
            try:
                res = subprocess.run(
                    ["cryptsetup", "status", self.mapper_name],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if res.returncode == 0:
                    details["crypt_info"] = res.stdout.strip()
            except Exception:
                pass

        return {
            "state": state.value,
            "unlocked": unlocked,
            "raw_device": self.raw_device_path,
            "mapper_name": self.mapper_name,
            "cipher": "aes-xts-plain64 (LUKS2)",
            "keysize": 512,
            "hash": "sha256",
            "is_simulated": False,
            "details": details
        }
