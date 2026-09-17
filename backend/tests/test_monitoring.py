import re
import pytest

from app.schemas.environment import EnvironmentInput, Soil, Climate, Land, Biodiversity, RainfallCategory
from app.schemas.recommendation import MonitoringMetric, RecommendationOutput
from app.services import reasoning


def test_monitoring_metric_schema():
    """Verify MonitoringMetric model structure and defaults."""
    metric = MonitoringMetric(
        metric="soil_organic_carbon",
        why_monitor="Tracks soil-health response to intervention.",
        horizon="medium",
    )
    assert metric.metric == "soil_organic_carbon"
    assert metric.why_monitor == "Tracks soil-health response to intervention."
    assert metric.horizon == "medium"


def test_monitoring_plan_generation_soc_and_water():
    """Verify SOC and Rainfall pathways trigger soil_organic_carbon and soil_moisture."""
    variables = ["SOC", "Rainfall"]
    relationships = [
        ["SOC", "Soil Structure", "Water Retention", "Plant Survival"],
        ["Rainfall", "Water availability", "Species survival"],
    ]
    plan = reasoning._generate_monitoring_plan(variables, relationships)
    metrics_included = [m.metric for m in plan]

    assert "soil_organic_carbon" in metrics_included
    assert "soil_moisture" in metrics_included
    # Check that reasons match expected monitoring purpose
    soc_item = next(m for m in plan if m.metric == "soil_organic_carbon")
    assert soc_item.horizon == "medium"
    assert "soil-health" in soc_item.why_monitor.lower()

    moisture_item = next(m for m in plan if m.metric == "soil_moisture")
    assert moisture_item.horizon == "short"
    assert "water" in moisture_item.why_monitor.lower()


def test_monitoring_plan_generation_land_use_and_biodiversity():
    """Verify Land-use and Biodiversity pathways trigger habitat_diversity and species_richness."""
    variables = ["Land-use intensity", "Biodiversity"]
    relationships = [
        ["Land-use intensity", "Habitat fragmentation", "Species movement", "Species richness"],
        ["Habitat loss", "biodiversity pressure"],
    ]
    plan = reasoning._generate_monitoring_plan(variables, relationships)
    metrics_included = [m.metric for m in plan]

    assert "habitat_diversity" in metrics_included
    assert "species_richness" in metrics_included

    hab_item = next(m for m in plan if m.metric == "habitat_diversity")
    assert hab_item.horizon == "medium"

    spec_item = next(m for m in plan if m.metric == "species_richness")
    assert spec_item.horizon == "long"


def test_monitoring_plan_relevance_only_includes_relevant():
    """Only include metrics relevant to the actual variables/reasoning; do NOT include unrelated metrics."""
    # Only SOC and Rainfall, no habitat or biodiversity nodes
    variables = ["SOC"]
    relationships = [["SOC", "Soil Biology"]]
    plan = reasoning._generate_monitoring_plan(variables, relationships)
    metrics_included = [m.metric for m in plan]

    assert "soil_organic_carbon" in metrics_included
    assert "soil_moisture" not in metrics_included
    assert "habitat_diversity" not in metrics_included
    assert "species_richness" not in metrics_included


def test_monitoring_plan_no_invented_numerical_targets():
    """Monitoring descriptions must be qualitative and free from invented numbers (e.g., +20%, 15%)."""
    variables = ["SOC", "Rainfall", "Land-use intensity", "Biodiversity"]
    relationships = [
        ["SOC", "Soil Structure", "Water Retention", "Plant Survival", "Vegetation", "Habitat Quality", "Biodiversity"],
        ["Land-use intensity", "Habitat fragmentation", "Habitat connectivity", "Species movement", "Species richness"],
    ]
    plan = reasoning._generate_monitoring_plan(variables, relationships)
    assert len(plan) > 0

    number_pattern = re.compile(r"\b\d+(?:\.\d+)?%?\b")
    for item in plan:
        # Neither metric, why_monitor, nor horizon should contain invented numerical claims
        assert not number_pattern.findall(item.why_monitor), f"Found invented number in why_monitor: {item.why_monitor}"
        assert not number_pattern.findall(item.metric)


def test_recommendation_output_contains_monitoring_in_normal_generation():
    """A full RecommendationOutput object contains a populated monitoring list."""
    env = EnvironmentInput(
        soil=Soil(organic_carbon=0.3),
        climate=Climate(rainfall_category=RainfallCategory.low),
        land=Land(land_use="wheat monoculture"),
    )
    # Mock retrieval to avoid ChromaDB dependency
    def mock_retrieve(env, top_k=10):
        return {
            "results": [
                {
                    "source": "study_2020",
                    "title": "Soil carbon study",
                    "chunk_id": "c1",
                    "text": "Agroforestry improves soil carbon and moisture.",
                    "similarity": 0.85,
                },
                {
                    "source": "study_2021",
                    "title": "Moisture study",
                    "chunk_id": "c2",
                    "text": "Cover crops improve water retention.",
                    "similarity": 0.80,
                },
            ]
        }

    original_retrieve = reasoning.retrieve
    original_verifier = reasoning._run_verifier
    try:
        reasoning.retrieve = mock_retrieve
        reasoning._run_verifier = lambda claim, evidence: True

        output = reasoning.reason(env)
        assert isinstance(output, RecommendationOutput)
        assert hasattr(output, "monitoring")
        assert isinstance(output.monitoring, list)
        assert len(output.monitoring) > 0
        metrics = [m.metric for m in output.monitoring]
        assert "soil_organic_carbon" in metrics
        assert "soil_moisture" in metrics
    finally:
        reasoning.retrieve = original_retrieve
        reasoning._run_verifier = original_verifier


def test_fallback_output_has_empty_monitoring_list():
    """Fallback output should safely provide an empty monitoring list without failing."""
    fallback = reasoning._fallback_output(1, "Only 1 variable detected")
    assert hasattr(fallback, "monitoring")
    assert fallback.monitoring == []
