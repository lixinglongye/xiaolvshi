import json

from services.case_ai_workbench import CaseAIWorkbenchService
from services.legal_rag_request_metadata import (
    legal_rag_citation_metadata,
    legal_rag_metadata_prompt_lines,
    sanitize_case_request_metadata,
)


def _raw_metadata():
    return {
        "schema_version": "case-request-metadata-v1",
        "source_component": "case_detail_page",
        "purpose": "case_document_generation",
        "document_type": "civil_complaint",
        "legal_rag_selected_source_ids": ["law:contract-001", "case_ref_002", "bad source with spaces"],
        "legal_rag": {
            "selected_source_ids": ["law:contract-001", "case_ref_002"],
            "selected_source_count": 2,
            "plan_status": "ready",
            "evaluation_status": "pass",
            "blocked": False,
            "freshness_statuses": ["active", "stale"],
            "coverage_counts": {"selected_source_count": 2, "raw_text_chars": "PRIVATE_TEXT"},
            "reason_codes": ["jurisdiction_match"],
            "metric_scores": {"citation_support": 0.92},
            "unsupported_claim_count": 0,
            "pii_finding_count": 0,
            "raw_legal_text": "PRIVATE_LEGAL_TEXT",
            "user_claim": "PRIVATE_USER_CLAIM",
            "email": "person@example.test",
            "phone": "13812345678",
        },
    }


def test_sanitize_case_request_metadata_keeps_only_safe_rag_fields():
    sanitized = sanitize_case_request_metadata(_raw_metadata())
    rendered = json.dumps(sanitized, ensure_ascii=False)

    assert sanitized is not None
    assert sanitized["legal_rag_selected_source_ids"] == ["law:contract-001", "case_ref_002"]
    assert sanitized["legal_rag"]["coverage_counts"] == {"selected_source_count": 2.0}
    assert sanitized["legal_rag"]["metric_scores"] == {"citation_support": 0.92}
    assert sanitized["legal_rag"]["privacy_boundary"] == {
        "raw_legal_text_included": False,
        "user_claims_included": False,
        "pii_included": False,
    }
    assert "PRIVATE_LEGAL_TEXT" not in rendered
    assert "PRIVATE_USER_CLAIM" not in rendered
    assert "person@example.test" not in rendered
    assert "13812345678" not in rendered


def test_prompt_lines_and_citation_metadata_use_selected_source_ids_only():
    sanitized = sanitize_case_request_metadata(_raw_metadata())
    lines = legal_rag_metadata_prompt_lines(sanitized)
    citation_metadata = legal_rag_citation_metadata(sanitized)
    rendered = "\n".join(lines)

    assert "law:contract-001, case_ref_002" in rendered
    assert "raw legal text, user claims, and PII are excluded" in rendered
    assert citation_metadata == {
        "legal_rag_selected_source_ids": ["law:contract-001", "case_ref_002"],
        "legal_rag_source_count": 2,
        "legal_rag_metadata_schema": "case-request-metadata-v1",
        "raw_legal_text_included": False,
        "user_claims_included": False,
        "pii_included": False,
    }


def test_case_ai_messages_include_safe_metadata_without_raw_text():
    service = CaseAIWorkbenchService(db=None)
    messages = service._build_messages(
        case_title="Synthetic Case",
        context_text="Case context",
        message="Need research",
        conversation_history=[],
        request_metadata=sanitize_case_request_metadata(_raw_metadata()),
    )
    rendered = "\n".join(message.content for message in messages)

    assert "selected_source_ids: law:contract-001, case_ref_002" in rendered
    assert "PRIVATE_LEGAL_TEXT" not in rendered
    assert "PRIVATE_USER_CLAIM" not in rendered
    assert "person@example.test" not in rendered
    assert "13812345678" not in rendered
