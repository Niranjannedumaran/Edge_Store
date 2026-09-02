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


app = FastAPI(
    title="EdgeStore Appliance API",
    description="Secure Local Storage Appliance with Hardware Abstraction Layer, Dual-Drive Replication, and LUKS2 Integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EdgeStoreException)
async def edge_store_exception_handler(request: Request, exc: EdgeStoreException):
    logger.warning(f"Domain exception: {exc.message} (status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


app.include_router(api_router)


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "app": "EdgeStore",
        "environment_mode": settings.ENVIRONMENT_MODE.value
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
