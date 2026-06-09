import json
import re

from services import model_catalog
from services.model_catalog_source_audit import ModelCatalogSourceAuditService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_model_catalog_source_audit_tracks_sources_pricing_and_defaults():
    audit = ModelCatalogSourceAuditService().build_audit(as_of_date="2026-06-09")
    checks = {check["id"]: check for check in audit["checks"]}
    rows = {row["model_id"]: row for row in audit["catalog_rows"]}
    source_reviews = {row["id"]: row for row in audit["source_review_records"]}

    assert audit["status"] == "warn"
    assert audit["summary"]["catalog_model_count"] >= 8
    assert audit["summary"]["source_reference_count"] == 2
    assert audit["summary"]["source_url_present_count"] == audit["summary"]["catalog_model_count"]
    assert audit["summary"]["official_source_url_count"] == audit["summary"]["catalog_model_count"]
    assert audit["summary"]["high_frequency_aligned_count"] == audit["summary"]["high_frequency_default_count"]
    assert checks["official-source-url-present"]["status"] == "pass"
    assert checks["high-frequency-defaults-cheap-first"]["status"] == "pass"
    assert checks["stable-defaults-not-preview-or-premium"]["status"] == "pass"
    assert checks["pricing-metadata-watchlist"]["status"] == "warn"
    assert checks["official-source-review-freshness"]["status"] == "pass"
    assert "pricing-metadata-watchlist" in audit["warning_check_ids"]
    assert audit["source_review_snapshot_as_of"] == "2026-06-09"
    assert audit["summary"]["source_review_current_count"] == 2
    assert audit["summary"]["source_review_stale_count"] == 0
    assert audit["summary"]["default_promotion_source_block_count"] == 0
    assert source_reviews["google-gemini-pricing"]["freshness_status"] == "current"
    assert source_reviews["google-gemini-pricing"]["default_promotion_allowed"] is True
    assert source_reviews["google-gemini-pricing"]["review_age_days"] == 0
    assert source_reviews["google-gemini-models"]["review_scope"].startswith("model names")
    assert rows["gemini-2.5-flash-lite"]["high_frequency_default_allowed"] is True
    assert rows["gemini-2.5-flash-lite"]["pricing_status"] == "token_priced"
    assert rows["gemini-3-flash-preview"]["catalog_status"] == "preview"
    assert rows["gemini-3-flash-preview"]["pricing_status"] == "token_priced"
    assert rows["gemini-3-flash-preview"]["high_frequency_default_allowed"] is False
    assert rows["gemini-3.5-flash"]["cost_tier"] == "premium"
    assert rows["gemini-3.5-flash"]["catalog_status"] == "stable"
    assert rows["gemini-3.5-flash"]["pricing_status"] == "token_priced"
    assert rows["gemini-3.5-flash"]["high_frequency_default_allowed"] is False
    assert rows["gemini-3.1-pro-preview-customtools"]["pricing_status"] == "token_priced"
    assert rows["gemini-3-pro-image"]["pricing_status"] == "image_priced"
    assert rows["gemini-3-pro-image"]["official_source_url"] is True
    assert audit["privacy_boundary"]["network_called"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(audit, ensure_ascii=False))


def test_model_catalog_source_audit_warns_when_official_source_review_is_stale():
    audit = ModelCatalogSourceAuditService().build_audit(as_of_date="2026-07-20")
    checks = {check["id"]: check for check in audit["checks"]}
    source_reviews = {row["id"]: row for row in audit["source_review_records"]}

    assert audit["status"] == "warn"
    assert checks["official-source-review-freshness"]["status"] == "warn"
    assert "official-source-review-freshness" in audit["warning_check_ids"]
    assert audit["summary"]["source_review_current_count"] == 0
    assert audit["summary"]["source_review_stale_count"] == 2
    assert audit["summary"]["default_promotion_source_block_count"] == 2
    assert source_reviews["google-gemini-pricing"]["freshness_status"] == "stale"
    assert source_reviews["google-gemini-pricing"]["default_promotion_allowed"] is False
    assert source_reviews["google-gemini-pricing"]["review_age_days"] == 41
    assert any("Refresh official Gemini pricing" in action for action in audit["recommended_actions"])


def test_model_catalog_source_audit_fails_when_high_frequency_default_drifts(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)

    audit = ModelCatalogSourceAuditService().build_audit()
    defaults = {row["task"]: row for row in audit["high_frequency_defaults"]}

    assert audit["status"] == "fail"
    assert "high-frequency-defaults-cheap-first" in audit["blocking_check_ids"]
    assert defaults["fast"]["default_model"] == "gemini-2.5-pro"
    assert defaults["fast"]["canonical_model"] == "gemini-2.5-pro"


def test_model_catalog_source_audit_route_and_model_ops_payload_include_readiness_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    audit_response = client.get("/api/v1/aihub/models/catalog-source-audit")
    assert audit_response.status_code == 200
    assert audit_response.json()["success"] is True
    assert audit_response.json()["data"]["summary"]["source_reference_count"] == 2

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["catalog_source_audit"]["summary"]["catalog_model_count"] >= 8
    assert any(
        check["source_key"] == "catalog_source_audit"
        for check in payload["model_ops_readiness"]["checks"]
    )
