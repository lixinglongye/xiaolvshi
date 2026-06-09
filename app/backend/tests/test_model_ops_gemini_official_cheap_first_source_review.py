import json
import re

from services import model_catalog
from services.model_catalog_source_audit import ModelCatalogSourceAuditService
from services.model_ops_gemini_official_cheap_first_source_review import (
    ModelOpsGeminiOfficialCheapFirstSourceReviewService,
)


SENSITIVE_PATTERN = re.compile(
    r"\bsk-[A-Za-z0-9_-]*[0-9][A-Za-z0-9_-]{20,}\b|Authorization:\s*Bearer",
    re.IGNORECASE,
)


def test_gemini_official_cheap_first_source_review_tracks_prices_and_defaults():
    review = ModelOpsGeminiOfficialCheapFirstSourceReviewService().build_review()
    checks = {check["id"]: check for check in review["checks"]}
    prices = {row["model_id"]: row for row in review["price_rows"]}
    comparisons = {row["model_id"]: row for row in review["comparison_rows"]}
    tasks = {row["task"]: row for row in review["task_default_rows"]}

    assert review["status"] == "ready"
    assert review["summary"]["review_model_count"] == 3
    assert review["summary"]["priced_text_model_count"] == 3
    assert review["summary"]["source_review_count"] == 2
    assert review["summary"]["source_review_stale_count"] == 0
    assert review["summary"]["flash_lite_input_cost_usd_per_million"] == 0.10
    assert review["summary"]["flash_lite_output_cost_usd_per_million"] == 0.40
    assert review["summary"]["largest_output_cost_ratio_vs_flash_lite"] >= 25
    assert prices["gemini-2.5-flash-lite"]["cheap_first_default_allowed"] is True
    assert prices["gemini-2.5-pro"]["requires_operator_review"] is True
    assert comparisons["gemini-2.5-flash"]["output_cost_ratio_vs_flash_lite"] == 6.25
    assert comparisons["gemini-2.5-pro"]["output_cost_ratio_vs_flash_lite"] == 25.0
    assert tasks["cheap"]["flash_lite_aligned"] is True
    assert tasks["fast"]["flash_lite_aligned"] is True
    assert checks["official-source-review-current"]["status"] == "pass"
    assert checks["text-model-prices-present"]["status"] == "pass"
    assert checks["high-frequency-defaults-flash-lite"]["status"] == "pass"
    assert review["privacy_boundary"]["network_called"] is False
    assert review["privacy_boundary"]["credentials_included"] is False
    assert review["claim_boundary"]["automatic_default_change_claimed"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(review, ensure_ascii=False))


def test_gemini_official_cheap_first_source_review_warns_on_stale_sources():
    stale_source_audit = ModelCatalogSourceAuditService().build_audit(as_of_date="2026-07-20")
    review = ModelOpsGeminiOfficialCheapFirstSourceReviewService().build_review(
        {"catalog_source_audit": stale_source_audit}
    )
    checks = {check["id"]: check for check in review["checks"]}

    assert review["status"] == "review_required"
    assert review["summary"]["source_review_stale_count"] == 2
    assert review["summary"]["default_promotion_block_count"] == 2
    assert checks["official-source-review-current"]["status"] == "warn"
    assert "official-source-review-current" in review["warning_check_ids"]
    assert any("Refresh official Gemini pricing/model source review" in action for action in review["recommended_actions"])


def test_gemini_official_cheap_first_source_review_blocks_high_frequency_drift(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)

    review = ModelOpsGeminiOfficialCheapFirstSourceReviewService().build_review()
    checks = {check["id"]: check for check in review["checks"]}
    tasks = {row["task"]: row for row in review["task_default_rows"]}

    assert review["status"] == "blocked"
    assert review["summary"]["default_promotion_block_count"] >= 1
    assert tasks["fast"]["default_model"] == "gemini-2.5-pro"
    assert tasks["fast"]["requires_review"] is True
    assert checks["high-frequency-defaults-flash-lite"]["status"] == "fail"
    assert "high-frequency-defaults-flash-lite" in review["blocking_check_ids"]


def test_gemini_official_cheap_first_source_review_route_and_aggregate_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-official-cheap-first-source-review")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-gemini-official-cheap-first-source-review"
    assert payload["data"]["summary"]["review_model_count"] == 3

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["gemini_official_cheap_first_source_review"]["summary"]["review_model_count"]
        == 3
    )
    assert any(
        check["source_key"] == "gemini_official_cheap_first_source_review"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
