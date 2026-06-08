import json
import re

from services.model_ops_cheap_first_cascade_research_gate import (
    ModelOpsCheapFirstCascadeResearchGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def test_cascade_research_gate_default_is_metadata_only_review_gate():
    gate = ModelOpsCheapFirstCascadeResearchGateService().build_gate()
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "review_required"
    assert gate["summary"]["source_count"] >= 7
    assert gate["summary"]["frugalgpt_basis_attached"] is True
    assert gate["summary"]["gemini_flash_lite_basis_attached"] is True
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["default_routes_changed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["raw_payload_echoed"] is False
    assert gate["claim_boundary"]["automatic_default_change_claimed"] is False
    assert "https://arxiv.org/abs/2305.05176" in serialized
    assert "https://ai.google.dev/models/gemini" in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_cascade_research_gate_passes_when_source_gates_pass():
    source = {
        "status": "pass",
        "summary": {"warning_check_count": 0, "blocking_check_count": 0},
        "blocking_check_ids": [],
        "warning_check_ids": [],
    }
    gate = ModelOpsCheapFirstCascadeResearchGateService().build_gate(
        {
            "gemini_cheap_first_route_preflight": source,
            "route_quality_budget": source,
            "cheap_first_escalation_budget": source,
            "failure_upgrade_budget": source,
            "cheap_first_calibration": source,
            "user_need_cheap_first_handoff": source,
        }
    )

    assert gate["status"] == "pass"
    assert gate["warning_check_ids"] == []
    assert gate["blocking_check_ids"] == []
    assert gate["summary"]["passing_source_count"] == gate["summary"]["source_count"]
    assert gate["cascade_policy"]["cheap_primary"].startswith("Start high-frequency")


def test_cascade_research_gate_blocks_on_source_failure():
    source = {
        "status": "pass",
        "summary": {},
        "blocking_check_ids": [],
        "warning_check_ids": [],
    }
    failing_escalation = {
        "status": "fail",
        "summary": {"blocking_check_count": 1},
        "blocking_check_ids": ["premium-review-coverage"],
        "warning_check_ids": [],
    }

    gate = ModelOpsCheapFirstCascadeResearchGateService().build_gate(
        {
            "gemini_cheap_first_route_preflight": source,
            "route_quality_budget": source,
            "cheap_first_escalation_budget": failing_escalation,
            "failure_upgrade_budget": source,
            "cheap_first_calibration": source,
            "user_need_cheap_first_handoff": source,
        }
    )

    assert gate["status"] == "fail"
    assert "local-gates-attached" in gate["blocking_check_ids"]
    assert any(row["id"] == "cheap-first-escalation-budget" and row["status"] == "fail" for row in gate["source_rows"])


def test_cascade_research_gate_rejects_sensitive_payload_without_echoing_values():
    secret = "s" + "k-" + "a" * 24
    email = "client" + "@" + "example.com"
    phone = "138" + "12345678"
    identity_number = "11010119900307123" + "4"
    payload = {
        "gemini_cheap_first_route_preflight": {"status": "pass"},
        "headers": {"authorization": secret},
        "prompt": "do not echo this",
        "raw_model_output": f"{email} {phone} {identity_number}",
    }

    gate = ModelOpsCheapFirstCascadeResearchGateService().build_gate(payload)
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "fail"
    assert "sanitized-source-signals" in gate["blocking_check_ids"]
    assert gate["summary"]["forbidden_payload_field_count"] >= 3
    assert gate["summary"]["secret_like_value_count"] >= 2
    assert secret not in serialized
    assert "do not echo this" not in serialized
    assert email not in serialized
    assert phone not in serialized
    assert gate["privacy_boundary"]["credentials_included"] is False


def test_cascade_research_gate_routes_and_model_ops_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-cascade-research-gate")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["privacy_boundary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/cheap-first-cascade-research-gate",
        json={"gemini_cheap_first_route_preflight": {"status": "pass"}},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "review_required"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert "cheap_first_cascade_research_gate" in models_payload
    assert "cheap_first_cascade_research_gate" in {
        check["source_key"] for check in models_payload["model_ops_readiness"]["checks"]
    }
