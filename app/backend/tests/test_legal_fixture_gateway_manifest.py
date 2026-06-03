from services.legal_fixture_gateway_manifest import LegalFixtureGatewayManifestService


def test_legal_fixture_gateway_manifest_builds_openai_compatible_requests():
    manifest = LegalFixtureGatewayManifestService().build_manifest()
    request = manifest["requests"][0]

    assert manifest["status"] == "ready"
    assert manifest["summary"]["request_count"] >= 4
    assert request["endpoint_path"] == "/v1/chat/completions"
    assert request["gateway_base_url_placeholder"] == "{{APP_AI_BASE_URL}}"
    assert request["auth_header_placeholder"] == "Bearer {{APP_AI_KEY}}"
    assert request["openai_request_body"]["messages"][0]["role"] == "system"
    assert request["openai_request_body"]["response_format"]["type"] == "json_object"
    assert request["openai_request_body"]["stream"] is False
    assert "sk-" not in str(manifest)


def test_legal_fixture_gateway_manifest_includes_app_request_and_smoke_template():
    manifest = LegalFixtureGatewayManifestService().build_manifest()
    request = next(row for row in manifest["requests"] if row["fixture_id"] == "fixture-service-agreement-small")

    assert request["app_request_body"]["task"] == "fast"
    assert request["app_request_body"]["allow_over_budget_model"] is False
    assert request["smoke_observation_template"]["fixture-service-agreement-small"]["route"] == "fast"
    assert "/fixture-smoke" in request["cheap_first_policy"]["post_success_to"]
    assert "/fixture-improvements" in request["cheap_first_policy"]["post_failure_to"]


def test_legal_fixture_gateway_manifest_tracks_cheap_first_escalation():
    manifest = LegalFixtureGatewayManifestService().build_manifest()
    pdf_request = next(row for row in manifest["requests"] if row["fixture_id"] == "fixture-low-text-pdf-page-small")

    assert pdf_request["cheap_first_policy"]["first_attempt_model"] == pdf_request["cheap_trial_model"]
    assert pdf_request["recommended_model"]
    assert pdf_request["cheap_first_policy"]["escalation_trigger"]
    assert manifest["summary"]["escalation_candidate_count"] >= 1
    assert pdf_request["fixture_id"] in manifest["warning_fixture_ids"]
    assert manifest["recommended_actions"]


def test_legal_fixture_gateway_manifest_route_returns_manifest():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/gateway-manifest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["request_count"] >= 4
