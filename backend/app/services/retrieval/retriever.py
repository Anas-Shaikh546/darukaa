"""
Retrieval layer for Darukaa.

Converts an EnvironmentInput into a set of retrieval queries, queries
ChromaDB, and returns ranked real evidence chunks with provenance.

Also supports direct knowledge-question retrieval for questions that do not
contain structured environmental variables.

Important: `similarity` here is a retrieval/vector-space similarity score,
NOT a scientific confidence score. The two concepts are deliberately kept
separate - scientific confidence belongs to a later reasoning layer.

Design note (found via manual per-facet testing): concatenating every
environmental facet into one combined query string and running a single
nearest-neighbor search lets whichever facet happens to embed closest to the
largest/densest cluster of chunks in the corpus dominate the results.

Fix: query each facet separately, then merge round-robin so no single facet
can crowd out the others.
"""

from __future__ import annotations

from app.schemas.environment import EnvironmentInput
from app.services.retrieval.ingest import get_collection

DEFAULT_TOP_K = 10


def build_facet_queries(env: EnvironmentInput) -> list[str]:
    """Build separate retrieval queries for each provided environmental facet.

    Missing fields contribute nothing. We never fabricate values to fill
    a query.
    """
    facets: list[str] = []

    if env.soil:
        if env.soil.organic_carbon is not None:
            level = "low" if env.soil.organic_carbon < 1.0 else "adequate"
            facets.append(f"soil organic carbon {level} soil health")

        if env.soil.pH is not None:
            facets.append(f"soil pH {env.soil.pH}")

        if env.soil.moisture is not None:
            facets.append(f"soil moisture {env.soil.moisture}")

    if env.climate:
        if env.climate.rainfall_category is not None:
            facets.append(
                f"{env.climate.rainfall_category.value} "
                f"rainfall water availability"
            )

        if env.climate.temperature is not None:
            facets.append(f"temperature {env.climate.temperature}")

    if env.land:
        if env.land.land_use:
            facets.append(
                f"{env.land.land_use} biodiversity land use effects"
            )

        if env.land.land_cover:
            facets.append(f"{env.land.land_cover} land cover")

    if env.biodiversity:
        if env.biodiversity.species_richness is not None:
            facets.append("species richness biodiversity")

        if env.biodiversity.habitat_diversity is not None:
            facets.append("habitat diversity")

        if env.biodiversity.status:
            facets.append(
                f"{env.biodiversity.status} biodiversity species"
            )

    if env.human_impact:
        if env.human_impact.pollution:
            facets.append(
                f"pollution {env.human_impact.pollution} biological effects"
            )

        if env.human_impact.deforestation:
            facets.append(
                f"deforestation {env.human_impact.deforestation} habitat effects"
            )

    if env.location and env.location.region:
        facets.append(f"{env.location.region} biodiversity habitat")

    return facets


def build_query_text(env: EnvironmentInput) -> str:
    """Build the combined query text for existing callers.

    Kept for compatibility with diagnostic.py and other existing code.
    Retrieval itself uses the individual facet queries.
    """
    return " | ".join(build_facet_queries(env))


def _format_hit(
    chunk_id: str,
    text: str,
    meta: dict,
    distance: float,
    matched_facet: str,
) -> dict:
    """Convert a Chroma result into Darukaa's evidence format."""
    similarity = 1 - distance

    return {
        "chunk_id": chunk_id,
        "matched_facet": matched_facet,
        "distance": round(distance, 4),
        "similarity": round(similarity, 4),
        "text": text,
        "source": meta.get("source"),
        "title": meta.get("title"),
        "source_url": meta.get("source_url"),
        "source_file": meta.get("source_file"),
        "page": meta.get("page"),
        "year": meta.get("year"),
        "document_type": meta.get("document_type"),
        "topic": meta.get("topic"),
        "variables": (
            meta.get("variables").split(",")
            if meta.get("variables")
            else []
        ),
        "location_scope": meta.get("location_scope"),
    }


def _query_facet(
    collection,
    facet: str,
    n_results: int,
) -> list[dict]:
    """Run one facet query against ChromaDB and return its hits."""
    raw = collection.query(
        query_texts=[facet],
        n_results=n_results,
    )

    ids = raw.get("ids", [[]])[0]
    docs = raw.get("documents", [[]])[0]
    metas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]

    hits = []

    for chunk_id, text, meta, distance in zip(
        ids,
        docs,
        metas,
        distances,
    ):
        hits.append(
            _format_hit(
                chunk_id=chunk_id,
                text=text,
                meta=meta,
                distance=distance,
                matched_facet=facet,
            )
        )

    return hits


def retrieve_knowledge(
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """Retrieve evidence directly for a natural-language knowledge question.

    Unlike environmental retrieval, this function does not construct or
    invent environmental variables. The user's question is sent directly
    to the existing Chroma collection.
    """
    query = query.strip()

    if not query:
        return {
            "query": "",
            "facets": [],
            "results": [],
        }

    collection = get_collection()

    if collection.count() == 0:
        return {
            "query": query,
            "facets": [query],
            "results": [],
        }

    hits = _query_facet(
        collection,
        query,
        min(top_k, collection.count()),
    )

    for rank, item in enumerate(hits, start=1):
        item["rank"] = rank

    return {
        "query": query,
        "facets": [query],
        "results": hits,
    }


def retrieve(
    env: EnvironmentInput,
    top_k: int = DEFAULT_TOP_K,
) -> dict:
    """Retrieve evidence independently for each facet and merge round-robin.

    Each environmental condition gets an opportunity to contribute results.
    Similarity scores from different facet queries are not globally compared
    because they come from different query texts and are not guaranteed to be
    directly comparable.
    """
    facets = build_facet_queries(env)

    if not facets:
        return {
            "query": "",
            "facets": [],
            "results": [],
        }

    collection = get_collection()
    combined_query = " | ".join(facets)

    if collection.count() == 0:
        return {
            "query": combined_query,
            "facets": facets,
            "results": [],
        }

    # Pull extra candidates from each facet so that duplicate chunks do not
    # prevent the final result set from reaching top_k.
    per_facet_n = min(
        max(1, -(-top_k // len(facets))) + 2,
        collection.count(),
    )

    per_facet_hits = [
        _query_facet(
            collection,
            facet,
            per_facet_n,
        )
        for facet in facets
    ]

    # Round-robin merge:
    #
    # Facet 1 → result 1
    # Facet 2 → result 1
    # Facet 3 → result 1
    # Facet 4 → result 1
    # Facet 1 → result 2
    # ...
    #
    # This prevents one facet from dominating the final results simply
    # because its similarity scores happen to be higher.
    seen_ids: set[str] = set()
    merged: list[dict] = []

    i = 0

    while (
        len(merged) < top_k
        and any(i < len(hits) for hits in per_facet_hits)
    ):
        for hits in per_facet_hits:
            if len(merged) >= top_k:
                break

            if (
                i < len(hits)
                and hits[i]["chunk_id"] not in seen_ids
            ):
                seen_ids.add(hits[i]["chunk_id"])
                merged.append(hits[i])

        i += 1

    # Add final ranks.
    for rank, item in enumerate(merged, start=1):
        item["rank"] = rank

    return {
        "query": combined_query,
        "facets": facets,
        "results": merged,
    }
