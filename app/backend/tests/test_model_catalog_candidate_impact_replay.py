import json
import re

from services.model_catalog_candidate_impact_replay import ModelCatalogCandidateImpactReplayService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", re.IGNORECASE)


def _future_flash_lite_profile() -> dict:
    return {
        "id": "google/gemini-4.0-flash-lite",
        "provider": "google",
        "family": "gemini",
        "cost_tier": "lowest",
        "latency_tier": "fastest",
        "capabilities": ["text", "vision", "json", "ocr", "classification", "grounding", "agentic"],
        "best_for": ["routing", "ocr", "classification", "agentic-routing", "grounded-research"],
        "status": "stable",
        "input_usd_per_million_tokens": 0.05,
        "output_usd_per_million_tokens": 0.2,
        "context_window_tokens": 1_000_000,
    }


def test_candidate_impact_replay_promotes_stable_priced_flash_lite_in_virtual_catalog():
    replay = ModelCatalogCandidateImpactReplayService().build_replay(
        {"candidate_profiles": [_future_flash_lite_profile()]}
    )
    rows = {row["task"]: row for row in replay["task_impact_rows"]}
    candidate = replay["candidate_rows"][0]

    assert replay["status"] == "ready"
    assert replay["summary"]["accepted_virtual_profile_count"] == 1
    assert replay["summary"]["cheap_first_would_promote_count"] >= 4
    assert candidate["model_id"] == "gemini-4.0-flash-lite"
    assert candidate["candidate_status"] == "accepted_for_replay"
    assert candidate["default_candidate_allowed"] is True
    assert rows["fast"]["replay_model"] == "gemini-4.0-flash-lite"
    assert rows["ocr"]["replay_model"] == "gemini-4.0-flash-lite"
    assert rows["classification"]["replay_model"] == "gemini-4.0-flash-lite"
    assert rows["agentic"]["replay_model"] == "gemini-4.0-flash-lite"
    assert rows["grounded-research"]["replay_model"] == "gemini-4.0-flash-lite"
    assert "fast" in replay["selector_delta"]["cheap_first_promoted_tasks"]
    assert replay["summary"]["configuration_written"] is False
    assert replay["summary"]["catalog_file_written"] is False


def test_candidate_impact_replay_keeps_preview_unpriced_and_media_candidates_review_only():
    replay = ModelCatalogCandidateImpactReplayService().build_replay(
        {
            "candidate_profiles": [
                {
                    **_future_flash_lite_profile(),
                    "id": "gemini-4.0-flash-lite-preview",
                    "status": "preview",
                },
                {
                    **_future_flash_lite_profile(),
                    "id": "gemini-4.0-flash-lite-unpriced",
                    "input_usd_per_million_tokens": None,
                    "output_usd_per_million_tokens": None,
                },
                {
                    "id": "gemini-4.0-flash-image",
                    "provider": "google",
                    "family": "gemini",
                    "cost_tier": "low",
                    "latency_tier": "medium",
                    "capabilities": ["image", "image-edit"],
                    "status": "stable",
                    "output_usd_per_image": 0.04,
                },
            ]
        }
    )
    rows = {row["model_id"]: row for row in replay["candidate_rows"]}
    fast = {row["task"]: row for row in replay["task_impact_rows"]}["fast"]

    assert replay["status"] == "review_required"
    assert replay["summary"]["review_required_candidate_count"] == 3
    assert rows["gemini-4.0-flash-lite-preview"]["candidate_status"] == "review_required"
    assert rows["gemini-4.0-flash-lite-unpriced"]["pricing_status"] == "missing"
    assert rows["gemini-4.0-flash-image"]["candidate_status"] == "review_required"
    assert fast["replay_model"] == "gemini-2.5-flash-lite"
    assert fast["selected_model_changed"] is False
    assert replay["summary"]["cheap_first_would_promote_count"] == 0


def test_candidate_impact_replay_uses_candidate_patch_plan_rows_as_review_only_sources():
    replay = ModelCatalogCandidateImpactReplayService().build_replay(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-5.0-flash-lite"},
                    {"id": "openai/gpt-4.1-mini"},
                ]
            }
        }
    )

    assert replay["status"] in {"review_required", "blocked"}
    assert replay["summary"]["candidate_profile_count"] >= 1
    assert any(row["model_id"] == "gemini-5.0-flash-lite" for row in replay["candidate_rows"])
    assert replay["summary"]["configuration_written"] is False
    assert replay["summary"]["gateway_called"] is False


def test_candidate_impact_replay_blocks_and_redacts_sensitive_candidate_input():
    replay = ModelCatalogCandidateImpactReplayService().build_replay(
        {
            "candidate_profiles": [
                {
                    "id": "sk-" + "a" * 24,
                    "capabilities": ["text", "json"],
                    "cost_tier": "lowest",
                    "status": "stable",
                    "input_usd_per_million_tokens": 0.01,
                    "output_usd_per_million_tokens": 0.01,
                }
            ]
        }
    )
    payload_text = json.dumps(replay, ensure_ascii=False)

    assert replay["status"] == "blocked"
    assert replay["summary"]["blocked_candidate_count"] == 1
    assert replay["candidate_rows"][0]["model_id"] == ""
    assert replay["privacy_boundary"]["raw_payload_echoed"] is False
    assert replay["privacy_boundary"]["credentials_included"] is False
    assert replay["claim_boundary"]["automatic_catalog_edit_claimed"] is False
    assert not SENSITIVE_PATTERN.search(payload_text)


def test_candidate_impact_replay_routes_return_replay_and_models_payload_includes_it():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/catalog-candidate-impact-replay")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["summary"]["configuration_written"] is False

    post_response = client.post(
        "/api/v1/aihub/models/catalog-candidate-impact-replay",
        json={"candidate_profiles": [_future_flash_lite_profile()]},
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["success"] is True
    assert post_payload["data"]["summary"]["cheap_first_would_promote_count"] >= 4

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["catalog_candidate_impact_replay"]["summary"]["configuration_written"] is False
    assert "catalog_candidate_impact_replay" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
