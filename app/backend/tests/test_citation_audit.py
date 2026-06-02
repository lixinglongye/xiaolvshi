from services.citation_audit import CitationAuditService


def _base_report() -> dict:
    return {
        "risk_items": [
            {
                "risk_id": "R-001",
                "risk_level": "high",
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
            },
            {
                "risk_id": "R-002",
                "risk_level": "medium",
                "citations": [
                    {
                        "source_id": "LS-002",
                        "source_name": "Practice Checklist",
                        "source_type": "checklist",
                        "authority_level": "practice reference",
                        "verification_status": "pending",
                    }
                ],
            },
        ],
        "legal_authority_appendix": [
            {
                "source_id": "LS-001",
                "source_name": "Civil Code",
                "source_type": "law",
                "authority_level": "national law",
                "verification_status": "verified",
                "confidence": 90,
                "cited_by_risks": ["R-001"],
            },
            {
                "source_id": "LS-002",
                "source_name": "Practice Checklist",
                "source_type": "checklist",
                "authority_level": "practice reference",
                "verification_status": "pending",
                "cited_by_risks": ["R-002"],
            },
        ],
    }


def test_citation_audit_passes_reviewable_sources():
    result = CitationAuditService().evaluate(_base_report())

    assert result["status"] == "pass"
    assert result["source_count"] == 2
    assert result["citation_count"] == 2
    assert result["verified_ratio"] == 0.5
    assert result["reviewable_ratio"] == 1.0
    assert result["risk_citation_coverage"] == 1.0
    assert result["high_risk_without_reviewable_citation"] == []
    assert result["source_type_counts"]["law"] == 1
    assert result["source_type_counts"]["practice_reference"] == 1


def test_citation_audit_fails_high_risk_without_reviewable_citation():
    report = _base_report()
    report["risk_items"][0]["citations"] = [{"source_id": "LS-003"}]
    report["legal_authority_appendix"] = []

    result = CitationAuditService().evaluate(report)

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["high_risk_without_reviewable_citation"] == ["R-001"]
    assert "Add a legal authority appendix before external delivery." in result["recommended_actions"]


def test_citation_audit_resolves_source_id_only_citations_from_appendix():
    report = _base_report()
    report["risk_items"][0]["citations"] = [{"source_id": "LS-001"}]

    result = CitationAuditService().evaluate(report)

    assert result["status"] == "pass"
    assert result["high_risk_without_reviewable_citation"] == []
    assert result["high_risk_without_verified_citation"] == []


def test_citation_audit_warns_on_weak_duplicate_and_missing_appendix_sources():
    report = _base_report()
    report["legal_authority_appendix"].append(
        {
            "source_id": "LS-002",
            "source_name": "",
            "source_type": "",
            "authority_level": "",
            "verification_status": "pending",
        }
    )
    report["risk_items"][1]["citations"].append(
        {
            "source_id": "LS-999",
            "source_name": "Missing appendix source",
            "source_type": "law",
            "authority_level": "national law",
            "verification_status": "pending",
        }
    )

    result = CitationAuditService().evaluate(report)

    assert result["status"] == "warn"
    assert "LS-002" in result["duplicate_source_ids"]
    assert "LS-002" in result["weak_source_ids"]
    assert result["missing_appendix_source_ids"] == ["LS-999"]
    assert any("Hydrate missing appendix sources" in action for action in result["recommended_actions"])
