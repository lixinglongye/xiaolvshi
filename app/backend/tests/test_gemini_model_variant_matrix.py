import json
import re

from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_gemini_model_variant_matrix_marks_cheap_first_and_exception_roles():
    matrix = GeminiModelVariantMatrixService().build_matrix()
    rows = {row["model_id"]: row for row in matrix["model_rows"]}
    families = {row["family"]: row for row in matrix["family_rows"]}

    assert matrix["status"] == "review_required"
    assert matrix["summary"]["catalog_model_count"] >= 8
    assert matrix["summary"]["high_frequency_default_allowed_count"] >= 1
    assert matrix["summary"]["cheap_first_default_model"] == "gemini-2.5-flash-lite"
    assert rows["gemini-2.5-flash-lite"]["route_role"] == "cheap_first_default"
    assert rows["gemini-2.5-flash-lite"]["high_frequency_default_allowed"] is True
    assert rows["gemini-2.5-flash"]["route_role"] == "balanced_retry"
    assert rows["gemini-2.5-pro"]["premium_exception_required"] is True
    assert rows["gemini-3.1-pro-preview"]["catalog_status"] == "preview"
    assert rows["gemini-3.1-pro-preview"]["route_role"] == "premium_exception"
    assert rows["gemini-2.5-flash-image"]["media_route_only"] is True
    assert rows["gemini-2.5-flash-lite"]["supported_request_shapes"] == [
        "gemini-2.5-flash-lite",
        "models/gemini-2.5-flash-lite",
        "google/gemini-2.5-flash-lite",
        "google:gemini-2.5-flash-lite",
    ]
    assert families["gemini-flash-lite"]["high_frequency_default_allowed"] is True
    assert families["gemini-pro"]["high_frequency_default_allowed"] is False
    assert matrix["privacy_boundary"]["gateway_called"] is False


def test_gemini_model_variant_matrix_reviews_unknown_observed_models_without_echoing_secrets():
    secret = "s" + "k-" + ("V" * 24)
    matrix = GeminiModelVariantMatrixService().build_matrix(
        {
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                "google/gemini-3.2-flash-lite",
                {"model": "vendor/not-gemini"},
                secret,
                "client@example.com",
            ]
        }
    )
    serialized = json.dumps(matrix, ensure_ascii=False)
    reviews = {row["raw_model"]: row for row in matrix["observed_model_reviews"]}

    assert matrix["status"] == "review_required"
    assert matrix["summary"]["observed_model_count"] == 3
    assert matrix["summary"]["catalog_review_count"] == 1
    assert matrix["summary"]["accepted_observed_model_count"] == 3
    assert matrix["source_summaries"]["observed_model_extraction"]["source_fields"] == ["observed_models"]
    assert matrix["source_summaries"]["observed_model_extraction"]["raw_payload_echoed"] is False
    assert reviews["models/gemini-2.5-flash-lite"]["status"] == "catalog_known"
    assert reviews["models/gemini-2.5-flash-lite"]["default_allowed_for_high_frequency"] is True
    assert reviews["google/gemini-3.2-flash-lite"]["status"] == "catalog_review"
    assert reviews["google/gemini-3.2-flash-lite"]["default_allowed_for_high_frequency"] is False
    assert reviews["vendor/not-gemini"]["status"] == "external_model"
    assert "observed-gemini-like-catalog-review" in matrix["warning_check_ids"]
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_model_variant_matrix_extracts_openai_compatible_model_list_without_echoing_payload():
    secret = "s" + "k-" + ("M" * 24)
    matrix = GeminiModelVariantMatrixService().build_matrix(
        {
            "models_response": {
                "object": "list",
                "data": [
                    {"id": "models/gemini-2.5-flash-lite", "object": "model"},
                    {"id": "google/gemini-3.2-flash-lite", "created": 0},
                    {"id": "vendor/not-gemini"},
                    {"id": secret},
                    {"name": "client@example.com"},
                ],
            },
            "model_ids": ["models/gemini-2.5-flash-lite"],
            "gateway_models": [{"model_id": "google/gemini-2.5-flash"}],
        }
    )
    serialized = json.dumps(matrix, ensure_ascii=False)
    reviews = {row["raw_model"]: row for row in matrix["observed_model_reviews"]}
    extraction = matrix["source_summaries"]["observed_model_extraction"]

    assert matrix["summary"]["observed_model_count"] == 4
    assert matrix["summary"]["catalog_review_count"] == 1
    assert matrix["summary"]["observed_model_candidate_count"] == 7
    assert matrix["summary"]["dropped_observed_model_count"] == 3
    assert extraction["source_fields"] == ["model_ids", "gateway_models", "models_response.data"]
    assert extraction["raw_payload_echoed"] is False
    assert reviews["models/gemini-2.5-flash-lite"]["status"] == "catalog_known"
    assert reviews["google/gemini-2.5-flash"]["status"] == "catalog_known"
    assert reviews["google/gemini-3.2-flash-lite"]["status"] == "catalog_review"
    assert reviews["vendor/not-gemini"]["status"] == "external_model"
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "object" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_model_variant_matrix_accepts_direct_data_model_list_shape():
    matrix = GeminiModelVariantMatrixService().build_matrix(
        {"data": [{"id": "models/gemini-2.5-flash-lite"}, {"id": "google/gemini-3.2-flash-lite"}]}
    )

    assert matrix["summary"]["observed_model_count"] == 2
    assert matrix["summary"]["catalog_review_count"] == 1
    assert matrix["source_summaries"]["observed_model_extraction"]["source_fields"] == ["data"]


def test_gemini_model_variant_matrix_route_returns_metadata_only_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/gemini-variant-matrix")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["summary"]["catalog_model_count"] >= 8

    post_response = client.post(
        "/api/v1/aihub/models/gemini-variant-matrix",
        json={"models_response": {"data": [{"id": "google/gemini-3.2-flash-lite"}]}},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["summary"]["catalog_review_count"] == 1
    assert post_response.json()["data"]["source_summaries"]["observed_model_extraction"]["source_fields"] == [
        "models_response.data"
    ]


def test_model_ops_route_includes_gemini_variant_matrix_readiness_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["gemini_variant_matrix"]["summary"]["catalog_model_count"] >= 8
    assert any(
        check["source_key"] == "gemini_variant_matrix"
        for check in payload["model_ops_readiness"]["checks"]
    )
