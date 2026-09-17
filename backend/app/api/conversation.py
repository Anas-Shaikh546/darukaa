from fastapi import APIRouter

from app.schemas.conversation import ConversationRequest, ConversationResponse
from app.services.conversation_service import process_conversation_turn

router = APIRouter(prefix="/api/v1/conversation", tags=["conversation"])


@router.post("/turn", response_model=ConversationResponse)
def handle_conversation_turn(request: ConversationRequest) -> ConversationResponse:
    """
    Process a single conversation turn, extracting environmental information,
    updating session state, and returning either a clarification request or
    a complete multi-variable recommendation.
    """
    return process_conversation_turn(request)
