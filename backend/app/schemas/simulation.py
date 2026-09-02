from pydantic import BaseModel
from typing import Optional


class DriveControlRequest(BaseModel):
    drive: str  # "primary" or "replica"
    action: str  # "fail", "disconnect", "connect", "recover", "unmount", "mount"


class KeyControlRequest(BaseModel):
    action: str  # "insert", "remove"
    valid: Optional[bool] = True


class BatteryControlRequest(BaseModel):
    level: int
    charging: Optional[bool] = True


class ReplicationFaultRequest(BaseModel):
    simulate_failure: bool
