import inspect
import re

import services.case_workbench_persistence_plan as persistence_plan_module
from services.case_workbench_persistence_plan import (
    SUPPORTED_SECTIONS,
    CaseWorkbenchPersistencePlanService,
)


SECRET_PATTERN = re.compile(
    r"s[k]-[A-Za-z0-9_-]{12,}|[^@\s]+@[^@\s]+\.[^@\s]+|Bearer\s+[A-Za-z0-9._-]{12,}",
    re.IGNORECASE,
)


def _service() -> CaseWorkbenchPersistencePlanService:
    return CaseWorkbenchPersistencePlanService()


def _state_delta(section: str) -> dict:
    deltas = {
        "parties": {
            "summary": {"party_count": 1, "review_required_count": 0},
            "party_states": [
                {
                    "party_ref_hash": "party_hash_abcdefghijkl",
                    "party_role": "claimant",
                    "party_type": "individual",
                    "status": "active",
                    "representation_status": "represented",
                    "conflict_status": "clear",
                    "identity_verification_status": "verified",
                    "authority_status": "confirmed",
                    "claim_alignment_codes": ["payment_recovery"],
                    "risk_flags": [],
                    "source_refs": ["src_hash_party_001"],
                    "sort_order": 1,
                }
            ],
        },
        "facts": {
            "summary": {"fact_count": 1, "review_required_count": 0},
            "fact_states": [
                {
                    "fact_ref_hash": "fact_hash_abcdefghijkl",
                    "fact_type": "payment_event",
                    "status": "verified",
                    "materiality": "high",
                    "dispute_status": "undisputed",
                    "chronology_date": "2026-06-04",
                    "date_precision": "day",
                    "confidence_level": "high",
                    "source_evidence_refs": ["evidence_hash_receipt_001"],
                    "legal_issue_codes": ["payment_default"],
                    "party_refs": ["party_hash_abcdefghijkl"],
                }
            ],
        },
        "tasks": {
            "summary": {"task_count": 1, "active_count": 1, "review_required_count": 0},
            "task_states": [
                {
                    "task_ref_hash": "task_hash_abcdefghijkl",
                    "task_type": "lawyer_review",
                    "status": "open",
                    "priority": "high",
                    "owner_role": "lawyer",
                    "due_at": "2026-06-05T08:00:00Z",
                    "due_date_status": "near",
                    "escalation_status": "none",
                    "blocker_codes": [],
                    "dependency_refs": ["fact_hash_abcdefghijkl"],
                }
            ],
        },
        "deadlines": {
            "summary": {"deadline_count": 1, "urgent_count": 0, "overdue_count": 0},
            "deadline_states": [
                {
                    "deadline_ref_hash": "deadline_hash_abcdefghijkl",
                    "deadline_type": "appeal_deadline",
                    "status": "scheduled",
                    "due_at": "2026-06-30T16:00:00Z",
                    "trigger_date": "2026-06-04",
                    "trigger_source_type": "judgment_date",
                    "urgency": "normal",
                    "days_until_due_bucket": "15_30_days",
                    "limitation_basis_code": "civil_appeal_window",
                    "computed_by_policy_version": "deadline-validation-v1",
                    "review_required": False,
                }
            ],
        },
        "evidence_graph": {
            "summary": {"node_count": 2, "edge_count": 1, "gap_count": 0, "blocking_gap_count": 0},
            "graph_nodes": [
                {
                    "node_ref_hash": "node_hash_fact_abcdefghijkl",
                    "node_type": "fact",
                    "entity_ref_hash": "fact_hash_abcdefghijkl",
                    "review_status": "ready",
                    "source_section": "facts",
                },
                {
                    "node_ref_hash": "node_hash_evidence_abcdef",
                    "node_type": "evidence",
                    "entity_ref_hash": "evidence_hash_receipt_001",
                    "review_status": "ready",
                    "source_section": "evidence",
                },
            ],
            "graph_edges": [
                {
                    "edge_ref_hash": "edge_hash_abcdefghijkl",
                    "edge_type": "supports",
                    "from_ref_hash": "node_hash_evidence_abcdef",
                    "to_ref_hash": "node_hash_fact_abcdefghijkl",
                    "support_strength": "strong",
                    "review_status": "ready",
                }
            ],
            "gap_flags": [],
        },
    }
    payload = deltas[section]
    payload.update(
        {
            "schema_version": "case-workbench-state-v1",
            "section": section,
            "state_version": 1,
            "updated_by_role": "lawyer",
            "source_component": "case_workbench_repository",
            "policy_version": "case-workbench-persistence-v1",
        }
    )
    return payload


