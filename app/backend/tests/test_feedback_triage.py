from services.feedback_triage import FeedbackTriageService


def test_feedback_triage_prioritizes_privacy_and_security():
    triage = FeedbackTriageService().triage(
        category="privacy",
        content="用户要求数据删除，并担心个人信息泄露。",
    )

    assert triage["priority"] == "P0"
    assert triage["assignee"] == "security_privacy_owner"
    assert "privacy" in triage["labels"]
    assert triage["sla_hours"] == 4


def test_feedback_triage_routes_legal_output_risk_to_reviewer():
    triage = FeedbackTriageService().triage(
        category="report",
        content="The report has an incorrect citation and missed risk in the indemnity clause.",
    )

    assert triage["priority"] == "P1"
    assert triage["assignee"] == "legal_review_owner"
    assert "legal_quality" in triage["labels"]
    assert "legal-output-risk" in triage["matched_rule_ids"]


def test_feedback_triage_combines_labels_but_uses_highest_priority():
    triage = FeedbackTriageService().triage(
        category="payment",
        content="支付后无法登录，上传 PDF 也失败。",
    )

    assert triage["priority"] == "P1"
    assert triage["assignee"] == "support_ops"
    assert "payment" in triage["labels"]
    assert "pipeline" in triage["labels"]


def test_feedback_triage_apply_to_payload_preserves_manual_values():
    payload = {
        "category": "feature",
        "content": "建议增加批量导出。",
        "priority": "P2",
        "status": "open",
    }

    enriched = FeedbackTriageService().apply_to_payload(payload)

    assert enriched["priority"] == "P2"
    assert enriched["status"] == "open"
    assert enriched["assignee"] == "product_maintainer"
    assert enriched["resolution_note"].startswith("Auto-triage")
