import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.schemas.environment import EnvironmentInput
from app.schemas.recommendation import (
    EvidenceItem,
    ImpactMetric,
    MonitoringMetric,
    Reasoning,
    RecommendationOutput,
)
from app.services.retrieval.retriever import retrieve

# Mapping of input variables to graph node identifiers
_VARIABLE_TO_NODE = {
    "soil_organic_carbon": "SOC",
    "rainfall_category": "Rainfall",
    "land_use": "Land-use intensity",
    "biodiversity": "Biodiversity",
}

_INTERVENTIONS = ["agroforestry", "intercropping", "cover cropping"]

# Retrieval / evidence pool configuration
RETRIEVAL_TOP_K = 10
EVIDENCE_K = 5
RETRY_RETRIEVAL_TOP_K = 20
RETRY_EVIDENCE_K = 8


def _detect_variables(env: EnvironmentInput) -> List[str]:
    """Detect presence of environmental input parameters."""
    vars_detected: List[str] = []
    if env.soil and env.soil.organic_carbon is not None:
        vars_detected.append(_VARIABLE_TO_NODE["soil_organic_carbon"])
    if env.climate and env.climate.rainfall_category is not None:
        vars_detected.append(_VARIABLE_TO_NODE["rainfall_category"])
    if env.land and env.land.land_use is not None:
        vars_detected.append(_VARIABLE_TO_NODE["land_use"])
    if env.biodiversity is not None:
        vars_detected.append(_VARIABLE_TO_NODE["biodiversity"])
    return vars_detected


def _load_graph() -> dict:
    """Load the deterministic ecological relationship graph from disk."""
    path = Path(__file__).parents[1] / "relationship_graph.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _traverse_graph(graph: dict, variables: List[str]) -> List[List[str]]:
    """Traverse graph and gather paths matching detected variables."""
    collected: List[List[str]] = []
    for category_paths in graph.values():
        for path in category_paths:
            if any(node in variables for node in path):
                collected.append(path)
    return collected


def _select_intervention(env: EnvironmentInput) -> str:
    """Select appropriate ecological intervention based on conditions."""
    low_soc = (
        env.soil
        and env.soil.organic_carbon is not None
        and env.soil.organic_carbon < 1.0
    )
    low_rain = (
        env.climate
        and env.climate.rainfall_category is not None
        and str(env.climate.rainfall_category).lower() == "low"
    )
    monoculture = (
        env.land
        and env.land.land_use is not None
        and "monoculture" in env.land.land_use.lower()
    )

    if low_soc:
        return "agroforestry"
    if monoculture or low_rain:
        return "intercropping"
    return _INTERVENTIONS[0]


# ---------------------------------------------------------------------------
# Part 3 — Validation utilities
# ---------------------------------------------------------------------------


def _validate_variable_count(variables: List[str]) -> Tuple[bool, str]:
    """Pass only if at least three meaningful variables are detected."""
    if len(variables) >= 3:
        return True, "Variable count OK"
    return False, f"Only {len(variables)} variable(s) detected; need >=3"


def _validate_evidence_presence(
    evidence: List[EvidenceItem],
) -> Tuple[bool, str]:
    """Ensure evidence list exists and items contain required fields."""
    if not evidence:
        return False, "No evidence retrieved"
    for ev in evidence:
        if not ev.source or not ev.title or not ev.chunk_id or not ev.text:
            return False, "Evidence item missing required fields or chunk text"
    return True, "Evidence present"


def _strip_numerical_claims(text: str) -> str:
    """Replace numerical terms with generic value placeholders."""
    return re.sub(r"\b\d+(?:\.\d+)?%?\b", "[value]", text)


def _validate_numerical_claims(
    text: str, evidence: List[EvidenceItem]
) -> Tuple[str, bool, str]:
    """Require numeric tokens in recommendations to be present in evidence text."""
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    if not numbers:
        return text, True, "No numeric claims"

    evidence_text = " ".join(ev.text or "" for ev in evidence)
    for num in numbers:
        escaped = re.escape(num)
        if not re.search(rf"\b{escaped}\b", evidence_text):
            stripped = _strip_numerical_claims(text)
            return (
                stripped,
                False,
                f"Numeric claim '{num}' unsupported by evidence text - stripped",
            )
    return text, True, "Numeric claim(s) supported by evidence"