def _changed_fields(section: str) -> list[str]:
    return {
        "parties": ["party_ref_hash", "party_role", "party_type", "status", "conflict_status"],
        "facts": ["fact_ref_hash", "fact_type", "status", "materiality", "source_evidence_refs"],
        "tasks": ["task_ref_hash", "task_type", "status", "priority", "owner_role"],
        "deadlines": ["deadline_ref_hash", "deadline_type", "status", "due_at", "urgency"],
        "evidence_graph": ["node_ref_hash", "edge_ref_hash", "edge_type", "support_strength"],
    }[section]


def _event(section: str = "parties") -> dict:
    return {
        "event_id": f"cwp-event-{section}-001",
        "event_type": "case_workbench_state_event",
        "timestamp": "2026-06-04T08:00:00Z",
        "idempotency_key": f"cwp:v1:case_hash_abcdefghijkl:{section}:1:src_001",
        "case_ref_hash": "case_hash_abcdefghijkl",
        "matter_ref_hash": "matter_hash_abcdefghijkl",
        "actor_ref_hash": "actor_hash_abcdefghijkl",
        "section": section,
        "operation": "upsert_snapshot",
        "state_version": 1,
        "previous_state_version": 0,
        "schema_version": "case-workbench-state-v1",
        "source_component": "case_workbench_repository",
        "payload_kind": "metadata_snapshot",
        "item_count": 1,
        "changed_item_refs": [f"{section}_item_hash_abcdefghijkl"],
        "changed_field_names": _changed_fields(section),
        "state_delta": _state_delta(section),
        "retention_bucket": "active_case_workbench",
        "policy_version": "case-workbench-persistence-v1",
        "review_required": False,
        "validation_status": "pass",
        "created_at": "2026-06-04T08:00:01Z",
    }


def test_case_workbench_persistence_plan_returns_template_contract():
    plan = _service().build_plan()

    assert plan["status"] == "template"
    assert plan["summary"]["database_migration_required"] is False
    assert plan["summary"]["router_integration_required"] is False
    assert plan["summary"]["release_or_ledger_integration_required"] is False
    assert plan["summary"]["case_workbench_payload_changes_required"] is False
    assert plan["summary"]["raw_payload_storage_allowed"] is False
    assert set(plan["state_schema"]["sections"]) == set(SUPPORTED_SECTIONS)
    assert "party_ref_hash" in plan["state_schema"]["sections"]["parties"]["collections"]["party_states"]["allowed_fields"]
    assert "fact_ref_hash" in plan["state_schema"]["sections"]["facts"]["collections"]["fact_states"]["required_fields"]
    assert "deadline_ref_hash" in plan["state_schema"]["sections"]["deadlines"]["collections"]["deadline_states"]["required_fields"]
    assert "graph_edges" in plan["state_schema"]["sections"]["evidence_graph"]["collections"]
    assert plan["sample_state_events_validation"]["checks"][0]["check_id"] == "case-workbench-persistence-template"
    assert plan["validation_commands"] == [
        "python -m pytest tests/test_case_workbench_persistence_plan.py -q",
        "python -m compileall services/case_workbench_persistence_plan.py tests/test_case_workbench_persistence_plan.py",
    ]


def test_case_workbench_persistence_plan_defines_repository_method_contracts():
    plan = _service().build_plan()
    method_names = {method["name"] for method in plan["repository_method_contracts"]["methods"]}

    assert plan["repository_method_contracts"]["implementation_status"] == "contract_only_no_database_binding"
    assert {
        "get_state",
        "upsert_section_state",
        "append_state_event",
        "list_state_events",
        "compact_state_events",
        "delete_state",
    }.issubset(method_names)
    assert "opaque refs" in plan["repository_method_contracts"]["methods"][3]["privacy_contract"]


def test_case_workbench_persistence_plan_passes_compliant_events_for_all_sections():
    plan = _service().build_plan([_event(section) for section in SUPPORTED_SECTIONS])

    assert plan["status"] == "pass"
    assert plan["summary"]["passing_event_count"] == len(SUPPORTED_SECTIONS)
    assert plan["summary"]["failing_event_count"] == 0
    assert all(check["allowed_to_persist"] is True for check in plan["persistence_checks"])
    assert all(check["forbidden_fields_present"] == [] for check in plan["persistence_checks"])
    assert all(check["forbidden_nested_fields"] == [] for check in plan["persistence_checks"])
    assert all(check["sensitive_value_findings"] == [] for check in plan["persistence_checks"])


