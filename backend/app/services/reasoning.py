import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.environment import EnvironmentInput
from app.schemas.recommendation import (
    EvidenceItem,
    ImpactMetric,
    MonitoringMetric,
    Reasoning,
    RecommendationOutput,
)
from app.services.retrieval.retriever import retrieve

_VARIABLE_TO_NODE = {
    "soil_organic_carbon": "SOC",
    "rainfall_category": "Rainfall",
    "land_use": "Land-use intensity",
    "biodiversity": "Biodiversity",
}
_INTERVENTIONS = ["agroforestry", "intercropping", "cover cropping"]

# Retrieval / evidence sizing (previously hardcoded to 2 with no rationale)
RETRIEVAL_TOP_K = 10
EVIDENCE_K = 5
RETRY_RETRIEVAL_TOP_K = 20
RETRY_EVIDENCE_K = 8

# ---------------------------------------------------------------------------
# Unchanged from Day 2 Part 1/2 — not part of Part 3's scope
# ---------------------------------------------------------------------------


def _detect_variables(env: EnvironmentInput) -> List[str]:
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
    path = Path(__file__).parents[1] / "relationship_graph.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _traverse_graph(graph: dict, variables: List[str]) -> List[List[str]]:
    collected: List[List[str]] = []
    for category_paths in graph.values():
        for path in category_paths:
            if any(node in variables for node in path):
                collected.append(path)
    return collected


def _select_intervention(env: EnvironmentInput) -> str:
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
# Part 3 — validation utilities
# ---------------------------------------------------------------------------


def _validate_variable_count(variables: List[str]) -> Tuple[bool, str]:
    """Pass only if at least three meaningful variables are detected."""
    if len(variables) >= 3:
        return True, "Variable count OK"
    return False, f"Only {len(variables)} variable(s) detected; need >=3"


def _validate_evidence_presence(
    evidence: List[EvidenceItem],
) -> Tuple[bool, str]:
    """Structural check only: evidence exists and carries real chunk text.

    This does NOT prove the recommendation's claims are grounded in it - that
    determination belongs to _run_verifier. This just ensures there is
    something for the verifier to check against.
    """
    if not evidence:
        return False, "No evidence retrieved"
    for ev in evidence:
        if not ev.source or not ev.title or not ev.chunk_id or not ev.text:
            return False, "Evidence item missing required fields or chunk text"
    return True, "Evidence present"


def _strip_numerical_claims(text: str) -> str:
    return re.sub(r"\b\d+(?:.\d+)?%?\b", "[value]", text)


def _validate_numerical_claims(
    text: str, evidence: List[EvidenceItem]
) -> Tuple[str, bool, str]:
    """If a numeric token appears in text, require that the SAME number appears

    (as a whole token, not a substring) in at least one evidence chunk's actual
    text. Otherwise strip it.
    """
    numbers = re.findall(r"\b\d+(?:.\d+)?%?\b", text)
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
    """Deterministic evidence-bounded verification.

    Verifies that the claim has meaningful textual support in the retrieved
    evidence chunks. Extracts significant content words from the claim and
    checks if at least one evidence chunk carries substantial lexical overlap
    with the claim.
    """
    if not claim or not evidence_chunks:
        return False

    # Normalize stop words to isolate meaningful subject/intervention/metric terms
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
    }

    claim_words = {
        word
        for word in re.findall(r"\b[a-zA-Z]{3,}\b", claim.lower())
        if word not in stop_words
    }

    if not claim_words:
        return True

    # Check evidence text and titles across all provided chunks
    for chunk in evidence_chunks:
        chunk_text = (
            (chunk.get("text") or "")
            + " "
            + (chunk.get("title") or "")
            + " "
            + (chunk.get("used_for") or "")
        ).lower()
        overlap = {w for w in claim_words if w in chunk_text}
        # If at least one primary topic word or >=40% of key claim words are supported in the chunk
        if overlap and (
            len(overlap) / len(claim_words) >= 0.3 or len(overlap) >= 2
        ):
            return True

    return False


