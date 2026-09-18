"""Environmental extraction and clarification service for Darukaa Day 3.

Provides deterministic natural-language extraction of environmental variables
into EnvironmentInput and determines whether clarification is needed to satisfy
the requirement of at least 3 connected environmental variables.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from app.schemas.environment import (
    Biodiversity,
    Climate,
    EnvironmentInput,
    HumanImpact,
    Land,
    Location,
    RainfallCategory,
    Soil,
)


def extract_environmental_info(message: str) -> EnvironmentInput:
    """Deterministically extract explicitly stated environmental information from text.

    Never invents missing values; only populates fields explicitly mentioned.
    """
    text = message.lower()

    soil_kwargs = {}
    climate_kwargs = {}
    land_kwargs = {}
    biodiversity_kwargs = {}
    human_impact_kwargs = {}
    location_kwargs = {}

    # 1. Soil Organic Carbon (SOC)
    # Patterns like:
    # "soil organic carbon is 0.3%"
    # "soc of 0.5"
    # "soc: 0.3"
    # "organic carbon is 0.4%"
    soc_match = re.search(
        r"(?:soil\s+organic\s+carbon|organic\s+carbon|soc)\s*"
        r"(?:is|of|:|=)?\s*"
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
        text,
    )

    if not soc_match:
        soc_match = re.search(
            r"(?:soil\s+organic\s+carbon|organic\s+carbon|soc)\s*"
            r"(?:is|of|:|=)?\s*"
            r"([0-9]+(?:\.[0-9]+)?)",
            text,
        )

    if soc_match:
        try:
            soil_kwargs["organic_carbon"] = float(soc_match.group(1))
        except ValueError:
            pass

    # Soil pH
    ph_match = re.search(
        r"(?:soil\s+)?ph\s*(?:is|of|:|=)?\s*([0-9]+(?:\.[0-9]+)?)",
        text,
    )

    if ph_match:
        try:
            soil_kwargs["pH"] = float(ph_match.group(1))
        except ValueError:
            pass

    # 2. Climate / Rainfall

    # Rainfall category
    if re.search(
        r"(?:rainfall|precipitation|rain)\s*"
        r"(?:is|level|pattern)?\s*(?:is|:|=)?\s*low\b"
        r"|\blow\s+(?:rainfall|rain|precipitation)\b",
        text,
    ):
        climate_kwargs["rainfall_category"] = RainfallCategory.low

    elif re.search(
        r"(?:rainfall|precipitation|rain)\s*"
        r"(?:is|level|pattern)?\s*(?:is|:|=)?\s*high\b"
        r"|\bhigh\s+(?:rainfall|rain|precipitation)\b",
        text,
    ):
        climate_kwargs["rainfall_category"] = RainfallCategory.high

    elif re.search(
        r"(?:rainfall|precipitation|rain)\s*"
        r"(?:is|level|pattern)?\s*(?:is|:|=)?\s*(?:medium|moderate)\b"
        r"|\b(?:medium|moderate)\s+(?:rainfall|rain|precipitation)\b",
        text,
    ):
        climate_kwargs["rainfall_category"] = RainfallCategory.medium

    # Rainfall mm/year
    rain_mm_match = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*"
        r"(?:mm|millimeters)\s*(?:/|\s*per\s*)?\s*year",
        text,
    )

    if rain_mm_match:
        try:
            climate_kwargs["rainfall_mm_year"] = float(rain_mm_match.group(1))
        except ValueError:
            pass

    # 3. Land use / crop pattern
    # Known agricultural and land-use phrases
    if (
        "monoculture" in text
        or "continuous wheat" in text
        or "grow wheat continuously" in text
        or "wheat monoculture" in text
    ):
        if "wheat" in text:
            land_kwargs["land_use"] = "wheat monoculture"
        else:
            land_kwargs["land_use"] = "monoculture"

    elif "agroforestry" in text:
        land_kwargs["land_use"] = "agroforestry"

    elif "intercropping" in text or "intercrop" in text:
        land_kwargs["land_use"] = "intercropping"

    elif "cover crop" in text or "cover crops" in text:
        land_kwargs["land_use"] = "cover cropping"

    elif "pasture" in text or "grazing" in text:
        land_kwargs["land_use"] = "pasture"

    elif "intensive farming" in text or "intensive agriculture" in text:
        land_kwargs["land_use"] = "intensive agriculture"

    else:
        # Check generic phrases like "grow <crop>" or "farming <type>"
        crop_match = re.search(
            r"(?:i\s+grow|growing|we\s+grow|farm\s+is\s+used\s+for|plant)\s+"
            r"([a-z\s]+?)(?:\.|$|,|\band\b)",
            text,
        )

        if crop_match:
            crop_name = crop_match.group(1).strip()
            if len(crop_name) > 2 and crop_name not in {
                "poor",
                "good",
                "low",
                "high",
            }:
                land_kwargs["land_use"] = crop_name

    # 4. Biodiversity
    #
    # Numeric biodiversity measurements are preserved exactly when supplied.
    species_richness_match = re.search(
        r"(?:species\s+richness|species\s+count)\s*"
        r"(?:is|of|:|=)?\s*([0-9]+(?:\.[0-9]+)?)",
        text,
    )

    if species_richness_match:
        try:
            biodiversity_kwargs["species_richness"] = float(
                species_richness_match.group(1)
            )
        except ValueError:
            pass

    # Qualitative biodiversity statements are stored as qualitative status.
    # No fabricated numeric species-richness value is created.
    elif re.search(
        r"\b(?:declining|decline|decreasing|decrease|falling|worsening)\b"
        r".{0,40}\b(?:biodiversity|species\s+richness|species\s+abundance)\b"
        r"|\b(?:biodiversity|species\s+richness|species\s+abundance)\b"
        r".{0,40}\b(?:declining|decline|decreasing|decrease|falling|worsening)\b",
        text,
    ) or re.search(
        r"\b(?:species\s+are|species\s+have\s+become|species\s+becoming)\b"
        r".{0,30}\b(?:less\s+common|rarer|less\s+abundant)\b",
        text,
    ):
        biodiversity_kwargs["status"] = "declining"

    elif re.search(
        r"\b(?:low|poor)\s+(?:biodiversity|species\s+richness)\b"
        r"|\b(?:biodiversity|species\s+richness)\s+is\s+"
        r"(?:low|poor)\b",
        text,
    ):
        biodiversity_kwargs["status"] = "low"

    elif re.search(
        r"\b(?:high|rich)\s+(?:biodiversity|species\s+richness)\b"
        r"|\b(?:biodiversity|species\s+richness)\s+is\s+"
        r"(?:high|rich)\b",
        text,
    ):
        biodiversity_kwargs["status"] = "high"

    elif re.search(
        r"\b(?:moderate|medium)\s+(?:biodiversity|species\s+richness)\b"
        r"|\b(?:biodiversity|species\s+richness)\s+is\s+"
        r"(?:moderate|medium)\b",
        text,
    ):
        biodiversity_kwargs["status"] = "moderate"

    # 5. Human impact / Pollution
    if (
        "pesticide" in text
        or "heavy fertilizer" in text
        or "chemical runoff" in text
        or "water pollution" in text
        or "soil pollution" in text
        or "pollution" in text
    ):
        if "pesticide" in text:
            human_impact_kwargs["pollution"] = "pesticide use"
        elif "fertilizer" in text:
            human_impact_kwargs["pollution"] = "chemical fertilizer"
        else:
            human_impact_kwargs["pollution"] = "moderate pollution"

    # 6. Location / Region
    if "semi-arid" in text:
        location_kwargs["region"] = "semi-arid"
    elif "arid" in text:
        location_kwargs["region"] = "arid"
    elif "tropical" in text:
        location_kwargs["region"] = "tropical"
    elif "temperate" in text:
        location_kwargs["region"] = "temperate"

    return EnvironmentInput(
        soil=Soil(**soil_kwargs) if soil_kwargs else None,
        climate=Climate(**climate_kwargs) if climate_kwargs else None,
        land=Land(**land_kwargs) if land_kwargs else None,
        biodiversity=(
            Biodiversity(**biodiversity_kwargs)
            if biodiversity_kwargs
            else None
        ),
        human_impact=(
            HumanImpact(**human_impact_kwargs)
            if human_impact_kwargs
            else None
        ),
        location=Location(**location_kwargs) if location_kwargs else None,
    )


def count_connected_variables(
    env: EnvironmentInput,
) -> Tuple[int, List[str]]:
    """Count variables aligned with Darukaa's multi-variable reasoning engine."""
    vars_detected: List[str] = []

    if env.soil and env.soil.organic_carbon is not None:
        vars_detected.append("soil_organic_carbon")

    if env.climate and (
        env.climate.rainfall_category is not None
        or env.climate.rainfall_mm_year is not None
    ):
        vars_detected.append("rainfall")

    if env.land and (
        env.land.land_use is not None
        or env.land.land_cover is not None
    ):
        vars_detected.append("land_use")

    if env.biodiversity and (
        env.biodiversity.species_richness is not None
        or env.biodiversity.habitat_diversity is not None
        or env.biodiversity.status is not None
    ):
        vars_detected.append("biodiversity")

    if env.human_impact and env.human_impact.pollution is not None:
        vars_detected.append("pollution")

    return len(vars_detected), vars_detected


