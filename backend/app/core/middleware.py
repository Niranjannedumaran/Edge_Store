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
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
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
