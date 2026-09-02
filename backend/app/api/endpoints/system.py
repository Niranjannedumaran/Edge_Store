from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.core.dependencies import get_current_user, require_permission
from backend.app.services.health_service import HealthService
from backend.app.hal import hal

router = APIRouter(prefix="/system", tags=["System & Health"])


@router.get("/health")
def get_system_health(
    current_user: User = Depends(require_permission("system.read")),
    db: Session = Depends(get_db)
):
    return HealthService.get_system_health(db)


@router.get("/metrics")
def get_system_metrics(current_user: User = Depends(require_permission("hardware.read"))):
    return hal.monitor.get_metrics()


@router.get("/power")
def get_power_telemetry(current_user: User = Depends(require_permission("power.read"))):
    return hal.power.get_telemetry()
