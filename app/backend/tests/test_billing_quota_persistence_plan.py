import re

from services.billing_quota_persistence_plan import BillingQuotaPersistencePlanService


SECRET_PATTERN = re.compile(
    r"s[k]-[A-Za-z0-9_-]{12,}|[^@\s]+@[^@\s]+\.[^@\s]+|cs_(test|live)_[A-Za-z0-9_]+",
    re.IGNORECASE,
)


def _service() -> BillingQuotaPersistencePlanService:
    return BillingQuotaPersistencePlanService()


def _compliant_event() -> dict:
    return {
        "event_id": "billing-quota-event-001",
        "event_type": "billing_quota_usage_counter",
        "timestamp": "2026-06-04T08:00:00Z",
        "idempotency_key": "bqp:v1:qsh_abcdefghijklmnop:2026-06:review:review_credits:src_001",
        "quota_subject_hash": "qsh_abcdefghijklmnop",
        "subject_type": "account",
        "plan_type": "personal",
        "subscription_status": "active",
        "action": "review",
        "usage_metric": "review_credits",
        "units": 1,
        "request_units": 1,
        "quota_window": "2026-06",
        "counter_bucket": "subject_metric_monthly",
        "bucket_start": "2026-06-01T00:00:00Z",
        "bucket_end": "2026-07-01T00:00:00Z",
        "allowed": True,
        "decision_status": "ready",
        "limit": 20,
        "used_before": 3,
        "remaining_before": 17,
        "remaining_after": 16,
        "over_limit_reason_codes": [],
        "policy_version": "billing-usage-quota-v1",
        "entitlement_snapshot_id": "ent_snap_opaque_001",
        "source_component": "quota_policy",
        "trace_ref_hash": "trace_hash_opaque_001",
        "created_at": "2026-06-04T08:00:01Z",
    }


def test_billing_quota_persistence_plan_returns_template_contract():
    plan = _service().build_plan()

    assert plan["status"] == "template"
    assert plan["summary"]["database_migration_required"] is False
    assert plan["summary"]["payment_integration_required"] is False
    assert plan["summary"]["network_required"] is False
    assert plan["summary"]["raw_payload_storage_allowed"] is False
    assert "quota_subject_hash" in plan["usage_counter_schema"]["required_fields"]
    assert "idempotency_key" in plan["usage_counter_schema"]["required_fields"]
    assert "subject_metric_monthly" in {item["bucket"] for item in plan["aggregation_buckets"]}
    assert plan["retention_policy"]["raw_event_retention"]["durable_raw_payload_allowed"] is False
    assert plan["idempotency_key_policy"]["required"] is True
    assert plan["validation_commands"] == [
        "python -m pytest tests/test_billing_quota_persistence_plan.py -q",
        "python -m compileall services/billing_quota_persistence_plan.py tests/test_billing_quota_persistence_plan.py",
    ]


def test_billing_quota_persistence_plan_passes_compliant_counter_event():
    plan = _service().build_plan([_compliant_event()])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "pass"
    assert plan["summary"]["passing_event_count"] == 1
    assert check["allowed_to_persist"] is True
    assert check["missing_required_fields"] == []
    assert check["forbidden_fields_present"] == []
    assert check["sensitive_value_findings"] == []
    assert check["idempotency_key_findings"] == []
    assert check["quota_subject_findings"] == []


