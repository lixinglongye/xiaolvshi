import json
import re

from services.modelops_observed_gateway_model_fit_matrix import ModelOpsObservedGatewayModelFitMatrixService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_observed_gateway_model_fit_matrix_scores_full_gateway_inventory():
    matrix = ModelOpsObservedGatewayModelFitMatrixService().build_matrix(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-flash-lite"},
                    {"id": "google/gemini-2.5-flash"},
                    {"id": "newapi/google/gemini-3.1-flash-lite@latest"},
                    {"id": "publishers/google/models/gemini-2.5-pro:generateContent"},
                    {"id": "yibuapi/google/gemini-2.5-flash-image"},
                ]
            }
        }
    )
    task_rows = {row["task"]: row for row in matrix["task_fit_rows"]}
    model_rows = {row["canonical_model"]: row for row in matrix["observed_model_rows"]}

    assert matrix["status"] == "review_required"
    assert matrix["summary"]["accepted_observed_model_count"] == 5
    assert matrix["summary"]["cheap_first_covered_count"] == matrix["summary"]["cheap_first_task_count"]
    assert matrix["summary"]["gateway_called"] is False
    assert matrix["summary"]["network_called"] is False
    assert matrix["summary"]["configuration_written"] is False
    assert task_rows["fast"]["gateway_fit_status"] == "cheap_fit"
    assert task_rows["classification"]["cheapest_canonical_model"] == "gemini-2.5-flash-lite"
    assert task_rows["ocr"]["configured_default_observed"] is True
    assert task_rows["review"]["gateway_fit_status"] == "balanced_fit"
    assert task_rows["agentic"]["cheapest_canonical_model"] == "gemini-3.1-flash-lite"
    assert task_rows["pdf"]["gateway_fit_status"] == "premium_exception_fit"
    assert task_rows["image"]["gateway_fit_status"] == "media_fit"
    assert model_rows["gemini-2.5-flash-lite"]["default_allowed_without_review"] is True
    assert model_rows["gemini-2.5-pro"]["explicit_review_required"] is True
    assert "premium_model" in model_rows["gemini-2.5-pro"]["reason_codes"]


def test_observed_gateway_model_fit_matrix_marks_sparse_inventory_gaps():
    matrix = ModelOpsObservedGatewayModelFitMatrixService().build_matrix(
        {
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                "newapi/google/gemini-3.9-flash-lite",
                "vendor/other-model",
            ]
        }
    )
    task_rows = {row["task"]: row for row in matrix["task_fit_rows"]}

    assert matrix["status"] == "review_required"
    assert matrix["summary"]["unknown_gemini_like_count"] == 1
    assert matrix["summary"]["external_model_count"] == 1
    assert task_rows["fast"]["gateway_fit_status"] == "cheap_fit"
    assert task_rows["review"]["gateway_fit_status"] == "missing"
    assert task_rows["agentic"]["gateway_fit_status"] == "missing"
    assert "task-capability-coverage" in matrix["warning_check_ids"]
    assert "review-only-model-boundary" in matrix["warning_check_ids"]


def test_observed_gateway_model_fit_matrix_blocks_missing_high_frequency_cheap_fit():
    matrix = ModelOpsObservedGatewayModelFitMatrixService().build_matrix(
        {
            "observed_models": [
                "models/gemini-2.5-pro",
            ]
        }
    )

    assert matrix["status"] == "blocked"
    assert "high-frequency-cheap-fit" in matrix["blocking_check_ids"]
    assert matrix["summary"]["cheap_first_covered_count"] == 0


def test_observed_gateway_model_fit_matrix_rejects_sensitive_values_without_echoing():
    matrix = ModelOpsObservedGatewayModelFitMatrixService().build_matrix(
        {
            "observed_models": [
                "s" + "k-" + "a" * 24,
                {"id": "client@example.com"},
                "models/gemini-2.5-flash-lite",
            ]
        }
    )
    serialized = json.dumps(matrix, ensure_ascii=False)

    assert matrix["status"] == "blocked"
    assert matrix["summary"]["rejected_sensitive_observed_model_count"] == 2
    assert "sensitive-observed-model-values" in matrix["blocking_check_ids"]
    assert matrix["privacy_boundary"]["raw_payload_echoed"] is False
    assert matrix["privacy_boundary"]["credentials_included"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_observed_gateway_model_fit_matrix_aihub_route_is_attached_to_readiness():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import _clear_model_ops_payload_cache, router

    _clear_model_ops_payload_cache()
    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/observed-gateway-model-fit-matrix")
    assert get_response.status_code == 200
    packet = get_response.json()["data"]
    assert packet["id"] == "modelops-observed-gateway-model-fit-matrix"
    assert packet["summary"]["gateway_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/observed-gateway-model-fit-matrix",
        json={"observed_models": ["models/gemini-2.5-flash-lite"]},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["summary"]["accepted_observed_model_count"] == 1

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["observed_gateway_model_fit_matrix"]["id"] == "modelops-observed-gateway-model-fit-matrix"
    assert "observed_gateway_model_fit_matrix" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
