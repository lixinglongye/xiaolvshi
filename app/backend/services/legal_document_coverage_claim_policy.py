from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from typing import Any

from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService


DOCUMENT_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "civil_complaint": ("civil complaint", "\u6c11\u4e8b\u8d77\u8bc9\u72b6", "\u8d77\u8bc9\u72b6"),
    "lawyer_letter": ("lawyer letter", "\u5f8b\u5e08\u51fd"),
    "contract_review": ("contract review", "\u5408\u540c\u5ba1\u67e5", "\u5408\u540c\u5ba1\u6838"),
    "evidence_catalog": ("evidence catalog", "\u8bc1\u636e\u76ee\u5f55"),
    "settlement_agreement": ("settlement agreement", "\u548c\u89e3\u534f\u8bae", "\u8c03\u89e3\u534f\u8bae"),
    "legal_opinion": ("legal opinion", "\u6cd5\u5f8b\u610f\u89c1\u4e66", "\u6cd5\u5f8b\u610f\u89c1"),
}

BROAD_COVERAGE_PATTERN = re.compile(
    r"\b(all|any|every|full|complete|universal)\s+(legal\s+)?documents?\b|"
    r"\bfull\s+coverage\b|"
    r"(\u6240\u6709|\u4efb\u4f55|\u5168\u90e8|\u5168\u7c7b\u578b|\u5168\u573a\u666f).{0,8}"
    r"(\u6cd5\u5f8b\u6587\u4e66|\u6587\u4e66)",
    re.I,
)
REAL_CLIENT_PATTERN = re.compile(
    r"\b(real client|production case|customer document|client document|law firm adoption)\b|"
    r"(\u771f\u5b9e\u5ba2\u6237|\u771f\u5b9e\u6848\u4ef6|\u751f\u4ea7\u73af\u5883|\u5f8b\u6240\u91c7\u7528)",
    re.I,
)
PUBLIC_BENCHMARK_PATTERN = re.compile(
    r"\b(legalbench|lexglue|coliee|leaderboard|public benchmark score)\b",
    re.I,
)
LOCAL_EVIDENCE_PATTERN = re.compile(
    r"\b(synthetic|fixture|local|repository|test|coverage matrix|metadata-only)\b|"
    r"(\u5408\u6210|\u672c\u5730|\u5c0f\u6837\u672c|\u6d4b\u8bd5|\u8986\u76d6\u77e9\u9635|\u4ed3\u5e93)",
    re.I,
)
UNSUPPORTED_DOCUMENT_HINTS = {
    "appeal_brief": re.compile(r"\bappeal brief\b|\u4e0a\u8bc9\u72b6|\u4e0a\u8bc9\u7b54\u8fa9", re.I),
    "arbitration_application": re.compile(r"\barbitration application\b|\u4ef2\u88c1\u7533\u8bf7", re.I),
    "bankruptcy_filing": re.compile(r"\bbankruptcy\b|\u7834\u4ea7\u7533\u8bf7", re.I),
}

PRIVACY_BOUNDARY = {
    "raw_claim_text_included": False,
    "client_document_text_included": False,
    "prompt_or_model_output_included": False,
    "pii_included": False,
    "secret_included": False,
    "output_scope": "claim hashes, matched document-type ids, reason codes, coverage counts, and status only",
}


