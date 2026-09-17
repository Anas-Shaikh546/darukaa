from __future__ import annotations

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.environment import EnvironmentInput
from app.schemas.recommendation import RecommendationOutput


class ConversationStatus(str, Enum):
    needs_clarification = "needs_clarification"
    complete = "complete"


class ConversationTurn(BaseModel):
    role: str = Field(..., description="Role of the speaker: user or assistant")
    message: str = Field(..., description="Content of the message")


class ConversationRequest(BaseModel):
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    message: str = Field(..., description="User message to the assistant")


class ConversationResponse(BaseModel):
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    status: ConversationStatus = Field(..., description="State of the conversation: needs_clarification or complete")
    message: str = Field(..., description="Assistant response or clarification question")
    environment: Optional[EnvironmentInput] = Field(None, description="Accumulated environmental context")
    recommendation: Optional[RecommendationOutput] = Field(None, description="Generated recommendation if complete")


class ConversationState(BaseModel):
    conversation_id: str
    environment: EnvironmentInput = Field(default_factory=EnvironmentInput)
    history: List[ConversationTurn] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
