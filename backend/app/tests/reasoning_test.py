import pytest
from app.schemas.environment import EnvironmentInput, Soil, Climate, Land, Biodiversity
from app.services.reasoning import reason

@pytest.fixture
def sample_env():
    return EnvironmentInput(
        soil=Soil(organic_carbon=0.3),
        climate=Climate(rainfall_category='low'),
        land=Land(land_use='wheat monoculture'),
        biodiversity=Biodiversity(),
    )

def test_reasoning_pipeline(sample_env):
    output = reason(sample_env)
    # Recommendation text exists
    assert output.recommendation
    # Variables list contains at least the three required identifiers
    required = {'SOC', 'Rainfall', 'Land-use intensity'}
    assert required.issubset(set(output.reasoning.variables))
    # Graph traversal produced at least one relationship path
    assert isinstance(output.reasoning.relationships, list)
    assert len(output.reasoning.relationships) > 0
    # Impact metrics present
    assert len(output.impacted_metrics) >= 1
    # Evidence list is a list (may be empty if no hits)
    assert isinstance(output.evidence, list)
