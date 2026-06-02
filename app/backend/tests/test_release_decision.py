from services.release_decision import ReleaseDecisionService


def _base_report() -> dict:
    return {
        "quality_gate": {
            "status": "pass",
            "score": 100,
            "blocking_gate_ids": [],
            "warning_gate_ids": [],
        },
        "citation_audit": {
            "status": "pass",
            "score": 92,
            "recommended_actions": [],
        },
        "evidence_audit": {
            "status": "pass",
            "score": 90,
            "recommended_actions": [],
            "blocking_pending_fact_count": 0,
        },
        "risk_scoring": {
            "overall_score": 55,
            "overall_level": "medium",
            "counts": {"critical": 0, "high": 0, "medium": 2, "low": 1},
        },
    }


def test_release_decision_ready_for_spot_check_when_audits_pass():
    result = ReleaseDecisionService().evaluate(_base_report())

    assert result["status"] == "ready_for_spot_check"
    assert result["release_level"] == "ready_for_lawyer_spot_check"
    assert result["client_delivery_allowed"] is True
    assert result["lawyer_review_required"] is False
    assert result["readiness_score"] >= 85


def test_release_decision_requires_lawyer_review_for_warnings_or_high_risk_pressure():
    report = _base_report()
    report["citation_audit"]["status"] = "warn"
    report["citation_audit"]["recommended_actions"] = ["Verify cited authorities."]
    report["risk_scoring"]["overall_score"] = 82
    report["risk_scoring"]["counts"]["high"] = 2

    result = ReleaseDecisionService().evaluate(report)

    assert result["status"] == "lawyer_review_required"
    assert result["client_delivery_allowed"] is False
    assert result["lawyer_review_required"] is True
    assert result["triage_level"] == "elevated"
    assert "Verify cited authorities." in result["required_actions"]


def test_release_decision_blocks_failed_quality_or_evidence_audits():
    report = _base_report()
    report["quality_gate"]["status"] = "fail"
    report["quality_gate"]["blocking_gate_ids"] = ["high-risk-citations"]
    report["evidence_audit"]["status"] = "fail"
    report["evidence_audit"]["high_risk_without_evidence_plan"] = ["R-001"]
    report["evidence_audit"]["recommended_actions"] = ["Add evidence plans for high-risk items: R-001"]

    result = ReleaseDecisionService().evaluate(report)

    assert result["status"] == "blocked"
    assert result["release_level"] == "internal_draft_only"
    assert result["client_delivery_allowed"] is False
    assert result["triage_level"] == "urgent"
    assert any("Quality gate failed" in reason for reason in result["blocking_reasons"])
    assert "Resolve quality gate: high-risk-citations" in result["required_actions"]
