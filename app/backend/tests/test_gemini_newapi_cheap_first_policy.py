import re

from services.gemini_newapi_cheap_first_policy import GeminiNewapiCheapFirstPolicyService


SENSITIVE_DATA_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|pass\s*word)",
    re.IGNORECASE,
)


def _policy(observed_models=None) -> dict:
    return GeminiNewapiCheapFirstPolicyService().build_policy(observed_models=observed_models)


def _marker_parts(model_id: str) -> set[str]:
    return {
        part
        for part in model_id.lower().replace("/", "-").replace(":", "-").replace("_", "-").split("-")
        if part
    }


def test_policy_lists_supported_gemini_families_and_newapi_prefixes():
    policy = _policy()
    families = {item["family"]: item for item in policy["supported_gemini_model_families"]}
    examples = {
        item["example"]
        for item in policy["newapi_openai_compatible_prefix_compatibility"]["accepted_prefix_examples"]
    }

    assert policy["status"] == "ready"
    assert {"gemini-flash-lite", "gemini-flash", "gemini-pro", "gemini-image"}.issubset(families)
    assert families["gemini-flash-lite"]["high_frequency_default_allowed"] is True
    assert families["gemini-pro"]["high_frequency_default_allowed"] is False
    assert policy["newapi_openai_compatible_prefix_compatibility"]["openai_compatible"] is True
    assert "google/gemini-2.5-flash-lite" in examples
    assert "models/gemini-2.5-flash-lite" in examples


def test_high_frequency_tasks_recommend_flash_lite_lowest_defaults():
    policy = _policy()
    defaults = {item["task"]: item for item in policy["default_model_recommendations"]}

    for task in ("fast", "classification", "ocr"):
        recommendation = defaults[task]
        assert recommendation["recommended_model"] == "gemini-2.5-flash-lite"
        assert recommendation["model_family"] == "gemini-flash-lite"
        assert recommendation["cost_tier"] == "lowest"
        assert recommendation["high_frequency"] is True

    high_volume = next(
        item for item in policy["cheap_first_task_ladder"] if item["task_group"] == "high_volume_preflight"
    )
    assert high_volume["ladder"][0]["model"] == "gemini-2.5-flash-lite"
    assert high_volume["ladder"][0]["cost_tier"] == "lowest"


def test_unknown_gemini_like_model_gets_catalog_review_warning():
    policy = _policy(
        observed_models=[
            "google/gemini-3.2-flash-lite",
            "models/gemini-2.5-flash-lite",
            {"id": "vendor/gemini-3-pro-preview"},
        ]
    )
    review = {item["raw_model"]: item for item in policy["observed_model_review"]}

    unknown_flash_lite = review["google/gemini-3.2-flash-lite"]
    known_prefixed = review["models/gemini-2.5-flash-lite"]
    unknown_preview = review["vendor/gemini-3-pro-preview"]

    assert unknown_flash_lite["status"] == "catalog_review"
    assert unknown_flash_lite["severity"] == "warn"
    assert unknown_flash_lite["action"] == "warn_allow_explicit_only"
    assert unknown_flash_lite["default_allowed_for_high_frequency"] is False
    assert "Unknown Gemini-like model" in " ".join(unknown_flash_lite["warnings"])

    assert known_prefixed["status"] == "catalog_known"
    assert known_prefixed["normalized_model"] == "gemini-2.5-flash-lite"
    assert known_prefixed["default_allowed_for_high_frequency"] is True

    assert unknown_preview["status"] == "catalog_review"
    assert unknown_preview["severity"] == "warn"
    assert unknown_preview["default_allowed_for_high_frequency"] is False
    assert "cannot be high-frequency defaults" in " ".join(unknown_preview["warnings"])
    assert policy["summary"]["catalog_review_count"] == 2


def test_pro_preview_and_premium_are_not_high_frequency_defaults():
    policy = _policy()
    blocked_markers = {"pro", "preview", "premium"}
    defaults = policy["default_model_recommendations"]

    for item in defaults:
        if item["task"] in {"fast", "classification", "ocr"}:
            assert _marker_parts(item["recommended_model"]).isdisjoint(blocked_markers)
            assert item["cost_tier"] == "lowest"

    high_frequency_rules = [
        item for item in policy["forbidden_default_rules"] if "high_frequency" in item["id"]
    ]
    assert high_frequency_rules
    assert blocked_markers.issubset(set(high_frequency_rules[0]["blocked_model_markers"]))
    assert set(high_frequency_rules[0]["applies_to_tasks"]).issuperset({"fast", "classification", "ocr"})


def test_policy_payload_has_no_credential_or_contact_patterns():
    payload = _policy(observed_models=["google/gemini-3.2-flash-lite"])

    assert not SENSITIVE_DATA_PATTERN.search(str(payload))
    assert "gateway credentials" in " ".join(payload["privacy_note"])
    assert payload["validation_commands"]


def test_gemini_newapi_cheap_first_policy_route_reviews_observed_models():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/gemini-newapi-cheap-first-policy",
        json={"observed_models": ["google/gemini-3.2-flash-lite"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["observed_model_review"][0]["status"] == "catalog_review"
