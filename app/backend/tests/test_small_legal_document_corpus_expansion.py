import re
from pathlib import Path

from services.small_legal_document_corpus_expansion import (
    CORE_TASKS,
    REQUIRED_DOMAINS,
    SmallLegalDocumentCorpusExpansionService,
)


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{20,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def test_small_corpus_builds_local_synthetic_payload():
    corpus = SmallLegalDocumentCorpusExpansionService().build_corpus()

    assert corpus["status"] == "ready"
    assert 6 <= corpus["summary"]["corpus_item_count"] <= 8
    assert len(corpus["corpus_items"]) == corpus["summary"]["corpus_item_count"]
    assert corpus["summary"]["language"] == "zh-CN"
    assert corpus["summary"]["synthetic_data_only"] is True
    assert corpus["summary"]["model_calls"] == "not_required"
    assert corpus["summary"]["network_access"] == "disabled"
    assert corpus["validation_commands"] == [
        "cd app/backend && python -m pytest tests/test_small_legal_document_corpus_expansion.py -q"
    ]


def test_small_corpus_covers_required_legal_domains_and_document_types():
    corpus = SmallLegalDocumentCorpusExpansionService().build_corpus()
    domains = {item["domain"] for item in corpus["corpus_items"]}
    document_types = {item["document_type"] for item in corpus["corpus_items"]}

    assert set(REQUIRED_DOMAINS).issubset(domains)
    assert corpus["coverage_matrix"]["missing_required_domains"] == []
    assert corpus["coverage_matrix"]["domain_count"] >= len(REQUIRED_DOMAINS)
    assert len(document_types) >= 6
    assert {
        "labor_arbitration_application",
        "lease_demand_letter",
        "sales_quality_claim_notice",
        "service_contract_claim_summary",
        "private_lending_claim_summary",
        "traffic_tort_claim_draft",
    }.issubset(document_types)


def test_small_corpus_covers_core_tasks_and_expected_metadata():
    corpus = SmallLegalDocumentCorpusExpansionService().build_corpus()
    covered_tasks = {row["id"] for row in corpus["coverage_matrix"]["tasks"]}

    assert set(CORE_TASKS).issubset(covered_tasks)
    assert corpus["coverage_matrix"]["task_count"] >= len(CORE_TASKS)
    for item in corpus["corpus_items"]:
        assert set(item["tasks"]).issubset(covered_tasks)
        assert len(item["synthetic_excerpt"]) <= corpus["expansion_plan"]["resource_profile"]["max_excerpt_chars"]
        assert item["expected_fields"]
        assert item["risk_tags"]
        assert item["local_checks"]


def test_small_corpus_contains_no_sensitive_patterns():
    corpus = SmallLegalDocumentCorpusExpansionService().build_corpus()
    payload_text = str(corpus)

    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, payload_text)
    assert "real client documents" in corpus["privacy_note"]
    assert "access secrets" in corpus["privacy_note"]


def test_small_corpus_expansion_plan_is_low_resource_and_local_only():
    corpus = SmallLegalDocumentCorpusExpansionService().build_corpus()
    plan = corpus["expansion_plan"]

    assert plan["model_call_policy"] == "never_call_external_models"
    assert plan["network_access"] == "disabled"
    assert plan["resource_profile"]["max_items"] == 8
    assert plan["resource_profile"]["parallelism"] == 1
    assert plan["resource_profile"]["storage"] == "in-memory dictionaries only"
    assert any("6-8" in criterion for criterion in plan["acceptance_criteria"])


def test_small_corpus_service_has_no_network_dependency():
    source_path = Path(__file__).parents[1] / "services" / "small_legal_document_corpus_expansion.py"
    source = source_path.read_text(encoding="utf-8")

    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib" not in source
    assert "socket" not in source


def test_small_corpus_route_returns_expansion_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/small-corpus-expansion")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["corpus_item_count"] >= 6
