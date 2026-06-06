import json
import re

from services import model_catalog
from services.model_catalog_source_audit import ModelCatalogSourceAuditService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_model_catalog_source_audit_tracks_sources_pricing_and_defaults():
    audit = ModelCatalogSourceAuditService().build_audit()
    checks = {check["id"]: check for check in audit["checks"]}
    rows = {row["model_id"]: row for row in audit["catalog_rows"]}

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
    assert "pricing-metadata-watchlist" in audit["warning_check_ids"]
    assert rows["gemini-2.5-flash-lite"]["high_frequency_default_allowed"] is True
    assert rows["gemini-2.5-flash-lite"]["pricing_status"] == "token_priced"
    assert rows["gemini-3-flash-preview"]["catalog_status"] == "preview"
    assert rows["gemini-3-flash-preview"]["pricing_status"] == "token_priced"
    assert rows["gemini-3-flash-preview"]["high_frequency_default_allowed"] is False
    assert rows["gemini-3.5-flash"]["cost_tier"] == "premium"
    assert rows["gemini-3.5-flash"]["catalog_status"] == "review"
    assert rows["gemini-3.5-flash"]["pricing_status"] == "missing"
    assert rows["gemini-3.5-flash"]["high_frequency_default_allowed"] is False
    assert rows["gemini-3-pro-image"]["pricing_status"] == "missing"
    assert rows["gemini-3-pro-image"]["official_source_url"] is True
    assert audit["privacy_boundary"]["network_called"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(audit, ensure_ascii=False))


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