def _run_verifier(claim: str, evidence_chunks: List[dict]) -> bool:
    """Verify that a claim is groundable in the retrieved evidence chunks."""
    if not claim or not evidence_chunks:
        return False

    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "in",
        "on",
        "at",
        "of",
        "for",
        "with",
        "by",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "can",
        "could",
        "should",
        "would",
        "may",
        "might",
        "must",
        "will",
        "shall",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "from",
        "into",
        "via",
        "using",
        "consider",
        "implementing",
        "improve",
        "improving",
        "ecosystem",
        "outcomes",
        "detected",
        "variables",
        "linked",
        "curated",
        "relationships",
        "selected",
        "intervention",
        "claim",
        "evidence",
        "support",
        "supports",
        "supporting",
        "conditions",
        "under",
    }

    claim_words = {
        word
        for word in re.findall(r"\b[a-zA-Z]{3,}\b", claim.lower())
        if word not in stop_words
    }

    if not claim_words:
        return True

    for chunk in evidence_chunks:
        chunk_text = (
            (chunk.get("text") or "")
            + " "
            + (chunk.get("title") or "")
            + " "
            + (chunk.get("used_for") or "")
        ).lower()
        overlap = {w for w in claim_words if w in chunk_text}
        if overlap and (
            len(overlap) / len(claim_words) >= 0.3 or len(overlap) >= 2
        ):
            return True

    return False


def _calculate_confidence(evidence: List[EvidenceItem]) -> float:
    """Calculate mean retrieval similarity across selected evidence."""
    scores = [
        float(ev.similarity) for ev in evidence if ev.similarity is not None
    ]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return max(0.0, min(1.0, avg))


def _generate_monitoring_plan(
    variables: List[str], relationships: List[List[str]]
) -> List[MonitoringMetric]:
    """Map reasoning paths to short-, medium-, and long-term monitoring indicators."""
    plan: List[MonitoringMetric] = []
    flattened_graph_nodes = {node for path in relationships for node in path}

    if "SOC" in variables or "SOC" in flattened_graph_nodes:
        plan.append(
            MonitoringMetric(
                metric="soil_organic_carbon",
                why_monitor="Tracks the soil-health response to the intervention.",
                horizon="medium",
            )
        )

    if (
        "Rainfall" in variables
        or "Water availability" in flattened_graph_nodes
        or "Water Retention" in flattened_graph_nodes
    ):
        plan.append(
            MonitoringMetric(
                metric="soil_moisture",
                why_monitor="Tracks water availability and retention.",
                horizon="short",
            )
        )

    if (
        "Land-use intensity" in variables
        or "Habitat fragmentation" in flattened_graph_nodes
        or "Habitat Quality" in flattened_graph_nodes
        or "Habitat connectivity" in flattened_graph_nodes
        or "Habitat loss" in flattened_graph_nodes
    ):
        plan.append(
            MonitoringMetric(
                metric="habitat_diversity",
                why_monitor="Tracks habitat structure and spatial connectivity.",
                horizon="medium",
            )
        )

    if (
        "Biodiversity" in variables
        or "Biodiversity" in flattened_graph_nodes
        or "Species richness" in flattened_graph_nodes
        or "Species movement" in flattened_graph_nodes
        or "Species survival" in flattened_graph_nodes
    ):
        plan.append(
            MonitoringMetric(
                metric="species_richness",
                why_monitor="Tracks the biodiversity response.",
                horizon="long",
            )
        )

    return plan


def _fallback_output(
    variable_count: int, reason_msg: str
) -> RecommendationOutput:
    """Return structured fallback when context/evidence criteria are unfulfilled."""
    reasoning = Reasoning(
        variables=[],
        relationships=[],
        explanation="Insufficient evidence to generate a confident recommendation.",
    )
    return RecommendationOutput(
        recommendation="Further analysis required; insufficient evidence to provide a confident recommendation.",
        reasoning=reasoning,
        impacted_metrics=[],
        time_horizon="medium",
        confidence=0.0,
        evidence=[],
        validation={
            "variable_count": variable_count,
            "evidence_grounded": False,
            "reason": reason_msg,
        },
        monitoring=[],
    )


# ---------------------------------------------------------------------------
# Evidence Selection & Processing
# ---------------------------------------------------------------------------


