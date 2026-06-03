from services.legal_grounding_quick_audit import LegalGroundingQuickAuditService


def _grounded_report() -> dict:
    return {
        "risk_items": [
            {
                "risk_id": "R-001",
                "risk_level": "high",
                "citations": [{"source_id": "LS-001"}],
                "legal_analysis": {"evidence_suggestion": ["Keep signed contract and delivery notices."]},
            },
            {
                "risk_id": "R-002",
                "risk_level": "medium",
                "citations": [{"source_id": "LS-002"}],
                "legal_analysis": {"evidence_suggestion": ["Save payment records."]},
            },
        ],
        "legal_authority_appendix": [
            {
                "source_id": "LS-001",
                "source_name": "Civil Code",
                "source_type": "law",
                "authority_level": "national law",
                "verification_status": "verified",
                "confidence": 95,
            },
            {
                "source_id": "LS-002",
                "source_name": "Contract Review Checklist",
                "source_type": "checklist",
                "authority_level": "practice reference",
                "verification_status": "verified",
                "confidence": 90,
            },
        ],
        "professional_review_framework": {
            "evidence_checklist": ["Signed contract", "Payment records", "Delivery notices"],
        },
        "pending_facts": [],
        "unsupported_claims": [],
    }


def test_grounding_quick_audit_passes_with_explicit_rag_run():
    report = _grounded_report()
    result = LegalGroundingQuickAuditService().evaluate(
        {
            "report": report,
            "rag_run": {
                "expected_source_ids": ["LS-001", "LS-002"],
                "retrieved_source_ids": ["LS-001", "LS-002"],
                "answer_citation_source_ids": ["LS-001", "LS-002"],
                "verified_claim_count": 2,
                "total_claim_count": 2,
                "unsupported_claims": [],
                "stale_source_ids": [],
                "pii_findings": [],
            },
        }
    )

    assert result["status"] == "pass"
    assert result["release_recommendation"] == "ready_for_lawyer_spot_check"
    assert result["summary"]["rag_run_source"] == "explicit"
    assert result["blocking_reasons"] == []
    assert "sk-" not in str(result)


def test_grounding_quick_audit_warns_when_rag_is_inferred():
    result = LegalGroundingQuickAuditService().evaluate({"report": _grounded_report()})

    assert result["status"] == "warn"
    assert result["summary"]["rag_run_source"] == "inferred_from_report"
    assert any("inferred" in reason for reason in result["warning_reasons"])


def test_grounding_quick_audit_blocks_ungrounded_high_risk_report():
    report = _grounded_report()
    report["risk_items"][0]["citations"] = []
    report["risk_items"][0]["legal_analysis"]["evidence_suggestion"] = []
    result = LegalGroundingQuickAuditService().evaluate(
        {
            "report": report,
            "rag_run": {
                "expected_source_ids": ["LS-001", "LS-002"],
                "retrieved_source_ids": ["LS-001"],
                "answer_citation_source_ids": ["UNKNOWN"],
                "verified_claim_count": 0,
                "total_claim_count": 2,
                "unsupported_claims": [{"claim": "Penalty is always void.", "severity": "high"}],
                "stale_source_ids": ["LS-001"],
                "pii_findings": [],
            },
        }
    )

    assert result["status"] == "fail"
    assert result["release_recommendation"] == "block_release_until_grounding_gaps_are_fixed"
    assert any(gap["type"] == "missing_reviewable_citation" for gap in result["grounding_gaps"])
    assert any(gap["type"] == "missing_evidence_plan" for gap in result["grounding_gaps"])
    assert "Unsupported high-impact legal claim." in result["blocking_reasons"]


def test_grounding_quick_audit_policy_and_route():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.legal_knowledge import router

    policy = LegalGroundingQuickAuditService().policy()
    assert "ragas" in [item["id"] for item in policy["method"]["research_basis"]]

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    policy_response = client.get("/api/v1/legal-knowledge/grounding-quick-audit-policy")
    assert policy_response.status_code == 200
    assert policy_response.json()["data"]["status"] == "ready"

    audit_response = client.post("/api/v1/legal-knowledge/grounding-quick-audit", json={"report": _grounded_report()})
    assert audit_response.status_code == 200
    assert audit_response.json()["data"]["summary"]["risk_count"] == 2
