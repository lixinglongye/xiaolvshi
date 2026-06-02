from services.report_quality_gate import ReportQualityGate


def _base_report() -> dict:
    return {
        "risk_items": [
            {
                "risk_id": "R-001",
                "title": "Unclear payment deadline",
                "risk_level": "high",
                "original_clause": {"clause_number": "3.1", "text": "Payment shall be made later."},
                "issue_location": "Payment deadline is vague.",
                "citations": [
                    {
                        "source_id": "LS-001",
                        "source_name": "Civil Code",
                        "source_type": "law",
                        "authority_level": "national law",
                        "verification_status": "verified",
                    }
                ],
                "revision_plan": {
                    "balanced_clause": "Payment shall be made within 10 working days after acceptance.",
                },
            }
        ],
        "pending_facts": [{"field": "acceptance date", "reason": "Needed for deadline calculation"}],
        "legal_authority_appendix": [
            {
                "source_id": "LS-001",
                "source_name": "Civil Code",
                "authority_level": "national law",
            }
        ],
        "disclaimer": "This AI-assisted report is not legal advice and should be reviewed by a lawyer.",
    }


def test_quality_gate_passes_reviewable_report():
    gate = ReportQualityGate()

    result = gate.evaluate(_base_report())

    assert result["status"] == "pass"
    assert result["release_level"] == "ready_for_lawyer_spot_check"
    assert result["fail_count"] == 0


def test_quality_gate_fails_missing_grounding_citation_revision_and_disclaimer():
    gate = ReportQualityGate()
    report = _base_report()
    risk = report["risk_items"][0]
    risk["original_clause"] = {}
    risk["issue_location"] = ""
    risk["citations"] = []
    risk["revision_plan"] = {}
    report["disclaimer"] = ""

    result = gate.evaluate(report)

    assert result["status"] == "fail"
    assert result["release_level"] == "internal_draft_only"
    assert set(result["blocking_gate_ids"]) >= {
        "risks-grounded",
        "high-risk-citations",
        "revision-plans",
        "disclaimer",
    }


def test_quality_gate_warns_when_appendix_or_pending_facts_are_missing():
    gate = ReportQualityGate()
    report = _base_report()
    report["pending_facts"] = []
    report["legal_authority_appendix"] = []

    result = gate.evaluate(report)

    assert result["status"] == "warn"
    assert result["release_level"] == "lawyer_review_required"
    assert set(result["warning_gate_ids"]) >= {"pending-facts", "legal-appendix"}
