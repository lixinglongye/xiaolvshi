import json

from services import model_catalog
from services.gemini_newapi_cheap_first_policy import GeminiNewapiCheapFirstPolicyService
from services.gemini_newapi_model_selector import GeminiNewapiModelSelectorService
from services.model_catalog import ModelProfile
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_price_refresh_monitor import ModelPriceRefreshMonitorService


def _future_flash_lite(*, status: str = "stable", input_price: float = 0.05, output_price: float = 0.20) -> ModelProfile:
    return ModelProfile(
        id="gemini-4.0-flash-lite",
        provider="google",
        family="gemini",
        cost_tier="lowest",
        latency_tier="fastest",
        capabilities=("text", "vision", "json", "ocr", "classification", "grounding", "agentic"),
        best_for=("routing", "ocr", "classification", "agentic-routing"),
        input_usd_per_million_tokens=input_price,
        output_usd_per_million_tokens=output_price,
        status=status,
        context_window_tokens=1_000_000,
    )


def test_default_candidate_selector_preserves_current_low_cost_defaults():
    selector = ModelDefaultCandidateSelectorService()

    assert selector.recommended_model_for_task("fast") == "gemini-2.5-flash-lite"
    assert selector.recommended_model_for_task("ocr") == "gemini-2.5-flash-lite"
    assert selector.recommended_model_for_task("classification") == "gemini-2.5-flash-lite"
    assert selector.recommended_model_for_task("review") == "gemini-2.5-flash"
    assert selector.recommended_model_for_task("agentic") == "gemini-3.1-flash-lite"
    assert selector.recommended_model_for_task("grounded-research") == "gemini-3.1-flash-lite"
    assert selector.recommended_model_for_task("image") == "gemini-2.5-flash-image"

    fast = selector.recommendation("fast")
    fast_ladder = selector.default_ladder_for_task("fast", limit=3)
    selector_payload = selector.build_selector()

    assert fast["eligible_candidate_count"] >= 1
    assert fast["review_only_candidate_count"] >= 1
    assert fast_ladder[0]["model"] == "gemini-2.5-flash-lite"
    assert fast_ladder[0]["candidate_stage"] == "default_eligible"
    assert fast_ladder[0]["review_required"] is False
    assert fast_ladder[0]["promotion_blockers"] == []
    assert fast_ladder[1]["candidate_stage"] == "review_only"
    assert fast_ladder[1]["review_required"] is True
    assert any(blocker.startswith("cost-tier:") for blocker in fast_ladder[1]["promotion_blockers"])
    assert selector_payload["summary"]["default_eligible_candidate_count"] >= fast["eligible_candidate_count"]
    assert selector_payload["summary"]["review_only_candidate_count"] >= fast["review_only_candidate_count"]

    image_ladder = selector.default_ladder_for_task("image")
    assert [item["model"] for item in image_ladder[:2]] == [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image",
    ]
    assert selector.recommended_model_for_task("audio") == "qwen3-tts-flash"
    assert selector.recommended_model_for_task("video") == "wan2.6-t2v"
    assert selector.recommended_model_for_task("transcription") == "scribe_v2"
    audio_ladder = selector.default_ladder_for_task("tts", limit=3)
    assert audio_ladder[0]["model"] == "gemini-2.5-flash-preview-tts"
    assert audio_ladder[0]["candidate_stage"] == "review_only"
    assert audio_ladder[0]["review_required"] is True
    assert "lifecycle:preview" in audio_ladder[0]["promotion_blockers"]
    assert "pricing:missing" in audio_ladder[0]["promotion_blockers"]
    video_ladder = selector.default_ladder_for_task("image-to-video", limit=2)
    assert video_ladder[0]["model"] == "veo-3.1-lite-generate-preview"
    assert video_ladder[0]["pricing_status"] == "missing"
    assert "pricing:missing" in video_ladder[0]["promotion_blockers"]
    transcription_ladder = selector.default_ladder_for_task("speech-to-text", limit=2)
    assert transcription_ladder[0]["model"] == "gemini-2.5-flash-native-audio-preview-12-2025"
    assert "lifecycle:preview" in transcription_ladder[0]["promotion_blockers"]
    assert selector.build_selector()["privacy_boundary"]["gateway_called"] is False


def test_default_candidate_selector_promotes_catalog_cheapest_stable_flash_lite(monkeypatch):
    future_model = _future_flash_lite()
    monkeypatch.setattr(
        model_catalog,
        "GEMINI_MODEL_CATALOG",
        (future_model, *model_catalog.GEMINI_MODEL_CATALOG),
    )

    selector = ModelDefaultCandidateSelectorService()

    assert selector.recommended_model_for_task("fast") == "gemini-4.0-flash-lite"
    assert selector.recommended_model_for_task("ocr") == "gemini-4.0-flash-lite"
    assert selector.recommended_model_for_task("classification") == "gemini-4.0-flash-lite"
    assert selector.recommended_model_for_task("agentic") == "gemini-4.0-flash-lite"

    policy = GeminiNewapiCheapFirstPolicyService(candidate_selector=selector).build_policy()
    defaults = {item["task"]: item for item in policy["default_model_recommendations"]}
    assert defaults["fast"]["recommended_model"] == "gemini-4.0-flash-lite"
    assert policy["summary"]["high_frequency_default_model"] == "gemini-4.0-flash-lite"

    model_selector = GeminiNewapiModelSelectorService(candidate_selector=selector).build_selector({"tasks": ["fast"]})
    assert model_selector["task_recommendations"][0]["escalation_chain"][0] == "gemini-4.0-flash-lite"


