"""Conversation orchestration service for Darukaa Day 3.

Coordinates multi-turn conversation flow:
1. Records user message turn into ConversationStore.
2. Extracts explicitly mentioned environmental variables.
3. Merges them into the cumulative conversation state.
4. Handles knowledge questions directly through the existing KB.
5. Checks whether >=3 connected environmental variables are available.
6. If incomplete, generates a targeted clarification request.
7. If sufficient, invokes the existing Day 2 reasoning pipeline reason(env).
8. Records the assistant's reply into conversation history.

Knowledge-question handling:
- A question with no environmental state is treated as a knowledge request.
- The question is sent directly to the existing Chroma knowledge layer.
- Only sufficiently relevant retrieved evidence is used.
- Answers prefer sentences that directly match the question's concepts.
- Quantitative questions require a relevant explicit numeric claim in retrieved
  evidence before a numeric answer is returned.
- Page numbers, figure numbers, and unrelated numbers are not treated as
  scientific numeric answers.
- If the KB does not contain sufficiently relevant evidence, the system
  explicitly says it does not have enough information instead of guessing.
"""

from __future__ import annotations

import re
from typing import Optional

from app.schemas.conversation import (
    ConversationRequest,
    ConversationResponse,
    ConversationStatus,
)
from app.services.conversation_store import (
    ConversationStore,
    store as default_store,
)
from app.services.extraction import (
    extract_environmental_info,
    evaluate_clarification_need,
)
from app.services.reasoning import reason
from app.services.retrieval.retriever import retrieve_knowledge


KNOWLEDGE_RELEVANCE_THRESHOLD = 0.50


def _is_knowledge_question(message: str) -> bool:
    """Detect a knowledge-style question with no explicit environmental state."""
    text = message.strip().lower()

    if not text:
        return False

    if "?" in text:
        return True

    question_starters = (
        "what ",
        "what are ",
        "what is ",
        "why ",
        "how ",
        "which ",
        "where ",
        "when ",
        "who ",
        "can you ",
        "could you ",
        "tell me ",
        "explain ",
        "does ",
        "do ",
        "is ",
        "are ",
    )

    return text.startswith(question_starters)


def _is_quantitative_question(message: str) -> bool:
    """Detect questions explicitly asking for an exact quantity or value."""
    text = message.strip().lower()

    quantitative_patterns = (
        r"\bhow much\b",
        r"\bhow many\b",
        r"\bwhat percentage\b",
        r"\bwhat percent\b",
        r"\bwhat proportion\b",
        r"\bwhat rate\b",
        r"\bwhat value\b",
        r"\bexact(?:ly)?\b",
        r"\bhow large\b",
        r"\bhow high\b",
        r"\bhow low\b",
        r"\bwhat is the (?:average|mean|median)\b",
        r"\bwhat was the (?:average|mean|median)\b",
    )

    return any(
        re.search(pattern, text)
        for pattern in quantitative_patterns
    )


def _knowledge_boundary_response() -> str:
    """Return a safe response when the KB lacks relevant evidence."""
    return (
        "I don't have enough information in the current knowledge base to "
        "answer this specific knowledge question confidently without making "
        "up information."
    )


def _quantitative_boundary_response() -> str:
    """Return a safe response when an exact numeric answer is unavailable."""
    return (
        "The knowledge base does not contain a sufficiently supported exact "
        "numeric value for this question, so I won't invent or estimate one."
    )


def _split_sentences(text: str) -> list[str]:
    """Split retrieved evidence into readable sentences."""
    cleaned = " ".join(text.split())

    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def _query_terms(query: str) -> set[str]:
    """Extract useful content terms from a knowledge question."""
    stop_words = {
        "what",
        "what's",
        "what",
        "are",
        "is",
        "the",
        "a",
        "an",
        "of",
        "to",
        "for",
        "and",
        "or",
        "in",
        "on",
        "how",
        "does",
        "do",
        "why",
        "which",
        "where",
        "when",
        "who",
        "can",
        "could",
        "you",
        "me",
        "tell",
        "about",
        "affect",
        "affects",
        "impact",
        "impacts",
        "exact",
        "exactly",
        "percentage",
        "percent",
        "proportion",
        "rate",
        "value",
        "average",
        "mean",
        "median",
        "much",
        "many",
    }

    words = re.findall(r"[a-z][a-z-]+", query.lower())

    return {
        word
        for word in words
        if word not in stop_words and len(word) > 2
    }


def _sentence_relevance(sentence: str, query_terms: set[str]) -> int:
    """Score how directly a sentence matches the question concepts."""
    sentence_words = set(
        re.findall(r"[a-z][a-z-]+", sentence.lower())
    )

    score = len(sentence_words.intersection(query_terms))

    # Treat common scientific word variants as related concepts.
    variant_groups = (
        {"vegetation", "vegetative"},
        {"productivity", "productive"},
        {"rainfall", "precipitation", "rain"},
        {"biodiversity", "biodiverse"},
        {"carbon", "organic"},
        {"soil", "soils"},
        {"plant", "plants"},
        {"growth", "growing"},
        {"habitat", "habitats"},
        {"species", "specie"},
        {"fragmentation", "fragmented"},
    )

    for group in variant_groups:
        if sentence_words.intersection(group) and query_terms.intersection(group):
            score += 2

    return score


