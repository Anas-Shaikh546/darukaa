from unittest.mock import patch
import pytest

from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationStatus,
)
from app.schemas.environment import (
    EnvironmentInput,
    Soil,
    Climate,
    Land,
    RainfallCategory,
)
from app.schemas.recommendation import (
    RecommendationOutput,
    Reasoning,
    ImpactMetric,
    EvidenceItem,
    MonitoringMetric,
)
from app.services.conversation_store import ConversationStore
from app.services.conversation_service import process_conversation_turn


@pytest.fixture
def store():
    return ConversationStore()


@pytest.fixture
def mock_recommendation_output():
    return RecommendationOutput(
        recommendation="Implement agroforestry with diverse native trees.",
        reasoning=Reasoning(
            variables=["SOC", "Rainfall", "Land-use intensity"],
            relationships=[
                ["SOC", "Soil Structure", "Water Retention", "Plant Survival"],
                ["Land-use intensity", "Habitat fragmentation", "Species richness"],
            ],
            explanation="Context with low SOC, low rainfall, and monoculture addressed by agroforestry.",
        ),
        impacted_metrics=[
            ImpactMetric(
                metric="soil_organic_carbon",
                estimate="potentially improved",
                basis="Agroforestry increases root and leaf litter.",
            ),
            ImpactMetric(
                metric="species_richness",
                estimate="potentially improved",
                basis="Creates diverse microhabitats.",
            ),
        ],
        time_horizon="medium",
        confidence=0.82,
        evidence=[
            EvidenceItem(
                source="study_2022",
                title="Agroforestry in semi-arid zones",
                chunk_id="chunk_10",
                used_for="supports recommendation",
                text="Agroforestry enhances soil organic carbon.",
                similarity=0.82,
            )
        ],
        validation={
            "variable_count": 3,
            "evidence_grounded": True,
            "numeric_claims_ok": True,
            "llm_verification_ok": True,
            "retry_used": False,
        },
        monitoring=[
            MonitoringMetric(
                metric="soil_organic_carbon",
                why_monitor="Tracks the soil-health response to the intervention.",
                horizon="medium",
            ),
            MonitoringMetric(
                metric="soil_moisture",
                why_monitor="Tracks water availability and retention.",
                horizon="short",
            ),
            MonitoringMetric(
                metric="species_richness",
                why_monitor="Tracks the biodiversity response.",
                horizon="long",
            ),
        ],
    )


def test_incomplete_turn_returns_clarification(store):
    """An initial message with <3 variables returns needs_clarification and asks for missing context."""
    req = ConversationRequest(
        conversation_id="conv-incomplete",
        message="My farm has soil organic carbon of 0.3%.",
    )
    resp = process_conversation_turn(req, store=store)

    assert isinstance(resp, ConversationResponse)
    assert resp.conversation_id == "conv-incomplete"
    assert resp.status == ConversationStatus.needs_clarification
    assert resp.recommendation is None
    assert "at least 3 environmental variables" in resp.message
    assert resp.environment.soil.organic_carbon == 0.3
    # Unmentioned variables must not be invented
    assert resp.environment.climate is None
    assert resp.environment.land is None


def test_two_turn_conversation_accumulates_context_and_completes(store, mock_recommendation_output):
    """Turn 1 collects SOC and rainfall (incomplete). Turn 2 adds land use, reaching 3 variables and calling reason()."""
    conv_id = "conv-twoturn"

    with patch("app.services.conversation_service.reason", return_value=mock_recommendation_output) as mock_reason:
        # Turn 1
        req1 = ConversationRequest(
            conversation_id=conv_id,
            message="My soil organic carbon is 0.3% and rainfall is low.",
        )
        resp1 = process_conversation_turn(req1, store=store)

        assert resp1.status == ConversationStatus.needs_clarification
        assert resp1.recommendation is None
        assert mock_reason.call_count == 0

        # Turn 2
        req2 = ConversationRequest(
            conversation_id=conv_id,
            message="I grow wheat continuously.",
        )
        resp2 = process_conversation_turn(req2, store=store)

        assert resp2.status == ConversationStatus.complete
        assert resp2.recommendation is not None
        assert mock_reason.call_count == 1

        # Check that reason(env) was called with the accumulated context
        called_env = mock_reason.call_args[0][0]
        assert isinstance(called_env, EnvironmentInput)
        assert called_env.soil.organic_carbon == 0.3
        assert called_env.climate.rainfall_category == RainfallCategory.low
        assert called_env.land.land_use == "wheat monoculture"


