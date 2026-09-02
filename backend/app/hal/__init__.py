from backend.app.config import settings, EnvironmentMode
from backend.app.hal.interfaces import (
    StorageProvider,
    KeyDeviceProvider,
    EncryptionProvider,
    ReplicationProvider,
    PowerProvider,
    SystemMonitorProvider
)
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

from backend.app.core.logger import logger


class HALContainer:
    """
    Dependency injection container for EdgeStore Hardware Abstraction Layer.
    Supplies singletons configured for either simulation or real Raspberry Pi mode.
    """

    def __init__(self):
        mode = settings.ENVIRONMENT_MODE
        logger.info(f"Initializing EdgeStore HAL Container in [{mode.value.upper()}] mode")

        if mode == EnvironmentMode.SIMULATION:
            self.primary_storage: StorageProvider = SimulationStorageProvider(
                settings.SIMULATION_PRIMARY_PATH, label="Drive A (Primary)"
            )
            self.replica_storage: StorageProvider = SimulationStorageProvider(
                settings.SIMULATION_REPLICA_PATH, label="Drive B (Replica)"
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