def _select_evidence(
    results: List[dict],
    intervention: str,
    variables: List[str],
    evidence_k: int,
) -> List[dict]:
    """Select evidence supporting the intervention and detected variables."""
    if not results:
        return []

    intervention_terms = {
        "agroforestry": {
            "agroforestry",
            "agroforestry practices",
            "tree",
            "trees",
            "biodiversity",
            "soil",
            "organic carbon",
        },
        "intercropping": {
            "intercropping",
            "intercrop",
            "crop diversification",
            "diversification",
            "biodiversity",
            "soil",
            "water",
        },
        "cover cropping": {
            "cover crop",
            "cover cropping",
            "vegetation",
            "soil",
            "organic carbon",
            "biodiversity",
        },
    }

    variable_terms = {
        "SOC": {
            "soil",
            "soil organic carbon",
            "organic carbon",
            "carbon",
            "soil health",
        },
        "Rainfall": {
            "rainfall",
            "rain",
            "water",
            "water availability",
            "water retention",
        },
        "Land-use intensity": {
            "land use",
            "land-use",
            "monoculture",
            "crop",
            "cropping",
            "habitat",
            "fragmentation",
            "biodiversity",
        },
        "Biodiversity": {
            "biodiversity",
            "species",
            "species richness",
            "habitat",
        },
    }

    target_terms = intervention_terms.get(intervention, {intervention})
    for variable in variables:
        target_terms = target_terms.union(variable_terms.get(variable, set()))

    scored_results = []

    for index, hit in enumerate(results):
        text = (
            f"{hit.get('title', '')} "
            f"{hit.get('source', '')} "
            f"{hit.get('text', '')}"
        ).lower()

        score = 0
        matched_terms = set()

        for term in target_terms:
            if term.lower() in text:
                score += 1
                matched_terms.add(term.lower())

        if intervention.lower() in text:
            score += 5

        similarity = hit.get("similarity")
        if similarity is not None:
            try:
                score += float(similarity)
            except (TypeError, ValueError):
                pass

        scored_results.append(
            (
                score,
                len(matched_terms),
                index,
                hit,
            )
        )

    scored_results.sort(
        key=lambda item: (item[0], item[1], -item[2]),
        reverse=True,
    )

    selected = []
    selected_ids = set()

    for _, _, _, hit in scored_results:
        chunk_id = hit.get("chunk_id")
        if chunk_id and chunk_id in selected_ids:
            continue

        selected.append(hit)
        if chunk_id:
            selected_ids.add(chunk_id)

        if len(selected) >= evidence_k:
            break

    return selected


# ---------------------------------------------------------------------------
# Recommendation Text
# ---------------------------------------------------------------------------


def _build_recommendation(
    env: EnvironmentInput,
    intervention: str,
    variables: List[str],
    impacted_metrics: List[ImpactMetric],
) -> str:
    """Build specific recommendation text without introducing unsupported numbers."""
    metric_phrases = {
        "soil_organic_carbon": "soil organic carbon",
        "soil_moisture": "water availability and soil moisture",
        "habitat_diversity": "habitat structure",
        "species_richness": "species richness",
    }

    metrics = [
        metric_phrases[metric.metric]
        for metric in impacted_metrics
        if metric.metric in metric_phrases
    ]

    if len(metrics) >= 2:
        if len(metrics) == 2:
            metric_text = f"{metrics[0]} and {metrics[1]}"
        else:
            metric_text = ", ".join(metrics[:-1]) + f", and {metrics[-1]}"
    elif metrics:
        metric_text = metrics[0]
    else:
        metric_text = "soil and biodiversity conditions"

    context_parts: List[str] = []

    if "SOC" in variables:
        context_parts.append("low soil-carbon conditions")

    if "Rainfall" in variables:
        rainfall = (
            str(env.climate.rainfall_category).lower()
            if env.climate and env.climate.rainfall_category is not None
            else ""
        )
        if rainfall == "low":
            context_parts.append("low rainfall")

    if "Land-use intensity" in variables and env.land and env.land.land_use:
        land_use = env.land.land_use.lower()
        if "monoculture" in land_use:
            context_parts.append("monoculture land use")
        else:
            context_parts.append("the current land-use pattern")

    if context_parts:
        if len(context_parts) == 1:
            context_text = context_parts[0]
        elif len(context_parts) == 2:
            context_text = f"{context_parts[0]} and {context_parts[1]}"
        else:
            context_text = (
                ", ".join(context_parts[:-1]) + f", and {context_parts[-1]}"
            )

        return (
            f"Consider {intervention} under {context_text} to support "
            f"{metric_text}."
        )

    return (
        f"Consider {intervention} to support {metric_text} "
        f"through the identified ecological relationships."
    )


# ---------------------------------------------------------------------------
# Core Generation & Pipeline Orchestration
# ---------------------------------------------------------------------------


