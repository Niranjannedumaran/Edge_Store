from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.config import settings
from backend.app.api.api_v1 import api_router
from backend.app.db.init_db import init_database
from backend.app.core.exceptions import EdgeStoreException
from backend.app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database initialized
    logger.info(f"Starting EdgeStore Phase 1 Backend in [{settings.ENVIRONMENT_MODE.value.upper()}] mode")
    try:
        init_database()
    except Exception as e:
        logger.error(f"Database startup initialization error: {e}")
    yield
    # Shutdown
    logger.info("EdgeStore backend shutting down cleanly")


from backend.app.core.middleware import SecurityHeadersMiddleware, RequestSizeLimitMiddleware

app = FastAPI(
    title="EdgeStore Appliance API",
    description="Secure Local Storage Appliance with Hardware Abstraction Layer, Dual-Drive Replication, and LUKS2 Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Defense-in-depth security middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

# Controlled CORS policy
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(EdgeStoreException)
async def edge_store_exception_handler(request: Request, exc: EdgeStoreException):
    logger.warning(f"Domain exception on {request.method} {request.url.path}: {exc.message} (status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    # Log detailed traceback internally for diagnostics
    logger.exception(f"Unhandled server exception on {request.method} {request.url.path}: {exc}")
    # Return sanitized generic error externally to prevent information leakage
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An internal server error occurred. Telemetry has been logged for administrative review."
        }
    )


from pathlib import Path
from fastapi.staticfiles import StaticFiles

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "app": "EdgeStore",
        "environment_mode": settings.ENVIRONMENT_MODE.value
    }


# Mount frontend production build if available for unified single-port deployment
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
