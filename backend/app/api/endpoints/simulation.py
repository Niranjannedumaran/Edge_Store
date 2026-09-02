from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.models.user import User
from backend.app.schemas.simulation import (
    DriveControlRequest,
    KeyControlRequest,
    BatteryControlRequest,
    ReplicationFaultRequest
)
from backend.app.core.dependencies import require_permission
from backend.app.hal import hal
from backend.app.config import settings, EnvironmentMode
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/simulation", tags=["Hardware Simulation Controls"])


def verify_simulation_mode():
    if settings.ENVIRONMENT_MODE != EnvironmentMode.SIMULATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hardware simulation controls are only available in simulation mode"
        )


@router.post("/drive")
def control_simulated_drive(
    req: DriveControlRequest,
    current_admin: User = Depends(require_permission("hardware.manage")),
    db: Session = Depends(get_db)
):
    verify_simulation_mode()
    provider = hal.primary_storage if req.drive.lower() == "primary" else hal.replica_storage
    drive_label = "Drive A (Primary)" if req.drive.lower() == "primary" else "Drive B (Replica)"

    action = req.action.lower()
    if action == "fail":
        provider.simulate_failure()
        event_type = "DRIVE_SIMULATED_FAILURE"
    elif action == "disconnect":
        provider.simulate_disconnect()
        event_type = "DRIVE_SIMULATED_DISCONNECT"
    elif action in ("connect", "recover"):
        provider.simulate_connect()
        event_type = "DRIVE_SIMULATED_RECOVERY"
    elif action == "unmount":
        provider.unmount()
        event_type = "DRIVE_SIMULATED_UNMOUNT"
    elif action == "mount":
        provider.mount()
        event_type = "DRIVE_SIMULATED_MOUNT"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown drive action: {req.action}")

    AuditService.log_event(
        db, event_type=event_type,
        description=f"Admin simulation control: {drive_label} set to action '{action}'",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return {
        "drive": req.drive,
        "action": req.action,
        "status": provider.get_status()
    }


@router.post("/key-sd")
def control_simulated_key_sd(
    req: KeyControlRequest,
    current_admin: User = Depends(require_permission("hardware.manage")),
    db: Session = Depends(get_db)
):
    verify_simulation_mode()
    action = req.action.lower()
    if action == "remove":
        hal.key_device.simulate_remove()
        AuditService.log_event(
            db, event_type="KEY_SIMULATED_REMOVAL",
            description="Hardware simulation: Key-SD physically removed",
            user_id=current_admin.id, username=current_admin.username, severity="WARNING"
        )
    elif action == "insert":
        hal.key_device.simulate_insert(valid=req.valid if req.valid is not None else True)
        AuditService.log_event(
            db, event_type="KEY_SIMULATED_INSERTION",
            description=f"Hardware simulation: Key-SD physically inserted (valid={req.valid})",
            user_id=current_admin.id, username=current_admin.username, severity="INFO"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown key action: {req.action}")

    return {
        "action": req.action,
        "status": hal.key_device.get_status()
    }


@router.post("/battery")
def control_simulated_battery(
    req: BatteryControlRequest,
    current_admin: User = Depends(require_permission("hardware.manage")),
    db: Session = Depends(get_db)
):
    verify_simulation_mode()
    hal.power.set_battery_level(req.level)
    if req.charging is not None:
        hal.power.set_charging(req.charging)

    AuditService.log_event(
        db, event_type="BATTERY_SIMULATED_CHANGE",
        description=f"Hardware simulation: Battery set to {req.level}% (charging={req.charging})",
        user_id=current_admin.id, username=current_admin.username, severity="INFO"
    )

    return hal.power.get_telemetry()


@router.post("/replication-fault")
def control_replication_fault(
    req: ReplicationFaultRequest,
    current_admin: User = Depends(require_permission("hardware.manage")),
    db: Session = Depends(get_db)
):
    verify_simulation_mode()
    hal.replication.set_simulate_failure_mode(req.simulate_failure)

    AuditService.log_event(
        db, event_type="REPLICATION_FAULT_TOGGLE",
        description=f"Hardware simulation: Replication failure simulation set to {req.simulate_failure}",
        user_id=current_admin.id, username=current_admin.username, severity="WARNING"
    )

    return hal.replication.get_status()
