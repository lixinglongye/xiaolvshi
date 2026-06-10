import json
import re

from services.legal_document_benchmark_route_plan_research_alignment import (
    ALIGNMENT_ID,
    LegalDocumentBenchmarkRoutePlanResearchAlignmentService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_route_plan_research_alignment_maps_sources_to_replay_scenarios():
    alignment = LegalDocumentBenchmarkRoutePlanResearchAlignmentService().build_alignment()
    rows = {row["id"]: row for row in alignment["alignment_rows"]}
    source_ids = {source["id"] for source in alignment["source_anchors"]}

    assert alignment["id"] == ALIGNMENT_ID
    assert alignment["status"] == "ready"
    assert alignment["summary"]["source_count"] == 5
    assert alignment["summary"]["dimension_count"] == 4
    assert alignment["summary"]["aligned_count"] == 4
    assert alignment["summary"]["route_plan_replay_status"] == "pass"
    assert alignment["summary"]["premium_block_count"] == 1
    assert alignment["summary"]["routed_to_recommended_count"] == 1
    assert alignment["summary"]["model_calls"] == "not_required"
    assert alignment["summary"]["network_access"] == "disabled"
    assert {
        "google-gemini-models",
        "google-gemini-pricing",
        "frugalgpt",
        "legalbench-rag",
        "lexeval",
    } == source_ids
    assert "https://ai.google.dev/gemini-api/docs/models" in alignment["source_urls"]
    assert "https://arxiv.org/abs/2408.10343" in alignment["source_urls"]
    assert rows["premium-cascade-and-block"]["release_action"] == "allow_metadata_claim"
    assert rows["premium-cascade-and-block"]["alignment_status"] == "aligned"
    assert "gemini-3.1-flash-lite" in rows["grounded-legal-opinion-route"]["observed_models"]
    assert "lexeval" in rows["zh-cn-document-task-family"]["source_ids"]


def test_route_plan_research_alignment_blocks_when_replay_scenario_drifts():
    alignment = LegalDocumentBenchmarkRoutePlanResearchAlignmentService().build_alignment(
        {
            "route_plan_replay": {
                "scenarios": [
                    {
                        "id": "contract-review-default-balanced",
                        "case_id": "ldoc-contract-review-mini",
                        "expected_plan_status": "ready",
                        "expected_primary_task": "review",
                        "expected_resolved_model": "gemini-2.5-pro",
                        "expected_cost_tier": "premium",
                        "expected_route_band": "blocked_premium_default",
                        "expected_routed_to_recommended": False,
                        "expected_blocking_check_ids": ["no-premium-primary-defaults"],
                    }
                ]
            }
        }
    )
    checks = {check["id"]: check for check in alignment["checks"]}

    assert alignment["status"] == "blocked"
    assert alignment["summary"]["route_plan_replay_status"] == "fail"
    assert "route-plan-replay-ready" in alignment["blocking_check_ids"]
    assert checks["route-plan-replay-ready"]["status"] == "fail"
    assert alignment["alignment_rows"][0]["alignment_status"] == "gap"
    assert alignment["alignment_rows"][0]["release_action"] == "block_claims"


def test_route_plan_research_alignment_keeps_sensitive_payload_out_of_output():
    secret = "s" + "k-" + ("z" * 28)
    alignment = LegalDocumentBenchmarkRoutePlanResearchAlignmentService().build_alignment(
        {
            "route_plan_replay": {
                "scenarios": [
                    {
                        "id": "reviewer@example.com",
                        "case_id": "ldoc-contract-review-mini",
                        "override_primary_task": "review",
                        "override_primary_model": secret,
                        "expected_plan_status": "ready",
                        "expected_primary_task": "review",
                        "expected_resolved_model": "gemini-2.5-flash",
                        "expected_cost_tier": "low",
                        "expected_route_band": "balanced_after_cheap_precheck",
                        "note": "secret raw legal text should not appear",
                    }
                ]
            },
            "operator_email": "operator@example.com",
        }
    )
    serialized = json.dumps(alignment, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert alignment["summary"]["rejected_sensitive_scenario_count"] == 1
    assert alignment["privacy_boundary"]["returns_raw_scenario_payload"] is False
    assert alignment["privacy_boundary"]["returns_credentials"] is False
    assert "secret raw legal text" not in serialized


def test_route_plan_research_alignment_route_returns_scorecard():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/document-route-plan/research-alignment")
    assert template_response.status_code == 200
    template_payload = template_response.json()
    assert template_payload["success"] is True
    assert template_payload["data"]["id"] == ALIGNMENT_ID
    assert template_payload["data"]["status"] == "ready"
    assert template_payload["data"]["summary"]["source_count"] == 5

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/research-alignment",
        json={"route_plan_replay": {}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["linked_replay_summary"]["status"] == "pass"
    assert payload["data"]["privacy_boundary"]["calls_model"] is False