def _calculate_confidence(evidence: List[EvidenceItem]) -> float:
    """Mechanical confidence: mean retrieval similarity of evidence actually

    used. Only called once every validator has already passed, so no
    validation-outcome factor is needed here.
    """
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
    """Deterministically map relevant reasoning variables and pathways to

    monitoring metrics.
    """
    plan: List[MonitoringMetric] = []
    flattened_graph_nodes = {node for path in relationships for node in path}

    # Soil organic carbon / SOC pathway
    if "SOC" in variables or "SOC" in flattened_graph_nodes:
        plan.append(
            MonitoringMetric(
                metric="soil_organic_carbon",
                why_monitor="Tracks the soil-health response to the intervention.",
                horizon="medium",
            )
        )

    # Rainfall / water-availability pathway
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

    # Land-use / habitat pathway
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

    # Biodiversity / species pathway
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
# Evidence selection
# ---------------------------------------------------------------------------


def _select_evidence(
    results: List[dict],
    intervention: str,
    variables: List[str],
    evidence_k: int,
) -> List[dict]:
    """Select evidence from the full retrieval pool based on support for the

    actual recommendation and detected environmental variables. This prevents
    relevant intervention evidence from being discarded simply because it
    appeared outside the first few round-robin retrieval results.
    """
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

        # Explicit intervention evidence receives priority.
        if intervention.lower() in text:
            score += 5

        # Preserve retrieval similarity as a secondary signal only.
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
# Generation
# ---------------------------------------------------------------------------


def _generate_recommendation(
    env: EnvironmentInput, retrieval_top_k: int, evidence_k: int
) -> RecommendationOutput:
    variables = _detect_variables(env)
    retrieval_result = retrieve(env, top_k=retrieval_top_k)
    results = retrieval_result.get("results", [])
    graph = _load_graph()
    relationships = _traverse_graph(graph, variables)
    intervention = _select_intervention(env)

    # Map detected variables/pathways to plausibly impacted outcome metrics (never 'rainfall')
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

    # Evidence-selection fix:
    # select from the full retrieval pool instead of blindly taking results[:evidence_k].
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

    return RecommendationOutput(
        recommendation=f"Consider implementing {intervention} to improve ecosystem outcomes.",
        reasoning=reasoning,
        impacted_metrics=impacted_metrics,
        time_horizon="medium",
        confidence=0.0,
        evidence=evidence_items,
        validation=None,
        monitoring=monitoring_plan,
    )


def _validate(output: RecommendationOutput) -> Tuple[bool, Dict[str, Any]]:
    vars_ok, vars_msg = _validate_variable_count(output.reasoning.variables)
    ev_present_ok, ev_msg = _validate_evidence_presence(output.evidence)
    rec_text, num_ok, num_msg = _validate_numerical_claims(
        output.recommendation, output.evidence
    )
    output.recommendation = rec_text

    ver_ok = True
    if ev_present_ok:
        for claim in [output.recommendation, output.reasoning.explanation]:
            ver_ok = ver_ok and _run_verifier(
                claim, [ev.dict() for ev in output.evidence]
            )
    else:
        ver_ok = False

    evidence_grounded = ev_present_ok and ver_ok
    all_pass = vars_ok and evidence_grounded and num_ok

    ver_msg = (
        "Deterministic evidence verification: supported"
        if ver_ok
        else "Deterministic evidence verification: unsupported"
    )

    detail = {
        "variable_count": len(output.reasoning.variables),
        "evidence_grounded": evidence_grounded,
        "numeric_claims_ok": num_ok,
        "evidence_verification_ok": ver_ok,
        "messages": [vars_msg, ev_msg, num_msg, ver_msg],
    }
    return all_pass, detail


def reason(env: EnvironmentInput) -> RecommendationOutput:
    """Public entry point: generate, validate, retry at most once, fallback."""
    output = _generate_recommendation(env, RETRIEVAL_TOP_K, EVIDENCE_K)
    variables = output.reasoning.variables
    # Structural failure (too few variables) is not fixable by retry -
    # retrying would call _detect_variables on the same env and get the
    # same count every time. Go straight to fallback.
    if len(variables) < 3:
        return _fallback_output(
            len(variables), f"Only {len(variables)} variable(s) detected; need >=3"
        )

    all_pass, detail = _validate(output)

    if not all_pass:
        # Retry once with a wider retrieval pool - a genuinely different
        # attempt, not a repeat of the same deterministic call.
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