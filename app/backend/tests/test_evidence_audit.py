from services.evidence_audit import EvidenceAuditService


def _base_report() -> dict:
    return {
        "professional_review_framework": {
            "evidence_checklist": ["Signed contract", "Payment records", "Delivery notices"],
        },
        "risk_items": [
            {
                "risk_id": "R-001",
                "risk_level": "high",
                "legal_analysis": {
                    "evidence_suggestion": [
                        "Keep signed contract and amendments.",
                        "Keep payment transfer records.",
                    ],
                },
            },
            {
                "risk_id": "R-002",
                "risk_level": "medium",
                "legal_analysis": {
                    "evidence_suggestion": ["Keep delivery notice screenshots."],
                },
            },
        ],
        "pending_facts": [
            {
                "field": "delivery date",
                "reason": "Needed for timeline confirmation",
                "impact": "May affect risk level",
            }
        ],
    }


def test_evidence_audit_passes_when_risks_have_evidence_plans():
    result = EvidenceAuditService().evaluate(_base_report())

    assert result["status"] == "pass"
    assert result["score"] >= 80
    assert result["risk_evidence_coverage"] == 1.0
    assert result["risk_with_evidence_count"] == 2
    assert result["framework_evidence_count"] == 3
    assert result["high_risk_without_evidence_plan"] == []


def test_evidence_audit_fails_high_risk_without_evidence_plan():
    report = _base_report()
    report["risk_items"][0]["legal_analysis"]["evidence_suggestion"] = []

    result = EvidenceAuditService().evaluate(report)

    assert result["status"] == "fail"
    assert result["high_risk_without_evidence_plan"] == ["R-001"]
    assert any("high-risk items" in action for action in result["recommended_actions"])


def test_evidence_audit_warns_on_blocking_pending_fact_and_missing_framework_checklist():
    report = _base_report()
    report["professional_review_framework"]["evidence_checklist"] = []
    report["pending_facts"] = [
        {
            "field": "signature authority",
            "reason": "Must confirm before delivery",
            "impact": "Unable to judge contract validity",
        }
    ]

    result = EvidenceAuditService().evaluate(report)

    assert result["status"] == "warn"
    assert result["blocking_pending_fact_count"] == 1
    assert result["blocking_pending_fact_ids"] == ["PF-001"]
    assert any(task["type"] == "pending_fact" for task in result["evidence_tasks"])
    assert any("matter-specific evidence checklist" in action for action in result["recommended_actions"])


def test_evidence_audit_flags_overly_repeated_evidence_suggestions():
    report = _base_report()
    repeated = "Keep all communications."
    for risk in report["risk_items"]:
        risk["legal_analysis"]["evidence_suggestion"] = [repeated]
    report["risk_items"].append(
        {
            "risk_id": "R-003",
            "risk_level": "low",
            "legal_analysis": {"evidence_suggestion": [repeated]},
        }
    )

    result = EvidenceAuditService().evaluate(report)

    assert "keepallcommunications." in result["duplicate_evidence_suggestions"]
