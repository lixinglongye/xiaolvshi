from services.risk_scoring import RiskScoringService


def _report() -> dict:
    return {
        "risk_matrix": [
            {
                "risk_id": "R-001",
                "risk_level": "high",
                "probability": "high",
                "severity": "high",
                "priority": 2,
            },
            {
                "risk_id": "R-002",
                "risk_level": "medium",
                "probability": "medium",
                "severity": "medium",
                "priority": 1,
            },
        ],
        "risk_items": [
            {
                "risk_id": "R-001",
                "title": "Uncapped penalty",
                "risk_level": "high",
                "original_clause": {"clause_number": "5.1", "text": "Penalty is uncapped."},
                "issue_location": "Penalty has no cap.",
                "citations": [
                    {
                        "source_id": "LS-001",
                        "source_name": "Civil Code",
                        "source_type": "law",
                        "authority_level": "national law",
                        "verification_status": "verified",
                        "confidence": 90,
                    }
                ],
                "revision_plan": {"balanced_clause": "Penalty shall be capped at direct losses."},
            },
            {
                "risk_id": "R-002",
                "title": "Missing notice detail",
                "risk_level": "medium",
                "original_clause": {"clause_number": "8.1", "text": "Notice by email."},
                "issue_location": "Notice address is incomplete.",
                "citations": [],
                "revision_plan": {"balanced_clause": "Add notice addresses and deemed delivery rules."},
            },
        ],
    }


def test_scores_and_ranks_high_reviewable_risk_first():
    result = RiskScoringService().score_report(_report())

    assert result["overall_score"] >= 70
    assert result["overall_level"] == "high"
    assert result["top_risk_ids"][0] == "R-001"
    assert result["risk_scores"][0]["risk_id"] == "R-001"
    assert result["risk_scores"][0]["priority_rank"] == 1
    assert result["counts"] == {"critical": 0, "high": 1, "medium": 1, "low": 0}


def test_missing_grounding_citation_and_revision_are_penalized():
    report = _report()
    weak = report["risk_items"][0]
    weak["original_clause"] = {}
    weak["issue_location"] = ""
    weak["citations"] = []
    weak["revision_plan"] = {}

    result = RiskScoringService().score_report(report)
    weak_score = next(item for item in result["risk_scores"] if item["risk_id"] == "R-001")

    assert weak_score["penalty"] == 12
    assert weak_score["citation_score"] == 20
    assert weak_score["grounding_score"] == 25
    assert weak_score["revision_score"] == 25
    assert weak_score["evidence_confidence_score"] < 50


def test_apply_to_report_enriches_and_sorts_risk_items():
    service = RiskScoringService()
    report = _report()
    scoring = service.score_report(report)

    service.apply_to_report(report, scoring)

    assert report["risk_items"][0]["risk_id"] == "R-001"
    assert report["risk_items"][0]["risk_score"] == scoring["risk_scores"][0]["score"]
    assert report["risk_matrix"][0]["priority"] == 1
