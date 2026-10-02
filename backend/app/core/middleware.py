from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from backend.app.config import settings
from backend.app.core.logger import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Defense-in-depth HTTP security headers middleware.
    Applies security headers to every response to prevent clickjacking, MIME-sniffing,
    unauthorized framing, and cross-site scripting (XSS).
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if settings.ENABLE_SECURITY_HEADERS:
            headers = response.headers
            headers["X-Content-Type-Options"] = "nosniff"
            headers["X-Frame-Options"] = "DENY"
            headers["X-XSS-Protection"] = "1; mode=block"
            headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            headers["Permissions-Policy"] = (
                "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
                "magnetometer=(), microphone=(), payment=(), usb=()"
            )
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data: blob:; "
                "frame-src 'self' blob:; "
                "object-src 'self' blob:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )

            # HSTS if enabled or over HTTPS
            if settings.STRICT_TRANSPORT_SECURITY or request.url.scheme == "https":
                headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Rejects oversized requests early before buffering to protect against DoS / memory exhaustion.
    """

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > settings.MAX_UPLOAD_SIZE_BYTES:
                    logger.warning(
                        f"Request payload {length} bytes exceeds maximum allowed {settings.MAX_UPLOAD_SIZE_BYTES} bytes"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "PayloadTooLarge",
                            "message": f"Request size exceeds limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB",
                            "details": {"max_bytes": settings.MAX_UPLOAD_SIZE_BYTES, "received_bytes": length}
                        }
                    )
            except ValueError:
                pass

        return await call_next(request)


class AntiBotDDoSShieldMiddleware(BaseHTTPMiddleware):
    """
    DDoS & Anti-Bot Shield Middleware.
    Screens incoming requests against active IP quarantine cache and sliding-window burst limits.
    Immediately drops DDoS attack floods with HTTP 429 before application, database, or disk load occurs.
    """

    EXEMPT_PATHS = (
        "/health",
        "/api/health",
        "/api/security/anti-bot",
        "/favicon.ico",
        "/assets",
        "/docs",
        "/openapi.json",
        "/redoc"
    )

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS):
            return await call_next(request)

        # Allow test client or resolve IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        bot_token = request.headers.get("x-anti-bot-token")

        from backend.app.core.anti_bot import AntiBotDDoSShield
        is_allowed, reason, retry_after = AntiBotDDoSShield.screen_request(client_ip, bot_token)
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={
                    "error": "DDoSAttackMitigation",
                    "message": "Traffic flood or automated bot activity detected. Your IP is temporarily quarantined.",
                    "details": {
                        "reason": reason,
                        "retry_after_seconds": retry_after,
                        "client_ip": client_ip,
                        "anti_bot_verification_url": "/api/security/anti-bot/challenge"
                    }
                }
            )

        return await call_next(request)

