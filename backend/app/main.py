from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from backend.app.config import settings
from backend.app.api.api_v1 import api_router
from backend.app.db.init_db import init_database
from backend.app.db.mongo import MongoDBManager
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

    try:
        await MongoDBManager.connect()
    except Exception as e:
        logger.warning(f"MongoDB startup initialization error: {e}")

    yield

    # Shutdown
    try:
        await MongoDBManager.disconnect()
    except Exception as e:
        logger.warning(f"MongoDB disconnect error: {e}")
    logger.info("EdgeStore backend shutting down cleanly")


from backend.app.core.middleware import SecurityHeadersMiddleware, RequestSizeLimitMiddleware, AntiBotDDoSShieldMiddleware

app = FastAPI(
    title="EdgeStore Appliance API",
    description="Secure Local Storage Appliance with Hardware Abstraction Layer, Dual-Drive Replication, and LUKS2 Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Defense-in-depth security middlewares
app.add_middleware(AntiBotDDoSShieldMiddleware)
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


# Serve production frontend SPA with assets mounting and client-side routing fallback
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa_frontend(request: Request, full_path: str):
        # Never intercept API, health, or OpenAPI docs
        if full_path.startswith("api") or full_path in ("docs", "redoc", "openapi.json", "health"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        target_file = frontend_dist / full_path
        if full_path and target_file.is_file():
            return FileResponse(str(target_file))

        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

        return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
