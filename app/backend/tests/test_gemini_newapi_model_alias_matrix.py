import json
import re

from services.gemini_newapi_model_alias_matrix import GeminiNewapiModelAliasMatrixService
from services.model_catalog import GEMINI_MODEL_CATALOG


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+"
)


def test_alias_matrix_defaults_cover_catalog_prefixes_and_cheap_first_flags():
    evidence = GeminiNewapiModelAliasMatrixService().build_matrix()
    rows = {(row["alias_model"], row["canonical_model"]): row for row in evidence["alias_rows"]}

    flash_lite = rows[("yibu/gemini-2.5-flash-lite", "gemini-2.5-flash-lite")]
    nested_flash_lite = rows[("openrouter/google/gemini-2.5-flash-lite", "gemini-2.5-flash-lite")]
    pro = rows[("google/gemini-2.5-pro", "gemini-2.5-pro")]

    assert evidence["status"] == "ready"
    assert evidence["summary"]["catalog_model_count"] == len(GEMINI_MODEL_CATALOG)
    assert evidence["summary"]["known_alias_count"] >= len(GEMINI_MODEL_CATALOG) * 6
    assert evidence["summary"]["raw_payload_echoed"] is False
    assert evidence["summary"]["gateway_called"] is False
    assert evidence["summary"]["credentials_included"] is False
    assert flash_lite["known_catalog_model"] is True
    assert flash_lite["high_frequency_default_allowed"] is True
    assert flash_lite["default_allowed_without_review"] is True
    assert nested_flash_lite["alias_shape"] == "nested_google_slash_prefix"
    assert nested_flash_lite["high_frequency_default_allowed"] is True
    assert pro["premium_exception"] is True
    assert pro["default_allowed_without_review"] is False
    assert evidence["privacy_boundary"]["raw_model_output_included"] is False


def test_alias_matrix_reviews_observed_unknowns_without_default_promotion():
    evidence = GeminiNewapiModelAliasMatrixService().build_matrix(
        {
            "include_catalog_aliases": False,
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                "yibu/gemini-3.1-flash-lite",
                "openrouter/google/gemini-2.5-pro",
                "google/gemini-3.2-flash-lite",
                "vendor/other-model",
            ],
        }
    )
    rows = {row["alias_model"]: row for row in evidence["alias_rows"]}

    assert evidence["status"] == "needs_catalog_review"
    assert evidence["summary"]["observed_model_count"] == 5
    assert evidence["summary"]["catalog_review_count"] == 1
    assert evidence["summary"]["external_model_count"] == 1
    assert rows["models/gemini-2.5-flash-lite"]["canonical_model"] == "gemini-2.5-flash-lite"
    assert rows["models/gemini-2.5-flash-lite"]["high_frequency_default_allowed"] is True
    assert rows["yibu/gemini-3.1-flash-lite"]["canonical_model"] == "gemini-3.1-flash-lite"
    assert rows["yibu/gemini-3.1-flash-lite"]["high_frequency_default_allowed"] is True
    assert rows["openrouter/google/gemini-2.5-pro"]["premium_exception"] is True
    assert rows["openrouter/google/gemini-2.5-pro"]["default_allowed_without_review"] is False
    assert rows["google/gemini-3.2-flash-lite"]["alias_status"] == "catalog_review"
    assert rows["google/gemini-3.2-flash-lite"]["default_allowed_without_review"] is False
    assert rows["vendor/other-model"]["alias_status"] == "external_model"
    assert rows["vendor/other-model"]["default_allowed_without_review"] is False


def test_alias_matrix_redacts_sensitive_observed_model_values():
    evidence = GeminiNewapiModelAliasMatrixService().build_matrix(
        {
            "include_catalog_aliases": False,
            "observed_models": [
                "s" + "k-" + "a" * 24,
                "client@example.com",
                {"id": "Bearer " + "b" * 16},
                "gemini-2.5-flash-lite",
            ],
        }
    )
    serialized = json.dumps(evidence, ensure_ascii=False)
    rejected_rows = [row for row in evidence["alias_rows"] if row["alias_status"] == "rejected_sensitive"]

    assert evidence["status"] == "needs_sanitization"
    assert evidence["summary"]["rejected_sensitive_count"] == 3
    assert len(rejected_rows) == 3
    assert not SENSITIVE_PATTERN.search(serialized)
    assert "redacted-sensitive-model-id-1" in serialized
    assert "client@example.com" not in serialized
    assert evidence["summary"]["raw_payload_echoed"] is False
    assert evidence["privacy_boundary"]["credentials_included"] is False


def test_gemini_newapi_model_alias_matrix_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/gemini-newapi-model-alias-matrix")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["known_alias_count"] >= len(GEMINI_MODEL_CATALOG) * 6

    response = client.post(
        "/api/v1/maintenance/gemini-newapi-model-alias-matrix",
        json={"include_catalog_aliases": False, "observed_models": ["google/gemini-3.2-flash-lite"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "needs_catalog_review"
    assert payload["data"]["summary"]["catalog_review_count"] == 1