def _generate_recommendation(
    env: EnvironmentInput, retrieval_top_k: int, evidence_k: int
) -> RecommendationOutput:
    """Generate recommendation output, reasoning, metrics, and evidence payload."""
    variables = _detect_variables(env)
    retrieval_result = retrieve(env, top_k=retrieval_top_k)
    results = retrieval_result.get("results", [])
    graph = _load_graph()
    relationships = _traverse_graph(graph, variables)
    intervention = _select_intervention(env)
    impacted_metrics: List[ImpactMetric] = []
    flattened_graph_nodes = {node for path in relationships for node in path}

    if "SOC" in variables or "SOC" in flattened_graph_nodes:
        impacted_metrics.append(
            ImpactMetric(
                metric="soil_organic_carbon",
                estimate="potentially improved",
                basis="intervention increases organic matter and root biomass",
            )
        )

    if (
        "Rainfall" in variables
        or "Water availability" in flattened_graph_nodes
        or "Water Retention" in flattened_graph_nodes
    ):
        impacted_metrics.append(
            ImpactMetric(
                metric="soil_moisture",
                estimate="potentially improved",
                basis="intervention improves soil structure and water retention capacity",
            )
        )

    if (
        "Land-use intensity" in variables
        or "Habitat fragmentation" in flattened_graph_nodes
        or "Habitat Quality" in flattened_graph_nodes
        or "Habitat connectivity" in flattened_graph_nodes
        or "Habitat loss" in flattened_graph_nodes
    ):
        impacted_metrics.append(
            ImpactMetric(
                metric="habitat_diversity",
                estimate="potentially improved",
                basis="intervention restores vegetative strata and reduces fragmentation",
            )
        )

    if (
        "Biodiversity" in variables
        or "Biodiversity" in flattened_graph_nodes
        or "Species richness" in flattened_graph_nodes
        or "Species movement" in flattened_graph_nodes
        or "Species survival" in flattened_graph_nodes
    ):
        impacted_metrics.append(
            ImpactMetric(
                metric="species_richness",
                estimate="potentially improved",
                basis="intervention provides diverse niches and supports organism survival",
            )
        )

    selected_results = _select_evidence(
        results=results,
        intervention=intervention,
        variables=variables,
        evidence_k=evidence_k,
    )

    evidence_items: List[EvidenceItem] = [
        EvidenceItem(
            source=hit.get("source", ""),
            title=hit.get("title", ""),
            chunk_id=hit.get("chunk_id", ""),
            used_for="retrieved evidence supporting reasoning",
            text=hit.get("text", ""),
            similarity=hit.get("similarity"),
        )
        for hit in selected_results
    ]

    reasoning = Reasoning(
        variables=variables,
        relationships=relationships,
        explanation=(
            f"Detected variables {variables} linked via curated relationships; "
            f"selected intervention '{intervention}'."
        ),
    )

    monitoring_plan = _generate_monitoring_plan(variables, relationships)

    recommendation = _build_recommendation(
        env=env,
        intervention=intervention,
        variables=variables,
        impacted_metrics=impacted_metrics,
    )

    return RecommendationOutput(
        recommendation=recommendation,
        reasoning=reasoning,
        impacted_metrics=impacted_metrics,
        time_horizon="medium",
        confidence=0.0,
        evidence=evidence_items,
        validation=None,
        monitoring=monitoring_plan,
    )


def _validate(output: RecommendationOutput) -> Tuple[bool, Dict[str, Any]]:
    """Perform deterministic validation across variables, evidence grounding, and claims."""
    vars_ok, vars_msg = _validate_variable_count(output.reasoning.variables)
    ev_present_ok, ev_msg = _validate_evidence_presence(output.evidence)
    rec_text, num_ok, num_msg = _validate_numerical_claims(
        output.recommendation, output.evidence
    )
    output.recommendation = rec_text

    if ev_present_ok:
        recommendation_verified = _run_verifier(
            output.recommendation,
            [ev.dict() for ev in output.evidence],
        )
    else:
        recommendation_verified = False

    evidence_grounded = ev_present_ok and recommendation_verified
    all_pass = vars_ok and evidence_grounded and num_ok

    ver_msg = (
        "Deterministic evidence verification: supported"
        if recommendation_verified
        else "Deterministic evidence verification: unsupported"
    )

    detail = {
        "variable_count": len(output.reasoning.variables),
        "evidence_grounded": evidence_grounded,
        "numeric_claims_ok": num_ok,
        "evidence_verification_ok": recommendation_verified,
        "messages": [vars_msg, ev_msg, num_msg, ver_msg],
    }

    return all_pass, detail


def reason(env: EnvironmentInput) -> RecommendationOutput:
    """Public entry point: generate, validate, retry at most once, and fallback on failure."""
    output = _generate_recommendation(env, RETRIEVAL_TOP_K, EVIDENCE_K)
    variables = output.reasoning.variables
    if len(variables) < 3:
        return _fallback_output(
            len(variables), f"Only {len(variables)} variable(s) detected; need >=3"
        )

    all_pass, detail = _validate(output)

    if not all_pass:
        output = _generate_recommendation(
            env, RETRY_RETRIEVAL_TOP_K, RETRY_EVIDENCE_K
        )
        all_pass, detail = _validate(output)
        detail["retry_used"] = True
    else:
        detail["retry_used"] = False

    if not all_pass:
        return _fallback_output(
            detail["variable_count"], "; ".join(detail["messages"])
        )

    output.confidence = _calculate_confidence(output.evidence)
    output.validation = detail
    return output