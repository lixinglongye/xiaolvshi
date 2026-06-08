import re

from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService


def test_user_need_benchmark_coverage_maps_high_priority_needs_to_fixtures():
    coverage = UserNeedBenchmarkCoverageService().build_coverage()

    assert coverage["status"] == "ready"
    assert coverage["summary"]["need_count"] >= 6
    assert coverage["summary"]["high_priority_gap_count"] == 0
    assert coverage["summary"]["covered_need_count"] >= coverage["summary"]["high_priority_need_count"]
    assert coverage["summary"]["public_benchmark_source_count"] >= 7
    assert coverage["summary"]["public_benchmark_mapped_need_count"] >= coverage["summary"]["high_priority_need_count"]
    assert coverage["summary"]["public_benchmark_document_fixture_mapped_need_count"] >= coverage["summary"][
        "high_priority_need_count"
    ]
    assert coverage["summary"]["public_benchmark_license_review_required_need_count"] >= 1
    assert coverage["summary"]["public_sampler_endpoint"] == "/api/v1/maintenance/legal-review-benchmark/public-sampler"
    assert coverage["summary"]["cheap_first_calibration_status"] == "pass"
    assert coverage["summary"]["cheap_first_calibration_task_count"] >= 6
    assert coverage["summary"]["cheap_first_calibration_mapped_need_count"] >= coverage["summary"]["high_priority_need_count"]
    assert coverage["summary"]["cheap_first_calibration_attention_need_count"] == 0
    assert coverage["source_summaries"]["public_sampler"]["source_count"] >= 4
    assert coverage["source_summaries"]["cheap_first_calibration"]["newapi_called"] is False
    assert coverage["summary"]["local_run_only"] is True
    rows = {row["need_id"]: row for row in coverage["coverage_rows"]}
    assert "service-contract-risk" in rows["cheap-first-review-routing"]["linked_benchmark_case_ids"]
    assert "fixture-service-agreement-small" in rows["traceable-legal-review"]["linked_fixture_ids"]
    assert rows["privacy-safe-upload"]["linked_document_fixture_ids"]
    assert rows["robust-extraction-quality"]["coverage_status"] == "covered"
    assert "fast-intake-preflight" in rows["cheap-first-review-routing"]["linked_calibration_task_ids"]
    assert "legal-review-balanced" in rows["cheap-first-review-routing"]["linked_calibration_task_ids"]
    assert rows["cheap-first-review-routing"]["calibration_status"] == "pass"
    assert rows["cheap-first-review-routing"]["calibration_decisions"]["fast-intake-preflight"] == "keep_cheap_first_default"
    assert rows["feedback-to-roadmap-loop"]["calibration_status"] == "pass"
    assert "feedback-roadmap-classification" in rows["feedback-to-roadmap-loop"]["linked_calibration_task_ids"]
    assert (
        rows["feedback-to-roadmap-loop"]["calibration_decisions"]["feedback-roadmap-classification"]
        == "keep_cheap_first_default"
    )
    assert "legalbench" in rows["traceable-legal-review"]["linked_public_source_ids"]
    assert "legalbench-rag" in rows["traceable-legal-review"]["linked_public_source_ids"]
    assert "lexeval" in rows["traceable-legal-review"]["linked_public_source_ids"]
    assert "casegen" in rows["plain-language-actionability"]["linked_public_source_ids"]
    assert "ldoc-legal-opinion-mini" in rows["traceable-legal-review"]["linked_public_document_fixture_ids"]
    assert "ldoc-settlement-agreement-mini" in rows["plain-language-actionability"][
        "linked_public_document_fixture_ids"
    ]
    assert rows["traceable-legal-review"]["public_sampling_states"]["legalbench"] == "license_review_required"
    assert rows["traceable-legal-review"]["public_benchmark_status"] == "license_review_required"
    assert "legal_reasoning_smoke" in rows["traceable-legal-review"]["linked_public_sampling_batch_ids"]


def test_user_need_benchmark_coverage_surfaces_planning_gaps_without_blocking_high_priority():
    coverage = UserNeedBenchmarkCoverageService().build_coverage()
    rows = {row["need_id"]: row for row in coverage["coverage_rows"]}
    feedback = rows["feedback-to-roadmap-loop"]

    assert feedback["coverage_status"] in {"gap", "partial"}
    assert "no_linked_synthetic_fixture" in feedback["gap_reasons"]
    assert "feedback-to-roadmap-loop" in coverage["gap_need_ids"] or feedback["coverage_status"] == "partial"
    assert coverage["high_priority_gap_need_ids"] == []
    assert any("High-priority user needs" in action for action in coverage["recommended_actions"])


def test_user_need_benchmark_coverage_is_metadata_only():
    coverage = UserNeedBenchmarkCoverageService().build_coverage()
    payload_text = str(coverage).lower()

    assert coverage["privacy_boundary"]["returns_fixture_snippets"] is False
    assert coverage["privacy_boundary"]["external_dataset_downloads"] is False
    assert coverage["privacy_boundary"]["model_calls"] is False
    assert coverage["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert coverage["privacy_boundary"]["returns_calibration_payloads"] is False
    assert coverage["source_summaries"]["public_sampler_resource_policy"]["network_access"] == "disabled_by_default"
    assert "service agreement. alpha service provider" not in payload_text
    assert "borrower id number" not in payload_text
    assert re.search(r"\bsk-[A-Za-z0-9]{20,}\b", payload_text) is None
    assert "@" not in payload_text


def test_user_need_benchmark_coverage_route_returns_map():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/user-needs/benchmark-coverage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["high_priority_gap_count"] == 0