def test_default_candidate_selector_supports_in_memory_catalog_injection():
    future_model = _future_flash_lite()

    selector = ModelDefaultCandidateSelectorService(catalog=(future_model, *model_catalog.GEMINI_MODEL_CATALOG))

    assert selector.recommended_model_for_task("fast") == "gemini-4.0-flash-lite"
    assert selector.recommended_model_for_task("ocr") == "gemini-4.0-flash-lite"
    assert selector.build_selector()["summary"]["catalog_model_count"] == len(model_catalog.GEMINI_MODEL_CATALOG) + 1
    matrix = ModelCapabilityMatrixService(candidate_selector=selector, catalog=selector.catalog).build_matrix()
    fast = {row["task"]: row for row in matrix["tasks"]}["fast"]
    assert matrix["coverage"]["catalog_model_count"] == len(model_catalog.GEMINI_MODEL_CATALOG) + 1
    assert fast["recommended_model"] == "gemini-4.0-flash-lite"


def test_default_candidate_selector_keeps_preview_and_unpriced_models_out_of_defaults(monkeypatch):
    preview_model = _future_flash_lite(status="preview", input_price=0.01, output_price=0.01)
    unpriced_model = _future_flash_lite(input_price=0.01, output_price=0.01)
    unpriced_model = ModelProfile(
        id="gemini-4.0-flash-lite-unpriced",
        provider=unpriced_model.provider,
        family=unpriced_model.family,
        cost_tier=unpriced_model.cost_tier,
        latency_tier=unpriced_model.latency_tier,
        capabilities=unpriced_model.capabilities,
        best_for=unpriced_model.best_for,
        status="stable",
    )
    monkeypatch.setattr(
        model_catalog,
        "GEMINI_MODEL_CATALOG",
        (preview_model, unpriced_model, *model_catalog.GEMINI_MODEL_CATALOG),
    )

    recommendation = ModelDefaultCandidateSelectorService().recommendation("fast")
    rows = {item["model_id"]: item for item in recommendation["candidates"]}

    assert recommendation["selected_model"] == "gemini-2.5-flash-lite"
    assert rows["gemini-4.0-flash-lite"]["default_eligible"] is False
    assert rows["gemini-4.0-flash-lite"]["catalog_status"] == "preview"
    assert rows["gemini-4.0-flash-lite"]["candidate_stage"] == "review_only"
    assert rows["gemini-4.0-flash-lite"]["review_required"] is True
    assert "lifecycle:preview" in rows["gemini-4.0-flash-lite"]["promotion_blockers"]
    assert rows["gemini-4.0-flash-lite-unpriced"]["default_eligible"] is False
    assert rows["gemini-4.0-flash-lite-unpriced"]["pricing_status"] == "missing"
    assert rows["gemini-4.0-flash-lite-unpriced"]["candidate_stage"] == "review_only"
    assert rows["gemini-4.0-flash-lite-unpriced"]["review_required"] is True
    assert "pricing:missing" in rows["gemini-4.0-flash-lite-unpriced"]["promotion_blockers"]

    ladder = ModelDefaultCandidateSelectorService().default_ladder_for_task("fast", limit=20)
    ladder_rows = {row["model"]: row for row in ladder}
    assert ladder_rows["gemini-4.0-flash-lite"]["role"] == "explicit preview review"
    assert ladder_rows["gemini-4.0-flash-lite-unpriced"]["role"] == "explicit price review"


def test_default_candidate_selector_accepts_task_subset_without_echoing_raw_values():
    secret = "s" + "k-" + "a" * 24
    selector = ModelDefaultCandidateSelectorService().build_selector(
        {"tasks": ["fast", secret, "ocr", "fast", {"raw": "ignored"}]}
    )
    serialized = json.dumps(selector, ensure_ascii=False)
    tasks = {item["task"] for item in selector["recommendations"]}

    assert selector["status"] == "ready"
    assert tasks == {"fast", "ocr", "review"}
    assert selector["summary"]["submitted_task_count"] == 3
    assert selector["summary"]["raw_payload_echoed"] is False
    assert selector["privacy_boundary"]["credentials_included"] is False
    assert secret not in serialized


def test_model_default_candidate_selector_routes_are_available():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router
    from routers.maintenance import router as maintenance_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    app.include_router(maintenance_router)
    client = testclient.TestClient(app)

    maintenance_response = client.get("/api/v1/maintenance/model-default-candidate-selector")
    assert maintenance_response.status_code == 200
    assert maintenance_response.json()["data"]["id"] == "model-default-candidate-selector"

    aihub_response = client.post(
        "/api/v1/aihub/models/model-default-candidate-selector",
        json={"tasks": ["fast", "document-generation"]},
    )
    assert aihub_response.status_code == 200
    payload = aihub_response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["task_count"] == 2
    assert payload["data"]["summary"]["raw_payload_echoed"] is False
    assert {item["task"] for item in payload["data"]["recommendations"]} == {"fast", "document-generation"}


def test_price_refresh_monitor_uses_catalog_derived_recommendation_for_drift(monkeypatch):
    future_model = _future_flash_lite()
    monkeypatch.setattr(
        model_catalog,
        "GEMINI_MODEL_CATALOG",
        (future_model, *model_catalog.GEMINI_MODEL_CATALOG),
    )
    monkeypatch.setattr(model_catalog.settings, "app_ai_fast_model", "gemini-2.5-pro", raising=False)

    payload = ModelPriceRefreshMonitorService().build_monitor()
    high_frequency = {item["id"]: item for item in payload["checks"]}["high-frequency-default-price-tier"]
    fast = {row["task"]: row for row in high_frequency["rows"]}["fast"]

    assert payload["status"] == "fail"
    assert fast["recommended_model"] == "gemini-4.0-flash-lite"
