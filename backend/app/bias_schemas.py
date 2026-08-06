from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models import BiasAlertSeverity


class BiasAlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: BiasAlertSeverity
    title: str
    description: str
    metric_payload: dict[str, Any]
    acknowledged: bool
    acknowledged_at: datetime | None
    created_at: datetime


class BiasOverviewResponse(BaseModel):
    alert_count: int
    unacknowledged_count: int
    alerts: list[BiasAlertResponse]
    notes: list[str]
