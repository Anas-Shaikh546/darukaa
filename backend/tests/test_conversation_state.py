import pytest

from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationState,
    ConversationStatus,
    ConversationTurn,
)
from app.schemas.environment import (
    EnvironmentInput,
    Soil,
    Climate,
    Land,
    Biodiversity,
    RainfallCategory,
)
from app.services.conversation_store import ConversationStore


@pytest.fixture
def fresh_store():
    return ConversationStore()


def test_conversation_can_be_created(fresh_store):
    """A new conversation can be created and initialized with an empty environment and history."""
    state = fresh_store.get_or_create("conv-1")
    assert state.conversation_id == "conv-1"
    assert isinstance(state.environment, EnvironmentInput)
    assert state.history == []


def test_context_can_be_stored_and_retrieved(fresh_store):
    """Context and turns can be stored and correctly retrieved by conversation_id."""
    fresh_store.get_or_create("conv-2")
    fresh_store.add_turn("conv-2", role="user", message="Soil is acidic and degraded.")
    fresh_store.update_environment("conv-2", soil=Soil(organic_carbon=0.4, pH=5.5))

    retrieved = fresh_store.get("conv-2")
    assert retrieved is not None
    assert len(retrieved.history) == 1
    assert retrieved.history[0].role == "user"
    assert retrieved.history[0].message == "Soil is acidic and degraded."
    assert retrieved.environment.soil is not None
    assert retrieved.environment.soil.organic_carbon == 0.4
    assert retrieved.environment.soil.pH == 5.5


def test_updating_context_preserves_previous_information(fresh_store):
    """Updating new environmental variables across turns preserves previously gathered context."""
    conv_id = "multi-turn-conv"
    fresh_store.get_or_create(conv_id)

    # Turn 1: Soil information
    fresh_store.update_environment(conv_id, soil=Soil(organic_carbon=0.3))
    # Turn 2: Climate information
    fresh_store.update_environment(conv_id, climate=Climate(rainfall_category=RainfallCategory.low))
    # Turn 3: Land-use information
    fresh_store.update_environment(conv_id, land=Land(land_use="wheat monoculture"))

    state = fresh_store.get(conv_id)
    assert state is not None
    # Previous turns' info must all be preserved
    assert state.environment.soil is not None
    assert state.environment.soil.organic_carbon == 0.3
    assert state.environment.climate is not None
    assert state.environment.climate.rainfall_category == RainfallCategory.low
    assert state.environment.land is not None
    assert state.environment.land.land_use == "wheat monoculture"


def test_two_different_conversation_ids_have_isolated_context(fresh_store):
    """Two different conversation_id values have strictly isolated context."""
    fresh_store.update_environment("conv-A", soil=Soil(organic_carbon=0.2))
    fresh_store.add_turn("conv-A", role="user", message="Farm A query")

    fresh_store.update_environment("conv-B", soil=Soil(organic_carbon=1.8), land=Land(land_use="agroforestry"))
    fresh_store.add_turn("conv-B", role="user", message="Farm B query")

    state_a = fresh_store.get("conv-A")
    state_b = fresh_store.get("conv-B")

    assert state_a.environment.soil.organic_carbon == 0.2
    assert state_a.environment.land is None
    assert len(state_a.history) == 1
    assert state_a.history[0].message == "Farm A query"

    assert state_b.environment.soil.organic_carbon == 1.8
    assert state_b.environment.land.land_use == "agroforestry"
    assert len(state_b.history) == 1
    assert state_b.history[0].message == "Farm B query"


def test_new_conversation_does_not_inherit_another_conversations_data(fresh_store):
    """A newly created conversation does not inherit any other conversation's state."""
    fresh_store.update_environment("existing-conv", soil=Soil(organic_carbon=0.5))
    fresh_store.add_turn("existing-conv", role="user", message="Existing message")

    new_state = fresh_store.get_or_create("brand-new-conv")
    assert new_state.environment.soil is None
    assert new_state.environment.climate is None
    assert new_state.environment.land is None
    assert new_state.environment.biodiversity is None
    assert new_state.history == []


def test_conversation_schemas_structure():
    """Verify request, response, and status schema structures."""
    req = ConversationRequest(conversation_id="test-id", message="Hello")
    assert req.conversation_id == "test-id"
    assert req.message == "Hello"

    resp_clarification = ConversationResponse(
        conversation_id="test-id",
        status=ConversationStatus.needs_clarification,
        message="What is the rainfall like in your region?",
    )
    assert resp_clarification.status == ConversationStatus.needs_clarification
    assert resp_clarification.recommendation is None

    resp_complete = ConversationResponse(
        conversation_id="test-id",
        status=ConversationStatus.complete,
        message="Recommendation ready.",
        environment=EnvironmentInput(soil=Soil(organic_carbon=0.3)),
    )
    assert resp_complete.status == ConversationStatus.complete
    assert resp_complete.environment.soil.organic_carbon == 0.3
