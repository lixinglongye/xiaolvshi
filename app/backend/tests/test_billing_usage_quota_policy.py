import re

from services.billing_usage_quota_policy import (
    BillingUsageQuotaPolicyService,
    PrivacySafeUsageEvent,
    UsageRequest,
    UsageSnapshot,
)


SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9]{20,}|cs_(test|live)_[A-Za-z0-9]+)")


def reason_codes(payload):
    return {item["code"] for item in payload["over_limit_reasons"]}


def test_plan_limits_extend_product_catalog_report_quotas():
    policy = BillingUsageQuotaPolicyService()
    limits = policy.plan_limits()

    assert limits["free"]["review_credits_monthly"] == 2
    assert limits["personal"]["review_credits_monthly"] == 20
    assert limits["lawyer"]["review_credits_monthly"] == 100
    assert limits["enterprise"]["review_credits_monthly"] == 1000
    assert limits["free"]["low_cost_model_first"] is True
    assert limits["admin"]["premium_model_allowed"] is True


def test_document_upload_consumes_count_and_storage_when_within_limits():
    result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(
            plan_type="free",
            document_uploads_used_month=1,
            document_storage_mb_used=20,
        ),
        UsageRequest(action="document_upload", upload_size_mb=5),
    )

    assert result["status"] == "ready"
    assert result["allowed"] is True
    assert result["remaining_before"]["document_uploads"] == 4
    assert result["remaining_after"]["document_uploads"] == 3
    assert result["remaining_before"]["document_storage_mb"] == 80
    assert result["remaining_after"]["document_storage_mb"] == 75
    assert result["consumption"] == {"document_uploads": 1, "document_storage_mb": 5}
    assert result["requires_real_payment"] is False
    assert result["requires_network"] is False


def test_document_upload_blocks_count_size_and_storage_overages():
    result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(
            plan_type="free",
            document_uploads_used_month=5,
            document_storage_mb_used=95,
        ),
        UsageRequest(action="upload", upload_size_mb=11),
    )

    assert result["status"] == "blocked"
    assert result["allowed"] is False
    assert reason_codes(result) == {
        "document_uploads_exhausted",
        "document_upload_too_large",
        "document_storage_exhausted",
    }
    assert result["remaining_after"] == result["remaining_before"]


def test_review_credit_guard_blocks_exhausted_plan():
    result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="free", review_credits_used_month=2),
        UsageRequest(action="review", units=1),
    )

    assert result["status"] == "blocked"
    assert result["remaining_before"]["review_credits"] == 0
    assert reason_codes(result) == {"review_credits_exhausted"}
    assert result["over_limit_reasons"][0]["metric"] == "review_credits"


def test_generated_document_guard_tracks_generated_doc_quota():
    result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="personal", generated_docs_used_month=19),
        UsageRequest(action="generated-document", units=2),
    )

    assert result["status"] == "blocked"
    assert result["remaining_before"]["generated_docs"] == 1
    assert reason_codes(result) == {"generated_docs_exhausted"}


def test_premium_model_escalation_is_explicit_and_plan_limited():
    free_result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="free"),
        UsageRequest(action="premium_model_escalation", requested_model_tier="premium"),
    )
    personal_result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="personal", premium_escalations_used_month=1),
        UsageRequest(
            action="premium_model_escalation",
            requested_model_tier="premium",
            operator_approved=True,
        ),
    )
    exhausted_result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="personal", premium_escalations_used_month=2),
        UsageRequest(
            action="premium_model_escalation",
            requested_model_tier="premium",
            operator_approved=True,
        ),
    )

    assert {
        "premium_model_not_allowed",
        "premium_operator_approval_required",
        "premium_escalations_exhausted",
    }.issuperset(reason_codes(free_result))
    assert "premium_model_not_allowed" in reason_codes(free_result)
    assert personal_result["status"] == "ready"
    assert personal_result["remaining_after"]["premium_escalations"] == 0
    assert reason_codes(exhausted_result) == {"premium_escalations_exhausted"}


