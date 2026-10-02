from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.app.core.anti_bot import AntiBotDDoSShield

router = APIRouter()


class ChallengeVerificationRequest(BaseModel):
    challenge_id: str = Field(..., description="The unique challenge identifier")
    solution: str = Field(..., description="The human solution to the anti-robot prompt")


@router.get("/anti-bot/challenge", summary="Get Not-a-Robot Verification Challenge")
def get_anti_bot_challenge(request: Request) -> Dict[str, Any]:
    """
    Issues a zero-dependency 'Not a Robot' mathematical challenge to verify human presence.
    Used by clients to prove authenticity and bypass DDoS quarantine.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return AntiBotDDoSShield.generate_challenge(client_ip)


@router.post("/anti-bot/verify", summary="Verify Not-a-Robot Solution")
def verify_anti_bot_challenge(payload: ChallengeVerificationRequest, request: Request) -> Dict[str, Any]:
    """
    Verifies the client's answer to the 'Not a Robot' challenge.
    Upon successful solution:
    - IP and cryptographic pass token are cached in the 24-hour verified human cache.
    - Any active DDoS quarantine / rate-limit penalty on the IP is immediately lifted.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    success, message, token = AntiBotDDoSShield.verify_challenge(
        payload.challenge_id, payload.solution, client_ip
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return {
        "success": True,
        "message": message,
        "anti_bot_token": token,
        "verified_ip": client_ip,
        "cache_duration_hours": 24
    }


@router.get("/ddos/stats", summary="Get Real-Time DDoS Shield and Bot Cache Telemetry")
def get_ddos_telemetry(request: Request) -> Dict[str, Any]:
    """
    Inspects live DDoS mitigation metrics, screened requests, active quarantined IPs,
    and verified human sessions currently stored in cache.
    """
    return AntiBotDDoSShield.get_stats()


@router.post("/ddos/reset", summary="Reset DDoS and Anti-Bot Caches")
def reset_ddos_cache() -> Dict[str, str]:
    """Clears in-memory DDoS quarantine and challenge caches."""
    AntiBotDDoSShield.reset()
    return {"status": "ok", "message": "DDoS quarantine and anti-bot caches successfully purged"}