class LegalDocumentCoverageClaimPolicyService:
    """Check legal-document coverage claims against the local synthetic fixture matrix."""

    def evaluate(self, claims: Iterable[Any] | None = None) -> dict[str, Any]:
        coverage = LegalDocumentBenchmarkCoverageService().build_matrix()
        covered_types = {
            row["label"]
            for row in coverage["dimensions"]["document_types"]
            if row.get("covered") is True
        }
        checks = [self._check_claim(str(claim or ""), covered_types) for claim in claims or []]
        blocked = [check for check in checks if check["status"] == "blocked"]
        review = [check for check in checks if check["status"] == "review_required"]
        status = "blocked" if blocked else "review_required" if review else "ready"

        return {
            "status": status,
            "policy_version": "legal-document-coverage-claim-policy-v1",
            "coverage_summary": {
                "coverage_status": coverage["status"],
                "target_document_type_count": coverage["summary"]["target_document_type_count"],
                "covered_document_type_count": coverage["summary"]["covered_document_type_count"],
                "missing_document_type_count": coverage["summary"]["missing_document_type_count"],
                "covered_document_types": sorted(covered_types),
                "source_endpoint": "/api/v1/maintenance/legal-review-benchmark/document-coverage",
            },
            "claim_checks": checks,
            "summary": {
                "claim_count": len(checks),
                "blocked_count": len(blocked),
                "review_required_count": len(review),
                "ready_count": sum(1 for check in checks if check["status"] == "ready"),
                "supported_type_claim_count": sum(1 for check in checks if check["matched_document_types"]),
                "unsupported_type_claim_count": sum(1 for check in checks if check["unsupported_document_types"]),
            },
            "recommended_actions": self._recommended_actions(status),
            "allowed_claim_template": (
                "Repository tests include synthetic local fixtures covering civil complaints, lawyer letters, "
                "contract review, evidence catalogs, settlement agreements, and legal opinions."
            ),
            "forbidden_claim_examples": [
                "Supports every legal document type.",
                "Validated on real client documents.",
                "Achieves public LegalBench leaderboard results.",
            ],
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }

    def _check_claim(self, claim: str, covered_types: set[str]) -> dict[str, Any]:
        matched_types = self._matched_document_types(claim)
        unsupported_types = self._unsupported_document_types(claim, covered_types, matched_types)
        reason_codes: list[str] = []

        if not claim.strip():
            reason_codes.append("empty_claim")
        if BROAD_COVERAGE_PATTERN.search(claim):
            reason_codes.append("broad_coverage_claim")
        if REAL_CLIENT_PATTERN.search(claim):
            reason_codes.append("real_client_or_production_claim")
        if PUBLIC_BENCHMARK_PATTERN.search(claim):
            reason_codes.append("public_benchmark_claim")
        if unsupported_types:
            reason_codes.append("unsupported_document_type_claim")
        if ("sk-" in claim.lower()) or ("@" in claim):
            reason_codes.append("sensitive_material_dropped")
        if matched_types and not LOCAL_EVIDENCE_PATTERN.search(claim):
            reason_codes.append("local_evidence_scope_missing")

        blocking_codes = {
            "broad_coverage_claim",
            "real_client_or_production_claim",
            "public_benchmark_claim",
            "unsupported_document_type_claim",
        }
        status = (
            "blocked"
            if any(code in blocking_codes for code in reason_codes)
            else "review_required"
            if reason_codes
            else "ready"
        )
        return {
            "claim_hash": hashlib.sha256(claim.encode("utf-8")).hexdigest()[:24],
            "status": status,
            "matched_document_types": sorted(matched_types),
            "unsupported_document_types": sorted(unsupported_types),
            "reason_codes": sorted(dict.fromkeys(reason_codes)),
        }

    def _matched_document_types(self, claim: str) -> set[str]:
        lower_claim = claim.lower()
        matched: set[str] = set()
        for document_type, aliases in DOCUMENT_TYPE_ALIASES.items():
            if any(alias.lower() in lower_claim for alias in aliases):
                matched.add(document_type)
        return matched

    def _unsupported_document_types(
        self,
        claim: str,
        covered_types: set[str],
        matched_types: set[str],
    ) -> set[str]:
        unsupported = {document_type for document_type in matched_types if document_type not in covered_types}
        for document_type, pattern in UNSUPPORTED_DOCUMENT_HINTS.items():
            if pattern.search(claim):
                unsupported.add(document_type)
        return unsupported

    def _recommended_actions(self, status: str) -> list[str]:
        if status == "ready":
            return ["Use only repository-backed synthetic fixture coverage claims."]
        if status == "blocked":
            return [
                "Replace broad, real-client, public-benchmark, or unsupported document-type claims with local fixture evidence.",
                "Name the covered synthetic document types and keep real client documents out of public release evidence.",
            ]
        return [
            "Add local/synthetic fixture wording to scoped document-type claims before publication.",
            "Have a maintainer review claim wording against the coverage matrix.",
        ]
