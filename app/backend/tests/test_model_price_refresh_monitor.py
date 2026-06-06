import re

from services import model_catalog
from services.model_price_refresh_monitor import ModelPriceRefreshMonitorService


SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password\s*[:=])",
    re.IGNORECASE,
)


def _monitor(**kwargs) -> dict:
    return ModelPriceRefreshMonitorService().build_monitor(**kwargs)


def test_price_refresh_monitor_passes_for_current_cheap_defaults():
    payload = _monitor()
    checks = {item["id"]: item for item in payload["checks"]}
    defaults = {
        row["task"]: row
        for row in checks["high-frequency-default-price-tier"]["rows"]
    }

    assert payload["status"] == "pass"
    assert defaults["fast"]["default_model"] == "gemini-2.5-flash-lite"
    assert defaults["classification"]["cost_tier"] == "lowest"
    assert defaults["ocr"]["has_price_metadata"] is True
    specialized_check = checks["specialized-text-default-price-tier"]
    specialized_defaults = {row["task"]: row for row in specialized_check["rows"]}
    assert specialized_check["status"] == "pass"
    assert specialized_defaults["agentic"]["default_model"] == "gemini-3.1-flash-lite"
    assert specialized_defaults["agentic"]["has_required_capability"] is True
    assert specialized_defaults["grounded-research"]["default_model"] == "gemini-3.1-flash-lite"
    assert specialized_defaults["grounded-research"]["has_required_capability"] is True
    media_check = checks["media-default-price-metadata"]
    image_default = {row["task"]: row for row in media_check["rows"]}["image"]
    assert media_check["status"] == "pass"
    assert image_default["default_model"] == "gemini-2.5-flash-image"
    assert image_default["output_usd_per_image"] == 0.039
    assert checks["cost-forecast-price-metadata"]["status"] == "pass"
    assert payload["summary"]["blocking_count"] == 0
    assert payload["summary"]["media_tasks"] == ["image"]


def test_price_refresh_monitor_warns_for_unknown_preview_or_premium_observed_models():
    payload = _monitor(
        observed_models=[
            "google/gemini-9-flash-lite",
            "models/gemini-3.1-pro-preview",
            "yibu/gemini-3.1-flash-image",
            {"id": "gemini-2.5-flash-lite"},
        ]
    )
    observed_check = {item["id"]: item for item in payload["checks"]}[
        "observed-gateway-model-refresh-review"
    ]
    observed_rows = {item["raw_model"]: item for item in observed_check["rows"]}
    warnings = [item for item in payload["drift_signals"] if item["severity"] == "warn"]
    signal_types = {item["signal_type"] for item in warnings}

    assert payload["status"] == "warn"
    assert observed_check["status"] == "warn"
    assert observed_check["summary"]["refresh_review_count"] == 2
    assert "unknown_gateway_model" in signal_types
    assert "premium_or_preview_refresh" in signal_types
    assert any(item["model"] == "google/gemini-9-flash-lite" for item in warnings)
    assert observed_rows["yibu/gemini-3.1-flash-image"]["status"] == "pass"
    assert observed_rows["yibu/gemini-3.1-flash-image"]["has_price_metadata"] is True


def test_price_refresh_monitor_fails_when_fast_default_is_no_longer_low_price(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)

    payload = _monitor()
    high_frequency = {item["id"]: item for item in payload["checks"]}[
        "high-frequency-default-price-tier"
    ]
    fast = {row["task"]: row for row in high_frequency["rows"]}["fast"]

    assert payload["status"] == "fail"
    assert high_frequency["status"] == "fail"
    assert fast["status"] == "fail"
    assert fast["cost_tier"] == "premium"
    assert fast["recommended_model"] == "gemini-2.5-flash-lite"
    assert any(signal["severity"] == "fail" for signal in payload["drift_signals"])


def test_price_refresh_monitor_fails_when_image_default_lacks_price_metadata(monkeypatch):
    monkeypatch.setattr(model_catalog.settings, "app_ai_image_model", "gemini-3-pro-image", raising=False)

    payload = _monitor()
    media_check = {item["id"]: item for item in payload["checks"]}["media-default-price-metadata"]
    image = {row["task"]: row for row in media_check["rows"]}["image"]

    assert payload["status"] == "fail"
    assert media_check["status"] == "fail"
    assert image["default_model"] == "gemini-3-pro-image"
    assert image["has_price_metadata"] is False
    assert image["recommended_model"] == "gemini-2.5-flash-image"
    assert any(
        signal["id"] == "media-default-image" and signal["signal_type"] == "missing_price_metadata"
        for signal in payload["drift_signals"]
    )


def test_price_refresh_monitor_detects_missing_forecast_price_metadata():
    payload = _monitor(
        cost_forecast={
            "profiles": [
                {
                    "task": "review",
                    "initial_model": "gemini-3-pro-image",
                    "escalation_model": "gemini-2.5-pro",
                    "premium_baseline_model": "gemini-2.5-pro",
                }
            ]
        }
    )
    forecast_check = {item["id"]: item for item in payload["checks"]}[
        "cost-forecast-price-metadata"
    ]
    missing_signals = [
        item
        for item in payload["drift_signals"]
        if item["signal_type"] == "missing_price_metadata"
    ]

    assert payload["status"] == "warn"
    assert forecast_check["status"] == "warn"
    assert forecast_check["summary"]["missing_price_metadata_count"] == 1
    assert missing_signals
    assert missing_signals[0]["model"] == "gemini-3-pro-image"


def test_price_refresh_monitor_redacts_sensitive_observed_values():
    payload = _monitor(
        observed_models=[
            {"id": "sk-" + "a" * 24, "secret": "unused"},
            {"model": "pass" + "word=value"},
            "owner" + "@example.test",
        ]
    )

    assert not SENSITIVE_PATTERN.search(str(payload))
    assert "[redacted-sensitive-model-id]" in str(payload)
    assert "credentials" in " ".join(payload["privacy_note"])
    assert payload["validation_commands"] == [
        "cd app/backend && python -m pytest tests/test_model_price_refresh_monitor.py -q",
        "cd app/backend && python -m compileall services/model_price_refresh_monitor.py tests/test_model_price_refresh_monitor.py",
    ]


def test_price_refresh_monitor_route_reviews_observed_models():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/model-price-refresh-monitor",
        json={"observed_models": ["google/gemini-9-flash-lite"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "warn"


def test_model_ops_route_includes_price_refresh_monitor_readiness_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["price_refresh_monitor"]["status"] in {"pass", "warn", "fail"}
    assert payload["price_refresh_monitor"]["summary"]["high_frequency_tasks"] == [
        "fast",
        "classification",
        "ocr",
    ]
    assert payload["price_refresh_monitor"]["summary"]["specialized_text_tasks"] == [
        "grounded-research",
        "agentic",
    ]
    assert payload["price_refresh_monitor"]["summary"]["media_tasks"] == ["image"]
    assert any(
        check["id"] == "specialized-text-default-price-tier"
        for check in payload["price_refresh_monitor"]["checks"]
    )
    assert any(
        check["id"] == "media-default-price-metadata"
        for check in payload["price_refresh_monitor"]["checks"]
    )
    assert any(
        check["source_key"] == "price_refresh_monitor"
        for check in payload["model_ops_readiness"]["checks"]
    )
