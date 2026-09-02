from fastapi import APIRouter
from backend.app.api.endpoints import auth, files, storage, replication, system, admin, simulation

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(files.router)
api_router.include_router(storage.router)
api_router.include_router(replication.router)
api_router.include_router(system.router)
api_router.include_router(admin.router)
api_router.include_router(simulation.router)
