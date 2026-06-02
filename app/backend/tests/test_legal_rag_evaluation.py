from services.legal_rag_evaluation import LegalRagEvaluationService


def test_legal_rag_evaluation_passes_grounded_run():
    result = LegalRagEvaluationService().evaluate(
        {
            "expected_source_ids": ["CIVIL-143", "CIVIL-577"],
            "retrieved_source_ids": ["CIVIL-143", "CIVIL-577", "CIVIL-585"],
            "answer_citation_source_ids": ["CIVIL-143", "CIVIL-577"],
            "verified_claim_count": 6,
            "total_claim_count": 6,
            "unsupported_claims": [],
            "stale_source_ids": [],
            "pii_findings": [],
        }
    )

    assert result["status"] == "pass"
    assert result["score"] >= 90
    assert result["blocking_reasons"] == []


def test_legal_rag_evaluation_blocks_poor_retrieval_and_citations():
    result = LegalRagEvaluationService().evaluate(
        {
            "expected_source_ids": ["CIVIL-143", "CIVIL-577", "CIVIL-585"],
            "retrieved_source_ids": ["CIVIL-143"],
            "answer_citation_source_ids": ["UNKNOWN-1", "UNKNOWN-2"],
            "verified_claim_count": 1,
            "total_claim_count": 4,
            "unsupported_claims": [{"claim": "Penalty is always void.", "severity": "high"}],
            "stale_source_ids": ["CIVIL-143"],
        }
    )

    assert result["status"] == "fail"
    assert "Retrieval recall is below 50% for expected sources." in result["blocking_reasons"]
    assert "Citation precision is below 60%." in result["blocking_reasons"]
    assert "CIVIL-577" in result["coverage"]["missing_expected_source_ids"]


def test_legal_rag_evaluation_blocks_critical_pii():
    result = LegalRagEvaluationService().evaluate(
        {
            "expected_source_ids": [],
            "retrieved_source_ids": [],
            "answer_citation_source_ids": [],
            "verified_claim_count": 2,
            "total_claim_count": 2,
            "pii_findings": [{"type": "id_number", "severity": "critical"}],
        }
    )

    assert result["status"] == "fail"
    assert "Critical PII finding requires remediation." in result["blocking_reasons"]


def test_legal_rag_policy_exposes_required_inputs_and_weights():
    policy = LegalRagEvaluationService().policy()

    assert "retrieval_recall" in policy["metric_weights"]
    assert "expected_source_ids" in policy["evaluation_inputs"]
