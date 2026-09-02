"""
EdgeStore Domain Exceptions
"""

class EdgeStoreException(Exception):
    """Base exception for all EdgeStore domain errors."""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class StorageUnavailableException(EdgeStoreException):
    """Raised when target storage volume is offline, unmounted, or failed."""
    def __init__(self, message: str = "Storage volume is unavailable or unmounted", details: dict = None):
        super().__init__(message, status_code=503, details=details)


class StorageDegradedException(EdgeStoreException):
    """Raised when primary storage has failed and operations fall back to degraded replica mode."""
    def __init__(self, message: str = "Operating in degraded storage mode", details: dict = None):
        super().__init__(message, status_code=200, details=details)


class VaultLockedException(EdgeStoreException):
    """Raised when accessing encrypted storage without an unlocked vault / missing Key-SD."""
    def __init__(self, message: str = "Storage vault is locked. Key-SD required.", details: dict = None):
        super().__init__(message, status_code=423, details=details)  # 423 Locked


class IntegrityVerificationException(EdgeStoreException):
    """Raised when SHA-256 hash does not match expected checksum."""
    def __init__(self, message: str = "File integrity verification failed: SHA-256 mismatch", details: dict = None):
        super().__init__(message, status_code=422, details=details)


class ReplicationException(EdgeStoreException):
    """Raised when file replication to secondary storage fails."""
    def __init__(self, message: str = "Replication operation failed", details: dict = None):
        super().__init__(message, status_code=502, details=details)


class AuthenticationException(EdgeStoreException):
    """Raised for authentication failures."""
    def __init__(self, message: str = "Invalid credentials or token expired", details: dict = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationException(EdgeStoreException):
    """Raised for RBAC privilege violations."""
    def __init__(self, message: str = "Insufficient permissions for this operation", details: dict = None):
        super().__init__(message, status_code=403, details=details)


class FileNotFoundException(EdgeStoreException):
    """Raised when requested file cannot be found in database or disk."""
    def __init__(self, message: str = "File not found", details: dict = None):
        super().__init__(message, status_code=404, details=details)


class ValidationException(EdgeStoreException):
    """Raised when input validation fails (e.g., malformed filenames, illegal characters)."""
    def __init__(self, message: str = "Input validation failed", details: dict = None):
        super().__init__(message, status_code=400, details=details)


class SecurityViolationException(EdgeStoreException):
    """Raised when an explicit security violation is detected (e.g., path traversal, executable upload)."""
    def __init__(self, message: str = "Security policy violation detected", details: dict = None):
        super().__init__(message, status_code=400, details=details)
