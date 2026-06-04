import re

from services.gemini_newapi_cheap_first_calibration import (
    GeminiNewapiCheapFirstCalibrationService,
    calibration_decision_order,
)


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_cheap_first_calibration_keeps_low_cost_defaults_without_newapi_calls():
    result = GeminiNewapiCheapFirstCalibrationService().build_calibration()
    rows = {row["id"]: row for row in result["calibration_rows"]}

    assert result["status"] == "pass"
    assert result["summary"]["task_count"] >= 6
    assert result["summary"]["cheap_first_retained_count"] >= 3
    assert result["summary"]["balanced_precheck_count"] >= 2
    assert result["summary"]["premium_exception_count"] == 1
    assert result["summary"]["cost_guardrail_status"] == "pass"
    assert result["summary"]["newapi_called"] is False
    assert result["summary"]["raw_payload_echoed"] is False
    assert rows["fast-intake-preflight"]["calibration_decision"] == "keep_cheap_first_default"
    assert rows["legal-review-balanced"]["calibration_decision"] == "keep_balanced_after_precheck"
    assert rows["large-pdf-premium-exception"]["calibration_decision"] == "require_operator_premium_exception"
    assert "calibration-pass" in rows["ocr-assist"]["reason_codes"]
    assert not SECRET_PATTERN.search(str(result))


def test_cheap_first_calibration_holds_defaults_when_fixture_quality_fails():
    result = GeminiNewapiCheapFirstCalibrationService().build_calibration(
        {
            "fixture_report": {
                "observations": {
                    "fixture-service-agreement-small": {
                        "route": "fast",
                        "output_text": "risk_matrix",
                    }
                }
            }
        }
    )
    rows = {row["id"]: row for row in result["calibration_rows"]}

    assert result["status"] == "fail"
    assert rows["legal-review-balanced"]["status"] == "fail"
    assert rows["legal-review-balanced"]["calibration_decision"] == "hold_for_fixture_evidence"
    assert "fixture-escalation-required" in rows["legal-review-balanced"]["reason_codes"]
    assert any("Hold review default changes" in action for action in result["recommended_actions"])


def test_cheap_first_calibration_decision_order_is_stable_for_ui_sorting():
    assert calibration_decision_order("keep_cheap_first_default") < calibration_decision_order(
        "keep_balanced_after_precheck"
    )
    assert calibration_decision_order("require_operator_premium_exception") < calibration_decision_order(
        "hold_for_fixture_evidence"
    )
    assert calibration_decision_order("unknown") == 99


def test_cheap_first_calibration_routes_return_metadata_only_payloads():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-calibration")
    assert get_response.status_code == 200
    get_payload = get_response.json()["data"]
    assert get_payload["status"] == "pass"
    assert get_payload["summary"]["newapi_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/cheap-first-calibration",
        json={
            "fixture_report": {
                "observations": {
                    "fixture-service-agreement-small": {
                        "route": "fast",
                        "output_text": "risk_matrix",
                    }
                }
            }
        },
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()["data"]
    assert post_payload["summary"]["raw_payload_echoed"] is False
    assert post_payload["privacy_boundary"]["credentials_included"] is False


def test_model_ops_route_includes_cheap_first_calibration_readiness_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cheap_first_calibration"]["status"] == "pass"
    assert any(
        check["source_key"] == "cheap_first_calibration"
        for check in payload["model_ops_readiness"]["checks"]
    )
