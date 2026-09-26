from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecordingResponse(BaseModel):
    id: UUID
    session_id: UUID
    content_type: str
    size_bytes: int
    duration_seconds: int | None
    created_at: datetime
