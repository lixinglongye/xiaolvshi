import json
import re

from services.legal_document_benchmark_route_plan import (
    PLAN_ID,
    LegalDocumentBenchmarkRoutePlanService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_legal_document_benchmark_route_plan_is_cheap_first_and_metadata_only():
    plan = LegalDocumentBenchmarkRoutePlanService().build_plan()

    assert plan["id"] == PLAN_ID
    assert plan["status"] == "ready"
    assert plan["summary"]["case_count"] == 7
    assert plan["summary"]["cheap_precheck_case_count"] == 7
    assert plan["summary"]["premium_primary_case_count"] == 0
    assert plan["summary"]["coverage_status"] == "ready"
    assert plan["summary"]["model_calls"] == "not_required"
    assert plan["summary"]["network_access"] == "disabled"
    assert plan["summary"]["raw_fixture_snippets_returned"] is False
    assert plan["privacy_boundary"]["returns_fixture_snippets"] is False
    assert plan["privacy_boundary"]["model_calls"] is False
    assert plan["privacy_boundary"]["network_access"] is False
    assert plan["claim_boundary"]["public_benchmark_score_claimed"] is False

    assert {check["id"]: check["status"] for check in plan["checks"]}["cheap-precheck-attached"] == "pass"
    assert {check["id"]: check["status"] for check in plan["checks"]}["no-premium-primary-defaults"] == "pass"
    assert all(row["precheck_route"]["model"] == "gemini-2.5-flash-lite" for row in plan["case_route_rows"])
    assert all(row["raw_fixture_snippet_returned"] is False for row in plan["case_route_rows"])


def test_legal_document_benchmark_route_plan_maps_document_types_to_budgeted_routes():
    plan = LegalDocumentBenchmarkRoutePlanService().build_plan()
    rows = {row["document_type"]: row for row in plan["case_route_rows"]}

    assert rows["evidence_catalog"]["primary_task"] == "classification"
    assert rows["evidence_catalog"]["primary_route"]["resolved_model"] == "gemini-2.5-flash-lite"
    assert rows["evidence_catalog"]["route_band"] == "cheap_primary_after_precheck"
    assert rows["legal_opinion"]["primary_task"] == "grounded-research"
    assert rows["legal_opinion"]["primary_route"]["resolved_model"] == "gemini-3.1-flash-lite"
    assert rows["legal_opinion"]["primary_route"]["cost_tier"] == "lowest"
    assert rows["civil_complaint"]["primary_task"] == "document-generation"
    assert rows["civil_complaint"]["primary_route"]["resolved_model"] == "gemini-2.5-flash"
    assert rows["civil_complaint"]["route_band"] == "balanced_after_cheap_precheck"
    assert plan["summary"]["lowest_primary_case_count"] >= 2
    assert plan["summary"]["balanced_primary_case_count"] >= 4


def test_legal_document_benchmark_route_plan_blocks_premium_primary_override():
    plan = LegalDocumentBenchmarkRoutePlanService().build_plan(
        {
            "case_route_overrides": {
                "ldoc-contract-review-mini": {
                    "primary_task": "review",
                    "primary_model": "gemini-2.5-pro",
                    "allow_over_budget_model": True,
                }
            }
        }
    )
    rows = {row["case_id"]: row for row in plan["case_route_rows"]}
    target = rows["ldoc-contract-review-mini"]

    assert plan["status"] == "blocked"
    assert "no-premium-primary-defaults" in plan["blocking_check_ids"]
    assert plan["summary"]["premium_primary_case_count"] == 1
    assert target["override_applied"] is True
    assert target["primary_route"]["resolved_model"] == "gemini-2.5-pro"
    assert target["route_band"] == "blocked_premium_default"


def test_legal_document_benchmark_route_plan_routes_unapproved_premium_to_recommended_flash():
    plan = LegalDocumentBenchmarkRoutePlanService().build_plan(
        {
            "case_route_overrides": {
                "ldoc-contract-review-mini": {
                    "primary_task": "review",
                    "primary_model": "gemini-2.5-pro",
                    "allow_over_budget_model": False,
                }
            }
        }
    )
    rows = {row["case_id"]: row for row in plan["case_route_rows"]}
    target = rows["ldoc-contract-review-mini"]

    assert plan["status"] == "ready"
    assert plan["summary"]["premium_primary_case_count"] == 0
    assert plan["summary"]["routed_to_recommended_count"] == 1
    assert target["primary_route"]["resolved_model"] == "gemini-2.5-flash"
    assert target["primary_route"]["routed_to_recommended_model"] is True
    assert "routed_to_recommended_model" in target["primary_route"]["reason_codes"]


def test_legal_document_benchmark_route_plan_rejects_sensitive_override_values():
    secret = "s" + "k-" + ("z" * 28)
    plan = LegalDocumentBenchmarkRoutePlanService().build_plan(
        {
            "case_route_overrides": {
                "ldoc-civil-complaint-mini": {
                    "primary_model": secret,
                    "primary_task": "document-generation",
                }
            },
            "operator_email": "reviewer@example.com",
        }
    )
    serialized = json.dumps(plan, ensure_ascii=False)
    rows = {row["case_id"]: row for row in plan["case_route_rows"]}

    assert not SENSITIVE_PATTERN.search(serialized)
    assert rows["ldoc-civil-complaint-mini"]["primary_route"]["requested_model"] is None
    assert plan["privacy_boundary"]["returns_credentials"] is False
    assert plan["summary"]["override_count"] == 1


def test_legal_document_benchmark_route_plan_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/document-route-plan")
    assert template_response.status_code == 200
    template_payload = template_response.json()
    assert template_payload["success"] is True
    assert template_payload["data"]["id"] == PLAN_ID
    assert template_payload["data"]["summary"]["cheap_precheck_case_count"] == 7

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan",
        json={
            "case_route_overrides": {
                "ldoc-contract-review-mini": {
                    "primary_task": "review",
                    "primary_model": "gemini-2.5-pro",
                    "allow_over_budget_model": True,
                }
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "blocked"
    assert "no-premium-primary-defaults" in payload["data"]["blocking_check_ids"]