def test_premium_tier_on_normal_review_requires_separate_escalation():
    result = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="lawyer", review_credits_used_month=0),
        UsageRequest(action="review", requested_model_tier="premium"),
    )

    assert result["status"] == "blocked"
    assert result["recommended_model_tier"] == "cheap"
    assert reason_codes(result) == {"premium_escalation_required"}
    assert "cheap-first" in " ".join(result["policy_notes"])


def test_inactive_subscription_and_unknown_plan_return_structured_reasons():
    inactive = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="personal", subscription_status="past_due"),
        UsageRequest(action="review"),
    )
    unknown = BillingUsageQuotaPolicyService().evaluate(
        UsageSnapshot(plan_type="legacy"),
        UsageRequest(action="review"),
    )

    assert reason_codes(inactive) == {"inactive_subscription"}
    assert reason_codes(unknown) == {"unknown_plan"}
    assert unknown["limits"] == {}


def test_privacy_safe_usage_aggregation_records_only_counters_and_categories():
    policy = BillingUsageQuotaPolicyService()
    result = policy.aggregate_usage(
        [
            PrivacySafeUsageEvent(
                plan_type="personal",
                action="review",
                allowed=True,
                units=1,
                prompt_tokens=100,
                completion_tokens=30,
            ),
            {
                "plan_type": "personal",
                "action": "review",
                "allowed": False,
                "units": 1,
                "requested_model_tier": "premium",
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "over_limit_codes": ["premium_escalation_required"],
                "user_id": "user-123",
                "file_name": "secret-contract.pdf",
                "prompt": "raw legal prompt",
                "api_key": "SENTINEL_API_KEY_VALUE",
                "payment_session_id": "SENTINEL_PAYMENT_SESSION",
            },
        ]
    )

    rendered = str(result)
    assert result["privacy_mode"] == "aggregate-only"
    assert result["content_fields_recorded"] == []
    assert result["totals"]["events"] == 2
    assert result["totals"]["blocked_events"] == 1
    assert result["totals"]["total_tokens"] == 145
    assert result["by_plan"]["personal"]["units"] == 2
    assert result["by_action"]["review"]["allowed_events"] == 1
    assert result["over_limit_reasons"] == {"premium_escalation_required": 1}
    assert "secret-contract.pdf" not in rendered
    assert "raw legal prompt" not in rendered
    assert "user-123" not in rendered
    assert "SENTINEL_API_KEY_VALUE" not in rendered
    assert "SENTINEL_PAYMENT_SESSION" not in rendered
    assert not SECRET_PATTERN.search(rendered)


def test_policy_evidence_documents_non_goals_and_validation_commands():
    result = BillingUsageQuotaPolicyService().build_policy_evidence()

    assert result["status"] == "backend_evidence_ready"
    assert result["scope"] == "billing-usage-quota"
    assert result["model_strategy"] == "low-cost-model-first"
    assert "premium-model-escalation-guard" in result["implemented_controls"]
    assert "privacy-safe-usage-aggregation" in result["implemented_controls"]
    assert "real-payment-processing" in result["non_goals"]
    assert "network-calls" in result["non_goals"]
    assert result["validation_commands"] == [
        "python -m pytest tests/test_billing_usage_quota_policy.py -q",
        "python -m compileall services/billing_usage_quota_policy.py tests/test_billing_usage_quota_policy.py",
    ]
    assert not SECRET_PATTERN.search(str(result))


def test_billing_usage_quota_policy_route_returns_evidence_and_decision():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/billing-usage-quota-policy")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "backend_evidence_ready"

    decision = client.post(
        "/api/v1/maintenance/billing-usage-quota-policy",
        json={
            "snapshot": {"plan_type": "free", "review_credits_used_month": 2},
            "request": {"action": "review", "units": 1},
        },
    )

    assert decision.status_code == 200
    assert decision.json()["data"]["status"] == "blocked"
    assert reason_codes(decision.json()["data"]) == {"review_credits_exhausted"}
