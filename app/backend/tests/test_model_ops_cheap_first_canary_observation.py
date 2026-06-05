import json
import re

from services.model_ops_cheap_first_canary_observation import ModelOpsCheapFirstCanaryObservationService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _signals() -> dict:
    return {
        "cheap_first_canary_plan": {
            "status": "ready",
            "canary_steps": [
                {
                    "id": "canary_1_percent-fast",
                    "task": "fast",
                    "phase": "canary_1_percent",
                },
                {
                    "id": "canary_10_percent-fast",
                    "task": "fast",
                    "phase": "canary_10_percent",
                    "step_status": "pending_after_prior_pass",
                },
                {
                    "id": "maintainer_review-review",
                    "task": "review",
                    "phase": "maintainer_review",
                    "step_status": "review_required",
                },
            ],
        }
    }


def test_canary_observation_review_passes_clean_aggregate_metrics():
    payload = {
        "observations": [
            {
                "step_id": "canary_1_percent-fast",
                "task": "fast",
                "phase": "canary_1_percent",
                "request_count": 100,
                "failure_count": 1,
                "over_budget_count": 0,
                "premium_request_count": 0,
                "operator_review_count": 2,
            }
        ]
    }

    review = ModelOpsCheapFirstCanaryObservationService().build_review(payload, _signals())
    row = review["observation_rows"][0]

    assert review["status"] == "pass"
    assert row["status"] == "pass"
    assert row["failure_rate"] == 0.01
    assert row["source_step_found"] is True
    assert review["summary"]["configuration_written"] is False
    assert review["summary"]["gateway_called"] is False
    assert review["summary"]["traffic_shifted"] is False
    assert review["privacy_boundary"]["raw_payload_echoed"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(review, ensure_ascii=False))


def test_canary_observation_review_fails_when_thresholds_are_breached():
    payload = {
        "observations": [
            {
                "step_id": "canary_1_percent-fast",
                "request_count": 100,
                "failure_count": 3,
                "over_budget_count": 2,
                "premium_request_count": 6,
                "operator_review_count": 12,
            }
        ]
    }

    review = ModelOpsCheapFirstCanaryObservationService().build_review(payload, _signals())
    row = review["observation_rows"][0]

    assert review["status"] == "fail"
    assert row["status"] == "fail"
    assert set(row["reason_codes"]) >= {
        "failure-rate",
        "over-budget-route-ratio",
        "premium-request-ratio",
        "operator-review-route-ratio",
    }
    assert review["blocking_observation_ids"] == ["canary-observation-canary_1_percent-fast"]


def test_canary_observation_review_warns_for_low_volume_or_unmatched_steps():
    payload = {
        "observations": [
            {
                "step_id": "canary_1_percent-review",
                "task": "review",
                "phase": "canary_1_percent",
                "request_count": 5,
            }
        ]
    }

    review = ModelOpsCheapFirstCanaryObservationService().build_review(payload, _signals())
    row = review["observation_rows"][0]

    assert review["status"] == "review_required"
    assert row["status"] == "warn"
    assert row["source_step_found"] is False
    assert "minimum-request-count" in row["reason_codes"]
    assert "source-step-found" in row["reason_codes"]


def test_canary_observation_review_fails_when_held_step_has_traffic():
    payload = {
        "observations": [
            {
                "step_id": "maintainer_review-review",
                "task": "review",
                "phase": "maintainer_review",
                "request_count": 25,
                "failure_count": 0,
            }
        ]
    }

    review = ModelOpsCheapFirstCanaryObservationService().build_review(payload, _signals())
    row = review["observation_rows"][0]

    assert review["status"] == "fail"
    assert row["status"] == "fail"
    assert "traffic-on-held-step" in row["reason_codes"]


def test_canary_observation_review_rejects_sensitive_payload_without_echoing_values():
    payload = {
        "observations": [
            {
                "step_id": "canary_1_percent-fast",
                "request_count": 100,
                "failure_count": 0,
            }
        ],
        "headers": {"authorization": "redacted"},
        "raw_model_output": "should never be echoed",
    }

    review = ModelOpsCheapFirstCanaryObservationService().build_review(payload, _signals())
    payload_text = json.dumps(review, ensure_ascii=False)

    assert review["status"] == "fail"
    assert review["summary"]["forbidden_payload_field_count"] >= 2
    assert "should never be echoed" not in payload_text
    assert review["privacy_boundary"]["credentials_included"] is False


def test_canary_observation_routes_return_metadata_only_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-canary-observation")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["status"] == "not_supplied"
    assert get_payload["data"]["summary"]["configuration_written"] is False

    post_response = client.post(
        "/api/v1/aihub/models/cheap-first-canary-observation",
        json={
            "observations": [
                {
                    "step_id": "monitor_existing_default-fast",
                    "task": "fast",
                    "request_count": 25,
                    "failure_count": 0,
                }
            ]
        },
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["success"] is True
    assert post_payload["data"]["summary"]["observation_count"] == 1
    assert post_payload["data"]["claim_boundary"]["production_traffic_shifted"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["cheap_first_canary_observation"]["status"] == "not_supplied"
