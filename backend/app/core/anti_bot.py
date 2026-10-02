import time
import uuid
import random
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple, Optional, Any
from backend.app.config import settings
from backend.app.core.logger import logger


class AntiBotDDoSShield:
    """
    Enterprise Anti-Bot & DDoS Mitigation Shield.
    Features:
    1. Sliding-window burst attack detection to stop L7 DDoS floods.
    2. Automated IP quarantine / cooldown cache that drops malicious traffic at the gate.
    3. 'Not a Robot' challenge-response proof system.
    4. Verified human cache (24h pass) that exempts genuine users from false-positive rate limiting.
    5. Real-time telemetry and audit stats.
    """

    _lock = Lock()
    # IP -> list of request timestamps
    _ip_burst_history: Dict[str, List[float]] = defaultdict(list)
    # IP -> timestamp when quarantine ends
    _quarantined_ips: Dict[str, float] = {}
    # Token / IP -> timestamp when verified human status expires
    _verified_human_cache: Dict[str, float] = {}
    # Challenge ID -> {"answer": str, "ip": str, "expires_at": float}
    _pending_challenges: Dict[str, Dict[str, Any]] = {}
    
    # Telemetry counters
    _total_screened: int = 0
    _floods_blocked: int = 0
    _challenges_issued: int = 0
    _challenges_solved: int = 0

    @classmethod
    def screen_request(cls, client_ip: str, bot_token: Optional[str] = None) -> Tuple[bool, str, int]:
        """
        Screens an incoming request against the DDoS quarantine and burst attack engine.
        Returns:
            (is_allowed: bool, reason: str, retry_after: int)
        """
        now = time.time()

        with cls._lock:
            cls._total_screened += 1

            # 1. Check if IP or Token is in verified 'Not a Robot' Cache
            if cls._is_verified_human_unlocked(client_ip, bot_token, now):
                return True, "verified_human", 0

            # 2. Check if IP is currently quarantined in DDoS cache
            if client_ip in cls._quarantined_ips:
                unban_time = cls._quarantined_ips[client_ip]
                if now < unban_time:
                    cls._floods_blocked += 1
                    retry_after = max(1, int(unban_time - now))
                    return False, "quarantined_ddos_flood", retry_after
                else:
                    # Quarantine expired
                    del cls._quarantined_ips[client_ip]
                    logger.info(f"[DDoS Shield] Quarantine expired for IP {client_ip}")

            # 3. Burst Rate Flood Check
            burst_window = getattr(settings, "DDOS_BURST_WINDOW_SECONDS", 5)
            burst_limit = getattr(settings, "DDOS_BURST_MAX_REQUESTS", 40)
            ban_duration = getattr(settings, "DDOS_BAN_DURATION_SECONDS", 180)

            cutoff = now - burst_window
            timestamps = [t for t in cls._ip_burst_history[client_ip] if t > cutoff]
            timestamps.append(now)
            cls._ip_burst_history[client_ip] = timestamps

            if len(timestamps) > burst_limit:
                # DDoS burst threshold breached! Quarantine this IP
                unban_at = now + ban_duration
                cls._quarantined_ips[client_ip] = unban_at
                cls._floods_blocked += 1
                logger.warning(
                    f"[DDoS Shield] Potential DDoS flood detected from IP {client_ip}: "
                    f"{len(timestamps)} requests in {burst_window}s. Quarantining for {ban_duration}s."
                )
                return False, "burst_limit_exceeded", ban_duration

            return True, "ok", 0

    @classmethod
    def _is_verified_human_unlocked(cls, client_ip: str, bot_token: Optional[str], now: float) -> bool:
        """Internal helper to check verified human cache."""
        # Check by token
        if bot_token and bot_token in cls._verified_human_cache:
            if cls._verified_human_cache[bot_token] > now:
                return True
            else:
                del cls._verified_human_cache[bot_token]

        # Check by IP
        ip_key = f"ip:{client_ip}"
        if ip_key in cls._verified_human_cache:
            if cls._verified_human_cache[ip_key] > now:
                return True
            else:
                del cls._verified_human_cache[ip_key]

        return False

    @classmethod
    def is_verified_human(cls, client_ip: str, bot_token: Optional[str] = None) -> bool:
        now = time.time()
        with cls._lock:
            return cls._is_verified_human_unlocked(client_ip, bot_token, now)

    @classmethod
    def consume_token_on_login(cls, client_ip: str, bot_token: Optional[str] = None) -> None:
        """
        Consumes (invalidates) the verified human token after a successful login.
        Forces the user to re-solve the 'Not a Robot' challenge on their next login.
        This makes the bot verification single-use per login session.
        """
        with cls._lock:
            # Remove the token from the verified cache
            if bot_token and bot_token in cls._verified_human_cache:
                del cls._verified_human_cache[bot_token]
                logger.info(f"[Anti-Bot] Token consumed after login for IP {client_ip}. Re-verification required on next login.")

            # Also remove the IP-level cache so the browser must re-verify
            ip_key = f"ip:{client_ip}"
            if ip_key in cls._verified_human_cache:
                del cls._verified_human_cache[ip_key]

    @classmethod
    def generate_challenge(cls, client_ip: str) -> Dict[str, Any]:
        """
        Generates a lightweight, zero-dependency mathematical 'Not a Robot' challenge.
        """
        now = time.time()
        challenge_id = str(uuid.uuid4())
        num1 = random.randint(11, 49)
        num2 = random.randint(11, 49)
        answer = str(num1 + num2)

        expire_seconds = getattr(settings, "ANTI_BOT_CHALLENGE_EXPIRE_SECONDS", 300)
        expires_at = now + expire_seconds

        with cls._lock:
            # Prune stale challenges
            stale_keys = [k for k, v in cls._pending_challenges.items() if v["expires_at"] < now]
            for k in stale_keys:
                del cls._pending_challenges[k]

            cls._pending_challenges[challenge_id] = {
                "answer": answer,
                "ip": client_ip,
                "expires_at": expires_at
            }
            cls._challenges_issued += 1

        return {
            "challenge_id": challenge_id,
            "prompt": f"Please prove you are human: What is {num1} + {num2}?",
            "expires_in_seconds": expire_seconds,
            "verification_endpoint": "/api/security/anti-bot/verify"
        }

    @classmethod
    def verify_challenge(cls, challenge_id: str, solution: str, client_ip: str) -> Tuple[bool, str, Optional[str]]:
        """
        Verifies the user's 'Not a Robot' solution.
        On success:
        - Caches IP and a generated cryptographic pass token for 24 hours.
        - Immediately unbans/clears the IP from any active DDoS quarantine!
        """
        now = time.time()
        solution_str = str(solution).strip()

        with cls._lock:
            challenge = cls._pending_challenges.get(challenge_id)
            if not challenge:
                return False, "Invalid or expired challenge ID", None

            if now > challenge["expires_at"]:
                del cls._pending_challenges[challenge_id]
                return False, "Challenge has expired. Please request a new challenge.", None

            if challenge["answer"] != solution_str:
                return False, "Incorrect answer to challenge.", None

            # Challenge solved successfully!
            del cls._pending_challenges[challenge_id]
            cls._challenges_solved += 1

            # Generate signed human token
            pass_duration = getattr(settings, "ANTI_BOT_VERIFIED_CACHE_SECONDS", 86400)
            token = f"human_{uuid.uuid4().hex}"
            expires_at = now + pass_duration

            # Cache in verified human cache (both by token and IP)
            cls._verified_human_cache[token] = expires_at
            cls._verified_human_cache[f"ip:{client_ip}"] = expires_at

            # Clear any active quarantine on this IP
            cls._quarantined_ips.pop(client_ip, None)
            cls._ip_burst_history.pop(client_ip, None)

            logger.info(f"[Anti-Bot] IP {client_ip} successfully verified as human. Whitelisted for {pass_duration}s.")
            return True, "Human verification successful. IP unblocked and cached.", token

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Returns live DDoS and Anti-Bot shield telemetry."""
        now = time.time()
        with cls._lock:
            active_quarantines = {
                ip: max(1, int(exp - now))
                for ip, exp in cls._quarantined_ips.items()
                if exp > now
            }
            active_humans = sum(1 for exp in cls._verified_human_cache.values() if exp > now)

        return {
            "status": "ACTIVE",
            "total_requests_screened": cls._total_screened,
            "floods_blocked": cls._floods_blocked,
            "active_quarantined_ips": len(active_quarantines),
            "quarantined_ips_detail": active_quarantines,
            "verified_humans_in_cache": active_humans,
            "challenges_issued": cls._challenges_issued,
            "challenges_solved": cls._challenges_solved,
            "burst_limit_config": {
                "max_burst_requests": getattr(settings, "DDOS_BURST_MAX_REQUESTS", 40),
                "burst_window_seconds": getattr(settings, "DDOS_BURST_WINDOW_SECONDS", 5),
                "quarantine_duration_seconds": getattr(settings, "DDOS_BAN_DURATION_SECONDS", 180),
                "human_cache_duration_seconds": getattr(settings, "ANTI_BOT_VERIFIED_CACHE_SECONDS", 86400),
            }
        }

    @classmethod
    def reset(cls):
        """Reset all in-memory DDoS and anti-bot caches (for testing)."""
        with cls._lock:
            cls._ip_burst_history.clear()
            cls._quarantined_ips.clear()
            cls._verified_human_cache.clear()
            cls._pending_challenges.clear()
            cls._total_screened = 0
            cls._floods_blocked = 0
            cls._challenges_issued = 0
            cls._challenges_solved = 0
