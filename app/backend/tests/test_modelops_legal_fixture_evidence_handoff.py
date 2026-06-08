import json
import re

from services.modelops_legal_fixture_evidence_handoff import (
    ModelOpsLegalFixtureEvidenceHandoffService,
)


FORBIDDEN_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{16,}|authorization|bearer|"
    r"client@example\.com|THIS_SHOULD_NOT_LEAK",
    re.IGNORECASE,
)


def _ready_payload():
    return {
        "local_run_review": {
            "status": "ready",
            "summary": {
                "response_count": 2,
                "normalized_observation_count": 2,
                "observed_fixture_count": 2,
                "not_run_fixture_count": 0,
                "warning_check_count": 0,
            },
            "blocking_check_ids": [],
            "warning_check_ids": [],
        },
        "cheap_first_benchmark_gate": {
            "status": "ready",
            "summary": {
                "evaluated_fixture_count": 2,
                "blocked_count": 0,
                "review_required_count": 0,
            },
            "blocking_check_ids": [],
            "warning_check_ids": [],
        },
        "default_promotion_packet": {
            "status": "ready",
            "summary": {
                "default_change_allowed_by_packet": True,
                "archived_fixture_count": 2,
                "blocking_item_count": 0,
                "review_item_count": 0,
            },
            "blocking_check_ids": [],
            "warning_check_ids": [],
        },
    }


def test_legal_fixture_evidence_handoff_builds_archive_safe_default_packet():
    handoff = ModelOpsLegalFixtureEvidenceHandoffService().build_handoff()
    rows = {row["id"]: row for row in handoff["handoff_rows"]}
    checks = {check["id"]: check for check in handoff["checks"]}

    assert handoff["id"] == "modelops-legal-fixture-evidence-handoff"
    assert handoff["status"] == "not_run"
    assert handoff["summary"]["handoff_source_count"] == 4
    assert handoff["summary"]["raw_payload_echoed"] is False
    assert handoff["summary"]["gateway_called"] is False
    assert handoff["summary"]["network_called"] is False
    assert handoff["summary"]["completion_claimed"] is False
    assert rows["local-run-review"]["handoff_status"] == "not_run"
    assert rows["cheap-first-benchmark-gate"]["source_status"] == "not_run"
    assert rows["default-promotion-packet"]["source_status"] == "not_ready"
    assert rows["continuous-session-run-monitor"]["source_status"] == "not_started"
    assert checks["handoff-source-chain-present"]["status"] == "pass"
    assert checks["continuous-run-monitor-non-completion-claim"]["status"] == "pass"
    assert handoff["privacy_boundary"]["returns_run_report_payload"] is False
    assert handoff["privacy_boundary"]["returns_gateway_response"] is False
    assert handoff["claim_boundary"]["twenty_four_hour_completion_claimed"] is False
    assert handoff["claim_boundary"]["hundred_update_completion_claimed"] is False


def test_legal_fixture_evidence_handoff_accepts_ready_summaries_without_claiming_completion():
    handoff = ModelOpsLegalFixtureEvidenceHandoffService().build_handoff(_ready_payload())
    rows = {row["id"]: row for row in handoff["handoff_rows"]}

    assert handoff["summary"]["release_ready"] is True
    assert handoff["summary"]["observed_fixture_count"] == 2
    assert handoff["summary"]["archived_fixture_count"] == 2
    assert handoff["summary"]["completion_claimed"] is False
    assert rows["local-run-review"]["handoff_status"] == "ready"
    assert rows["cheap-first-benchmark-gate"]["handoff_status"] == "ready"
    assert rows["default-promotion-packet"]["handoff_status"] == "ready"
    assert rows["continuous-session-run-monitor"]["handoff_status"] == "not_run"
    assert "Do not treat this handoff as proof" in " ".join(handoff["recommended_actions"])


def test_legal_fixture_evidence_handoff_does_not_echo_raw_or_secret_payloads():
    payload = {
        "responses": {
            "fixture-service-agreement-small": {
                "gateway_response": {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"route":"fast","output_text":"THIS_SHOULD_NOT_LEAK '
                                    'sk-THIS_SHOULD_NOT_LEAK_1234567890"}'
                                )
                            }
                        }
                    ],
                    "headers": {"authorization": "Bearer THIS_SHOULD_NOT_LEAK_123456"},
                },
                "client_email": "client@example.com",
            }
        }
    }

    handoff = ModelOpsLegalFixtureEvidenceHandoffService().build_handoff(payload)
    serialized = json.dumps(handoff, ensure_ascii=False)

    assert handoff["summary"]["raw_input_field_count"] >= 1
    assert handoff["privacy_boundary"]["returns_gateway_headers"] is False
    assert handoff["privacy_boundary"]["returns_generated_text"] is False
    assert not FORBIDDEN_PATTERN.search(serialized)


def test_legal_fixture_evidence_handoff_routes_and_modelops_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router
    from routers.maintenance import router as maintenance_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    app.include_router(maintenance_router)
    client = testclient.TestClient(app)

    maintenance_response = client.get("/api/v1/maintenance/legal-review-benchmark/evidence-handoff")
    assert maintenance_response.status_code == 200
    assert maintenance_response.json()["data"]["id"] == "modelops-legal-fixture-evidence-handoff"

    posted = client.post("/api/v1/maintenance/legal-review-benchmark/evidence-handoff", json=_ready_payload())
    assert posted.status_code == 200
    assert posted.json()["data"]["summary"]["observed_fixture_count"] == 2

    direct_response = client.get("/api/v1/aihub/models/legal-fixture-evidence-handoff")
    assert direct_response.status_code == 200
    assert direct_response.json()["data"]["privacy_boundary"]["returns_run_report_payload"] is False

    posted_modelops = client.post("/api/v1/aihub/models/legal-fixture-evidence-handoff", json=_ready_payload())
    assert posted_modelops.status_code == 200
    assert posted_modelops.json()["data"]["summary"]["release_ready"] is True

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["legal_fixture_evidence_handoff"]["id"] == "modelops-legal-fixture-evidence-handoff"
    assert "legal_fixture_evidence_handoff" in {
        check["source_key"] for check in models_payload["model_ops_readiness"]["checks"]
    }
