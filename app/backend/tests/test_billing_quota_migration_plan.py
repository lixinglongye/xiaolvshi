import re

from services.billing_quota_migration_plan import BillingQuotaMigrationPlanService


SECRET_PATTERN = re.compile(
    r"s[k]-[A-Za-z0-9_-]{12,}|[^@\s]+@[^@\s]+\.[^@\s]+|postgres(?:ql)?://|cs_(test|live)_[A-Za-z0-9_]+",
    re.IGNORECASE,
)


def _service() -> BillingQuotaMigrationPlanService:
    return BillingQuotaMigrationPlanService()


def _compliant_checks() -> list[dict]:
    return [
        {
            "check_id": "bqmp-schema-001",
            "check_type": "schema_contract",
            "target": "billing_quota_usage_counters",
            "status": "pass",
            "blocking": True,
            "observed_count": 31,
            "expected_count": 31,
            "migration_batch_id": "batch_opaque_001",
            "evidence_ref": "evidence_ref_schema_001",
            "checked_at": "2026-06-04T08:00:00Z",
        },
        {
            "check_id": "bqmp-forbidden-columns-001",
            "check_type": "forbidden_columns",
            "target": "all_billing_quota_tables",
            "status": "pass",
            "blocking": True,
            "observed_count": 0,
            "expected_count": 0,
            "migration_batch_id": "batch_opaque_001",
            "evidence_ref": "evidence_ref_forbidden_001",
            "checked_at": "2026-06-04T08:01:00Z",
        },
        {
            "check_id": "bqmp-unique-001",
            "check_type": "unique_constraints",
            "target": "billing_quota_unique_constraints",
            "status": "pass",
            "blocking": True,
            "observed_count": 8,
            "expected_count": 8,
            "migration_batch_id": "batch_opaque_001",
            "evidence_ref": "evidence_ref_unique_001",
            "checked_at": "2026-06-04T08:02:00Z",
        },
        {
            "check_id": "bqmp-replay-001",
            "check_type": "idempotency_replay",
            "target": "billing_quota_idempotency_keys",
            "status": "pass",
            "blocking": True,
            "observed_count": 1,
            "expected_count": 1,
            "migration_batch_id": "batch_opaque_001",
            "evidence_ref": "evidence_ref_replay_001",
            "checked_at": "2026-06-04T08:03:00Z",
        },
        {
            "check_id": "bqmp-rollup-001",
            "check_type": "rollup_reconciliation",
            "target": "billing_quota_subject_monthly_rollups",
            "status": "pass",
            "blocking": True,
            "observed_count": 42,
            "expected_count": 42,
            "migration_batch_id": "batch_opaque_001",
            "evidence_ref": "evidence_ref_rollup_001",
            "checked_at": "2026-06-04T08:04:00Z",
        },
        {
            "check_id": "bqmp-rollback-001",
            "check_type": "rollback_reversibility",
            "target": "migration_batch_rollback_delta",
            "status": "pass",
            "blocking": True,
            "observed_count": 0,
            "expected_count": 0,
            "migration_batch_id": "batch_opaque_001",
            "evidence_ref": "evidence_ref_rollback_001",
            "checked_at": "2026-06-04T08:05:00Z",
        },
    ]


