from fastapi import APIRouter

from app.config import settings
from app.schemas import HealthResponse, utc_now_iso

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="UP",
        application=settings.app_name,
        timestamp=utc_now_iso(),
    )
