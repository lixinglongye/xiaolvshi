import json
import re

from services.gemini_newapi_alias_capability_coverage import GeminiNewapiAliasCapabilityCoverageService
from services.model_catalog import GEMINI_MODEL_CATALOG, canonical_model_id


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_alias_capability_coverage_expands_gateway_shapes_and_tasks():
    coverage = GeminiNewapiAliasCapabilityCoverageService().build_coverage()
    rows = {(row["alias_model"], row["canonical_model"]): row for row in coverage["coverage_rows"]}

    assert coverage["status"] == "ready"
    assert coverage["summary"]["catalog_model_count"] == len(GEMINI_MODEL_CATALOG)
    assert coverage["summary"]["alias_shape_count"] >= 10
    assert coverage["summary"]["known_coverage_count"] >= len(GEMINI_MODEL_CATALOG) * 10
    assert coverage["summary"]["cheap_first_high_frequency_alias_count"] >= 10
    assert coverage["summary"]["text_json_capable_alias_count"] > coverage["summary"]["image_capable_alias_count"]
    assert coverage["summary"]["configuration_written"] is False
    assert coverage["summary"]["gateway_called"] is False
    assert coverage["summary"]["network_called"] is False

    yibu_flash_lite = rows[("yibu:gemini-2.5-flash-lite", "gemini-2.5-flash-lite")]
    action_suffix = rows[
        ("publishers/google/models/gemini-2.5-flash-lite:generateContent", "gemini-2.5-flash-lite")
    ]
    agentic = rows[("newapi/google/gemini-3.1-flash-lite@latest", "gemini-3.1-flash-lite")]

    assert yibu_flash_lite["high_frequency_default_allowed"] is True
    assert "fast" in yibu_flash_lite["covered_high_frequency_tasks"]
    assert action_suffix["alias_shape"] == "google_publishers_models"
    assert action_suffix["default_allowed_without_review"] is True
    assert "agentic" in agentic["covered_tasks"]
    assert "grounded-research" in agentic["covered_tasks"]
    assert agentic["balanced_after_precheck_allowed"] is True
    assert canonical_model_id("models/gemini-2.5-flash-lite:generateContent") == "gemini-2.5-flash-lite"
    assert canonical_model_id("models/gemini-2.5-flash-lite:generateContent@latest") == "gemini-2.5-flash-lite"
    assert canonical_model_id("publishers/google/models/gemini-2.5-flash-lite:generateContent?alt=sse") == "gemini-2.5-flash-lite"
    assert canonical_model_id("newapi/google/gemini-3.1-flash-lite@latest") == "gemini-3.1-flash-lite"


def test_alias_capability_coverage_reviews_unknown_and_external_observed_models():
    coverage = GeminiNewapiAliasCapabilityCoverageService().build_coverage(
        {
            "include_catalog_aliases": False,
            "observed_models": [
                "yibuapi/google/gemini-3.9-flash-lite",
                "newapi/google/gemini-2.5-flash-lite",
                "vendor/other-model",
            ],
        }
    )
    rows = {row["alias_model"]: row for row in coverage["coverage_rows"]}

    assert coverage["status"] == "review_required"
    assert coverage["summary"]["coverage_row_count"] == 3
    assert coverage["summary"]["review_required_count"] == 2
    assert coverage["summary"]["external_model_count"] == 1
    assert rows["yibuapi/google/gemini-3.9-flash-lite"]["coverage_status"] == "review_required"
    assert rows["yibuapi/google/gemini-3.9-flash-lite"]["default_allowed_without_review"] is False
    assert rows["newapi/google/gemini-2.5-flash-lite"]["coverage_status"] == "covered"
    assert rows["newapi/google/gemini-2.5-flash-lite"]["high_frequency_default_allowed"] is True
    assert rows["vendor/other-model"]["coverage_status"] == "external"
    assert rows["vendor/other-model"]["default_allowed_without_review"] is False


def test_alias_capability_coverage_redacts_sensitive_observed_values():
    coverage = GeminiNewapiAliasCapabilityCoverageService().build_coverage(
        {
            "include_catalog_aliases": False,
            "observed_models": [
                "s" + "k-" + "a" * 24,
                {"id": "client@example.com"},
                "google/gemini-2.5-flash-lite",
            ],
        }
    )
    serialized = json.dumps(coverage, ensure_ascii=False)
    blocked_rows = [row for row in coverage["coverage_rows"] if row["coverage_status"] == "blocked"]

    assert coverage["status"] == "blocked"
    assert coverage["summary"]["blocked_count"] == 2
    assert len(blocked_rows) == 2
    assert coverage["privacy_boundary"]["raw_payload_echoed"] is False
    assert coverage["privacy_boundary"]["credentials_included"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_alias_capability_coverage_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/gemini-newapi-alias-capability-coverage")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["summary"]["known_coverage_count"] >= len(GEMINI_MODEL_CATALOG) * 10

    post_response = client.post(
        "/api/v1/maintenance/gemini-newapi-alias-capability-coverage",
        json={"include_catalog_aliases": False, "observed_models": ["yibuapi/google/gemini-3.9-flash-lite"]},
    )
    assert post_response.status_code == 200
    payload = post_response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "review_required"
    assert payload["data"]["summary"]["review_required_count"] == 1


def test_alias_capability_coverage_model_ops_route_is_attached_to_readiness():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import _clear_model_ops_payload_cache, router

    _clear_model_ops_payload_cache()
    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-newapi-alias-capability-coverage")
    assert response.status_code == 200
    packet = response.json()["data"]
    assert packet["id"] == "gemini-newapi-alias-capability-coverage"
    assert packet["summary"]["gateway_called"] is False
    assert packet["summary"]["configuration_written"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["gemini_newapi_alias_capability_coverage"]["summary"]["known_coverage_count"] >= (
        len(GEMINI_MODEL_CATALOG) * 10
    )
    assert "gemini_newapi_alias_capability_coverage" in {
        check["source_key"] for check in models_payload["model_ops_readiness"]["checks"]
    }