def test_billing_quota_migration_plan_returns_template_contract():
    plan = _service().build_plan()
    table_names = {table["name"] for table in plan["tables"]}
    index_names = {index["name"] for index in plan["indexes"]}
    constraint_names = {constraint["name"] for constraint in plan["unique_constraints"]}

    assert plan["status"] == "template"
    assert plan["summary"]["target_migration_required_before_durable_quota_storage"] is True
    assert plan["summary"]["actual_database_migration_executed"] is False
    assert plan["summary"]["database_connection_required"] is False
    assert plan["summary"]["payment_integration_required"] is False
    assert plan["summary"]["network_required"] is False
    assert plan["summary"]["router_changes_allowed"] is False
    assert plan["summary"]["release_changes_allowed"] is False
    assert plan["summary"]["ledger_changes_allowed"] is False
    assert plan["summary"]["raw_payload_storage_allowed"] is False
    assert "billing_quota_usage_counters" in table_names
    assert "billing_quota_idempotency_keys" in table_names
    assert "ix_bq_usage_subject_metric_window" in index_names
    assert "uq_bq_usage_idempotency_key" in constraint_names
    assert "uq_bq_subject_monthly_metric" in constraint_names
    assert set(plan["sample_migration_checks"]["contract"]["required_check_types_before_execution"]) == {
        "schema_contract",
        "forbidden_columns",
        "unique_constraints",
        "idempotency_replay",
        "rollup_reconciliation",
        "rollback_reversibility",
    }
    assert plan["validation_commands"] == [
        "python -m pytest tests/test_billing_quota_migration_plan.py -q",
        "python -m compileall services/billing_quota_migration_plan.py tests/test_billing_quota_migration_plan.py",
    ]


def test_billing_quota_migration_plan_passes_complete_sample_checks():
    plan = _service().build_plan(_compliant_checks())
    checks = plan["sample_migration_checks"]["checks"]

    assert plan["status"] == "pass"
    assert plan["summary"]["checked_sample_count"] == len(_compliant_checks())
    assert plan["summary"]["passing_sample_count"] == len(_compliant_checks())
    assert plan["sample_migration_checks"]["coverage"]["complete"] is True
    assert plan["sample_migration_checks"]["coverage"]["missing_required_check_types"] == []
    assert all(check["allowed_to_use_as_evidence"] is True for check in checks)


def test_billing_quota_migration_plan_defines_idempotent_replay_and_unique_guards():
    plan = _service().build_plan()
    idempotency = plan["idempotency"]
    replay_phases = [step["phase"] for step in plan["replay_steps"]]
    constraints = {item["name"]: item for item in plan["unique_constraints"]}

    assert idempotency["required"] is True
    assert idempotency["dedup_table"] == "billing_quota_idempotency_keys"
    assert idempotency["collision_behavior"]["same_key_same_hash"] == "no_op_and_increment_seen_count"
    assert idempotency["collision_behavior"]["same_key_different_hash"] == "quarantine_batch_and_do_not_update_rollups"
    assert replay_phases == ["preflight", "batch_start", "dedup", "counter_write", "rollup", "verify"]
    assert constraints["uq_bq_usage_idempotency_key"]["columns"] == ["idempotency_key"]
    assert constraints["uq_bq_dedup_idempotency_key"]["columns"] == ["idempotency_key"]


def test_billing_quota_migration_plan_has_batch_scoped_rollback_plan():
    rollback = _service().build_plan()["rollback_plan"]

    assert rollback["rollback_safe_until"] == "before application read path is switched to the migrated quota store"
    assert "rollup_reconciliation" in rollback["verification_checks"]
    assert "idempotency_replay" in rollback["verification_checks"]
    assert "rollback_reversibility" in rollback["verification_checks"]
    assert any("migration_batch_id" in step for step in rollback["steps"])
    assert "No payment refund or invoice mutation." in rollback["non_goals"]
    assert "No router or release toggle change." in rollback["non_goals"]
    assert "No continuous update ledger mutation." in rollback["non_goals"]
    assert "No direct database execution from this service." in rollback["non_goals"]


def test_billing_quota_migration_plan_minimizes_data_and_forbids_sensitive_columns():
    plan = _service().build_plan()
    forbidden = set(plan["forbidden_fields"])
    rendered_columns = {
        column["name"]
        for table in plan["tables"]
        for column in table["columns"]
    }
    data_minimization = plan["data_minimization"]

    assert "quota_subject_hash" in rendered_columns
    assert "idempotency_key" in rendered_columns
    assert "user_id" in forbidden
    assert "document_text" in forbidden
    assert "prompt" in forbidden
    assert "payment" in forbidden
    assert "api_key" in forbidden
    assert not {"user_id", "email", "document_text", "prompt", "payment_intent", "api_key"} & rendered_columns
    assert "raw request bodies" in " ".join(data_minimization["forbidden_categories"])
    assert data_minimization["subject_policy"].startswith("quota_subject_hash is required")


