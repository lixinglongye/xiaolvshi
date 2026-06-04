import json
import re

from services.gemini_newapi_selector_replay import GeminiNewapiSelectorReplayService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_selector_replay_passes_default_scenarios():
    replay = GeminiNewapiSelectorReplayService().run_replay()
    scenarios = {item["id"]: item for item in replay["replay_results"]}
    expected_scenario_ids = {
        "fast-default-flash-lite",
        "classification-default-flash-lite",
        "ocr-default-flash-lite",
        "review-balanced-after-precheck",
        "document-generation-balanced-after-precheck",
        "large-pdf-premium-exception",
        "final-review-premium-exception",
        "unknown-gemini-like-catalog-review",
        "fast-explicit-pro-premium-exception",
    }

    assert replay["status"] == "pass"
    assert set(scenarios) == expected_scenario_ids
    assert replay["summary"]["scenario_count"] == len(expected_scenario_ids)
    assert replay["summary"]["fail_count"] == 0
    assert replay["summary"]["cheap_first_pass_count"] >= 3
    assert replay["summary"]["premium_exception_count"] >= 3
    assert replay["summary"]["catalog_review_count"] >= 1
    assert scenarios["fast-default-flash-lite"]["actual"]["selected_model"] == "gemini-2.5-flash-lite"
    assert scenarios["review-balanced-after-precheck"]["actual"]["decision"] == "balanced_after_precheck"
    assert scenarios["large-pdf-premium-exception"]["actual"]["decision"] == "premium_exception_required"
    assert scenarios["final-review-premium-exception"]["actual"]["decision"] == "premium_exception_required"
    assert any(
        "High-frequency tasks" in warning
        for warning in scenarios["fast-explicit-pro-premium-exception"]["actual"]["warnings"]
    )
    assert replay["privacy_boundary"]["newapi_called"] is False


def test_selector_replay_flags_submitted_premium_fast_route():
    replay = GeminiNewapiSelectorReplayService().run_replay(
        {
            "scenarios": [
                {
                    "id": "fast-pro-request",
                    "task": "fast",
                    "explicit_model": "google/gemini-2.5-pro",
                    "expected_decision": "cheap_first_ready",
                    "max_cost_tier": "lowest",
                    "expected_selector_status": "ready",
                    "rationale": "Premium fast route should fail if expected as cheap-first.",
                }
            ]
        }
    )
    result = replay["replay_results"][0]

    assert replay["status"] == "fail"
    assert result["id"] == "fast-pro-request"
    assert result["actual"]["decision"] == "premium_exception_required"
    assert {check["id"] for check in result["checks"] if check["status"] == "fail"} >= {
        "decision",
        "cost-tier",
        "premium-exception",
    }


def test_selector_replay_keeps_sensitive_payload_out_of_output():
    replay = GeminiNewapiSelectorReplayService().run_replay(
        {
            "scenarios": [
                {
                    "id": "client@example.com",
                    "task": "fast",
                    "explicit_model": "s" + "k-" + "a" * 24,
                    "observed_models": ["s" + "k-" + "b" * 24],
                    "expected_decision": "cheap_first_ready",
                    "max_cost_tier": "lowest",
                    "expected_selector_status": "ready",
                    "rationale": "secret raw client text",
                }
            ]
        }
    )
    serialized = json.dumps(replay, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert replay["summary"]["raw_payload_echoed"] is False
    assert replay["privacy_boundary"]["prompts_included"] is False
    assert replay["replay_results"][0]["id"].startswith("submitted-selector-scenario")


def test_selector_replay_does_not_echo_submitted_legal_rationale():
    legal_rationale = "张三主张合同履行中存在付款争议，需要先保持低成本模型路径。"

    replay = GeminiNewapiSelectorReplayService().run_replay(
        {
            "scenarios": [
                {
                    "id": "submitted-fast-route",
                    "task": "fast",
                    "expected_decision": "cheap_first_ready",
                    "max_cost_tier": "lowest",
                    "expected_selector_status": "ready",
                    "rationale": legal_rationale,
                }
            ]
        }
    )
    serialized = json.dumps(replay, ensure_ascii=False)

    assert legal_rationale not in serialized
    assert replay["replay_results"][0]["scenario"]["rationale"] == (
        "Submitted metadata-only selector scenario; maintainer rationale is not echoed."
    )
    assert replay["summary"]["raw_payload_echoed"] is False


def test_gemini_newapi_selector_replay_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/gemini-newapi-selector-replay")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["status"] == "pass"

    response = client.post(
        "/api/v1/maintenance/gemini-newapi-selector-replay",
        json={
            "scenarios": [
                {
                    "id": "unknown-gemini",
                    "task": "fast",
                    "observed_models": ["google/gemini-3.2-flash-lite"],
                    "expected_decision": "cheap_first_ready",
                    "max_cost_tier": "lowest",
                    "expected_selector_status": "needs_catalog_review",
                }
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
