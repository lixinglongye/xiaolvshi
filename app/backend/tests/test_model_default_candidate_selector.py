from services import model_catalog
from services.gemini_newapi_cheap_first_policy import GeminiNewapiCheapFirstPolicyService
from services.gemini_newapi_model_selector import GeminiNewapiModelSelectorService
from services.model_catalog import ModelProfile
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
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

    image_ladder = selector.default_ladder_for_task("image")
    assert [item["model"] for item in image_ladder[:2]] == [
        "gemini-2.5-flash-image",
        "gemini-3.1-flash-image",
    ]
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
    assert rows["gemini-4.0-flash-lite-unpriced"]["default_eligible"] is False
    assert rows["gemini-4.0-flash-lite-unpriced"]["pricing_status"] == "missing"


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
