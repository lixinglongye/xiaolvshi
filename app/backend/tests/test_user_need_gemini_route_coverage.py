import re

from services.user_need_gemini_route_coverage import UserNeedGeminiRouteCoverageService


def test_user_need_gemini_route_coverage_maps_needs_to_route_preflight():
    coverage = UserNeedGeminiRouteCoverageService().build_coverage()
    rows = {row["need_id"]: row for row in coverage["coverage_rows"]}

    assert coverage["id"] == "user-need-gemini-route-coverage"
    assert coverage["status"] in {"review_required", "blocked"}
    assert coverage["summary"]["need_count"] >= 7
    assert coverage["summary"]["high_priority_need_count"] >= 4
    assert coverage["summary"]["source_route_preflight_status"] == "review_required"
    assert coverage["summary"]["source_calibration_status"] == "pass"
    assert coverage["summary"]["route_task_count"] == 10
    assert coverage["summary"]["official_source_count"] == 4
    assert coverage["summary"]["cheap_first_route_need_count"] >= 4
    assert coverage["summary"]["high_priority_route_protected_count"] >= 3
    assert coverage["summary"]["configuration_written"] is False

    cheap_first = rows["cheap-first-review-routing"]
    assert cheap_first["route_coverage_status"] == "review_required"
    assert cheap_first["high_frequency_route_ready"] is True
    assert "fast" in cheap_first["linked_route_tasks"]
    assert "classification" in cheap_first["linked_route_tasks"]
    assert "ocr" in cheap_first["linked_route_tasks"]
    assert "review" in cheap_first["linked_route_tasks"]
    assert "gemini-2.5-flash-lite" in cheap_first["linked_default_models"]
    assert cheap_first["cheap_first_route_count"] >= 3
    assert cheap_first["balanced_route_count"] >= 1
    assert cheap_first["blocked_reason_codes"] == []
    assert "public_benchmark_license_review_required" in cheap_first["review_reason_codes"]

    privacy = rows["privacy-safe-upload"]
    assert privacy["route_coverage_status"] == "review_required"
    assert privacy["route_task_source"] == "user_need_route_hint"
    assert privacy["high_frequency_route_ready"] is True
    assert "fast" in privacy["linked_route_tasks"]
    assert "classification" in privacy["linked_route_tasks"]
    assert "route_hint_needs_calibration_evidence" in privacy["review_reason_codes"]

    traceable = rows["traceable-legal-review"]
    assert traceable["route_coverage_status"] == "review_required"
    assert "review" in traceable["linked_route_tasks"]
    assert "pdf" in traceable["linked_route_tasks"]
    assert "premium_exception_review_required" in traceable["review_reason_codes"]
    assert "public_benchmark_license_review_required" in traceable["review_reason_codes"]

    feedback = rows["feedback-to-roadmap-loop"]
    assert feedback["route_coverage_status"] == "blocked"
    assert feedback["route_task_source"] == "unmapped"
    assert "no_gemini_route_task_mapped" in feedback["blocked_reason_codes"]
    assert "high_priority_route_unmapped" not in feedback["blocked_reason_codes"]


def test_user_need_gemini_route_coverage_boundaries_are_metadata_only():
    coverage = UserNeedGeminiRouteCoverageService().build_coverage()
    serialized = str(coverage).lower()

    assert coverage["privacy_boundary"]["metadata_only"] is True
    assert coverage["privacy_boundary"]["returns_raw_benchmark_samples"] is False
    assert coverage["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert coverage["privacy_boundary"]["returns_fixture_snippets"] is False
    assert coverage["privacy_boundary"]["returns_calibration_payloads"] is False
    assert coverage["privacy_boundary"]["returns_route_payloads"] is False
    assert coverage["privacy_boundary"]["returns_raw_legal_text"] is False
    assert coverage["privacy_boundary"]["returns_prompts"] is False
    assert coverage["privacy_boundary"]["returns_raw_model_output"] is False
    assert coverage["privacy_boundary"]["returns_credentials"] is False
    assert coverage["privacy_boundary"]["returns_emails"] is False
    assert coverage["privacy_boundary"]["model_calls"] is False
    assert coverage["privacy_boundary"]["gateway_calls"] is False
    assert coverage["privacy_boundary"]["network_access"] is False
    assert coverage["claim_boundary"]["claims_24h_completion"] is False
    assert coverage["claim_boundary"]["claims_public_benchmark_scores"] is False
    assert coverage["claim_boundary"]["claims_live_gateway_execution"] is False
    assert coverage["claim_boundary"]["claims_default_route_changed"] is False
    assert "service agreement. alpha service provider" not in serialized
    assert "borrower id number" not in serialized
    assert re.search(r"\bsk-[A-Za-z0-9]{20,}\b", serialized) is None
    assert "@" not in serialized


def test_user_need_gemini_route_coverage_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/user-needs/gemini-route-coverage")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "user-need-gemini-route-coverage"
    assert payload["data"]["summary"]["model_calls"] == "not_required"
    assert payload["data"]["source_boundaries"]["changes_default_routes"] is False
