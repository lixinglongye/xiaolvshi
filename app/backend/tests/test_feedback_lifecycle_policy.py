from services.feedback_lifecycle_policy import FeedbackLifecyclePolicyService


class UnmappedAlignmentService:
    def align(self, item=None, **kwargs):
        return {
            "status": "unmapped",
            "triage": {
                "status": "triaged",
                "priority": "P1",
                "assignee": "legal_review_owner",
                "labels": ["legal_quality", "high_risk_output"],
                "matched_rule_ids": ["legal-output-risk"],
            },
            "top_need_id": None,
            "matches": [],
        }


def _check(result: dict, check_id: str) -> dict:
    return next(item for item in result["checks"] if item["id"] == check_id)


def test_feedback_lifecycle_policy_exposes_state_machine_and_commands():
    policy = FeedbackLifecyclePolicyService().build_policy()

    assert policy["status"] == "ready"
    assert policy["state_machine"]["happy_path"] == [
        "intake",
        "triage",
        "linked_gap",
        "in_progress",
        "release_validation",
        "customer_visible_resolution",
        "closed",
    ]
    assert policy["state_machine"]["transitions"][0]["from"] == "intake"
    assert policy["state_machine"]["transitions"][-1]["to"] == "closed"
    assert any(check["id"] == "high_risk_feedback_linked" for check in policy["transition_checks"])
    assert any("pytest" in command for command in policy["validation_commands"])
    assert "AI model" in policy["privacy_note"]
    assert "sk-" not in str(policy)


def test_high_risk_feedback_is_linked_to_roadmap_gap_and_release_gate():
    result = FeedbackLifecyclePolicyService().evaluate_ticket(
        state="triage",
        category="report",
        content="The generated report has an incorrect citation and hallucination.",
    )

    assert result["high_risk"] is True
    assert result["linkage"]["roadmap_gap_id"] == "traceable-legal-review"
    assert "citation_audit" in result["linkage"]["release_gate_links"]
    assert _check(result, "high_risk_feedback_linked")["status"] == "pass"
    assert result["next_allowed_states"] == ["linked_gap"]


def test_unmapped_high_risk_feedback_cannot_leave_triage():
    result = FeedbackLifecyclePolicyService(UnmappedAlignmentService()).evaluate_ticket(
        state="triage",
        category="report",
        content="The legal answer is wrong and needs review.",
    )

    assert result["high_risk"] is True
    assert result["linkage"]["satisfies_high_risk_policy"] is False
    assert "high_risk_feedback_linked" in result["blocking_check_ids"]
    assert result["next_allowed_states"] == []
    assert result["required_actions"] == [
        "Attach roadmap_gap_id or release_gate_links before scheduling work.",
        "High-risk feedback must reference a roadmap gap or release gate before it leaves triage.",
    ]


def test_release_validation_requires_public_resolution_before_customer_state():
    blocked = FeedbackLifecyclePolicyService().evaluate_ticket(
        state="release_validation",
        category="security",
        content="User reported a privacy leak in upload history.",
        release_validation_status="pass",
    )

    assert "customer-resolution-note-present" in blocked["blocking_check_ids"]
    assert blocked["next_allowed_states"] == []

    allowed = FeedbackLifecyclePolicyService().evaluate_ticket(
        state="release_validation",
        category="security",
        content="User reported a privacy leak in upload history.",
        release_validation_status="waived",
        customer_visible_resolution="Upload privacy handling was reviewed and redacted before further support work.",
    )

    assert allowed["next_allowed_states"] == ["customer_visible_resolution"]
    assert _check(allowed, "privacy-safe-public-note")["status"] == "pass"


def test_customer_visible_resolution_can_close_with_notification_and_summary():
    result = FeedbackLifecyclePolicyService().evaluate_ticket(
        state="customer_visible_resolution",
        category="bug",
        content="PDF OCR returned blank output.",
        release_validation_status="pass",
        customer_visible_resolution="Blank OCR output is now blocked before review.",
        customer_notified=True,
        closure_summary="Added extraction-quality guard to the feedback loop.",
    )

    assert result["high_risk"] is False
    assert result["next_allowed_states"] == ["closed"]
    assert result["blocking_check_ids"] == []
    assert "release-validation-accepted" not in result["blocking_check_ids"]


def test_sample_ticket_evaluations_keep_high_risk_items_linked():
    policy = FeedbackLifecyclePolicyService().build_policy()
    samples = policy["sample_tickets_evaluation"]
    high_risk_samples = [sample for sample in samples if sample["high_risk"]]

    assert len(samples) >= 4
    assert high_risk_samples
    assert all(sample["linkage"]["satisfies_high_risk_policy"] for sample in high_risk_samples)
    assert all(sample["linkage"]["roadmap_gap_id"] or sample["linkage"]["release_gate_links"] for sample in samples)


def test_feedback_lifecycle_policy_route_returns_policy_and_evaluation():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/feedback-lifecycle-policy")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ready"

    evaluated = client.post(
        "/api/v1/maintenance/feedback-lifecycle-policy",
        json={
            "state": "triage",
            "category": "report",
            "content": "The generated report has an incorrect citation.",
        },
    )

    assert evaluated.status_code == 200
    assert evaluated.json()["data"]["high_risk"] is True
