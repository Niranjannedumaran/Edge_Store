import hashlib
import time
from typing import Dict, Any, List
from backend.app.hal.interfaces import ReplicationProvider, StorageProvider
from backend.app.config import ReplicaSyncState
from backend.app.core.logger import logger


class SimulationReplicationProvider(ReplicationProvider):
    """
    Simulation Replication Provider.
    Performs real data transfer between StorageProvider instances using buffer copy
    and authentic SHA-256 verification, reflecting rsync-like guarantees.
    """

    def __init__(self):
        self._state: ReplicaSyncState = ReplicaSyncState.SYNCED
        self._last_sync_timestamp: float = time.time()
        self._total_synced_files: int = 0
        self._failed_files: List[str] = []
        self._simulate_failure_mode: bool = False

    def replicate(self, relative_path: str, source: StorageProvider, target: StorageProvider) -> bool:
        if self._simulate_failure_mode:
            logger.error(f"[Replication Engine] Simulated failure mode active, failing replication of {relative_path}")
            self._state = ReplicaSyncState.FAILED
            if relative_path not in self._failed_files:
                self._failed_files.append(relative_path)
            return False

        if not source.is_available():
            logger.error(f"[Replication Engine] Source storage is unavailable for {relative_path}")
            self._state = ReplicaSyncState.DEGRADED
            return False

        if not target.is_available():
            logger.error(f"[Replication Engine] Target replica storage is unavailable for {relative_path}")
            self._state = ReplicaSyncState.DEGRADED
            if relative_path not in self._failed_files:
                self._failed_files.append(relative_path)
            return False

        self._state = ReplicaSyncState.RUNNING
        try:
            # Read from source
            data = source.read(relative_path)
            source_checksum = hashlib.sha256(data).hexdigest()

            # Write to target
            target.write(relative_path, data)

            # Verification step: read back from target and verify SHA-256
            if not self.verify(relative_path, source_checksum, target):
                self._state = ReplicaSyncState.FAILED
                if relative_path not in self._failed_files:
                    self._failed_files.append(relative_path)
                return False

            self._total_synced_files += 1
            if relative_path in self._failed_files:
                self._failed_files.remove(relative_path)

            self._last_sync_timestamp = time.time()
            self._state = ReplicaSyncState.SYNCED if not self._failed_files else ReplicaSyncState.DEGRADED
            logger.info(f"[Replication Engine] Successfully replicated & verified {relative_path} (SHA-256: {source_checksum[:12]}...)")
            return True
        except Exception as e:
            logger.error(f"[Replication Engine] Replication failed for {relative_path}: {e}")
            self._state = ReplicaSyncState.FAILED
            if relative_path not in self._failed_files:
                self._failed_files.append(relative_path)
            return False

    def rebuild(self, source: StorageProvider, target: StorageProvider) -> Dict[str, Any]:
        """
        Semi-automated rebuild workflow:
        Copies all files present on healthy source to replacement target volume, verifying each one.
        """
        logger.warning("[Replication Engine] Initiating Semi-Automated Replica Rebuild...")
        self._state = ReplicaSyncState.RECOVERING

        if not source.is_available() or not target.is_available():
            self._state = ReplicaSyncState.DEGRADED
            return {
                "success": False,
                "message": "Both source and target storage must be available and mounted to perform rebuild.",
                "rebuilt_count": 0,
                "errors": ["Storage unavailable"]
            }

        files_to_sync = source.list()
        rebuilt_count = 0
        errors = []

        for rel_path in files_to_sync:
            success = self.replicate(rel_path, source, target)
            if success:
                rebuilt_count += 1
            else:
                errors.append(f"Failed to rebuild {rel_path}")

        if not errors:
            self._state = ReplicaSyncState.SYNCED
            self._failed_files.clear()
            self._last_sync_timestamp = time.time()
            logger.info(f"[Replication Engine] Rebuild complete. Successfully synchronized {rebuilt_count} files.")
            return {
                "success": True,
                "message": f"Successfully rebuilt {rebuilt_count} files to replica.",
                "rebuilt_count": rebuilt_count,
                "errors": []
            }
        else:
            self._state = ReplicaSyncState.DEGRADED
            logger.error(f"[Replication Engine] Rebuild completed with {len(errors)} errors.")
            return {
                "success": False,
                "message": f"Rebuild completed with errors. Rebuilt: {rebuilt_count}/{len(files_to_sync)}",
                "rebuilt_count": rebuilt_count,
                "errors": errors
            }

    def verify(self, relative_path: str, expected_checksum: str, provider: StorageProvider) -> bool:
        try:
            data = provider.read(relative_path)
            actual_checksum = hashlib.sha256(data).hexdigest()
            is_valid = actual_checksum.lower() == expected_checksum.lower()
            if not is_valid:
                logger.error(f"[Replication Engine] Checksum mismatch on {relative_path}: expected {expected_checksum}, got {actual_checksum}")
            return is_valid
        except Exception as e:
            logger.error(f"[Replication Engine] Verify read exception for {relative_path}: {e}")
            return False

    def retry(self, relative_path: str) -> bool:
        # Handled at service layer with references to providers
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self._state.value,
            "last_sync_timestamp": self._last_sync_timestamp,
            "total_synced_files": self._total_synced_files,
            "failed_files": list(self._failed_files),
            "pending_count": len(self._failed_files),
            "is_simulated": True,
            "engine": "Simulation-BufferSync (rsync-equivalent with SHA-256 verification)"
        }

    # Simulation Fault Injection
    def set_simulate_failure_mode(self, enabled: bool):
        logger.warning(f"Hardware Simulation: Replication simulate_failure_mode = {enabled}")
        self._simulate_failure_mode = enabled
        if enabled:
            self._state = ReplicaSyncState.FAILED
