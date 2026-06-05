import json
import re

from services.model_ops_gemini_default_change_review import ModelOpsGeminiDefaultChangeReviewService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_gemini_default_change_review_accepts_current_agentic_defaults():
    review = ModelOpsGeminiDefaultChangeReviewService().build_review()
    rows = {row["task"]: row for row in review["proposal_rows"]}

    assert review["status"] == "ready"
    assert review["summary"]["proposal_count"] == 2
    assert review["summary"]["configuration_written"] is False
    assert review["summary"]["gateway_called"] is False
    assert review["summary"]["network_called"] is False
    assert rows["agentic"]["review_status"] == "ready"
    assert rows["agentic"]["env_var"] == "APP_AI_AGENTIC_MODEL"
    assert rows["agentic"]["proposed_model"] == "gemini-3.1-flash-lite"
    assert rows["agentic"]["reason_codes"] == ["proposal-ready"]
    assert rows["grounded-research"]["env_var"] == "APP_AI_GROUNDED_RESEARCH_MODEL"
    assert review["privacy_boundary"]["real_env_read"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(review, ensure_ascii=False))


def test_gemini_default_change_review_requires_review_for_preview_premium_exception():
    review = ModelOpsGeminiDefaultChangeReviewService().build_review(
        {
            "proposed_changes": [
                {
                    "task": "grounded-research",
                    "env_var": "APP_AI_GROUNDED_RESEARCH_MODEL",
                    "current_model": "gemini-3.1-flash-lite",
                    "proposed_model": "gemini-3.1-pro-preview",
                    "review_note": "maintainer metadata review only",
                }
            ]
        }
    )
    row = review["proposal_rows"][0]

    assert review["status"] == "review_required"
    assert row["review_status"] == "review_required"
    assert row["premium_exception"] is True
    assert "lifecycle-preview" in row["reason_codes"]
    assert "over-task-cost-budget" in row["reason_codes"]
    assert "manual-premium-exception-review" in row["reason_codes"]
    assert row["release_action"] == "require_maintainer_review_before_env_change"


def test_gemini_default_change_review_blocks_non_gemini_and_redacts_sensitive_notes():
    review = ModelOpsGeminiDefaultChangeReviewService().build_review(
        {
            "proposed_changes": [
                {
                    "task": "fast",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "proposed_model": "not-a-gemini-model",
                    "review_note": "contains authorization and email-like data",
                }
            ]
        }
    )
    row = review["proposal_rows"][0]

    assert review["status"] == "blocked"
    assert row["review_status"] == "blocked"
    assert row["proposed_model_known"] is False
    assert "non-gemini-or-unknown-model" in row["reason_codes"]
    assert row["review_note"] == "redacted-sensitive-review-note"
    assert review["blocking_proposal_ids"] == ["gemini-default-change-review-fast"]
    serialized = json.dumps(review, ensure_ascii=False)
    assert "email-like" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_default_change_review_route_and_models_payload_include_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-default-change-review")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["status"] == "ready"
    assert route_payload["data"]["summary"]["configuration_written"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/gemini-default-change-review",
        json={
            "proposed_changes": [
                {
                    "task": "fast",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "proposed_model": "gemini-2.5-flash",
                }
            ]
        },
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["gemini_default_change_review"]["status"] == "ready"
    assert any(
        check["source_key"] == "gemini_default_change_review"
        for check in payload["model_ops_readiness"]["checks"]
    )
