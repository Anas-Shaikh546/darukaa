"""
Environmental input schema for Darukaa.

Design rule (Day 1): every field is optional unless the caller actually
provides it. We never invent defaults for missing environmental data —
the retrieval layer must be able to tell the difference between
"value is 0" and "value was not given".
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RainfallCategory(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Soil(BaseModel):
    pH: Optional[float] = None
    organic_carbon: Optional[float] = Field(
        default=None, description="Soil organic carbon, percent"
    )
    moisture: Optional[float] = None


class Climate(BaseModel):
    temperature: Optional[float] = None
    rainfall_category: Optional[RainfallCategory] = None
    rainfall_mm_year: Optional[float] = None


class Land(BaseModel):
    land_use: Optional[str] = None
    land_cover: Optional[str] = None


class Biodiversity(BaseModel):
    species_richness: Optional[float] = None
    habitat_diversity: Optional[float] = None
    status: Optional[str] = None


class HumanImpact(BaseModel):
    pollution: Optional[str] = None
    deforestation: Optional[str] = None


class Location(BaseModel):
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EnvironmentInput(BaseModel):
    """Top-level environmental state submitted to the retrieval endpoint."""

    soil: Optional[Soil] = None
    climate: Optional[Climate] = None
    land: Optional[Land] = None
    biodiversity: Optional[Biodiversity] = None
    human_impact: Optional[HumanImpact] = None
    location: Optional[Location] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "soil": {"organic_carbon": 0.3},
                "climate": {"rainfall_category": "low"},
                "land": {"land_use": "wheat monoculture"},
                "location": {"region": "semi-arid"},
            }
        }
    )