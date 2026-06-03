import json

from services.legal_rag_selected_source_validation import (
    LegalRagSelectedSourceValidationService,
    validate_selected_source_citations,
)


def test_selected_source_citation_validation_passes_for_selected_citations_only():
    result = validate_selected_source_citations(
        request_metadata={
            "legal_rag_selected_source_ids": ["law:contract-001", "case_ref_002"],
            "legal_rag": {"selected_source_ids": ["law:contract-001", "case_ref_002"]},
        },
        citation_map={
            "sections": [
                {"paragraph": "intro", "source_id": "law:contract-001"},
                {"paragraph": "analysis", "source_ids": ["case_ref_002"]},
            ],
        },
    )

    assert result["status"] == "pass"
    assert result["selected_source_ids"] == ["law:contract-001", "case_ref_002"]
    assert result["cited_source_ids"] == ["law:contract-001", "case_ref_002"]
    assert result["unexpected_source_ids"] == []
    assert result["missing_selected_source_ids"] == []
    assert result["reason_codes"] == []
    assert result["privacy_boundary"] == {
        "raw_legal_text_included": False,
        "user_claims_included": False,
        "pii_included": False,
        "output_scope": "sanitized source identifiers, status, counts, and reason codes only",
    }


def test_selected_source_citation_validation_blocks_stale_unknown_unexpected_and_missing_sources():
    result = LegalRagSelectedSourceValidationService().validate(
        request_metadata={
            "legal_rag_selected_source_ids": [
                "law:contract-001",
                "stale-statute",
                "unknown-guidance",
                "missing-template",
            ],
            "legal_rag": {
                "stale_source_ids": ["stale-statute"],
                "unknown_source_ids": ["unknown-guidance"],
            },
        },
        citation_map={
            "citations": [
                {"source_id": "law:contract-001"},
                {"source_id": "stale-statute"},
                {"source_id": "unknown-guidance"},
                {"source_id": "external-source"},
            ],
        },
    )

    assert result["status"] == "blocked"
    assert result["unexpected_source_ids"] == ["external-source"]
    assert result["missing_selected_source_ids"] == ["missing-template"]
    assert result["stale_source_ids"] == ["stale-statute"]
    assert result["unknown_source_ids"] == ["unknown-guidance", "external-source"]
    assert set(result["reason_codes"]) == {
        "unexpected_cited_source_ids",
        "stale_cited_source_ids",
        "unknown_cited_source_ids",
        "missing_selected_source_citations",
    }


def test_selected_source_citation_validation_cleans_duplicate_and_invalid_source_ids():
    result = validate_selected_source_citations(
        request_metadata={
            "legal_rag_selected_source_ids": [
                "law:001",
                "law:001",
                "bad source with spaces",
                None,
                "law:002",
            ],
        },
        generation_plan={
            "outline": [
                {
                    "title": "Synthetic section",
                    "source_ids": [
                        "law:001",
                        "bad cited source with spaces",
                        "law:001",
                        "law:002",
                    ],
                }
            ]
        },
    )

    assert result["selected_source_ids"] == ["law:001", "law:002"]
    assert result["cited_source_ids"] == ["law:001", "law:002"]
    assert result["unexpected_source_ids"] == []
    assert result["missing_selected_source_ids"] == []
    assert result["counts"]["invalid_selected_source_id_count"] == 2
    assert result["counts"]["duplicate_selected_source_id_count"] == 1
    assert result["counts"]["invalid_cited_source_id_count"] == 1
    assert result["counts"]["duplicate_cited_source_id_count"] == 1
    assert "invalid_selected_source_ids_dropped" in result["reason_codes"]
    assert "duplicate_selected_source_ids_dropped" in result["reason_codes"]
    assert "invalid_cited_source_ids_dropped" in result["reason_codes"]
    assert "duplicate_cited_source_ids_dropped" in result["reason_codes"]
    assert "bad source with spaces" not in json.dumps(result, ensure_ascii=False)
    assert "bad cited source with spaces" not in json.dumps(result, ensure_ascii=False)


def test_selected_source_citation_validation_does_not_echo_raw_text_claims_or_pii():
    raw_legal_text = "原始证据正文-不得回显"
    user_claim = "用户主张-不得回显"
    email = "person@example.test"
    phone = "13812345678"

    result = validate_selected_source_citations(
        request_metadata={
            "legal_rag_selected_source_ids": ["law:contract-001"],
            "raw_legal_text": raw_legal_text,
            "user_claim": user_claim,
            "email": email,
            "phone": phone,
            "legal_rag": {
                "selected_source_ids": ["law:contract-001"],
                "raw_legal_text": raw_legal_text,
                "user_claim": user_claim,
            },
        },
        citation_map={
            "citations": [
                {"source_id": "law:contract-001", "quote": raw_legal_text},
                {"source_id": raw_legal_text},
                {"source_id": phone},
            ],
            "user_claim": user_claim,
            "pii": {"email": email, "phone": phone},
        },
        generation_plan={
            "draft_summary": raw_legal_text,
            "claim": user_claim,
            "contact": email,
        },
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "pass_with_warnings"
    assert result["selected_source_ids"] == ["law:contract-001"]
    assert result["cited_source_ids"] == ["law:contract-001"]
    assert result["counts"]["invalid_cited_source_id_count"] == 2
    assert raw_legal_text not in rendered
    assert user_claim not in rendered
    assert email not in rendered
    assert phone not in rendered
