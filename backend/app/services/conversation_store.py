"""In-memory conversation state store for Darukaa Day 3.

Provides isolated, thread-safe access to multi-turn conversation states
keyed by conversation_id without external databases or dependencies.
"""

from __future__ import annotations

from threading import Lock
from typing import Dict, Optional, Any

from app.schemas.conversation import ConversationState, ConversationTurn
from app.schemas.environment import (
    EnvironmentInput,
    Soil,
    Climate,
    Land,
    Biodiversity,
    HumanImpact,
    Location,
)


class ConversationStore:
    """In-memory conversation store keyed by conversation_id."""

    def __init__(self) -> None:
        self._store: Dict[str, ConversationState] = {}
        self._lock = Lock()

    def get_or_create(self, conversation_id: str) -> ConversationState:
        """Retrieve existing state or create a fresh isolated conversation state."""
        with self._lock:
            if conversation_id not in self._store:
                self._store[conversation_id] = ConversationState(
                    conversation_id=conversation_id,
                    environment=EnvironmentInput(),
                    history=[],
                    metadata={},
                )
            return self._store[conversation_id]

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve state for a conversation_id, or None if not found."""
        with self._lock:
            return self._store.get(conversation_id)

    def add_turn(self, conversation_id: str, role: str, message: str) -> ConversationState:
        """Append a message turn to conversation history."""
        state = self.get_or_create(conversation_id)
        with self._lock:
            state.history.append(ConversationTurn(role=role, message=message))
            return state

    def update_environment(
        self,
        conversation_id: str,
        *,
        soil: Optional[Soil] = None,
        climate: Optional[Climate] = None,
        land: Optional[Land] = None,
        biodiversity: Optional[Biodiversity] = None,
        human_impact: Optional[HumanImpact] = None,
        location: Optional[Location] = None,
    ) -> ConversationState:
        """Merge new non-None environmental attributes into the conversation state.
        
        Preserves previously recorded attributes unless explicitly updated with a non-None value.
        """
        state = self.get_or_create(conversation_id)
        with self._lock:
            current_env = state.environment

            if soil is not None:
                if current_env.soil is None:
                    current_env.soil = soil
                else:
                    # Update fields within Soil
                    for field, val in soil.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(current_env.soil, field, val)

            if climate is not None:
                if current_env.climate is None:
                    current_env.climate = climate
                else:
                    for field, val in climate.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(current_env.climate, field, val)

            if land is not None:
                if current_env.land is None:
                    current_env.land = land
                else:
                    for field, val in land.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(current_env.land, field, val)

            if biodiversity is not None:
                if current_env.biodiversity is None:
                    current_env.biodiversity = biodiversity
                else:
                    for field, val in biodiversity.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(current_env.biodiversity, field, val)

            if human_impact is not None:
                if current_env.human_impact is None:
                    current_env.human_impact = human_impact
                else:
                    for field, val in human_impact.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(current_env.human_impact, field, val)

            if location is not None:
                if current_env.location is None:
                    current_env.location = location
                else:
                    for field, val in location.model_dump(exclude_unset=True).items():
                        if val is not None:
                            setattr(current_env.location, field, val)

            return state

    def update_environment_input(
        self, conversation_id: str, new_env: EnvironmentInput
    ) -> ConversationState:
        """Merge an entire EnvironmentInput object into the stored state."""
        return self.update_environment(
            conversation_id,
            soil=new_env.soil,
            climate=new_env.climate,
            land=new_env.land,
            biodiversity=new_env.biodiversity,
            human_impact=new_env.human_impact,
            location=new_env.location,
        )

    def clear(self, conversation_id: Optional[str] = None) -> None:
        """Clear a specific conversation or all stored conversations."""
        with self._lock:
            if conversation_id is not None:
                self._store.pop(conversation_id, None)
            else:
                self._store.clear()


# Global store instance for app usage
store = ConversationStore()
