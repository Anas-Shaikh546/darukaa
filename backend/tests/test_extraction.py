import pytest

from app.schemas.environment import (
    EnvironmentInput,
    Soil,
    Climate,
    Land,
    Biodiversity,
    RainfallCategory,
)
from app.services.conversation_store import ConversationStore
from app.services.extraction import (
    extract_environmental_info,
    count_connected_variables,
    evaluate_clarification_need,
)


def test_soc_extraction():
    """Extract soil organic carbon percentage explicitly stated by the user."""
    msg = "My soil organic carbon is 0.3% and we need advice."
    env = extract_environmental_info(msg)
    assert env.soil is not None
    assert env.soil.organic_carbon == 0.3

    msg2 = "SOC: 1.25%, with sandy texture"
    env2 = extract_environmental_info(msg2)
    assert env2.soil is not None
    assert env2.soil.organic_carbon == 1.25


def test_rainfall_extraction():
    """Extract rainfall / water availability categories or mm/year explicitly stated."""
    msg = "The rainfall is low in this area."
    env = extract_environmental_info(msg)
    assert env.climate is not None
    assert env.climate.rainfall_category == RainfallCategory.low

    msg2 = "We experience high rainfall throughout the year."
    env2 = extract_environmental_info(msg2)
    assert env2.climate is not None
    assert env2.climate.rainfall_category == RainfallCategory.high

    msg3 = "Annual precipitation is 450 mm/year"
    env3 = extract_environmental_info(msg3)
    assert env3.climate is not None
    assert env3.climate.rainfall_mm_year == 450.0


def test_land_use_and_crop_extraction():
    """Extract land use and crop patterns explicitly stated."""
    msg = "I grow wheat continuously on this plot."
    env = extract_environmental_info(msg)
    assert env.land is not None
    assert env.land.land_use == "wheat monoculture"

    msg2 = "The current system is agroforestry."
    env2 = extract_environmental_info(msg2)
    assert env2.land is not None
    assert env2.land.land_use == "agroforestry"


def test_merging_extracted_values_with_previous_context():
    """Multi-turn interaction correctly merges newly extracted information into store context."""
    store = ConversationStore()
    conv_id = "test-extract-merge"

    # Turn 1: user mentions SOC and rainfall
    msg1 = "My soil organic carbon is 0.3% and rainfall is low."
    env1 = extract_environmental_info(msg1)
    store.update_environment_input(conv_id, env1)

    state1 = store.get(conv_id)
    assert state1.environment.soil.organic_carbon == 0.3
    assert state1.environment.climate.rainfall_category == RainfallCategory.low
    assert state1.environment.land is None

    # Check that after Turn 1, context is still incomplete
    needs_clarif, _ = evaluate_clarification_need(state1.environment)
    assert needs_clarif is True

    # Turn 2: user mentions continuous wheat
    msg2 = "I grow wheat continuously."
    env2 = extract_environmental_info(msg2)
    store.update_environment_input(conv_id, env2)

    state2 = store.get(conv_id)
    # Merged context has all three
    assert state2.environment.soil.organic_carbon == 0.3
    assert state2.environment.climate.rainfall_category == RainfallCategory.low
    assert state2.environment.land.land_use == "wheat monoculture"

    # Check that after Turn 2, context is now complete (>= 3 variables)
    needs_clarif2, _ = evaluate_clarification_need(state2.environment)
    assert needs_clarif2 is False


def test_incomplete_context_triggers_clarification():
    """Context with fewer than 3 connected variables triggers clarification requesting missing info."""
    env = EnvironmentInput(
        soil=Soil(organic_carbon=0.3),
        climate=Climate(rainfall_category=RainfallCategory.low),
    )
    needs_clarif, clarif_msg = evaluate_clarification_need(env)
    assert needs_clarif is True
    assert clarif_msg is not None
    assert "land use" in clarif_msg.lower() or "crop" in clarif_msg.lower()


def test_sufficient_three_variable_context_no_clarification():
    """Context with at least 3 connected variables requires no clarification."""
    env = EnvironmentInput(
        soil=Soil(organic_carbon=0.3),
        climate=Climate(rainfall_category=RainfallCategory.low),
        land=Land(land_use="wheat monoculture"),
    )
    needs_clarif, clarif_msg = evaluate_clarification_need(env)
    assert needs_clarif is False
    assert clarif_msg is None


def test_missing_values_are_never_invented():
    """When a message only mentions soil, other fields remain strictly None."""
    msg = "The soil organic carbon is 0.5%."
    env = extract_environmental_info(msg)
    assert env.soil is not None
    assert env.soil.organic_carbon == 0.5
    # Strict check: unmentioned fields must be None
    assert env.climate is None
    assert env.land is None
    assert env.biodiversity is None
    assert env.human_impact is None
    assert env.location is None
