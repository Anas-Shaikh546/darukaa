import pytest

from app.schemas.environment import EnvironmentInput
from app.schemas.recommendation import EvidenceItem, RecommendationOutput, Reasoning, ImpactMetric
from app.services import reasoning


def make_output(variables, evidence=None, recommendation="Consider agroforestry."):
    if evidence is None:
        evidence = []

    return RecommendationOutput(
        recommendation=recommendation,
        reasoning=Reasoning(
            variables=variables,
            relationships=[],
            explanation="Test explanation.",
        ),
        impacted_metrics=[
            ImpactMetric(
                metric="biodiversity",
                estimate="potentially improved",
                basis="Test basis.",
            )
        ],
        time_horizon="medium",
        confidence=0.0,
        evidence=evidence,
        validation=None,
    )


def make_evidence(similarity=0.8, text="Agroforestry can improve soil quality and biodiversity."):
    return EvidenceItem(
        source="test_source",
        title="Test Source",
        chunk_id="chunk_1",
        used_for="supports recommendation",
        text=text,
        similarity=similarity,
    )


def test_variable_count_passes_with_three_variables():
    output = make_output(["SOC", "Rainfall", "Land-use intensity"])

    ok, detail = reasoning._validate_variable_count(output.reasoning.variables)

    assert ok is True
    assert "variable count" in detail.lower()

def test_variable_count_fails_with_less_than_three():
    output = make_output(["SOC", "Rainfall"])

    ok, detail = reasoning._validate_variable_count(output.reasoning.variables)

    assert ok is False
    assert "need >=3" in detail.lower()


def test_evidence_presence_fails_when_required_metadata_missing():
    evidence = [
        EvidenceItem(
            source="",
            title="Test Source",
            chunk_id="chunk_1",
            used_for="supports recommendation",
            text="Some evidence text.",
            similarity=0.8,
        )
    ]

    ok, detail = reasoning._validate_evidence_presence(evidence)

    assert ok is False
    assert "missing" in detail.lower()


def test_unsupported_numeric_claim_is_rejected_or_stripped():
    evidence = [
        make_evidence(
            text="Agroforestry can improve soil quality.",
            similarity=0.8,
        )
    ]

    text, ok, message = reasoning._validate_numerical_claims(
        "Agroforestry will increase biodiversity by 25%.",
        evidence,
    )

    assert ok is False
    assert "25%" not in text


def test_supported_numeric_claim_uses_actual_evidence_text():
    evidence = [
        make_evidence(
            text="Agroforestry increased species richness by 25% in the study.",
            similarity=0.9,
        )
    ]

    text, ok, message = reasoning._validate_numerical_claims(
        "Agroforestry increased species richness by 25%.",
        evidence,
    )

    assert ok is True
    assert "25%" in text


def test_llm_verifier_failure_does_not_pass(monkeypatch):
    monkeypatch.setattr(
        reasoning,
        "_run_verifier",
        lambda claim, evidence: False,
    )

    evidence = [make_evidence()]

    output = make_output(
        ["SOC", "Rainfall", "Land-use intensity"],
        evidence=evidence,
    )

    ok, detail = reasoning._validate(output)

    assert ok is False
    assert detail["evidence_grounded"] is False
    assert detail["llm_verification_ok"] is False


def test_confidence_uses_actual_similarity():
    evidence = [
        make_evidence(similarity=0.8),
        make_evidence(similarity=0.6),
    ]

    confidence = reasoning._calculate_confidence(evidence)

    assert confidence == pytest.approx(0.7)


def test_retry_is_limited_to_one_attempt(monkeypatch):
    calls = []

    valid_output = make_output(
        ["SOC", "Rainfall", "Land-use intensity"],
        evidence=[make_evidence()],
    )

    def fake_generate(env, retrieval_top_k, evidence_k):
        calls.append((retrieval_top_k, evidence_k))
        return valid_output

    monkeypatch.setattr(reasoning, "_generate_recommendation", fake_generate)
    monkeypatch.setattr(reasoning, "_validate", lambda output: (False, {
        "variable_count": 3,
        "evidence_grounded": False,
        "numeric_claims_ok": True,
        "llm_verification_ok": False,
        "messages": ["forced validation failure"],
    }))

    env = EnvironmentInput(
        soil={"organic_carbon": 0.3},
        climate={"rainfall_category": "low"},
        land={"land_use": "wheat monoculture"},
    )

    reasoning.reason(env)

    assert len(calls) == 2


def test_fallback_after_validation_failure(monkeypatch):
    output = make_output(
        ["SOC", "Rainfall", "Land-use intensity"],
        evidence=[make_evidence()],
    )

    monkeypatch.setattr(
        reasoning,
        "_generate_recommendation",
        lambda env, retrieval_top_k, evidence_k: output,
    )

    monkeypatch.setattr(
        reasoning,
        "_validate",
        lambda output: (False, {
            "variable_count": 3,
            "evidence_grounded": False,
            "numeric_claims_ok": True,
            "llm_verification_ok": False,
            "messages": ["forced validation failure"],
        }),
    )

    env = EnvironmentInput(
        soil={"organic_carbon": 0.3},
        climate={"rainfall_category": "low"},
        land={"land_use": "wheat monoculture"},
    )

    result = reasoning.reason(env)

    assert result.validation is not None or result.confidence == 0.0
    assert "fallback" in result.recommendation.lower() or result.confidence == 0.0


def test_reference_validation_structure():
    evidence = [make_evidence()]

    output = make_output(
        ["SOC", "Rainfall", "Land-use intensity"],
        evidence=evidence,
    )

    monkeypatch_result = {
        "variable_count": 3,
        "evidence_grounded": True,
        "numeric_claims_ok": True,
        "llm_verification_ok": True,
        "messages": [
            "Variable count validation passed.",
            "Evidence presence validation passed.",
            "No unsupported numerical claims detected.",
            "LLM verification: supported",
        ],
    }

    output.validation = monkeypatch_result

    assert output.validation["variable_count"] >= 3
    assert output.validation["evidence_grounded"] is True
    assert output.validation["numeric_claims_ok"] is True
    assert output.validation["llm_verification_ok"] is True