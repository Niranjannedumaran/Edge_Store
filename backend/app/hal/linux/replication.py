import subprocess
import hashlib
import time
from typing import Dict, Any, List
from backend.app.hal.interfaces import ReplicationProvider, StorageProvider
from backend.app.config import ReplicaSyncState
from backend.app.core.logger import logger


class LinuxReplicationProvider(ReplicationProvider):
    """
    Real Linux Replication Provider.
    Leverages Linux-native rsync utility with archive mode, inplace writing,
    and post-copy SHA-256 verification.
    """

    def __init__(self):
        self._state = ReplicaSyncState.SYNCED
        self._last_sync_timestamp = time.time()
        self._total_synced_files = 0
        self._failed_files: List[str] = []

    def replicate(self, relative_path: str, source: StorageProvider, target: StorageProvider) -> bool:
        if not source.is_available() or not target.is_available():
            self._state = ReplicaSyncState.DEGRADED
            return False

        self._state = ReplicaSyncState.RUNNING
        try:
            # We can use direct rsync for the single file
            src_file = str(source.mount_point / relative_path)
            tgt_file = str(target.mount_point / relative_path)

            res = subprocess.run(
                ["rsync", "-avz", "--checksum", src_file, tgt_file],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                # Compute and verify SHA-256 on target
                with open(src_file, "rb") as f:
                    expected_hash = hashlib.sha256(f.read()).hexdigest()

                if self.verify(relative_path, expected_hash, target):
                    self._state = ReplicaSyncState.SYNCED
                    self._total_synced_files += 1
                    self._last_sync_timestamp = time.time()
                    if relative_path in self._failed_files:
                        self._failed_files.remove(relative_path)
                    logger.info(f"[rsync] Replicated and verified {relative_path}")
                    return True

            self._state = ReplicaSyncState.FAILED
            if relative_path not in self._failed_files:
                self._failed_files.append(relative_path)
            logger.error(f"[rsync] Replication failed for {relative_path}: {res.stderr}")
            return False
        except Exception as e:
            logger.error(f"[rsync] Replication exception: {e}")
            self._state = ReplicaSyncState.FAILED
            if relative_path not in self._failed_files:
                self._failed_files.append(relative_path)
            return False

    def rebuild(self, source: StorageProvider, target: StorageProvider) -> Dict[str, Any]:
        logger.warning("[rsync Rebuild] Starting full volume rsync synchronization...")
        self._state = ReplicaSyncState.RECOVERING

        if not source.is_available() or not target.is_available():
            self._state = ReplicaSyncState.DEGRADED
            return {
                "success": False,
                "message": "Source or target volume unavailable",
                "rebuilt_count": 0,
                "errors": ["Storage unavailable"]
            }

        try:
            src_dir = f"{source.mount_point}/"
            tgt_dir = f"{target.mount_point}/"

            res = subprocess.run(
                ["rsync", "-avz", "--delete", "--checksum", src_dir, tgt_dir],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                self._state = ReplicaSyncState.SYNCED
                self._failed_files.clear()
                self._last_sync_timestamp = time.time()
                logger.info("[rsync Rebuild] Full synchronization completed successfully.")
                return {
                    "success": True,
                    "message": "Full replica volume rebuilt successfully via rsync.",
                    "rebuilt_count": len(target.list()),
                    "errors": []
                }
            else:
                self._state = ReplicaSyncState.DEGRADED
                logger.error(f"[rsync Rebuild] rsync exited with error: {res.stderr}")
                return {
                    "success": False,
                    "message": f"rsync rebuild failed: {res.stderr}",
                    "rebuilt_count": 0,
                    "errors": [res.stderr]
                }
        except Exception as e:
            self._state = ReplicaSyncState.DEGRADED
            logger.error(f"[rsync Rebuild] Exception: {e}")
            return {
                "success": False,
                "message": f"rsync rebuild exception: {e}",
                "rebuilt_count": 0,
                "errors": [str(e)]
            }

    def verify(self, relative_path: str, expected_checksum: str, provider: StorageProvider) -> bool:
        try:
            data = provider.read(relative_path)
            actual = hashlib.sha256(data).hexdigest()
            return actual.lower() == expected_checksum.lower()
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "last_sync_timestamp": self._last_sync_timestamp,
            "total_synced_files": self._total_synced_files,
            "failed_files": list(self._failed_files),
            "pending_count": len(self._failed_files),
            "is_simulated": False,
            "engine": "Linux-rsync (native block delta & checksum)"
        }