def test_case_workbench_persistence_plan_rejects_raw_content_and_sensitive_values_without_echoing():
    secret_value = "s" + "k-" + ("A" * 24)
    client_email = "client" + "@example.com"
    raw_fact = "UNSAFE_RAW_FACT_TEXT_SHOULD_NOT_ECHO"
    client_name = "UNSAFE_CLIENT_NAME_SHOULD_NOT_ECHO"
    event = _event("facts")
    event.update(
        {
            "client_email": client_email,
            "api_key": secret_value,
        }
    )
    event["state_delta"]["fact_states"][0]["fact_text"] = raw_fact
    event["state_delta"]["metadata"] = {"client_name": client_name}
    event["changed_field_names"].append("fact_text")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]
    rendered = str(plan)

    assert plan["status"] == "fail"
    assert check["blocking"] is True
    assert {"client_email", "api_key"}.issubset(set(check["forbidden_fields_present"]))
    assert any(path.endswith(".fact_text") for path in check["forbidden_nested_fields"])
    assert any(path.endswith(".client_name") for path in check["forbidden_nested_fields"])
    assert any(item["type"] == "api_key_like" for item in check["sensitive_value_findings"])
    assert any(item["type"] == "email_like" for item in check["sensitive_value_findings"])
    assert raw_fact not in rendered
    assert client_name not in rendered
    assert client_email not in rendered
    assert secret_value not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_case_workbench_persistence_plan_fails_for_missing_required_event_fields():
    event = _event("deadlines")
    event.pop("case_ref_hash")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "fail"
    assert check["allowed_to_persist"] is False
    assert "case_ref_hash" in check["missing_required_fields"]
    assert "missing_required_fields" in check["failures"]


def test_case_workbench_persistence_plan_warns_for_missing_recommended_event_fields():
    event = _event("tasks")
    event.pop("idempotency_key")
    event.pop("actor_ref_hash")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "warn"
    assert check["allowed_to_persist"] is True
    assert check["blocking"] is False
    assert set(check["missing_recommended_fields"]) >= {"idempotency_key", "actor_ref_hash"}


def test_case_workbench_persistence_plan_fails_invalid_section_state_schema():
    event = _event("tasks")
    event["state_delta"]["task_states"][0].pop("task_ref_hash")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "fail"
    assert check["allowed_to_persist"] is False
    assert "invalid_section_state_schema" in check["failures"]
    assert any(item["type"] == "missing_required_section_field" for item in check["section_schema_findings"])


def test_case_workbench_persistence_plan_warns_for_unknown_metadata_fields():
    event = _event("tasks")
    event["state_delta"]["task_states"][0]["display_label_code"] = "task_display_001"
    event["changed_field_names"].append("display_label_code")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "warn"
    assert check["allowed_to_persist"] is True
    assert any(path.endswith(".display_label_code") for path in check["unknown_nested_fields"])
    assert any(item["type"] == "unknown_changed_field" for item in check["changed_field_findings"])


def test_case_workbench_persistence_plan_exposes_privacy_safe_and_forbidden_field_sets():
    plan = _service().build_policy()

    assert "case_ref_hash" in plan["privacy_safe_fields"]["event_fields"]
    assert "party_ref_hash" in plan["privacy_safe_fields"]["section_item_fields"]["parties"]["party_states"]
    assert "fact_ref_hash" in plan["privacy_safe_fields"]["section_item_fields"]["facts"]["fact_states"]
    assert "deadline_ref_hash" in plan["privacy_safe_fields"]["section_item_fields"]["deadlines"]["deadline_states"]
    assert {"party_name", "fact_text", "document_text", "prompt", "model_output"}.issubset(
        set(plan["forbidden_raw_content_fields"])
    )
    assert "raw case content" in plan["privacy_note"]


def test_case_workbench_persistence_plan_stays_independent_from_payload_router_and_database():
    source = inspect.getsource(persistence_plan_module)

    assert "import case_workbench_payload" not in source
    assert "from services.case_workbench_payload" not in source
    assert "from routers" not in source
    assert "from models" not in source
    assert "Session" not in source


def test_case_workbench_persistence_plan_route_returns_template_and_event_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/case-workbench-persistence-plan")
    event_response = client.post("/api/v1/maintenance/case-workbench-persistence-plan", json=[_event("facts")])

    assert template_response.status_code == 200
    assert template_response.json()["success"] is True
    assert template_response.json()["data"]["status"] == "template"
    assert event_response.status_code == 200
    assert event_response.json()["data"]["status"] == "pass"
    assert event_response.json()["data"]["summary"]["passing_event_count"] == 1
