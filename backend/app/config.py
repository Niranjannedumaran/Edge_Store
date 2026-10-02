import os
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentMode(str, Enum):
    SIMULATION = "simulation"
    DOCKER = "docker"
    RASPBERRY_PI = "raspberry_pi"


class DriveState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    UNMOUNTED = "unmounted"


class ReplicaSyncState(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    DEGRADED = "degraded"
    RECOVERING = "recovering"


class KeySDState(str, Enum):
    INSERTED = "inserted"
    REMOVED = "removed"
    INVALID = "invalid"


class VaultState(str, Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"


class PowerMode(str, Enum):
    NORMAL = "normal"
    CONSERVATION = "conservation"
    CRITICAL = "critical"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Environment
    ENVIRONMENT_MODE: EnvironmentMode = EnvironmentMode.SIMULATION
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security / JWT
    JWT_SECRET: str = "edgestore_phase1_super_secret_jwt_key_change_in_production_32b"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "sqlite:///./edgestore.db"
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "edgestore_clients"

    # Storage Paths (Universal abstraction: works for local, Docker volumes, and simulation)
    PRIMARY_STORAGE_PATH: Optional[str] = None
    REPLICA_STORAGE_PATH: Optional[str] = None

    # Simulation Storage Paths (Backward compatibility fallback)
    SIMULATION_PRIMARY_PATH: str = "./simulation/primary"
    SIMULATION_REPLICA_PATH: str = "./simulation/replica"
    SIMULATION_KEY_SD_PATH: str = "./simulation/key_sd"

    # Real Hardware Settings (Raspberry Pi mode)
    LINUX_PRIMARY_DEVICE: str = "/dev/mapper/edgestore_primary"
    LINUX_PRIMARY_MOUNT: str = "/mnt/edgestore/primary"
    LINUX_REPLICA_DEVICE: str = "/dev/mapper/edgestore_replica"
    LINUX_REPLICA_MOUNT: str = "/mnt/edgestore/replica"
    LINUX_KEY_SD_DEVICE_UUID: str = "EDGESTORE-KEY-01"
    LINUX_KEY_SD_MOUNT: str = "/mnt/edgestore/key_sd"
    LINUX_KEY_FILE_NAME: str = "vault.key"

    # Replication Settings
    REPLICATION_INTERVAL_SECONDS: int = 10
    AUTO_RETRY_FAILED_REPLICATIONS: bool = True
    MAX_REPLICATION_RETRIES: int = 3

    # Storage Exhaustion Safeguards & Sharing Defaults
    MIN_FREE_DISK_BYTES: int = 10 * 1024 * 1024  # 10 MB headroom to avoid full disk lockups
    DEFAULT_SHARE_EXPIRE_HOURS: int = 24

    # Optional S3-Compatible Storage Provider (for real cloud storage integration)
    CLOUD_STORAGE_ENABLED: bool = False
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION_NAME: Optional[str] = "us-east-1"

    @property
    def effective_primary_path(self) -> str:
        return self.PRIMARY_STORAGE_PATH or self.SIMULATION_PRIMARY_PATH

    @property
    def effective_replica_path(self) -> str:
        return self.REPLICA_STORAGE_PATH or self.SIMULATION_REPLICA_PATH

    # Power Policy Thresholds (%)
    BATTERY_NORMAL_THRESHOLD: int = 50
    BATTERY_CONSERVATION_THRESHOLD: int = 25
    BATTERY_CRITICAL_THRESHOLD: int = 10

    # Initial Admin Seed
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "AdminEdgeStore2026!"
    INITIAL_ADMIN_EMAIL: str = "admin@edgestore.local"

    # Cybersecurity Hardening Settings
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300  # 5 minute lockout window
    RATE_LIMIT_DEFAULT_REQUESTS: int = 120  # requests per minute per IP
    MAX_UPLOAD_SIZE_BYTES: int = 104857600  # 100 MB max request / file size
    ALLOWED_CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    ENABLE_SECURITY_HEADERS: bool = True
    STRICT_TRANSPORT_SECURITY: bool = False  # Set True in production HTTPS deployment

    # Anti-Bot & DDoS Mitigation Shield
    DDOS_PROTECTION_ENABLED: bool = True
    DDOS_BURST_MAX_REQUESTS: int = 40  # Max requests per burst window
    DDOS_BURST_WINDOW_SECONDS: int = 5  # Sliding window (seconds)
    DDOS_BAN_DURATION_SECONDS: int = 180  # Temporary quarantine duration (seconds)
    ANTI_BOT_VERIFIED_CACHE_SECONDS: int = 86400  # 24 hours verified human cache
    ANTI_BOT_CHALLENGE_EXPIRE_SECONDS: int = 300  # 5 minutes challenge validity
    REQUIRE_BOT_VERIFICATION_BEFORE_LOGIN: bool = True  # Enforce Not a Robot verification before login




settings = Settings()
