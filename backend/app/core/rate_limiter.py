import time
from collections import defaultdict
from threading import Lock
from typing import Optional, Tuple
from fastapi import HTTPException, Request, status
from backend.app.config import settings
from backend.app.core.logger import logger

_lock = Lock()
_request_history: dict[str, list[float]] = defaultdict(list)
_failed_login_attempts: dict[str, list[float]] = defaultdict(list)


class RateLimiter:
    """
    Sliding window in-memory rate limiter with thread safety.
    """

    @classmethod
    def is_rate_limited(cls, key: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window_seconds
        with _lock:
            timestamps = _request_history[key]
            # Prune old timestamps
            _request_history[key] = [t for t in timestamps if t > cutoff]
            if len(_request_history[key]) >= max_requests:
                # Exceeded
                retry_after = int(window_seconds - (now - _request_history[key][0]))
                return True, max(1, retry_after)
            _request_history[key].append(now)
            return False, 0

    @classmethod
    def reset(cls):
        """Reset all rate limiter states (useful for testing)"""
        with _lock:
            _request_history.clear()
            _failed_login_attempts.clear()


class LoginBruteForceTracker:
    """
    Brute-force and credential stuffing defense tracker.
    Protects against automated password guessing without creating permanent account lockout.
    """

    @classmethod
    def check_lockout(cls, ip_address: str, username: str) -> Tuple[bool, int]:
        now = time.time()
        window = settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
        max_attempts = settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS
        cutoff = now - window

        keys = [f"ip:{ip_address}", f"user:{username.lower().strip()}"]
        with _lock:
            for key in keys:
                attempts = [t for t in _failed_login_attempts[key] if t > cutoff]
                _failed_login_attempts[key] = attempts
                if len(attempts) >= max_attempts:
                    remaining = int(window - (now - attempts[0]))
                    return True, max(1, remaining)
        return False, 0

    @classmethod
    def record_failed_attempt(cls, ip_address: str, username: str):
        now = time.time()
        keys = [f"ip:{ip_address}", f"user:{username.lower().strip()}"]
        with _lock:
            for key in keys:
                _failed_login_attempts[key].append(now)
        logger.warning(f"Recorded failed login attempt for user '{username}' from {ip_address}")

    @classmethod
    def record_successful_login(cls, ip_address: str, username: str):
        keys = [f"ip:{ip_address}", f"user:{username.lower().strip()}"]
        with _lock:
            for key in keys:
                _failed_login_attempts.pop(key, None)

    @classmethod
    def get_stats(cls) -> dict:
        now = time.time()
        cutoff = now - settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
        with _lock:
            active_locks = sum(
                1 for attempts in _failed_login_attempts.values()
                if len([t for t in attempts if t > cutoff]) >= settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS
            )
            total_tracked = len(_failed_login_attempts)
        return {
            "protection_enabled": True,
            "max_attempts": settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
            "lockout_window_seconds": settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
            "active_locked_entities": active_locks,
            "tracked_entities": total_tracked,
        }


def rate_limit_dependency(max_requests: Optional[int] = None, window_seconds: int = 60):
    """
    FastAPI dependency factory for endpoint rate limiting.
    """
    limit = max_requests or settings.RATE_LIMIT_DEFAULT_REQUESTS

    def dependency(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        endpoint = request.url.path
        key = f"{client_ip}:{endpoint}"
        limited, retry_after = RateLimiter.is_rate_limited(key, limit, window_seconds)
        if limited:
            logger.warning(f"Rate limit exceeded for {key}: {limit} reqs/{window_seconds}s")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please retry in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )

    return dependency
