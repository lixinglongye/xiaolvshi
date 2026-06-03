import json

from services.legal_fixture_response_normalizer import LegalFixtureResponseNormalizerService


def _content(**overrides):
    payload = {
        "fixture_id": "fixture-service-agreement-small",
        "route": "fast",
        "risk_matrix": [{"risk": "liability cap"}],
        "missing_facts": ["missing SLA"],
        "replacement_clause": "Add confidentiality carveout.",
        "release_decision": "warn",
        "route_reason": "cheap-first local smoke run",
    }
    payload.update(overrides)
    return json.dumps(payload, ensure_ascii=False)


def test_response_normalizer_template_is_safe_and_ready():
    template = LegalFixtureResponseNormalizerService().template()

    assert template["status"] == "ready"
    assert "responses" in template["payload_shape"]
    assert "sk-" not in str(template)
    assert template["validation_command"].startswith("python -m pytest")


def test_response_normalizer_extracts_openai_choice_content():
    payload = {
        "responses": {
            "fixture-service-agreement-small": {
                "phase": "cheap_first",
                "model": "gemini-2.5-flash-lite",
                "http_status": 200,
                "latency_ms": 900,
                "estimated_cost_usd": 0.0003,
                "gateway_response": {
                    "model": "gemini-2.5-flash-lite",
                    "choices": [{"message": {"content": _content()}}],
                },
            }
        }
    }

    result = LegalFixtureResponseNormalizerService().normalize(payload)
    observation = result["observations"]["fixture-service-agreement-small"]
    metadata = result["run_report_payload"]["run_metadata"]["fixture-service-agreement-small"]

    assert result["status"] == "ready"
    assert result["summary"]["normalized_observation_count"] == 1
    assert result["summary"]["parsed_json_content_count"] == 1
    assert observation["route"] == "fast"
    assert "liability cap" in observation["output_text"]
    assert observation["structured_outputs"]["fixture_id"] == "fixture-service-agreement-small"
    assert metadata["model"] == "gemini-2.5-flash-lite"
    assert metadata["json_content_parsed"] is True
    assert "choices" not in str(result["response_summaries"])


def test_response_normalizer_accepts_direct_content_rows():
    result = LegalFixtureResponseNormalizerService().normalize(
        {
            "responses": [
                {
                    "fixture_id": "fixture-lease-dispute-notice-small",
                    "route": "review",
                    "model": "gemini-2.5-flash-lite",
                    "content": "evidence tasks include deposit amount, missing invoice, repair notice dates, pending facts",
                    "http_status": 200,
                }
            ]
        }
    )

    observation = result["observations"]["fixture-lease-dispute-notice-small"]

    assert result["status"] == "ready"
    assert observation["route"] == "review"
    assert "deposit amount" in observation["output_text"]
    assert result["summary"]["parsed_json_content_count"] == 0


def test_response_normalizer_redacts_secret_like_content_without_echoing_secret():
    secret = "s" + "k-" + ("A" * 24)
    result = LegalFixtureResponseNormalizerService().normalize(
        {
            "fixture_id": "fixture-service-agreement-small",
            "route": "fast",
            "model": "gemini-2.5-flash-lite",
            "content": f"risk matrix ok but leaked {secret}",
            "http_status": 200,
        }
    )
    output = result["observations"]["fixture-service-agreement-small"]["output_text"]

    assert result["status"] == "warn"
    assert "[redacted-secret]" in output
    assert secret not in str(result)
    assert result["summary"]["redacted_response_count"] == 1


def test_response_normalizer_fails_when_content_is_missing():
    result = LegalFixtureResponseNormalizerService().normalize(
        {
            "fixture_id": "fixture-service-agreement-small",
            "model": "gemini-2.5-flash-lite",
            "gateway_response": {"choices": [{"message": {}}]},
            "http_status": 200,
        }
    )

    assert result["status"] == "fail"
    assert result["summary"]["normalized_observation_count"] == 0
    assert any(check["id"].endswith(":content-present") and check["status"] == "fail" for check in result["checks"])


def test_response_normalizer_route_returns_template_and_normalized_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/local-response-normalizer")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["status"] == "ready"

    normalize_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/local-response-normalizer",
        json={
            "responses": {
                "fixture-service-agreement-small": {
                    "route": "fast",
                    "content": _content(),
                    "http_status": 200,
                }
            }
        },
    )

    assert normalize_response.status_code == 200
    assert normalize_response.json()["data"]["summary"]["normalized_observation_count"] == 1
