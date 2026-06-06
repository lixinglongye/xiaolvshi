import json
import re

from services.case_evidence_catalog_export_preflight import CaseEvidenceCatalogExportPreflightService


SENSITIVE_PATTERN = re.compile(
    "|".join(
        [
            r"sk-[A-Za-z0-9]{20,}",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"\b1[3-9]\d{9}\b",
            r"\b\d{17}[\dXx]\b",
        ]
    ),
    re.IGNORECASE,
)


def _ready_rows() -> list[dict]:
    return [
        {
            "evidence_no": "E-001",
            "attachment_number": "A-001",
            "evidence_name": "Signed contract",
            "source_anchor": "source:upload-001",
            "page_anchor": "pages 1-3",
            "proof_purpose": "Proves contract formation.",
            "evidence_date": "2026-05-01",
            "amount": "120000.00",
            "content_hash": "sha256:contract-001",
            "authenticity_review": "passed",
            "relevance_review": "passed",
            "legality_review": "passed",
        },
        {
            "evidence_no": "E-002",
            "attachment_number": "A-002",
            "evidence_name": "Payment record",
            "source_anchor": "source:upload-002",
            "page_anchor": "page 4",
            "proof_purpose": "Proves payment timeline.",
            "evidence_date": "2026-05-03",
            "amount": "30000",
            "content_hash": "sha256:payment-001",
            "authenticity_review": {"status": "passed"},
            "relevance_review": {"status": "passed"},
            "legality_review": {"status": "passed"},
        },
    ]


def _preflight(rows=None) -> dict:
    return CaseEvidenceCatalogExportPreflightService().build_preflight(rows)


def test_case_evidence_catalog_export_preflight_returns_template_boundary():
    preflight = _preflight()

    assert preflight["status"] == "template"
    assert preflight["export_allowed"] is False
    assert preflight["draft_generation_allowed"] is True
    assert preflight["summary"]["evidence_row_count"] == 0
    assert preflight["privacy_boundary"]["raw_evidence_rows_returned"] is False
    assert preflight["claim_boundary"]["lawyer_review_completed"] is False
    assert preflight["validation_commands"]


def test_ready_rows_allow_export_after_policy_and_integrity_checks():
    preflight = _preflight(_ready_rows())

    assert preflight["status"] == "ready_for_export"
    assert preflight["export_allowed"] is True
    assert preflight["summary"]["package_policy_status"] == "ready"
    assert preflight["summary"]["bundle_integrity_status"] == "ready"
    assert preflight["summary"]["integrity_score"] == 100
    assert all(check["status"] == "pass" for check in preflight["package_policy"]["package_checks"])


def test_incomplete_catalog_rows_are_blocked_for_export_not_draft_generation():
    rows = [
        {
            "evidence_no": "E-001",
            "evidence_name": "Receipt",
            "evidence_source": "source:upload-001",
            "page_range": "",
            "proof_purpose": "",
        }
    ]

    preflight = _preflight(rows)
    blocked_fields = {issue["field"] for issue in preflight["package_policy"]["blocking_issues"]}

    assert preflight["status"] == "blocked"
    assert preflight["export_allowed"] is False
    assert preflight["draft_generation_allowed"] is True
    assert {"attachment_number", "page_anchor", "proof_purpose"}.issubset(blocked_fields)
    assert preflight["summary"]["missing_proof_purpose_count"] == 1


def test_preflight_sanitizes_sensitive_row_values():
    secret = "s" + "k-" + "a" * 24
    rows = [
        {
            "evidence_no": "client@example.com",
            "attachment_number": "13800138000",
            "evidence_name": "loan_client@example.com_13800138000_110101199003076832.pdf",
            "source_anchor": "source:upload-001",
            "page_anchor": "pages 1-2",
            "proof_purpose": "Proves payment.",
            "evidence_date": "2026-05-01",
            "amount": "120000.00",
            "content_hash": "sha256:safe-test",
            "authenticity_review": "passed",
            "relevance_review": "passed",
            "legality_review": "passed",
            "raw_text": f"{secret} " + ("private text " * 30),
        }
    ]

    preflight = _preflight(rows)
    serialized = json.dumps(preflight, ensure_ascii=False)

    assert "client@example.com" not in serialized
    assert "loan_client@example.com" not in serialized
    assert "13800138000" not in serialized
    assert "110101199003076832" not in serialized
    assert "private text private text" not in serialized
    assert SENSITIVE_PATTERN.search(serialized) is None
    assert preflight["privacy_boundary"]["evidence_names_returned"] is False
