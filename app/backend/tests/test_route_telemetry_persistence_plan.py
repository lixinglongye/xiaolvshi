import re

from services.route_telemetry_persistence_plan import RouteTelemetryPersistencePlanService


SECRET_PATTERN = re.compile(r"s[k]-[A-Za-z0-9_-]{12,}|[^@\s]+@[^@\s]+\.[^@\s]+", re.IGNORECASE)


def _service() -> RouteTelemetryPersistencePlanService:
    return RouteTelemetryPersistencePlanService()


def _compliant_event() -> dict:
    return {
        "event_id": "route-event-001",
        "event_type": "model_route_decision",
        "timestamp": "2026-06-04T08:00:00Z",
        "route_id": "cheap-first-fast",
        "task": "fast",
        "inference_source": "explicit",
        "requested_model": "gemini-2.5-pro",
        "resolved_model": "gemini-2.5-flash-lite",
        "gateway": "newapi",
        "provider": "google",
        "routed_to_recommended_model": True,
        "is_over_budget": True,
        "requires_operator_review": False,
        "allow_over_budget_model": False,
        "is_known_model": True,
        "estimated_input_tokens": 1200,
        "estimated_output_tokens": 500,
        "estimated_cost_usd": 0.0012,
        "latency_ms": 860,
        "success": True,
        "error_category": "",
        "stream": False,
        "cache_hit": False,
        "http_status": 200,
    }


def test_route_telemetry_persistence_plan_returns_template_without_events():
    plan = _service().build_plan()

    assert plan["status"] == "template"
    assert plan["summary"]["database_migration_required"] is False
    assert plan["summary"]["raw_payload_storage_allowed"] is False
    assert plan["event_schema"]["required_fields"]
    assert plan["retention_policy"]["aggregate_retention"]
    assert plan["validation_commands"] == [
        "python -m pytest tests/test_route_telemetry_persistence_plan.py -q",
        "python -m compileall services/route_telemetry_persistence_plan.py",
    ]


def test_route_telemetry_persistence_plan_passes_compliant_event():
    plan = _service().build_plan([_compliant_event()])

    assert plan["status"] == "pass"
    assert plan["summary"]["passing_event_count"] == 1
    assert plan["summary"]["failing_event_count"] == 0
    assert plan["persistence_checks"][0]["allowed_to_persist"] is True
    assert plan["persistence_checks"][0]["forbidden_fields_present"] == []
    assert plan["persistence_checks"][0]["sensitive_value_findings"] == []


def test_route_telemetry_persistence_plan_fails_prompt_client_info_and_secret():
    secret_value = "s" + "k-" + ("A" * 24)
    client_email = "client" + "@example.com"
    raw_prompt = "UNSAFE_RAW_PROMPT_TEXT_SHOULD_NOT_ECHO"
    event = _compliant_event()
    event.update(
        {
            "raw_prompt": raw_prompt,
            "client_email": client_email,
            "api_key": secret_value,
            "metadata": {"client_name": "UNSAFE_CLIENT_NAME_SHOULD_NOT_ECHO"},
        }
    )

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]
    rendered = str(plan)

    assert plan["status"] == "fail"
    assert check["blocking"] is True
    assert "raw_prompt" in check["forbidden_fields_present"]
    assert "client_email" in check["forbidden_fields_present"]
    assert "api_key" in check["forbidden_fields_present"]
    assert any(item["type"] == "api_key_like" for item in check["sensitive_value_findings"])
    assert raw_prompt not in rendered
    assert client_email not in rendered
    assert secret_value not in rendered
    assert "UNSAFE_CLIENT_NAME_SHOULD_NOT_ECHO" not in rendered


def test_route_telemetry_persistence_plan_warns_for_missing_recommended_fields():
    event = _compliant_event()
    event.pop("route_id")
    event.pop("requested_model")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "warn"
    assert check["blocking"] is False
    assert check["allowed_to_persist"] is True
    assert check["missing_required_fields"] == []
    assert set(check["missing_recommended_fields"]) >= {"route_id", "requested_model"}


def test_route_telemetry_persistence_plan_fails_for_missing_required_fields():
    event = _compliant_event()
    event.pop("resolved_model")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "fail"
    assert check["blocking"] is True
    assert "resolved_model" in check["missing_required_fields"]
    assert "missing_required_fields" in check["failures"]
    assert check["allowed_to_persist"] is False


def test_route_telemetry_persistence_plan_output_has_no_sensitive_values():
    secret_value = "s" + "k-" + ("B" * 24)
    client_email = "owner" + "@example.com"
    event = _compliant_event()
    event["authorization"] = "Bearer " + secret_value
    event["user_email"] = client_email

    plan = _service().build_policy([event])
    rendered = str(plan)

    assert plan["status"] == "fail"
    assert secret_value not in rendered
    assert client_email not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_route_telemetry_persistence_plan_route_evaluates_events():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/route-telemetry-persistence-plan")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["status"] == "template"

    eval_response = client.post("/api/v1/maintenance/route-telemetry-persistence-plan", json=[_compliant_event()])
    assert eval_response.status_code == 200
    payload = eval_response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
