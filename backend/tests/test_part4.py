from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.environment import EnvironmentInput, Soil, Climate, Land, RainfallCategory
from app.schemas.recommendation import (
    RecommendationOutput,
    Reasoning,
    ImpactMetric,
    EvidenceItem,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_recommendation_generate_endpoint_success(client):
    # Mock reason() so Part 4 API test is completely decoupled from ChromaDB and external LLMs
    mock_output = RecommendationOutput(
        recommendation="Implement agroforestry system with native tree species.",
        reasoning=Reasoning(
            variables=["SOC", "Rainfall", "Land-use intensity"],
            relationships=[
                ["SOC", "Soil Structure", "Water Retention", "Plant Survival"],
                ["Land-use intensity", "Habitat fragmentation", "Species richness"],
            ],
            explanation="Addressing low SOC and land use pressure via agroforestry.",
        ),
        impacted_metrics=[
            ImpactMetric(
                metric="species_richness",
                estimate="+15%",
                basis="Agroforestry restores multi-strata habitat.",
            )
        ],
        time_horizon="medium",
        confidence=0.85,
        evidence=[
            EvidenceItem(
                source="agroforestry_study_2021",
                title="Agroforestry and Soil Health",
                chunk_id="chunk_101",
                used_for="supports recommendation",
                text="Agroforestry improves soil organic carbon and biodiversity.",
                similarity=0.85,
            )
        ],
        validation={
            "variable_count": 3,
            "evidence_grounded": True,
            "numeric_claims_ok": True,
            "llm_verification_ok": True,
            "messages": [],
            "retry_used": False,
        },
    )

    with patch("app.api.recommendation.reason", return_value=mock_output) as mock_reason:
        payload = {
            "soil": {"organic_carbon": 0.3},
            "climate": {"rainfall_category": "low"},
            "land": {"land_use": "wheat monoculture"},
        }
        response = client.post("/api/v1/recommendation/generate", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verify endpoint called reason() with parsed EnvironmentInput
        assert mock_reason.called
        call_arg = mock_reason.call_args[0][0]
        assert isinstance(call_arg, EnvironmentInput)
        assert call_arg.soil.organic_carbon == 0.3
        assert call_arg.climate.rainfall_category == RainfallCategory.low
        assert call_arg.land.land_use == "wheat monoculture"

        # Verify response matches RecommendationOutput schema
        assert data["recommendation"] == "Implement agroforestry system with native tree species."
        assert data["reasoning"]["variables"] == ["SOC", "Rainfall", "Land-use intensity"]
        assert len(data["reasoning"]["relationships"]) == 2
        assert len(data["impacted_metrics"]) == 1
        assert data["impacted_metrics"][0]["metric"] == "species_richness"
        assert data["confidence"] == 0.85
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["source"] == "agroforestry_study_2021"
        assert data["validation"]["retry_used"] is False


def test_recommendation_generate_endpoint_invalid_input(client):
    # Test invalid payload types (e.g. soil.organic_carbon as string that cannot be parsed as float)
    response = client.post(
        "/api/v1/recommendation/generate",
        json={"soil": {"organic_carbon": "not-a-number"}},
    )
    assert response.status_code == 422
