from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


CLAUSE_TYPES = (
    "parties",
    "payment",
    "delivery",
    "term",
    "termination",
    "liability",
    "confidentiality",
    "dispute_resolution",
    "governing_law",
)
REQUIRED_CLAUSE_TYPES = {
    "parties",
    "payment",
    "delivery",
    "term",
    "termination",
    "liability",
    "dispute_resolution",
}
SENSITIVE_PATTERN = re.compile(
    r"(s" r"k-[A-Za-z0-9]{20,}|APP_AI_KEY=s" r"k-|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ClauseField:
    id: str
    label: str
    required: bool
    description: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ContractClauseExtractionSchemaService:
    """Define deterministic clause extraction and review metadata for contracts."""

    def build_schema(self, extracted_clauses: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        normalized = [self._normalize_clause(item) for item in extracted_clauses or []]
        missing_types = sorted(REQUIRED_CLAUSE_TYPES - {item["clause_type"] for item in normalized})
        clause_reviews = [self._review_clause(item) for item in normalized]
        risk_flags = self._risk_flags(clause_reviews, missing_types)

        if not extracted_clauses:
            status = "template"
        elif any(flag["severity"] == "blocking" for flag in risk_flags):
            status = "blocked"
        elif risk_flags:
            status = "review_recommended"
        else:
            status = "ready"

        return {
            "status": status,
            "summary": {
                "supported_clause_type_count": len(CLAUSE_TYPES),
                "submitted_clause_count": len(normalized),
                "required_clause_count": len(REQUIRED_CLAUSE_TYPES),
                "missing_required_clause_types": missing_types,
                "risk_flag_count": len(risk_flags),
                "ready_for_clause_level_review": status == "ready",
            },
            "schema_version": "contract-clause-extraction-v1",
            "clause_types": list(CLAUSE_TYPES),
            "required_clause_types": sorted(REQUIRED_CLAUSE_TYPES),
            "fields": [field.to_api() for field in self._fields()],
            "clause_reviews": clause_reviews,
            "risk_flags": risk_flags,
            "recommended_actions": self._recommended_actions(status, missing_types, risk_flags),
            "privacy_note": (
                "This privacy-safe schema accepts clause metadata and short labels only. Do not include raw "
                "contracts, client contact details, credentials, API keys, passwords, or full confidential text."
            ),
            "validation_commands": [
                "python -m pytest tests/test_contract_clause_extraction_schema.py -q",
                "python -m compileall services/contract_clause_extraction_schema.py tests/test_contract_clause_extraction_schema.py",
            ],
        }

    def _fields(self) -> tuple[ClauseField, ...]:
        return (
            ClauseField("clause_id", "Clause ID", True, "Stable local identifier for the extracted clause."),
            ClauseField("clause_type", "Clause type", True, "One of the supported clause type values."),
            ClauseField("heading", "Heading", True, "Short sanitized heading or label."),
            ClauseField("summary", "Summary", True, "Brief metadata-only summary of the clause effect."),
            ClauseField("risk_level", "Risk level", True, "low, medium, high, or critical."),
            ClauseField("source_anchor", "Source anchor", True, "Citation, page, section, or paragraph anchor."),
            ClauseField("proposed_edit_required", "Proposed edit required", False, "Whether replacement language is needed."),
            ClauseField("lawyer_review_required", "Lawyer review required", True, "Whether a lawyer must review before delivery."),
        )

    def _normalize_clause(self, item: dict[str, Any]) -> dict[str, Any]:
        def value(name: str, fallback: str = "") -> str:
            return self._sanitize(str(item.get(name) or fallback)).strip()

        risk_level = value("risk_level", "medium").lower()
        if risk_level not in {"low", "medium", "high", "critical"}:
            risk_level = "medium"

        clause_type = value("clause_type").lower()
        if clause_type not in CLAUSE_TYPES:
            clause_type = "unknown"

        return {
            "clause_id": value("clause_id", "clause-unspecified"),
            "clause_type": clause_type,
            "heading": value("heading", "Untitled clause"),
            "summary": value("summary", "Summary not supplied"),
            "risk_level": risk_level,
            "source_anchor": value("source_anchor"),
            "proposed_edit_required": bool(item.get("proposed_edit_required", risk_level in {"high", "critical"})),
            "lawyer_review_required": bool(item.get("lawyer_review_required", risk_level in {"high", "critical"})),
        }

    def _review_clause(self, clause: dict[str, Any]) -> dict[str, Any]:
        flags: list[str] = []
        if clause["clause_type"] == "unknown":
            flags.append("unsupported_clause_type")
        if not clause["source_anchor"]:
            flags.append("missing_source_anchor")
        if clause["risk_level"] in {"high", "critical"} and not clause["lawyer_review_required"]:
            flags.append("high_risk_without_lawyer_review")
        if clause["risk_level"] == "critical" and not clause["proposed_edit_required"]:
            flags.append("critical_clause_without_proposed_edit")

        return {
            **clause,
            "status": "blocked" if any(flag in BLOCKING_FLAGS for flag in flags) else ("warn" if flags else "pass"),
            "flags": flags,
        }

    def _risk_flags(self, reviews: list[dict[str, Any]], missing_types: list[str]) -> list[dict[str, Any]]:
        flags = [
            {
                "id": "missing-required-clause-types",
                "severity": "blocking",
                "message": "Required clause types are missing from the extraction result.",
                "clause_types": missing_types,
            }
        ] if missing_types else []

        for review in reviews:
            for flag in review["flags"]:
                flags.append(
                    {
                        "id": flag,
                        "severity": "blocking" if flag in BLOCKING_FLAGS else "warning",
                        "clause_id": review["clause_id"],
                        "clause_type": review["clause_type"],
                    }
                )
        return flags

    def _recommended_actions(
        self,
        status: str,
        missing_types: list[str],
        risk_flags: list[dict[str, Any]],
    ) -> list[str]:
        if status == "template":
            return ["Submit clause metadata after extraction to review readiness."]
        actions: list[str] = []
        if missing_types:
            actions.append("Extract or manually mark all required clause types before contract delivery.")
        if risk_flags:
            actions.append("Resolve blocking clause flags and route high-risk clauses to lawyer review.")
        if not actions:
            actions.append("Use clause reviews as input to risk grading and proposed edit drafting.")
        return actions

    def _sanitize(self, value: str) -> str:
        return SENSITIVE_PATTERN.sub("[redacted]", value)


BLOCKING_FLAGS = {
    "unsupported_clause_type",
    "missing_source_anchor",
    "high_risk_without_lawyer_review",
    "critical_clause_without_proposed_edit",
}
