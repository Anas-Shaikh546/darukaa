"""Conversation orchestration service for Darukaa Day 3.

Coordinates multi-turn conversation flow:
1. Records user message turn into ConversationStore.
2. Extracts explicitly mentioned environmental variables.
3. Merges them into the cumulative conversation state.
4. Checks whether >=3 connected environmental variables are available.
5. If incomplete, generates a targeted clarification request.
6. If sufficient, invokes the existing Day 2 reasoning pipeline reason(env).
7. Records the assistant's reply into conversation history.
"""

from __future__ import annotations

from typing import Optional

from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationStatus,
)
from app.services.conversation_store import ConversationStore, store as default_store
from app.services.extraction import (
    extract_environmental_info,
    evaluate_clarification_need,
)
from app.services.reasoning import reason


def process_conversation_turn(
    request: ConversationRequest,
    store: Optional[ConversationStore] = None,
) -> ConversationResponse:
    """Process a single conversation turn and return a ConversationResponse."""
    active_store = store or default_store
    conv_id = request.conversation_id
    user_msg = request.message

    # 1. Save user turn
    active_store.add_turn(conv_id, role="user", message=user_msg)

    # 2. Extract explicitly provided environmental info from this turn
    extracted_env = extract_environmental_info(user_msg)

    # 3. Merge with existing conversation context
    state = active_store.update_environment_input(conv_id, extracted_env)
    current_env = state.environment

    # 4. Evaluate whether clarification is needed (<3 connected variables)
    needs_clarification, clarification_msg = evaluate_clarification_need(current_env)

    if needs_clarification:
        reply_text = clarification_msg or "Please provide more details on your environmental conditions."
        # 6. Save assistant clarification response in history
        active_store.add_turn(conv_id, role="assistant", message=reply_text)

        return ConversationResponse(
            conversation_id=conv_id,
            status=ConversationStatus.needs_clarification,
            message=reply_text,
            environment=current_env,
            recommendation=None,
        )

    # 5. Sufficient context (>=3 variables): call existing reason(env)
    rec_output = reason(current_env)
    reply_text = rec_output.recommendation

    # 6. Save assistant recommendation response in history
    active_store.add_turn(conv_id, role="assistant", message=reply_text)

    return ConversationResponse(
        conversation_id=conv_id,
        status=ConversationStatus.complete,
        message=reply_text,
        environment=current_env,
        recommendation=rec_output,
    )