def test_billing_quota_migration_plan_warns_for_missing_required_sample_coverage():
    checks = [_compliant_checks()[0]]

    plan = _service().build_plan(checks)
    coverage = plan["sample_migration_checks"]["coverage"]

    assert plan["status"] == "warn"
    assert coverage["complete"] is False
    assert "idempotency_replay" in coverage["missing_required_check_types"]
    assert "rollback_reversibility" in coverage["missing_required_check_types"]
    assert plan["sample_migration_checks"]["checks"][0]["status"] == "pass"


def test_billing_quota_migration_plan_fails_failed_or_blocking_sample_check():
    checks = _compliant_checks()
    checks[3] = {
        **checks[3],
        "status": "fail",
        "blocking": True,
    }

    plan = _service().build_plan(checks)
    failed = plan["sample_migration_checks"]["checks"][3]

    assert plan["status"] == "fail"
    assert failed["blocking"] is True
    assert "sample_check_reported_failure" in failed["failures"]
    assert "blocking_sample_check_not_passed" in failed["failures"]
    assert failed["allowed_to_use_as_evidence"] is False


def test_billing_quota_migration_plan_rejects_forbidden_fields_without_echoing_values():
    secret_value = "s" + "k-" + ("A" * 24)
    client_email = "client" + "@example.com"
    db_url = "postgresql://quota_user:password@example.invalid/quota"
    raw_payload = "UNSAFE_RAW_COUNTER_PAYLOAD_SHOULD_NOT_ECHO"
    payment_session = "cs_test_" + ("B" * 18)
    checks = _compliant_checks()
    checks.append(
        {
            "check_id": "bqmp-privacy-001",
            "check_type": "data_minimization",
            "target": "billing_quota_usage_counters",
            "status": "pass",
            "blocking": True,
            "raw_payload": raw_payload,
            "api_key": secret_value,
            "database_url": db_url,
            "payment_session_id": payment_session,
            "notes": ["contains forbidden client email", client_email],
        }
    )

    plan = _service().build_plan(checks)
    check = plan["sample_migration_checks"]["checks"][-1]
    rendered = str(plan)

    assert plan["status"] == "fail"
    assert {"raw_payload", "api_key", "database_url", "payment_session_id"}.issubset(
        set(check["forbidden_fields_present"])
    )
    assert any(item["type"] == "api_key_like" for item in check["sensitive_value_findings"])
    assert any(item["type"] == "email_like" for item in check["sensitive_value_findings"])
    assert any(item["type"] == "db_connection_uri_like" for item in check["sensitive_value_findings"])
    assert any(item["type"] == "payment_provider_id_like" for item in check["sensitive_value_findings"])
    assert raw_payload not in rendered
    assert secret_value not in rendered
    assert client_email not in rendered
    assert db_url not in rendered
    assert payment_session not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_billing_quota_migration_plan_rejects_non_object_sample_check():
    plan = _service().build_plan(["not-a-dict"])
    check = plan["sample_migration_checks"]["checks"][0]

    assert plan["status"] == "fail"
    assert check["blocking"] is True
    assert check["failures"] == ["sample_check_must_be_object"]
    assert check["allowed_to_use_as_evidence"] is False


def test_billing_quota_migration_plan_route_returns_template_and_sample_check():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/billing-quota-migration-plan")
    check_response = client.post("/api/v1/maintenance/billing-quota-migration-plan", json=_compliant_checks())

    assert template_response.status_code == 200
    assert template_response.json()["success"] is True
    assert template_response.json()["data"]["status"] == "template"
    assert check_response.status_code == 200
    assert check_response.json()["data"]["status"] == "pass"
    assert check_response.json()["data"]["sample_migration_checks"]["coverage"]["complete"] is True
