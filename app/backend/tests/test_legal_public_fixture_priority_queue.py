import json
import re

from services.legal_public_fixture_priority_queue import LegalPublicFixturePriorityQueueService


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{12,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def test_public_fixture_priority_queue_builds_metadata_only_queue():
    queue = LegalPublicFixturePriorityQueueService().build_queue()

    assert queue["status"] == "ready_with_priority_queue"
    assert queue["method"]["type"] == "public-benchmark-to-synthetic-fixture-priority-queue"
    assert queue["summary"]["source_count"] >= 8
    assert queue["summary"]["queue_row_count"] == len(queue["queue_rows"])
    assert queue["summary"]["high_priority_row_count"] >= 4
    assert queue["summary"]["chinese_source_count"] >= 3
    assert queue["summary"]["lawbench_source_present"] is True
    assert queue["summary"]["local_rule_baseline_status"] == "pass"
    assert queue["summary"]["local_rule_baseline_required"] is True
    assert queue["summary"]["model_calls"] == "not_required"
    assert queue["summary"]["network_access"] == "disabled"
    assert queue["summary"]["external_dataset_downloads"] is False
    assert queue["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert queue["privacy_boundary"]["returns_dataset_examples"] is False
    assert queue["privacy_boundary"]["returns_local_fixture_snippets"] is False
    assert queue["privacy_boundary"]["returns_small_corpus_excerpts"] is False
    assert queue["privacy_boundary"]["model_calls"] is False
    assert queue["privacy_boundary"]["network_access"] is False
    assert queue["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert queue["claim_boundary"]["public_dataset_coverage_claimed"] is False


def test_public_fixture_priority_queue_prioritizes_chinese_legal_sources_and_user_needs():
    queue = LegalPublicFixturePriorityQueueService().build_queue()
    rows = {row["source_id"]: row for row in queue["queue_rows"]}

    assert {"lawbench", "lexeval", "casegen"}.issubset(rows)
    assert rows["lawbench"]["priority_band"] == "high"
    assert rows["lawbench"]["priority_score"] >= rows["pile-of-law"]["priority_score"]
    assert "lawbench_task_taxonomy" in rows["lawbench"]["reason_codes"]
    assert "chinese_legal_source" in rows["lawbench"]["reason_codes"]
    assert "high_priority_user_need_linked" in rows["lawbench"]["reason_codes"]
    assert "legal_reasoning_smoke" in rows["lawbench"]["sampling_batch_ids"]
    assert "chinese_legal_document_generation_smoke" in rows["lawbench"]["sampling_batch_ids"]
    assert rows["lawbench"]["linked_high_priority_need_ids"]
    assert rows["lawbench"]["document_fixture_ids"]
    assert rows["lawbench"]["small_corpus_item_ids"]
    assert rows["lawbench"]["gate_status"] == "metadata_only_until_license_review"
    assert rows["lawbench"]["raw_text_returned"] is False


def test_public_fixture_priority_queue_surfaces_fixture_gaps_without_blocking_local_baseline():
    queue = LegalPublicFixturePriorityQueueService().build_queue()
    rows = {row["source_id"]: row for row in queue["queue_rows"]}

    assert "cuad" in rows
    assert "document_fixture_mapping_missing" in rows["cuad"]["reason_codes"]
    assert rows["cuad"]["gate_status"] == "needs_synthetic_fixture_mapping"
    assert "pile-of-law" in queue["fixture_gap_source_ids"]
    assert "catalog_reference_only" in rows["pile-of-law"]["reason_codes"]
    assert rows["pile-of-law"]["gate_status"] in {"needs_synthetic_fixture_mapping", "catalog_reference_only"}
    assert any("synthetic zh-CN fixture" in action for action in queue["recommended_actions"])


def test_public_fixture_priority_queue_does_not_return_raw_samples_or_secrets():
    queue = LegalPublicFixturePriorityQueueService().build_queue()
    serialized = json.dumps(queue, ensure_ascii=False)

    assert "Service Agreement. Alpha Service Provider" not in serialized
    assert "OCR page 7 text fragment" not in serialized
    assert "synthetic_excerpt" not in serialized
    assert "sample_text" not in serialized
    assert "input_excerpt" not in serialized
    for pattern in SENSITIVE_PATTERNS:
        assert re.search(pattern, serialized) is None


def test_public_fixture_priority_queue_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get(
        "/api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["lawbench_source_present"] is True
    assert payload["data"]["queue_rows"][0]["priority_band"] == "high"
