from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import User, UserRole
from app.optional_schemas import AssistantQueryRequest, AssistantQueryResponse
from app.services.assistant_agent import AssistantAgentService

router = APIRouter(prefix="/api/assistant", tags=["assistant"])
assistant = AssistantAgentService()


@router.post("/query", response_model=AssistantQueryResponse)
def query_assistant(
    request: AssistantQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.RECRUITER)),
) -> AssistantQueryResponse:
    result = assistant.answer(db, current_user.id, request.message.strip())
    return AssistantQueryResponse(**result)
