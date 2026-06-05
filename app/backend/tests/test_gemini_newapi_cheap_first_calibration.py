import re

from services.gemini_newapi_cheap_first_calibration import (
    GeminiNewapiCheapFirstCalibrationService,
    calibration_decision_order,
)


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}")


def test_cheap_first_calibration_keeps_low_cost_defaults_without_newapi_calls():
    result = GeminiNewapiCheapFirstCalibrationService().build_calibration()
    rows = {row["id"]: row for row in result["calibration_rows"]}
    mappings = {row["source_id"]: row for row in result["external_research_mappings"]}

    assert result["status"] == "pass"
    assert result["summary"]["task_count"] >= 6
    assert result["summary"]["cheap_first_retained_count"] >= 3
    assert result["summary"]["balanced_precheck_count"] >= 2
    assert result["summary"]["premium_exception_count"] == 1
    assert result["summary"]["cost_guardrail_status"] == "pass"
    assert result["summary"]["external_research_source_count"] >= 5
    assert result["summary"]["research_mapped_task_count"] == result["summary"]["task_count"]
    assert result["summary"]["forbidden_payload_field_count"] == 0
    assert result["summary"]["secret_like_value_count"] == 0
    assert result["summary"]["newapi_called"] is False
    assert result["summary"]["raw_payload_echoed"] is False
    assert rows["fast-intake-preflight"]["calibration_decision"] == "keep_cheap_first_default"
    assert rows["legal-review-balanced"]["calibration_decision"] == "keep_balanced_after_precheck"
    assert rows["large-pdf-premium-exception"]["calibration_decision"] == "require_operator_premium_exception"
    assert "lexglue" in rows["classification-routing"]["research_source_ids"]
    assert "doclaynet" in rows["ocr-assist"]["research_source_ids"]
    assert "legalbench" in rows["legal-review-balanced"]["research_source_ids"]
    assert "coliee" in rows["large-pdf-premium-exception"]["research_source_ids"]
    assert mappings["cuad"]["import_policy"].startswith("Metadata only")
    assert "calibration-pass" in rows["ocr-assist"]["reason_codes"]
    assert not SECRET_PATTERN.search(str(result))


def test_cheap_first_calibration_research_mappings_are_metadata_only():
    result = GeminiNewapiCheapFirstCalibrationService().build_calibration()

    assert result["privacy_boundary"]["raw_legal_text_included"] is False
    assert result["privacy_boundary"]["raw_model_output_included"] is False
    assert any(
        guardrail.startswith("Do not import LegalBench")
        for guardrail in result["release_guardrails"]
    )
    assert "DocLayNet" in " ".join(result["release_guardrails"])
    for mapping in result["external_research_mappings"]:
        assert mapping["import_policy"].lower().startswith("metadata only")
        assert "sample" not in mapping
        assert "prompt" not in mapping
        assert "output" not in mapping
        assert mapping["url"].startswith("https://")


def test_cheap_first_calibration_blocks_forbidden_payload_metadata_without_echoing_values():
    result = GeminiNewapiCheapFirstCalibrationService().build_calibration(
        {
            "fixture_report": {
                "headers": {"authorization": "Bearer redacted"},
                "observations": {
                    "fixture-service-agreement-small": {
                        "route": "review",
                        "output_text": "liability_cap risk_matrix cost_route",
                    }
                },
            },
            "prompt": "redacted placeholder",
            "metadata": {"token": "sk-" + ("x" * 24)},
        }
    )

    assert result["status"] == "fail"
    assert result["summary"]["forbidden_payload_field_count"] >= 2
    assert result["summary"]["secret_like_value_count"] == 1
    assert result["privacy_boundary"]["forbidden_payload_detected"] is True
    assert result["source_summaries"]["payload_safety"]["raw_values_echoed"] is False
    assert "Remove forbidden payload fields" in result["recommended_actions"][0]
    assert "redacted placeholder" not in str(result)
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