def test_sufficient_single_turn_calls_reason_immediately(store, mock_recommendation_output):
    """When a single message contains >=3 variables, reason(env) is invoked immediately."""
    with patch("app.services.conversation_service.reason", return_value=mock_recommendation_output) as mock_reason:
        req = ConversationRequest(
            conversation_id="conv-single-turn",
            message="Soil organic carbon is 0.4%, rainfall is low, and land is used for continuous wheat monoculture.",
        )
        resp = process_conversation_turn(req, store=store)

        assert resp.status == ConversationStatus.complete
        assert mock_reason.call_count == 1
        assert resp.recommendation == mock_recommendation_output


def test_returned_recommendation_reuses_existing_recommendation_output(store, mock_recommendation_output):
    """Verify that RecommendationOutput fields (metrics, evidence, confidence, monitoring, validation) are intact."""
    with patch("app.services.conversation_service.reason", return_value=mock_recommendation_output):
        req = ConversationRequest(
            conversation_id="conv-full-check",
            message="SOC 0.3%, rainfall low, wheat monoculture.",
        )
        resp = process_conversation_turn(req, store=store)
        rec = resp.recommendation

        assert rec.recommendation == "Implement agroforestry with diverse native trees."
        assert rec.confidence == 0.82
        assert len(rec.impacted_metrics) == 2
        assert len(rec.evidence) == 1
        assert rec.validation["variable_count"] == 3
        assert len(rec.monitoring) == 3
        assert rec.monitoring[0].metric == "soil_organic_carbon"


def test_assistant_response_saved_in_history(store, mock_recommendation_output):
    """Both user questions and assistant replies (clarifications and recommendations) are stored in history."""
    conv_id = "conv-history-check"

    with patch("app.services.conversation_service.reason", return_value=mock_recommendation_output):
        # Turn 1: Clarification
        req1 = ConversationRequest(conversation_id=conv_id, message="My farm has low rainfall.")
        process_conversation_turn(req1, store=store)

        state1 = store.get(conv_id)
        assert len(state1.history) == 2
        assert state1.history[0].role == "user"
        assert state1.history[0].message == "My farm has low rainfall."
        assert state1.history[1].role == "assistant"
        assert "at least 3 environmental variables" in state1.history[1].message

        # Turn 2: Recommendation
        req2 = ConversationRequest(conversation_id=conv_id, message="SOC is 0.3% and we practice wheat monoculture.")
        process_conversation_turn(req2, store=store)

        state2 = store.get(conv_id)
        assert len(state2.history) == 4
        assert state2.history[2].role == "user"
        assert state2.history[3].role == "assistant"
        assert state2.history[3].message == mock_recommendation_output.recommendation


def test_separate_conversation_ids_remain_isolated(store, mock_recommendation_output):
    """Context and turns in one conversation do not bleed into or satisfy another conversation."""
    with patch("app.services.conversation_service.reason", return_value=mock_recommendation_output) as mock_reason:
        # Conversation 1 gives SOC and rainfall
        req1 = ConversationRequest(conversation_id="farm-alpha", message="Soil organic carbon is 0.3% and rainfall is low.")
        resp1 = process_conversation_turn(req1, store=store)
        assert resp1.status == ConversationStatus.needs_clarification

        # Conversation 2 only gives crop pattern
        req2 = ConversationRequest(conversation_id="farm-beta", message="We grow wheat continuously.")
        resp2 = process_conversation_turn(req2, store=store)
        # Beta must need clarification because Alpha's SOC and rainfall are isolated!
        assert resp2.status == ConversationStatus.needs_clarification
        assert mock_reason.call_count == 0

        # State check
        state_alpha = store.get("farm-alpha")
        state_beta = store.get("farm-beta")
        assert state_alpha.environment.soil.organic_carbon == 0.3
        assert state_alpha.environment.land is None
        assert state_beta.environment.soil is None
        assert state_beta.environment.land.land_use == "wheat monoculture"
