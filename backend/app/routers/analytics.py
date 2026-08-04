from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics_schemas import AnalyticsOverviewResponse
from app.database import get_db
from app.dependencies import require_role
from app.models import User, UserRole
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
analytics = AnalyticsService()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> AnalyticsOverviewResponse:
    payload = analytics.overview(db, current_user.id)
    return AnalyticsOverviewResponse(**payload)
