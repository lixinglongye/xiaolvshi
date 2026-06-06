import json
import re

from services.model_catalog_candidate_patch_plan import ModelCatalogCandidatePatchPlanService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_catalog_candidate_patch_plan_builds_review_only_candidates():
    plan = ModelCatalogCandidatePatchPlanService().build_plan(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-flash-lite"},
                    {"id": "google/gemini-3.2-flash-lite"},
                    {"id": "newapi/gemini-4.0-flash-lite-preview"},
                    {"id": "vendor/other-model"},
                ]
            }
        }
    )
    candidate_rows = {row["proposed_catalog_id"]: row for row in plan["candidate_patch_rows"]}
    existing = {row["observed_model"]: row for row in plan["existing_catalog_diffs"]}
    external = {row["observed_model"]: row for row in plan["external_model_ignores"]}

    assert plan["status"] == "review_required"
    assert plan["summary"]["candidate_patch_count"] == 2
    assert plan["summary"]["existing_catalog_review_count"] == 1
    assert plan["summary"]["external_ignore_count"] == 1
    assert plan["summary"]["candidate_patch_written"] is False
    assert plan["summary"]["configuration_written"] is False
    assert plan["summary"]["gateway_called"] is False
    assert existing["models/gemini-2.5-flash-lite"]["cheap_first_default_allowed"] is True
    assert "gemini-3.2-flash-lite" in candidate_rows
    assert candidate_rows["gemini-3.2-flash-lite"]["patch_action"] == "add_manual_model_profile_candidate"
    assert candidate_rows["gemini-3.2-flash-lite"]["default_allowed_for_high_frequency"] is False
    assert candidate_rows["gemini-3.2-flash-lite"]["cheap_first_candidate_status"] == (
        "blocked_until_price_lifecycle_and_probe_pass"
    )
    assert candidate_rows["gemini-3.2-flash-lite"]["proposed_profile_stub"]["status"] == "review_required"
    assert "pricing_source_review" in candidate_rows["gemini-3.2-flash-lite"]["required_metadata_checks"]
    assert candidate_rows["gemini-4.0-flash-lite-preview"]["cheap_first_candidate_status"] == (
        "premium_or_preview_explicit_only"
    )
    assert external["vendor/other-model"]["patch_action"] == "ignore_non_gemini_model"
    assert plan["privacy_boundary"]["candidate_patch_written"] is False
    assert plan["claim_boundary"]["automatic_catalog_edit_claimed"] is False


def test_catalog_candidate_patch_plan_blocks_sensitive_or_raw_payloads_without_echoing_values():
    secret = "s" + "k-" + "a" * 24
    plan = ModelCatalogCandidatePatchPlanService().build_plan(
        {
            "model_ids": [secret, {"not_model": "ignored malformed row"}, "gemini-2.5-flash-lite"],
            "prompt": "client@example.com raw prompt should not be echoed",
        }
    )
    serialized = json.dumps(plan, ensure_ascii=False)

    assert plan["status"] == "blocked"
    assert plan["summary"]["rejected_sensitive_count"] == 1
    assert plan["summary"]["rejected_invalid_count"] == 1
    assert plan["summary"]["rejected_model_count"] == 2
    assert plan["summary"]["forbidden_payload_field_count"] >= 1
    assert plan["summary"]["blocked_count"] >= 3
    assert "sanitized-model-metadata-only" in plan["blocking_check_ids"]
    assert not SENSITIVE_PATTERN.search(serialized)
    assert "raw prompt should not be echoed" not in serialized
    assert "ignored malformed row" not in serialized
    assert plan["privacy_boundary"]["raw_payload_echoed"] is False
    assert plan["privacy_boundary"]["credentials_included"] is False


def test_catalog_candidate_patch_plan_consumes_intake_and_probe_signal_metadata():
    plan = ModelCatalogCandidatePatchPlanService().build_plan(
        signals={
            "observed_gemini_model_intake_queue": {
                "queue_items": [
                    {
                        "raw_model": "newapi/gemini-3.2-flash-lite",
                        "intake_status": "blocked",
                    }
                ]
            },
            "gateway_probe_evaluation": {
                "model_rows": [
                    {
                        "model": "models/gemini-2.5-flash-lite",
                        "chat_probe_status": "pass",
                    }
                ]
            },
        }
    )
    candidate_ids = {row["proposed_catalog_id"] for row in plan["candidate_patch_rows"]}
    existing_ids = {row["canonical_model"] for row in plan["existing_catalog_diffs"]}

    assert plan["status"] == "review_required"
    assert "gemini-3.2-flash-lite" in candidate_ids
    assert "gemini-2.5-flash-lite" in existing_ids
    assert plan["summary"]["raw_payload_echoed"] is False


def test_catalog_candidate_patch_plan_route_and_models_payload_include_readiness_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/catalog-candidate-patch-plan")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["configuration_written"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/catalog-candidate-patch-plan",
        json={"model_ids": ["newapi/gemini-3.2-flash-lite"]},
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "review_required"
    assert eval_response.json()["data"]["candidate_patch_rows"][0]["proposed_catalog_id"] == "gemini-3.2-flash-lite"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert "catalog_candidate_patch_plan" in payload
    assert payload["catalog_candidate_patch_plan"]["summary"]["configuration_written"] is False
    assert any(
        check["source_key"] == "catalog_candidate_patch_plan"
        for check in payload["model_ops_readiness"]["checks"]
    )
