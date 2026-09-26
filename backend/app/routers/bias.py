from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.bias_schemas import BiasAlertResponse, BiasOverviewResponse, OrganisationBiasResponse
from app.database import get_db
from app.dependencies import require_role
from app.models import BiasAlert, User, UserRole
from app.services.bias_detection import BiasDetectionService

router = APIRouter(prefix="/api/bias", tags=["bias"])
bias_service = BiasDetectionService()


def _alert_response(alert: BiasAlert) -> BiasAlertResponse:
    return BiasAlertResponse(
        id=alert.id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        title=alert.title,
        description=alert.description,
        metric_payload=alert.metric_payload or {},
        acknowledged=alert.acknowledged,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


@router.get("/overview", response_model=BiasOverviewResponse)
def get_bias_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> BiasOverviewResponse:
    alerts = bias_service.analyze(db, current_user.id)
    unack = [item for item in alerts if not item.acknowledged]
    return BiasOverviewResponse(
        alert_count=len(alerts),
        unacknowledged_count=len(unack),
        alerts=[_alert_response(item) for item in alerts],
        notes=[
            "Monitoring uses role, match-score bands, and interview score patterns only.",
            "No demographic attributes are inferred from CV text.",
            "Alerts are advisory and do not block hiring decisions.",
        ],
    )


@router.get("/organisation", response_model=OrganisationBiasResponse)
def get_organisation_bias(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> OrganisationBiasResponse:
    # Always scoped to the caller's own company - never an arbitrary value from the request.
    result = bias_service.analyze_organisation(db, current_user.company, current_user.id)
    return OrganisationBiasResponse(**result)


@router.post("/alerts/{alert_id}/acknowledge", response_model=BiasAlertResponse)
def acknowledge_alert(
    alert_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> BiasAlertResponse:
    alert = db.get(BiasAlert, alert_id)
    if alert is None or alert.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    bias_service.acknowledge(db, alert)
    return _alert_response(alert)
