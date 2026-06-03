from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


ChecklistSeverity = Literal["blocking", "required", "advisory"]


@dataclass(frozen=True)
class DeliveryChecklistItem:
    id: str
    title: str
    severity: ChecklistSeverity
    owner: str
    product_gap: str
    required_evidence: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    client_visible: bool = True

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_evidence"] = list(self.required_evidence)
        data["acceptance_criteria"] = list(self.acceptance_criteria)
        return data


@dataclass(frozen=True)
class DeliveryDisclosure:
    id: str
    audience: Literal["client", "lawyer", "internal"]
    i18n_key: str
    display_text: str
    acceptance_signal: str
    required_before_delivery: bool

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ClientDeliveryRiskChecklistService:
    """Builds a deterministic pre-delivery checklist for legal AI outputs."""

    def build_checklist(self) -> dict[str, Any]:
        checklist_items = [item.to_api() for item in self._checklist_items()]
        disclosures = [disclosure.to_api() for disclosure in self._disclosures()]
        blocking_items = [item for item in checklist_items if item["severity"] == "blocking"]

        client_disclosures = [
            disclosure
            for disclosure in disclosures
            if disclosure["audience"] == "client"
        ]
        lawyer_disclosures = [
            disclosure
            for disclosure in disclosures
            if disclosure["audience"] == "lawyer"
        ]

        return {
            "status": "ready",
            "purpose": "Prevent client delivery of legal AI output until disclosure, evidence, and lawyer-review gates are satisfied.",
            "delivery_allowed_by_default": False,
            "checklist_items": checklist_items,
            "blocking_items": blocking_items,
            "client_disclosures": client_disclosures,
            "lawyer_review_items": self._lawyer_review_items(),
            "displayable_statements": {
                "client": client_disclosures,
                "lawyer": lawyer_disclosures,
                "internal": [
                    disclosure
                    for disclosure in disclosures
                    if disclosure["audience"] == "internal"
                ],
            },
            "perspectives": {
                "client": {
                    "summary": "Plain-language risk notice for a client who needs to understand what was checked and what remains uncertain.",
                    "must_see_before_delivery": [
                        "AI output is a draft analysis aid, not a substitute for independent legal advice.",
                        "Citation and evidence gaps must be clearly marked before the client relies on any conclusion.",
                        "Jurisdiction, deadline, and fact assumptions must be visible in the delivery package.",
                    ],
                },
                "lawyer": {
                    "summary": "Professional-review gate for the responsible lawyer before releasing any client-facing result.",
                    "must_confirm_before_delivery": [
                        "Legal conclusions are reviewed against the matter facts and controlling sources.",
                        "Unsupported claims are removed, caveated, or linked to traceable evidence.",
                        "Client instructions, scope limits, conflicts, and filing deadlines are not inferred by the model.",
                    ],
                },
            },
            "audit_record_requirements": self._audit_record_requirements(),
            "low_resource_validation_commands": [
                {
                    "id": "client-delivery-risk-checklist-tests",
                    "command": "python -m pytest tests/test_client_delivery_risk_checklist.py -q",
                    "resource_note": "Runs deterministic unit tests only; no network, model call, or large fixture is required.",
                },
                {
                    "id": "payload-credential-address-scan",
                    "command": "rg -n \"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}|(?i)(pwd|pass\\\\s*word|token)\\\\s*[:=]\" app/backend/services/client_delivery_risk_checklist.py app/backend/tests/test_client_delivery_risk_checklist.py docs/CLIENT_DELIVERY_RISK_CHECKLIST.md",
                    "resource_note": "Expected result is no matches.",
                },
            ],
            "privacy_notes": [
                "Checklist output must use matter IDs or document IDs instead of raw client names.",
                "Delivery logs should store acknowledgement status and evidence references, not full client narratives.",
                "Client-facing downloads should redact personal identifiers unless the responsible lawyer approves inclusion.",
            ],
            "future_api": {
                "suggested_endpoint": "GET /api/v1/client-delivery/risk-checklist",
                "suggested_post_gate": "POST /api/v1/client-delivery/risk-checklist/evaluate",
                "integration_note": "Wire this service after existing citation, evidence, and lawyer-review checks can provide real pass or fail states.",
            },
        }

    def _checklist_items(self) -> tuple[DeliveryChecklistItem, ...]:
        return (
            DeliveryChecklistItem(
                id="citation-evidence-required",
                title="Every legal conclusion has citation or evidence support",
                severity="blocking",
                owner="responsible_lawyer",
                product_gap="AI drafts can currently be delivered without proving source grounding to the client.",
                required_evidence=(
                    "citation_ids",
                    "evidence_document_ids",
                    "quote_or_page_reference",
                ),
                acceptance_criteria=(
                    "Each client-visible conclusion links to a cited authority, uploaded evidence, or explicit uncertainty note.",
                    "Unsupported conclusions are blocked from final delivery.",
                    "The delivery package keeps a compact evidence appendix that a reviewer can inspect.",
                ),
            ),
            DeliveryChecklistItem(
                id="lawyer-review-required",
                title="Responsible lawyer review is complete",
                severity="blocking",
                owner="responsible_lawyer",
                product_gap="Legal AI output must not bypass professional judgment before client delivery.",
                required_evidence=(
                    "reviewer_id",
                    "review_completed_at",
                    "review_decision",
                ),
                acceptance_criteria=(
                    "A lawyer records approve, revise, or reject before the client receives the output.",
                    "Material caveats and scope limits are written in client-readable language.",
                    "Rejected or superseded AI drafts are not exposed as final advice.",
                ),
            ),
            DeliveryChecklistItem(
                id="scope-and-assumption-disclosure",
                title="Scope, assumptions, and unknown facts are disclosed",
                severity="blocking",
                owner="case_owner",
                product_gap="Clients need a clear boundary between verified facts, assumptions, and unknowns.",
                required_evidence=(
                    "scope_statement",
                    "assumption_list",
                    "open_fact_list",
                ),
                acceptance_criteria=(
                    "Delivery text separates known facts, assumptions, and items needing client confirmation.",
                    "The client can see what information would change the conclusion.",
                    "Urgent deadlines and jurisdiction limits are surfaced when present.",
                ),
            ),
            DeliveryChecklistItem(
                id="not-legal-advice-disclosure",
                title="AI limitation statement is visible",
                severity="required",
                owner="product",
                product_gap="Client-facing screens need internationalized language saying the AI draft is not legal advice.",
                required_evidence=(
                    "i18n_key:delivery.disclosure.not_legal_advice",
                    "client_acknowledgement_status",
                ),
                acceptance_criteria=(
                    "The disclosure appears before export, share, or send actions.",
                    "The client must acknowledge the disclosure for self-service delivery flows.",
                    "The English internal key contains not legal advice for localization review.",
                ),
            ),
            DeliveryChecklistItem(
                id="risk-language-readable",
                title="Risk disclosure is understandable to the client",
                severity="required",
                owner="legal_operations",
                product_gap="Dense legal caveats can hide important delivery risk from non-lawyer clients.",
                required_evidence=(
                    "plain_language_summary",
                    "risk_level_labels",
                    "next_step_recommendations",
                ),
                acceptance_criteria=(
                    "Risk levels use clear labels such as low, medium, high, or blocked.",
                    "The client receives concrete next steps rather than only internal reviewer notes.",
                    "Technical model-quality language is translated into practical client impact.",
                ),
            ),
        )

    def _disclosures(self) -> tuple[DeliveryDisclosure, ...]:
        return (
            DeliveryDisclosure(
                id="not-legal-advice",
                audience="client",
                i18n_key="delivery.disclosure.not_legal_advice",
                display_text="This AI-generated draft is not legal advice and must be reviewed by a qualified lawyer before you rely on it.",
                acceptance_signal="client_acknowledged_not_legal_advice",
                required_before_delivery=True,
            ),
            DeliveryDisclosure(
                id="lawyer-review",
                audience="client",
                i18n_key="delivery.disclosure.lawyer_review_required",
                display_text="A lawyer review is required because legal outcomes depend on jurisdiction, facts, timing, and source authority.",
                acceptance_signal="client_acknowledged_lawyer_review_required",
                required_before_delivery=True,
            ),
            DeliveryDisclosure(
                id="evidence-boundary",
                audience="client",
                i18n_key="delivery.disclosure.evidence_boundary",
                display_text="Conclusions without a linked source or uploaded evidence are marked as uncertain and should not be treated as final.",
                acceptance_signal="client_acknowledged_evidence_boundary",
                required_before_delivery=True,
            ),
            DeliveryDisclosure(
                id="professional-duty",
                audience="lawyer",
                i18n_key="delivery.lawyer.professional_duty_review",
                display_text="Confirm the draft satisfies professional duties, scope limits, client instructions, and citation grounding before release.",
                acceptance_signal="lawyer_confirmed_professional_review",
                required_before_delivery=True,
            ),
            DeliveryDisclosure(
                id="audit-policy",
                audience="internal",
                i18n_key="delivery.internal.audit_policy",
                display_text="Record delivery decision, reviewer, citation coverage, disclosure acknowledgement, and redaction status for each release.",
                acceptance_signal="audit_record_created",
                required_before_delivery=True,
            ),
        )

    def _lawyer_review_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "source-grounding-review",
                "title": "Review citation and evidence grounding",
                "must_confirm": [
                    "Each legal conclusion has a source, evidence link, or explicit caveat.",
                    "Quoted authority is not taken out of context.",
                    "Client-visible uncertainty is not softened into a definitive conclusion.",
                ],
            },
            {
                "id": "client-reliance-review",
                "title": "Review reliance and delivery risk",
                "must_confirm": [
                    "The output does not present the AI as a lawyer or final legal opinion.",
                    "Known fact gaps, jurisdiction limits, and deadline risks are disclosed.",
                    "Recommended next steps fit the client's actual matter scope.",
                ],
            },
            {
                "id": "privacy-redaction-review",
                "title": "Review privacy and redaction",
                "must_confirm": [
                    "Personal identifiers are redacted from examples, audit samples, and support exports unless needed.",
                    "Matter data used in the delivery record is minimized.",
                    "Client acknowledgement records avoid storing unnecessary narrative detail.",
                ],
            },
        ]

    def _audit_record_requirements(self) -> list[dict[str, Any]]:
        return [
            {
                "field": "delivery_decision",
                "reason": "Shows whether the item was approved, revised, blocked, or withdrawn.",
                "retention_note": "Store decision state and timestamp; avoid duplicating full generated text when an immutable document version exists.",
            },
            {
                "field": "lawyer_review",
                "reason": "Proves a responsible lawyer reviewed the draft before client delivery.",
                "retention_note": "Store reviewer reference, review outcome, and material caveat summary.",
            },
            {
                "field": "citation_coverage",
                "reason": "Supports later dispute review when a client asks why a conclusion was shown.",
                "retention_note": "Store source IDs, evidence IDs, and unsupported conclusion count.",
            },
            {
                "field": "client_disclosure_acknowledgement",
                "reason": "Shows the client saw key limitations before export, share, or send.",
                "retention_note": "Store acknowledgement status and disclosure version, not extra personal details.",
            },
            {
                "field": "redaction_status",
                "reason": "Confirms delivery artifacts avoid unnecessary exposure of personal identifiers.",
                "retention_note": "Store redaction state and reviewer reference for exceptions.",
            },
        ]
