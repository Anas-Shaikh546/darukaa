from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ImpactMetric(BaseModel):
    """Metric impact estimation for a recommendation."""
    metric: str = Field(..., description='Name of the metric, e.g. species_richness')
    estimate: str = Field(..., description='Estimated change, e.g. +5%')
    basis: str = Field(..., description='Explanation of the basis for the estimate')


class EvidenceItem(BaseModel):
    """Reference to a retrieved chunk used as evidence."""
    source: str = Field(..., description='Source identifier')
    title: str = Field(..., description='Title of the source document')
    chunk_id: str = Field(..., description='Identifier of the specific chunk used')
    used_for: str = Field(..., description='Aspect of the recommendation the chunk supports')
    text: Optional[str] = Field(None, description='Actual retrieved chunk text, used for grounding/numeric validation')
    similarity: Optional[float] = Field(None, description='Retrieval similarity score (0-1), used for confidence calculation')


class MonitoringMetric(BaseModel):
    """Post-recommendation monitoring metric."""
    metric: str = Field(..., description='Name of the environmental metric to monitor')
    why_monitor: str = Field(..., description='Reason for monitoring this metric post-intervention')
    horizon: str = Field(..., description='Monitoring time horizon, e.g. short, medium, long')


class Reasoning(BaseModel):
    """Structure describing the reasoning chain for a recommendation."""
    variables: List[str] = Field(default_factory=list, description='Environmental variables considered')
    relationships: List[List[str]] = Field(default_factory=list, description='Relationship paths traversed')
    explanation: str = Field(..., description='Human readable explanation')


class RecommendationOutput(BaseModel):
    """Day 2 recommendation contract."""
    recommendation: str = Field(..., description='Actionable recommendation text')
    reasoning: Reasoning
    impacted_metrics: List[ImpactMetric] = Field(..., description='Metrics expected to be affected')
    time_horizon: str = Field(..., description='Time horizon, e.g. short, medium, long')
    confidence: float = Field(..., ge=0.0, le=1.0, description='Confidence score 0-1')
    evidence: List[EvidenceItem] = Field(..., description='Evidence supporting the recommendation')
    validation: Optional[dict] = Field(None, description='Optional validation block')
    monitoring: List[MonitoringMetric] = Field(default_factory=list, description='Post-intervention monitoring plan')
