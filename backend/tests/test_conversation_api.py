from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationStatus,
)
from app.schemas.environment import EnvironmentInput, Soil, Climate, Land, RainfallCategory
from app.schemas.recommendation import (
    RecommendationOutput,
    Reasoning,
    ImpactMetric,
    EvidenceItem,
    MonitoringMetric,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_conversation_turn_endpoint_path_and_acceptance(client):
    """POST /api/v1/conversation/turn accepts valid ConversationRequest and calls process_conversation_turn."""
    mock_response = ConversationResponse(
        conversation_id="test-conv-1",
        status=ConversationStatus.needs_clarification,
        message="Please provide more details on your rainfall conditions.",
        environment=EnvironmentInput(soil=Soil(organic_carbon=0.3)),
        recommendation=None,
    )

    with patch(
        "app.api.conversation.process_conversation_turn", return_value=mock_response
    ) as mock_service:
        payload = {
            "conversation_id": "test-conv-1",
            "message": "My soil organic carbon is 0.3%.",
        }
        response = client.post("/api/v1/conversation/turn", json=payload)

        assert response.status_code == 200
        assert mock_service.called
        call_arg = mock_service.call_args[0][0]
        assert isinstance(call_arg, ConversationRequest)
        assert call_arg.conversation_id == "test-conv-1"
        assert call_arg.message == "My soil organic carbon is 0.3%."


def test_conversation_turn_needs_clarification_response(client):
    """Verify serialization of a needs_clarification response."""
    mock_response = ConversationResponse(
        conversation_id="test-conv-clarify",
        status=ConversationStatus.needs_clarification,
        message="Could you please share your land use or current crop pattern?",
        environment=EnvironmentInput(
            soil=Soil(organic_carbon=0.3),
            climate=Climate(rainfall_category=RainfallCategory.low),
        ),
        recommendation=None,
    )

    with patch(
        "app.api.conversation.process_conversation_turn", return_value=mock_response
    ):
        payload = {
            "conversation_id": "test-conv-clarify",
            "message": "SOC is 0.3% and rainfall is low.",
        }
        response = client.post("/api/v1/conversation/turn", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-conv-clarify"
        assert data["status"] == "needs_clarification"
        assert "land use" in data["message"]
        assert data["recommendation"] is None
        assert data["environment"]["soil"]["organic_carbon"] == 0.3
        assert data["environment"]["climate"]["rainfall_category"] == "low"


def test_conversation_turn_complete_response_with_recommendation(client):
    """Verify serialization of a complete response including RecommendationOutput and monitoring plan."""
    mock_rec = RecommendationOutput(
        recommendation="Consider implementing agroforestry.",
        reasoning=Reasoning(
            variables=["SOC", "Rainfall", "Land-use intensity"],
            relationships=[["SOC", "Soil Structure", "Water Retention"]],
            explanation="Addressing low SOC and low rainfall.",
        ),
        impacted_metrics=[
            ImpactMetric(
                metric="soil_organic_carbon",
                estimate="potentially improved",
                basis="Agroforestry restores organic inputs.",
            )
        ],
        time_horizon="medium",
        confidence=0.85,
        evidence=[
            EvidenceItem(
                source="study_2022",
                title="Agroforestry Paper",
                chunk_id="chunk_1",
                used_for="supporting recommendation",
                text="Agroforestry improves soil organic carbon.",
                similarity=0.85,
            )
        ],
        validation={"variable_count": 3, "retry_used": False},
        monitoring=[
            MonitoringMetric(
                metric="soil_organic_carbon",
                why_monitor="Tracks the soil-health response to the intervention.",
                horizon="medium",
            )
        ],
    )

    mock_response = ConversationResponse(
        conversation_id="test-conv-complete",
        status=ConversationStatus.complete,
        message="Consider implementing agroforestry.",
        environment=EnvironmentInput(
            soil=Soil(organic_carbon=0.3),
            climate=Climate(rainfall_category=RainfallCategory.low),
            land=Land(land_use="wheat monoculture"),
        ),
        recommendation=mock_rec,
    )

    with patch(
        "app.api.conversation.process_conversation_turn", return_value=mock_response
    ):
        payload = {
            "conversation_id": "test-conv-complete",
            "message": "I grow wheat continuously.",
        }
        response = client.post("/api/v1/conversation/turn", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-conv-complete"
        assert data["status"] == "complete"
        assert data["recommendation"] is not None
        assert data["recommendation"]["recommendation"] == "Consider implementing agroforestry."
        assert data["recommendation"]["confidence"] == 0.85
        assert len(data["recommendation"]["monitoring"]) == 1
        assert data["recommendation"]["monitoring"][0]["metric"] == "soil_organic_carbon"


def test_conversation_turn_invalid_request_returns_422(client):
    """Missing required fields (e.g. missing message or conversation_id) trigger FastAPI 422."""
    # Missing 'message'
    response1 = client.post(
        "/api/v1/conversation/turn", json={"conversation_id": "test-id"}
    )
    assert response1.status_code == 422

    # Missing 'conversation_id'
    response2 = client.post(
        "/api/v1/conversation/turn", json={"message": "hello"}
    )
    assert response2.status_code == 422

    # Empty payload
    response3 = client.post("/api/v1/conversation/turn", json={})
    assert response3.status_code == 422


def test_conversation_turn_exact_endpoint_path(client):
    """Verify that the route is mounted exactly at /api/v1/conversation/turn."""
    mock_response = ConversationResponse(
        conversation_id="test-path",
        status=ConversationStatus.needs_clarification,
        message="Clarification question.",
    )
    with patch(
        "app.api.conversation.process_conversation_turn", return_value=mock_response
    ):
        # Correct path
        res_ok = client.post(
            "/api/v1/conversation/turn",
            json={"conversation_id": "test-path", "message": "test"},
        )
        assert res_ok.status_code == 200

        # Wrong path should 404
        res_404 = client.post(
            "/api/v1/conversation/wrong",
            json={"conversation_id": "test-path", "message": "test"},
        )
        assert res_404.status_code == 404