def test_billing_quota_persistence_plan_persists_block_reason_codes_and_numeric_snapshot():
    event = _compliant_event()
    event.update(
        {
            "event_id": "billing-quota-event-002",
            "idempotency_key": "bqp:v1:qsh_abcdefghijklmnop:2026-06:review:review_credits:src_002",
            "allowed": False,
            "decision_status": "blocked",
            "used_before": 20,
            "remaining_before": 0,
            "remaining_after": 0,
            "over_limit_reason_codes": ["review_credits_exhausted"],
            "over_limit_reasons": [
                {
                    "code": "review_credits_exhausted",
                    "metric": "review_credits",
                    "limit": 20,
                    "used": 20,
                    "requested": 1,
                    "remaining": 0,
                    "quota_window": "2026-06",
                    "policy_version": "billing-usage-quota-v1",
                    "blocked_at": "2026-06-04T08:00:00Z",
                    "source_component": "quota_policy",
                }
            ],
        }
    )

    plan = _service().build_policy([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "pass"
    assert check["over_limit_reason_findings"] == []
    reason_schema = plan["usage_counter_schema"]["over_limit_reason_persistence"]
    assert reason_schema["message_storage_allowed"] is False
    assert reason_schema["free_text_allowed"] is False
    assert set(reason_schema["required_when_blocked"]) == {"code", "metric"}


def test_billing_quota_persistence_plan_fails_blocked_event_without_reason_persistence():
    event = _compliant_event()
    event.update(
        {
            "allowed": False,
            "decision_status": "blocked",
            "remaining_before": 0,
            "remaining_after": 0,
            "over_limit_reason_codes": [],
        }
    )

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "fail"
    assert check["blocking"] is True
    assert "invalid_over_limit_reason_persistence" in check["failures"]
    assert check["over_limit_reason_findings"][0]["type"] == "missing_when_blocked"
    assert check["allowed_to_persist"] is False


def test_billing_quota_persistence_plan_rejects_reason_free_text_fields():
    event = _compliant_event()
    event.update(
        {
            "allowed": False,
            "decision_status": "blocked",
            "remaining_before": 0,
            "remaining_after": 0,
            "over_limit_reason_codes": ["review_credits_exhausted"],
            "over_limit_reasons": [
                {
                    "code": "review_credits_exhausted",
                    "metric": "review_credits",
                    "message": "UNSAFE_REASON_MESSAGE_SHOULD_NOT_BE_ALLOWED",
                }
            ],
        }
    )

    plan = _service().build_plan([event])
    rendered = str(plan)
    check = plan["persistence_checks"][0]

    assert plan["status"] == "fail"
    assert "invalid_over_limit_reason_persistence" in check["failures"]
    assert any(item["type"] == "unapproved_reason_fields" for item in check["over_limit_reason_findings"])
    assert "UNSAFE_REASON_MESSAGE_SHOULD_NOT_BE_ALLOWED" not in rendered


def test_billing_quota_persistence_plan_fails_forbidden_fields_and_sensitive_values_without_echoing_them():
    secret_value = "s" + "k-" + ("A" * 24)
    client_email = "client" + "@example.com"
    payment_session = "cs_test_" + ("B" * 18)
    raw_prompt = "UNSAFE_RAW_PROMPT_TEXT_SHOULD_NOT_ECHO"
    event = _compliant_event()
    event.update(
        {
            "raw_prompt": raw_prompt,
            "client_email": client_email,
            "api_key": secret_value,
            "payment_session_id": payment_session,
            "metadata": {"user_id": "UNSAFE_USER_ID_SHOULD_NOT_ECHO"},
        }
    )

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]
    rendered = str(plan)

    assert plan["status"] == "fail"
    assert check["blocking"] is True
    assert {"raw_prompt", "client_email", "api_key", "payment_session_id"}.issubset(
        set(check["forbidden_fields_present"])
    )
    assert any(item["type"] == "api_key_like" for item in check["sensitive_value_findings"])
    assert any(item["type"] == "email_like" for item in check["sensitive_value_findings"])
    assert any(item["type"] == "payment_provider_id_like" for item in check["sensitive_value_findings"])
    assert raw_prompt not in rendered
    assert client_email not in rendered
    assert secret_value not in rendered
    assert payment_session not in rendered
    assert "UNSAFE_USER_ID_SHOULD_NOT_ECHO" not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_billing_quota_persistence_plan_warns_for_missing_recommended_fields():
    event = _compliant_event()
    event.pop("entitlement_snapshot_id")
    event.pop("source_component")

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "warn"
    assert check["blocking"] is False
    assert check["allowed_to_persist"] is True
    assert set(check["missing_recommended_fields"]) >= {"entitlement_snapshot_id", "source_component"}
    assert check["missing_required_fields"] == []


def test_billing_quota_persistence_plan_rejects_direct_subjects_bad_idempotency_and_bad_counters():
    event = _compliant_event()
    event.update(
        {
            "idempotency_key": "review-user-123",
            "quota_subject_hash": "user-123",
            "units": 0,
            "allowed": "yes",
        }
    )

    plan = _service().build_plan([event])
    check = plan["persistence_checks"][0]

    assert plan["status"] == "fail"
    assert "invalid_idempotency_key" in check["failures"]
    assert "invalid_quota_subject_hash" in check["failures"]
    assert "invalid_counter_values" in check["failures"]
    assert check["idempotency_key_findings"] == [{"field": "idempotency_key", "type": "invalid_format"}]
    assert check["quota_subject_findings"] == [{"field": "quota_subject_hash", "type": "must_be_opaque_hash"}]


def test_billing_quota_persistence_plan_forbidden_patterns_cover_billing_and_content_fields():
    schema = _service().build_plan()["usage_counter_schema"]
    forbidden = set(schema["forbidden_field_patterns"])

    assert "user_id" in forbidden
    assert "document_text" in forbidden
    assert "prompt" in forbidden
    assert "file_name" in forbidden
    assert "payment" in forbidden
    assert "stripe" in forbidden
    assert "api_key" in forbidden


def test_billing_quota_persistence_plan_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/billing-quota-persistence-plan")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "template"

    reviewed = client.post("/api/v1/maintenance/billing-quota-persistence-plan", json=[_compliant_event()])

    assert reviewed.status_code == 200
    assert reviewed.json()["data"]["status"] == "pass"
