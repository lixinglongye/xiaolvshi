from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class IntakeRequirement:
    id: str
    title: str
    category: str
    required_fields: tuple[str, ...]
    evidence_needed: tuple[str, ...]
    blocks_next_step: bool
    reviewer_action: str

    def to_api(self, provided_fields: set[str]) -> dict[str, Any]:
        missing_fields = [field for field in self.required_fields if field not in provided_fields]
        data = asdict(self)
        data["required_fields"] = list(self.required_fields)
        data["evidence_needed"] = list(self.evidence_needed)
        data["missing_fields"] = missing_fields
        data["status"] = "complete" if not missing_fields else "missing"
        data["blocks"] = self.blocks_next_step and bool(missing_fields)
        return data


class CaseIntakeCompletenessService:
    """Evaluate whether case intake metadata is ready for drafting or review."""

    def build_checklist(self, intake: dict[str, Any] | None = None) -> dict[str, Any]:
        provided_fields = self._provided_fields(intake or {})
        requirements = [requirement.to_api(provided_fields) for requirement in self._requirements()]
        blockers = [item for item in requirements if item["blocks"]]
        missing = [item for item in requirements if item["status"] == "missing"]

        if intake is None:
            status = "template"
        elif blockers:
            status = "blocked"
        elif missing:
            status = "needs_review"
        else:
            status = "ready"

        return {
            "status": status,
            "summary": {
                "requirement_count": len(requirements),
                "complete_requirement_count": sum(1 for item in requirements if item["status"] == "complete"),
                "missing_requirement_count": len(missing),
                "blocking_requirement_count": len(blockers),
                "ready_for_document_generation": status == "ready",
                "ready_for_lawyer_review": status in {"ready", "needs_review"},
            },
            "requirements": requirements,
            "blocking_items": [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "missing_fields": item["missing_fields"],
                    "reviewer_action": item["reviewer_action"],
                }
                for item in blockers
            ],
            "next_actions": self._next_actions(blockers, missing),
            "validation_commands": [
                "python -m pytest tests/test_case_intake_completeness.py -q",
                "python -m pytest tests/test_case_evidence_graph.py tests/test_release_readiness.py -q",
            ],
            "privacy_note": (
                "This checklist uses field names and presence metadata only. It must not store raw client documents, "
                "private matter narratives, login credentials, API keys, user contact details, or model outputs."
            ),
        }

    def _requirements(self) -> tuple[IntakeRequirement, ...]:
        return (
            IntakeRequirement(
                id="party-identity",
                title="Party identity and roles",
                category="case_profile",
                required_fields=("client_name", "opposing_party", "party_roles"),
                evidence_needed=("identity materials", "organization or agency authorization when relevant"),
                blocks_next_step=True,
                reviewer_action="Confirm the legal relationship and whether the submitting user is authorized to act.",
            ),
            IntakeRequirement(
                id="jurisdiction-and-venue",
                title="Jurisdiction and venue",
                category="case_profile",
                required_fields=("jurisdiction", "venue_or_court", "case_type"),
                evidence_needed=("contract venue clause", "performance location", "defendant domicile when relevant"),
                blocks_next_step=True,
                reviewer_action="Select the applicable court or review path before generating filing-ready drafts.",
            ),
            IntakeRequirement(
                id="timeline-and-deadlines",
                title="Timeline and limitation deadlines",
                category="fact_timeline",
                required_fields=("key_dates", "deadline_risks"),
                evidence_needed=("contracts", "notices", "delivery records", "payment records"),
                blocks_next_step=True,
                reviewer_action="Check limitation periods, notice windows, and urgent preservation deadlines.",
            ),
            IntakeRequirement(
                id="claim-and-remedy",
                title="Claims, remedies, and target outcome",
                category="legal_strategy",
                required_fields=("claims", "requested_remedy", "desired_outcome"),
                evidence_needed=("loss calculation", "contract basis", "statutory basis when available"),
                blocks_next_step=True,
                reviewer_action="Confirm requested relief before drafting pleadings or negotiation letters.",
            ),
            IntakeRequirement(
                id="evidence-inventory",
                title="Evidence inventory and source support",
                category="evidence",
                required_fields=("evidence_items", "source_citations"),
                evidence_needed=("uploaded exhibits", "source excerpts", "page or clause anchors"),
                blocks_next_step=True,
                reviewer_action="Link each major fact to reviewable evidence before client delivery.",
            ),
            IntakeRequirement(
                id="risk-and-disclosure",
                title="Risk disclosure and lawyer review",
                category="delivery_safety",
                required_fields=("known_risks", "lawyer_review_required", "client_disclosure_acknowledged"),
                evidence_needed=("risk notes", "unsupported-fact list", "client-facing limitation notice"),
                blocks_next_step=False,
                reviewer_action="Route incomplete or high-risk matters to lawyer review before export.",
            ),
        )

    def _provided_fields(self, intake: dict[str, Any]) -> set[str]:
        provided: set[str] = set()
        for key, value in intake.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, (list, tuple, set, dict)) and not value:
                continue
            provided.add(str(key))
        return provided

    def _next_actions(self, blockers: list[dict[str, Any]], missing: list[dict[str, Any]]) -> list[str]:
        if blockers:
            return [
                "Collect the missing blocking fields before document generation.",
                "Keep the case in intake state until parties, venue, timeline, claims, and evidence are reviewable.",
                "Escalate urgent deadline or missing-authority matters to lawyer review.",
            ]
        if missing:
            return [
                "Allow lawyer review but keep client delivery blocked until non-blocking disclosures are acknowledged.",
                "Add missing risk notes and client-facing limitations before export.",
            ]
        return [
            "Proceed to lawyer review or document generation with source-backed fields.",
            "Archive the checklist result with the case audit trail before client delivery.",
        ]
