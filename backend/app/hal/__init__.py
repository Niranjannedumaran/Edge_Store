from backend.app.config import settings, EnvironmentMode
from backend.app.hal.interfaces import (
    StorageProvider,
    KeyDeviceProvider,
    EncryptionProvider,
    ReplicationProvider,
    PowerProvider,
    SystemMonitorProvider
)
from backend.app.hal.local_storage import LocalStorageProvider
from backend.app.hal.simulation.storage import SimulationStorageProvider
from backend.app.hal.simulation.key_device import SimulationKeyProvider
from backend.app.hal.simulation.encryption import SimulationEncryptionProvider
from backend.app.hal.simulation.replication import SimulationReplicationProvider
from backend.app.hal.simulation.power import SimulationPowerProvider
from backend.app.hal.simulation.monitor import SimulationSystemMonitorProvider

from backend.app.hal.linux.storage import LinuxStorageProvider
from backend.app.hal.linux.key_device import LinuxKeyProvider
from backend.app.hal.linux.encryption import LinuxEncryptionProvider
from backend.app.hal.linux.replication import LinuxReplicationProvider
from backend.app.hal.linux.power import LinuxPowerProvider
from backend.app.hal.linux.monitor import LinuxSystemMonitorProvider

from backend.app.hal.docker_hal import (
    DockerReplicationProvider,
    DockerEncryptionProvider,
    DockerHardwareAuthProvider,
    DockerPowerProvider,
    DockerSystemMonitorProvider
)
from backend.app.core.logger import logger


class HALContainer:
    """
    Dependency injection container for EdgeStore Hardware Abstraction Layer.
    Supplies singletons configured for simulation, Docker persistent storage, or real Raspberry Pi mode.
    """

    def __init__(self):
        self.reconfigure(settings.ENVIRONMENT_MODE)

    def reconfigure(self, mode: EnvironmentMode = None):
        target_mode = mode or settings.ENVIRONMENT_MODE
        logger.info(f"Initializing EdgeStore HAL Container in [{target_mode.value.upper()}] mode")

        if target_mode == EnvironmentMode.DOCKER:
            self.primary_storage: StorageProvider = LocalStorageProvider(
                settings.effective_primary_path, label="Drive A (Primary - Docker)"
            )
            self.replica_storage: StorageProvider = LocalStorageProvider(
                settings.effective_replica_path, label="Drive B (Replica - Docker)"
            )
            self.key_device: KeyDeviceProvider = DockerHardwareAuthProvider()
            self.encryption: EncryptionProvider = DockerEncryptionProvider()
            self.replication: ReplicationProvider = DockerReplicationProvider()
            self.power: PowerProvider = DockerPowerProvider()
            self.monitor: SystemMonitorProvider = DockerSystemMonitorProvider()
        elif target_mode == EnvironmentMode.SIMULATION:
            self.primary_storage: StorageProvider = SimulationStorageProvider(
                settings.effective_primary_path, label="Drive A (Primary)"
            )
            self.replica_storage: StorageProvider = SimulationStorageProvider(
                settings.effective_replica_path, label="Drive B (Replica)"
            )
            self.key_device: KeyDeviceProvider = SimulationKeyProvider(
                settings.SIMULATION_KEY_SD_PATH, settings.LINUX_KEY_FILE_NAME
            )
            self.encryption: EncryptionProvider = SimulationEncryptionProvider()
            self.replication: ReplicationProvider = SimulationReplicationProvider()
            self.power: PowerProvider = SimulationPowerProvider()
            self.monitor: SystemMonitorProvider = SimulationSystemMonitorProvider()
        else:
            self.primary_storage: StorageProvider = LinuxStorageProvider(
                settings.LINUX_PRIMARY_DEVICE, settings.LINUX_PRIMARY_MOUNT, label="Drive A (Primary)"
            )
            self.replica_storage: StorageProvider = LinuxStorageProvider(
                settings.LINUX_REPLICA_DEVICE, settings.LINUX_REPLICA_MOUNT, label="Drive B (Replica)"
            )
            self.key_device: KeyDeviceProvider = LinuxKeyProvider(
                settings.LINUX_KEY_SD_DEVICE_UUID, settings.LINUX_KEY_SD_MOUNT, settings.LINUX_KEY_FILE_NAME
            )
            self.encryption: EncryptionProvider = LinuxEncryptionProvider(
                settings.LINUX_PRIMARY_DEVICE, "edgestore_primary"
            )
            self.replication: ReplicationProvider = LinuxReplicationProvider()
            self.power: PowerProvider = LinuxPowerProvider()
            self.monitor: SystemMonitorProvider = LinuxSystemMonitorProvider()

        # Initialize storage providers
        self.primary_storage.initialize()
        self.replica_storage.initialize()


# Global HAL instance
hal = HALContainer()
