import json
import re

from services.model_ops_request_execution_preflight import ModelOpsRequestExecutionPreflightService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_request_execution_preflight_allows_default_cheap_first_rows():
    preflight = ModelOpsRequestExecutionPreflightService().build_preflight()
    rows = {row["request_id"]: row for row in preflight["request_rows"]}

    assert preflight["id"] == "modelops-request-execution-preflight"
    assert preflight["status"] == "ready"
    assert preflight["summary"]["request_count"] == 5
    assert preflight["summary"]["ready_request_count"] == 5
    assert preflight["summary"]["blocked_request_count"] == 0
    assert preflight["summary"]["high_frequency_request_count"] == 3
    assert preflight["summary"]["cheap_first_ready_count"] == 3
    assert preflight["summary"]["model_called"] is False
    assert preflight["summary"]["gateway_called"] is False
    assert preflight["summary"]["network_called"] is False
    assert preflight["summary"]["configuration_written"] is False
    assert preflight["blocking_check_ids"] == []
    assert preflight["warning_check_ids"] == []

    assert rows["fast-default"]["resolved_model"] == "gemini-2.5-flash-lite"
    assert rows["fast-default"]["cheap_first_aligned"] is True
    assert rows["fast-default"]["estimated_request_cost_usd"] < rows["fast-default"]["request_cost_limit_usd"]
    assert rows["fast-default"]["fallback_rows"][0]["cheap_first_candidate"] is True
    assert rows["review-balanced"]["execution_status"] == "ready"
    assert rows["agentic-cheap-first"]["resolved_model"] == "gemini-3.1-flash-lite"
    assert rows["embedding-default"]["resolved_model"] == "gemini-embedding-001"
    assert rows["embedding-default"]["estimated_output_tokens"] == 0
    assert preflight["privacy_boundary"]["request_body_included"] is False
    assert preflight["claim_boundary"]["request_sent"] is False


def test_request_execution_preflight_blocks_cost_over_limit():
    preflight = ModelOpsRequestExecutionPreflightService().build_preflight(
        {
            "requests": [
                {
                    "id": "fast-cost-cap",
                    "task": "fast",
                    "model": "auto",
                    "estimated_input_tokens": 1200,
                    "estimated_output_tokens": 512,
                    "max_cost_usd": 0.000001,
                }
            ]
        }
    )
    row = preflight["request_rows"][0]

    assert preflight["status"] == "blocked"
    assert row["execution_status"] == "blocked"
    assert "estimated_cost_over_limit" in row["reason_codes"]
    assert row["release_action"] == "block_request_until_cost_bound_is_safe"
    assert "request-cost-within-bounds" in preflight["blocking_check_ids"]


def test_request_execution_preflight_reviews_explicit_over_budget_exception():
    preflight = ModelOpsRequestExecutionPreflightService().build_preflight(
        {
            "requests": [
                {
                    "id": "review-pro-reviewed",
                    "task": "review",
                    "model": "gemini-2.5-pro",
                    "allow_over_budget_model": True,
                    "estimated_input_tokens": 1200,
                    "estimated_output_tokens": 128,
                    "fallback_chain": ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"],
                }
            ]
        }
    )
    row = preflight["request_rows"][0]

    assert preflight["status"] == "review_required"
    assert row["execution_status"] == "review_required"
    assert row["resolved_model"] == "gemini-2.5-pro"
    assert row["allow_over_budget_model"] is True
    assert "explicit_over_budget_review_exception" in row["reason_codes"]
    assert "request-review-exceptions-visible" in preflight["warning_check_ids"]


def test_request_execution_preflight_blocks_bad_fallback_order():
    preflight = ModelOpsRequestExecutionPreflightService().build_preflight(
        {
            "requests": [
                {
                    "id": "fast-premium-first",
                    "task": "fast",
                    "model": "auto",
                    "fallback_chain": ["gemini-2.5-pro", "gemini-2.5-flash-lite"],
                }
            ]
        }
    )
    row = preflight["request_rows"][0]

    assert preflight["status"] == "blocked"
    assert "fallback_chain_not_cheap_first" in row["reason_codes"]
    assert "premium_fallback_before_cheap_first_exhausted" in row["reason_codes"]
    assert "fallback-chain-cost-ordered" in preflight["blocking_check_ids"]


def test_request_execution_preflight_rejects_raw_payload_fields_without_echoing_values():
    secret = "s" + "k-" + ("P" * 24)
    preflight = ModelOpsRequestExecutionPreflightService().build_preflight(
        {
            "requests": [{"id": "fast", "task": "fast", "model": "gemini-2.5-flash-lite"}],
            "headers": {"authorization": f"Bearer {secret}"},
            "messages": [{"role": "user", "content": "client@example.com copied legal text"}],
            "prompt": "raw prompt should not be retained",
        }
    )
    serialized = json.dumps(preflight, ensure_ascii=False)

    assert preflight["status"] == "blocked"
    assert preflight["summary"]["forbidden_payload_field_count"] >= 3
    assert "sanitized-execution-metadata-only" in preflight["blocking_check_ids"]
    assert preflight["privacy_boundary"]["raw_payload_echoed"] is False
    assert secret not in serialized
    assert "client@example.com" not in serialized
    assert "copied legal text" not in serialized
    assert "raw prompt should not be retained" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_request_execution_preflight_route_and_models_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/request-execution-preflight")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == "modelops-request-execution-preflight"
    assert response.json()["data"]["summary"]["gateway_called"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/request-execution-preflight",
        json={"requests": [{"task": "fast", "model": "auto", "max_cost_usd": 0.000001}]},
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["request_execution_preflight"]["summary"]["configuration_written"] is False
    assert "request_execution_preflight" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
