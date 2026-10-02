from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from backend.app.config import DriveState, ReplicaSyncState, KeySDState, VaultState, PowerMode


class StorageProvider(ABC):
    """
    Abstract Hardware Abstraction Layer interface for block storage / file volumes.
    Implemented by SimulationStorageProvider (laptop) and LinuxStorageProvider (Raspberry Pi).
    """

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the storage device/directory and verify accessibility."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if storage volume is connected, online, and healthy."""
        pass

    @abstractmethod
    def is_mounted(self) -> bool:
        """Check if filesystem is currently mounted and writable."""
        pass

    @abstractmethod
    def mount(self) -> bool:
        """Mount the volume to its designated target mountpoint."""
        pass

    @abstractmethod
    def unmount(self) -> bool:
        """Safely flush and unmount the filesystem."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive hardware and filesystem status dictionary."""
        pass

    @abstractmethod
    def get_capacity(self) -> int:
        """Total capacity in bytes."""
        pass

    @abstractmethod
    def get_usage(self) -> Dict[str, Any]:
        """Return usage dictionary containing total, used, free (in bytes), and percent."""
        pass

    @abstractmethod
    def write(self, relative_path: str, data: bytes) -> bool:
        """Write raw binary data to the designated relative path."""
        pass

    @abstractmethod
    def read(self, relative_path: str) -> bytes:
        """Read binary data from the designated relative path."""
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Delete file at relative path."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Check if file exists on volume."""
        pass

    @abstractmethod
    def list(self, subpath: str = "") -> List[str]:
        """List relative file paths residing in the storage volume."""
        pass


class HardwareAuthenticationProvider(ABC):
    """
    Abstract HAL interface for removable physical hardware authentication (Key-SD, cryptographic tokens, USB keys).
    Supports future Key-SD integration, removable device detection, and boot authorization.
    """

    @abstractmethod
    def is_present(self) -> bool:
        """Check physical or environment presence of authentication hardware."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate partition signature, filesystem, and keyfile integrity."""
        pass

    @abstractmethod
    def get_key_material(self) -> Optional[bytes]:
        """Extract securely stored key material from hardware device."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return hardware authentication state dictionary."""
        pass


class KeyDeviceProvider(HardwareAuthenticationProvider):
    """
    Abstract HAL interface for removable physical Key-SD hardware.
    Subclasses HardwareAuthenticationProvider for backward-compatible naming.
    """
    pass


class EncryptionProvider(ABC):
    """
    Abstract HAL interface for LUKS2 disk encryption / simulated vault layer.
    """

    @abstractmethod
    def is_unlocked(self) -> bool:
        """Check if crypt mapped volume is opened / unlocked."""
        pass

    @abstractmethod
    def unlock(self, key_material: bytes) -> bool:
        """Unlock storage using provided key material."""
        pass

    @abstractmethod
    def lock(self) -> bool:
        """Close crypt mapping and securely lock the vault."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return LUKS/vault security status."""
        pass


class ReplicationProvider(ABC):
    """
    Abstract HAL interface for dual-drive data replication engine.
    """

    @abstractmethod
    def replicate(self, relative_path: str, source: StorageProvider, target: StorageProvider) -> bool:
        """Replicate a single file from source volume to target volume with SHA-256 verification."""
        pass

    @abstractmethod
    def rebuild(self, source: StorageProvider, target: StorageProvider) -> Dict[str, Any]:
        """Perform semi-automated total rebuild of target volume from source volume."""
        pass

    @abstractmethod
    def verify(self, relative_path: str, expected_checksum: str, provider: StorageProvider) -> bool:
        """Compute SHA-256 on target provider and verify against expected checksum."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return replication state machine telemetry."""
        pass


class PowerProvider(ABC):
    """
    Abstract HAL interface for Battery/UPS telemetry and power management.
    """

    @abstractmethod
    def get_battery_level(self) -> int:
        """Return battery percentage (0 - 100)."""
        pass

    @abstractmethod
    def is_charging(self) -> bool:
        """Return True if AC/mains power is connected and charging."""
        pass

    @abstractmethod
    def get_power_mode(self) -> PowerMode:
        """Return current power policy mode (NORMAL, CONSERVATION, CRITICAL)."""
        pass

    @abstractmethod
    def get_telemetry(self) -> Dict[str, Any]:
        """Return power telemetry dictionary."""
        pass


class SystemMonitorProvider(ABC):
    """
    Abstract HAL interface for system resources (CPU, RAM, temperature, uptime).
    """

    @abstractmethod
    def get_cpu_percent(self) -> float:
        """CPU utilization percentage."""
        pass

    @abstractmethod
    def get_memory_usage(self) -> Dict[str, Any]:
        """RAM usage (total, used, free, percent)."""
        pass

    @abstractmethod
    def get_temperature(self) -> Optional[float]:
        """SoC / CPU core temperature in Celsius."""
        pass

    @abstractmethod
    def get_uptime_seconds(self) -> float:
        """System uptime in seconds."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Consolidated system metrics dictionary."""
        pass
