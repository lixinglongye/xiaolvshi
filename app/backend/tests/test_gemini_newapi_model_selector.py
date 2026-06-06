import json
import re

from services.gemini_newapi_model_selector import GeminiNewapiModelSelectorService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_model_selector_defaults_to_cheap_first_task_routes():
    selector = GeminiNewapiModelSelectorService().build_selector()
    recommendations = {item["task"]: item for item in selector["task_recommendations"]}

    assert selector["status"] == "ready"
    assert selector["summary"]["task_count"] >= 7
    assert selector["summary"]["cheap_first_ready_count"] >= 4
    assert selector["summary"]["premium_exception_count"] >= 1
    assert recommendations["fast"]["selected_model"] == "gemini-2.5-flash-lite"
    assert recommendations["classification"]["decision"] == "cheap_first_ready"
    assert recommendations["ocr"]["cost_tier"] == "lowest"
    assert recommendations["review"]["decision"] == "balanced_after_precheck"
    assert recommendations["large-pdf"]["decision"] == "premium_exception_required"
    assert selector["privacy_boundary"]["raw_model_output_included"] is False


def test_model_selector_normalizes_newapi_prefixes_and_flags_unknown_gemini_like():
    selector = GeminiNewapiModelSelectorService().build_selector(
        {
            "tasks": ["fast", "review"],
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                "google/gemini-2.5-flash",
                "google:gemini-3.2-flash-lite",
            "vendor/other-model",
            ],
        }
    )
    reviews = {item["raw_model"]: item for item in selector["observed_model_reviews"]}

    assert selector["status"] == "needs_catalog_review"
    assert reviews["models/gemini-2.5-flash-lite"]["canonical_model"] == "gemini-2.5-flash-lite"
    assert reviews["models/gemini-2.5-flash-lite"]["default_allowed_for_high_frequency"] is True
    assert reviews["google/gemini-2.5-flash"]["canonical_model"] == "gemini-2.5-flash"
    assert reviews["google:gemini-3.2-flash-lite"]["status"] == "catalog_review"
    assert reviews["google:gemini-3.2-flash-lite"]["default_allowed_for_high_frequency"] is False
    assert reviews["vendor/other-model"]["status"] == "external_model"
    assert selector["summary"]["catalog_review_count"] == 1
    assert selector["summary"]["unknown_model_count"] == 2


def test_model_selector_extracts_observed_models_from_wrapped_model_lists():
    selector = GeminiNewapiModelSelectorService().build_selector(
        {
            "tasks": ["fast"],
            "models_response": {
                "models": [
                    {"name": "models/gemini-2.5-flash-lite"},
                    {"model_id": "newapi/google/gemini-3.2-flash-lite"},
                ]
            },
            "result": {"items": [{"id": "vendor/other-model"}]},
        }
    )
    reviews = {item["raw_model"]: item for item in selector["observed_model_reviews"]}

    assert selector["status"] == "needs_catalog_review"
    assert selector["summary"]["observed_model_candidate_count"] == 3
    assert selector["summary"]["accepted_observed_model_count"] == 3
    assert selector["source_summaries"]["observed_model_extraction"]["extractor_version"] == (
        "gemini-newapi-observed-model-extraction-v1"
    )
    assert reviews["models/gemini-2.5-flash-lite"]["status"] == "catalog_known"
    assert reviews["newapi/google/gemini-3.2-flash-lite"]["status"] == "catalog_review"
    assert reviews["vendor/other-model"]["status"] == "external_model"


def test_model_selector_blocks_premium_high_frequency_explicit_default():
    selector = GeminiNewapiModelSelectorService().build_selector(
        {
            "tasks": ["fast"],
            "explicit_models": {"fast": "google/gemini-2.5-pro"},
        }
    )
    recommendation = selector["task_recommendations"][0]

    assert recommendation["task"] == "fast"
    assert recommendation["canonical_model"] == "gemini-2.5-pro"
    assert recommendation["premium_exception"] is True
    assert recommendation["decision"] == "premium_exception_required"
    assert any("High-frequency tasks" in warning for warning in recommendation["warnings"])


def test_model_selector_uses_catalog_derived_ladders_for_agentic_and_image_tasks():
    selector = GeminiNewapiModelSelectorService().build_selector({"tasks": ["agentic", "grounded-research", "image"]})
    recommendations = {item["task"]: item for item in selector["task_recommendations"]}

    assert recommendations["agentic"]["selected_model"] == "gemini-3.1-flash-lite"
    assert recommendations["agentic"]["escalation_chain"][:2] == [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ]
    assert recommendations["grounded-research"]["escalation_chain"][0] == "gemini-3.1-flash-lite"
    assert recommendations["image"]["selected_model"] == "gemini-2.5-flash-image"
    assert recommendations["image"]["escalation_chain"][:2] == [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image",
    ]


def test_model_selector_redacts_sensitive_inputs_from_output():
    selector = GeminiNewapiModelSelectorService().build_selector(
        {
            "tasks": ["fast", "client@example.com"],
            "observed_models": ["s" + "k-" + "a" * 24, "gemini-2.5-flash-lite"],
            "explicit_models": {"fast": "s" + "k-" + "b" * 24},
        }
    )
    serialized = json.dumps(selector, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert selector["summary"]["raw_payload_echoed"] is False
    assert selector["privacy_boundary"]["credential_material_included"] is False
    assert selector["task_recommendations"][0]["selected_model"] == "gemini-2.5-flash-lite"


def test_gemini_newapi_model_selector_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/gemini-newapi-model-selector")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["cheap_first_ready_count"] >= 4

    response = client.post(
        "/api/v1/maintenance/gemini-newapi-model-selector",
        json={"observed_models": ["google/gemini-3.2-flash-lite"], "tasks": ["fast", "review"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "needs_catalog_review"
