import json

from services.legal_fixture_local_run_review import LegalFixtureLocalRunReviewService
from services.legal_review_benchmark import LegalReviewBenchmarkService


def _fixture_payload(fixture_id: str, route: str, text: str) -> dict:
    return {
        "phase": "cheap_first",
        "model": "gemini-2.5-flash-lite",
        "http_status": 200,
        "latency_ms": 800,
        "estimated_cost_usd": 0.0002,
        "gateway_response": {
            "model": "gemini-2.5-flash-lite",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "fixture_id": fixture_id,
                                "route": route,
                                "output_text": text,
                                "release_decision": "pass",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        },
    }


def _passing_payload() -> dict:
    fixtures = LegalReviewBenchmarkService().build_fixture_smoke_template()["fixtures"]
    return {
        "responses": {
            fixture["id"]: _fixture_payload(
                fixture["id"],
                fixture["expected_routes"][0],
                " ".join([*fixture["expected_signals"], *fixture["expected_tasks"]]),
            )
            for fixture in fixtures
        }
    }


def test_local_run_review_template_is_safe_and_ready():
    template = LegalFixtureLocalRunReviewService().template()

    assert template["status"] == "ready"
    assert "responses" in template["payload_shape"]
    assert "/api/v1/maintenance/legal-review-benchmark/local-run-review" in template["follow_up_endpoints"]
    assert "sk-" not in str(template)
    assert template["validation_command"].startswith("python -m pytest")


def test_local_run_review_builds_ready_bundle_when_all_fixtures_pass():
    result = LegalFixtureLocalRunReviewService().review(_passing_payload())

    assert result["status"] == "ready"
    assert result["release_decision"] == "keep_cheap_first_defaults"
    assert result["summary"]["normalized_observation_count"] == 4
    assert result["summary"]["smoke_status"] == "pass"
    assert result["summary"]["evidence_bundle_status"] == "ready"
    assert result["normalizer_summary"]["redacted_response_count"] == 0
    assert result["run_report"]["status"] == "ready"
    assert result["evidence_bundle"]["summary"]["release_decision"] == "keep_cheap_first_defaults"
    assert "choices" not in str(result["response_summaries"])


def test_local_run_review_flags_single_small_fixture_for_more_review():
    result = LegalFixtureLocalRunReviewService().review(
        {
            "responses": {
                "fixture-service-agreement-small": _fixture_payload(
                    "fixture-service-agreement-small",
                    "fast",
                    "risk_matrix liability_cap missing_sla replacement_clause",
                )
            }
        }
    )

    assert result["status"] == "needs_escalation"
    assert result["summary"]["normalized_observation_count"] == 1
    assert result["summary"]["not_run_fixture_count"] == 3
    assert result["summary"]["blocking_check_count"] >= 1
    assert "hold_default_changes" in result["release_decision"]


def test_local_run_review_fails_when_response_content_missing():
    result = LegalFixtureLocalRunReviewService().review(
        {
            "fixture_id": "fixture-service-agreement-small",
            "model": "gemini-2.5-flash-lite",
            "gateway_response": {"choices": [{"message": {}}]},
            "http_status": 200,
        }
    )

    assert result["status"] == "fail"
    assert result["summary"]["normalized_observation_count"] == 0
    assert "normalizer-ready" in result["blocking_check_ids"]
    assert "observations-present" in result["blocking_check_ids"]


def test_local_run_review_redacts_secret_like_content_without_echoing_secret():
    secret = "s" + "k-" + ("B" * 24)
    result = LegalFixtureLocalRunReviewService().review(
        {
            "fixture_id": "fixture-service-agreement-small",
            "route": "fast",
            "model": "gemini-2.5-flash-lite",
            "content": f"risk_matrix liability cap missing SLA replacement clause {secret}",
            "http_status": 200,
        }
    )

    assert result["summary"]["redacted_response_count"] == 1
    assert "[redacted-secret]" in result["run_report_payload"]["observations"]["fixture-service-agreement-small"]["output_text"]
    assert secret not in str(result)


def test_local_run_review_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/legal-review-benchmark/local-run-review")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["status"] == "ready"

    review_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/local-run-review",
        json=_passing_payload(),
    )

    assert review_response.status_code == 200
    assert review_response.json()["data"]["summary"]["normalized_observation_count"] == 4