def _has_relevant_numeric_claim(
    sentence: str,
    query: str,
    query_terms: set[str],
) -> bool:
    """Check whether a sentence contains a relevant explicit numeric claim."""
    lowered = sentence.lower()
    query_lower = query.lower()

    if not _sentence_relevance(sentence, query_terms):
        return False

    if not re.search(r"\b\d+(?:\.\d+)?\b", lowered):
        return False

    # Percentage questions require an explicit percentage expression.
    if re.search(
        r"\bwhat percentage\b|\bwhat percent\b|\bwhat proportion\b",
        query_lower,
    ):
        return bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*%"
                r"|\b\d+(?:\.\d+)?\s*percent(?:age)?\b",
                lowered,
            )
        )

    # Rate questions should contain an explicit rate-like expression.
    if re.search(r"\bwhat rate\b", query_lower):
        return bool(
            re.search(
                r"\b\d+(?:\.\d+)?\s*%"
                r"|\b\d+(?:\.\d+)?\s*(?:per|/)\b",
                lowered,
            )
        )

    # Generic numeric questions can use an explicit number when the sentence
    # is already strongly relevant to the requested concepts.
    return _sentence_relevance(sentence, query_terms) >= 2


def _build_knowledge_answer(
    query: str,
    results: list[dict],
) -> str:
    """Build an extractive answer using only retrieved KB evidence."""
    if not results:
        return _knowledge_boundary_response()

    relevant_results = [
        item
        for item in results
        if float(item.get("similarity", 0.0) or 0.0)
        >= KNOWLEDGE_RELEVANCE_THRESHOLD
    ]

    if not relevant_results:
        if _is_quantitative_question(query):
            return _quantitative_boundary_response()

        return _knowledge_boundary_response()

    quantitative = _is_quantitative_question(query)
    query_terms = _query_terms(query)

    candidate_sentences: list[tuple[int, str, str | None]] = []
    seen_sentences: set[str] = set()

    for item in relevant_results[:5]:
        text = item.get("text") or ""
        title = item.get("title")
        source = item.get("source")
        provenance = title or source

        for sentence in _split_sentences(text):
            normalized = sentence.lower()

            if normalized in seen_sentences:
                continue

            relevance = _sentence_relevance(
                sentence,
                query_terms,
            )

            if quantitative:
                if not _has_relevant_numeric_claim(
                    sentence,
                    query,
                    query_terms,
                ):
                    continue
            elif relevance <= 0:
                continue

            seen_sentences.add(normalized)
            candidate_sentences.append(
                (relevance, sentence, provenance)
            )

    if not candidate_sentences:
        if quantitative:
            return _quantitative_boundary_response()

        return _knowledge_boundary_response()

    candidate_sentences.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected_sentences: list[str] = []
    used_sources: list[str] = []

    for _, sentence, provenance in candidate_sentences:
        selected_sentences.append(sentence)

        if provenance and provenance not in used_sources:
            used_sources.append(provenance)

        if len(selected_sentences) >= 3:
            break

    answer_parts = [
        "According to the Darukaa knowledge base:",
        " ".join(selected_sentences),
    ]

    if used_sources:
        answer_parts.append(
            "Sources: " + "; ".join(used_sources[:3]) + "."
        )

    return " ".join(answer_parts)


def _answer_knowledge_question(message: str) -> str:
    """Retrieve and answer a knowledge question from the existing KB."""
    retrieval = retrieve_knowledge(message)

    return _build_knowledge_answer(
        query=message,
        results=retrieval.get("results", []),
    )


def process_conversation_turn(
    request: ConversationRequest,
    store: Optional[ConversationStore] = None,
) -> ConversationResponse:
    """Process a single conversation turn and return a ConversationResponse."""
    active_store = store or default_store
    conv_id = request.conversation_id
    user_msg = request.message

    # 1. Save user turn
    active_store.add_turn(
        conv_id,
        role="user",
        message=user_msg,
    )

    # 2. Extract explicitly provided environmental info from this turn
    extracted_env = extract_environmental_info(user_msg)

    # 3. Merge with existing conversation context
    state = active_store.update_environment_input(
        conv_id,
        extracted_env,
    )
    current_env = state.environment

    # 4. Detect whether this is a knowledge question rather than
    # an incomplete environmental scenario.
    has_current_environment = any(
        value is not None
        for value in (
            current_env.soil,
            current_env.climate,
            current_env.land,
            current_env.biodiversity,
            current_env.human_impact,
            current_env.location,
        )
    )

    if not has_current_environment and _is_knowledge_question(user_msg):
        reply_text = _answer_knowledge_question(user_msg)

        active_store.add_turn(
            conv_id,
            role="assistant",
            message=reply_text,
        )

        return ConversationResponse(
            conversation_id=conv_id,
            status=ConversationStatus.needs_clarification,
            message=reply_text,
            environment=current_env,
            recommendation=None,
        )

    # 5. Existing environmental-context flow remains unchanged.
    needs_clarification, clarification_msg = evaluate_clarification_need(
        current_env
    )

    if needs_clarification:
        reply_text = (
            clarification_msg
            or "Please provide more details on your environmental conditions."
        )

        active_store.add_turn(
            conv_id,
            role="assistant",
            message=reply_text,
        )

        return ConversationResponse(
            conversation_id=conv_id,
            status=ConversationStatus.needs_clarification,
            message=reply_text,
            environment=current_env,
            recommendation=None,
        )

    # 6. Sufficient context (>=3 variables): call existing reason(env)
    rec_output = reason(current_env)
    reply_text = rec_output.recommendation

    # 7. Save assistant recommendation response in history
    active_store.add_turn(
        conv_id,
        role="assistant",
        message=reply_text,
    )

    return ConversationResponse(
        conversation_id=conv_id,
        status=ConversationStatus.complete,
        message=reply_text,
        environment=current_env,
        recommendation=rec_output,
    )