def evaluate_clarification_need(
    env: EnvironmentInput,
) -> Tuple[bool, Optional[str]]:
    """Evaluate whether accumulated environmental context satisfies >=3 variables.

    Returns:
        (needs_clarification, clarification_message)
    """
    count, present_vars = count_connected_variables(env)

    if count >= 3:
        return False, None

    # Construct targeted clarification asking for missing variables.
    missing_prompts = []

    if "soil_organic_carbon" not in present_vars:
        missing_prompts.append(
            "soil details (such as soil organic carbon or soil quality)"
        )

    if "rainfall" not in present_vars:
        missing_prompts.append(
            "rainfall conditions (e.g. low, medium, or high rainfall)"
        )

    if "land_use" not in present_vars:
        missing_prompts.append(
            "land use or current crop pattern "
            "(e.g. monoculture, agroforestry, crop type)"
        )

    if "biodiversity" not in present_vars and len(missing_prompts) < 2:
        missing_prompts.append(
            "observed biodiversity or species richness"
        )

    needed = (
        missing_prompts[: 3 - count]
        if missing_prompts
        else ["more environmental details"]
    )

    if len(needed) == 1:
        needed_str = needed[0]
    else:
        needed_str = (
            " and ".join([", ".join(needed[:-1]), needed[-1]])
            if len(needed) > 2
            else f"{needed[0]} and {needed[1]}"
        )

    msg = (
        "To provide an evidence-grounded recommendation, we need at least "
        "3 environmental variables. "
        f"Could you please share your {needed_str}?"
    )

    return True, msg