from __future__ import annotations

from copy import deepcopy
from typing import Any


class LegalDocumentTemplateMatrixService:
    """Build product coverage rules for legal document template delivery."""

    _LAWYER_REVIEW_GATE: dict[str, Any] = {
        "id": "lawyer-review-required",
        "label": "\u5f8b\u5e08\u590d\u6838",
        "critical": True,
        "required_before": ["client_delivery", "court_filing", "external_send", "archive_as_final"],
        "review_scope": [
            "party_identity_and_authorization",
            "facts_evidence_claims_or_opinions_consistency",
            "law_jurisdiction_deadline_and_amount_check",
            "format_signature_attachment_and_delivery_version",
        ],
        "failure_behavior": "If review fails, keep the document as draft and block final export or external delivery.",
    }

    _EXPORT_FORMATS = ["docx", "pdf", "markdown", "json"]

    def build_matrix(self) -> dict[str, Any]:
        rows = [self._document_row(item) for item in self._document_definitions()]
        return {
            "status": "ready",
            "method": {
                "type": "legal-document-template-coverage-delivery-matrix",
                "notes": [
                    "Tracks delivery requirements for legal-document generation as product rules, not model output.",
                    "Separates required input fields, formatting constraints, blockers, review gates, and export readiness.",
                    "Keeps lawyer review as a hard gate before any final external delivery.",
                ],
            },
            "summary": {
                "document_type_count": len(rows),
                "benchmark_document_type_count": len({row["benchmark_document_type"] for row in rows}),
                "review_gate_required_count": sum(1 for row in rows if row["review_gate"]["critical"]),
                "blocking_condition_count": sum(len(row["pre_generation_blockers"]) for row in rows),
                "export_format_count": len({fmt for row in rows for fmt in row["export_formats"]}),
                "ready_for_delivery_count": 0,
            },
            "lawyer_review_gate": deepcopy(self._LAWYER_REVIEW_GATE),
            "document_types": rows,
            "low_resource_validation_commands": [
                "python -m pytest tests/test_legal_document_template_matrix.py -q",
                "python -m pytest tests/test_legal_document_template_matrix.py tests/test_legal_document_benchmark_coverage.py -q",
                "python -m pytest tests/test_legal_fixture_prompt_pack.py -q",
            ],
            "delivery_policy": [
                "Generated documents remain drafts by default.",
                "Required fields, blockers, format checks, and lawyer review must all pass before final export.",
                "Client, court, counterparty, or third-party delivery must retain reviewed-version and export records.",
            ],
            "privacy_notes": [
                "The matrix stores template field names, delivery rules, and validation commands only.",
                "Real names, identity numbers, phone numbers, addresses, raw case facts, and full model outputs must not be stored here.",
                "Fixtures should use redacted placeholders and run privacy checks before export.",
            ],
        }

    def _document_row(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item["id"],
            "document_type": item["document_type"],
            "benchmark_document_type": item["benchmark_document_type"],
            "product_gap_closed": item["product_gap_closed"],
            "required_fields": item["required_fields"],
            "format_requirements": item["format_requirements"],
            "pre_generation_blockers": item["pre_generation_blockers"],
            "review_gate": deepcopy(self._LAWYER_REVIEW_GATE),
            "export_formats": item.get("export_formats", self._EXPORT_FORMATS),
            "delivery_checklist": [
                "all_required_fields_are_collected_and_sourced",
                "format_requirements_pass_automatic_or_manual_check",
                "blocking_conditions_are_cleared_with_audit_record",
                "lawyer_review_result_is_pass",
                "exported_file_matches_reviewed_version",
            ],
            "low_resource_validation_command": (
                "python -m pytest tests/test_legal_document_template_matrix.py -q"
            ),
            "privacy_notes": [
                "Use redacted fact summaries and field placeholders for local validation.",
                "Check attachments, comments, headers, footers, and metadata before export.",
            ],
        }

    def _document_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "civil-complaint",
                "benchmark_document_type": "civil_complaint",
                "document_type": "\u6c11\u4e8b\u8d77\u8bc9\u72b6",
                "product_gap_closed": "Turns litigation drafting into a filing-ready delivery flow.",
                "required_fields": [
                    "plaintiff_identity",
                    "defendant_identity",
                    "claims",
                    "facts_and_reasons",
                    "evidence_summary",
                    "filing_court",
                    "document_date",
                ],
                "format_requirements": [
                    "centered_standard_title",
                    "party_sections_are_separate",
                    "claims_are_numbered",
                    "facts_follow_timeline_or_legal_relationship",
                    "closing_has_court_signer_and_date",
                ],
                "pre_generation_blockers": [
                    "missing_party_identity_or_authorization",
                    "unclear_claim_amount_or_performance_request",
                    "unconfirmed_jurisdiction",
                    "core_evidence_not_linked_to_claimed_facts",
                ],
            },
            {
                "id": "defense-answer",
                "benchmark_document_type": "defense_answer",
                "document_type": "\u7b54\u8fa9\u72b6",
                "product_gap_closed": "Structures claim-by-claim response, defenses, and evidence references.",
                "required_fields": [
                    "respondent_identity",
                    "opposing_party_identity",
                    "case_number_or_cause",
                    "response_to_each_claim",
                    "fact_defenses",
                    "legal_basis",
                    "evidence_list",
                ],
                "format_requirements": [
                    "court_and_case_number_at_start",
                    "responses_follow_opposing_claim_order",
                    "fact_and_legal_defenses_are_separate",
                    "evidence_numbers_match_body_references",
                    "closing_has_party_agent_and_date",
                ],
                "pre_generation_blockers": [
                    "complaint_or_opposing_core_claims_missing",
                    "answer_deadline_not_confirmed",
                    "defense_fact_has_no_evidence_source",
                    "admission_waiver_or_settlement_language_without_authorization",
                ],
            },
            {
                "id": "evidence-catalog",
                "benchmark_document_type": "evidence_catalog",
                "document_type": "\u8bc1\u636e\u76ee\u5f55",
                "product_gap_closed": "Adds evidence numbering, proof purpose, source, and attachment export checks.",
                "required_fields": [
                    "evidence_number",
                    "evidence_name",
                    "evidence_source",
                    "proof_purpose",
                    "page_or_attachment_location",
                    "submission_target",
                    "submission_date",
                ],
                "format_requirements": [
                    "table_has_number_name_source_purpose_and_page",
                    "evidence_numbers_are_unique",
                    "proof_purpose_maps_to_fact_or_dispute",
                    "attachment_names_match_catalog_numbers",
                    "page_count_copy_count_and_original_status_are_listed",
                ],
                "pre_generation_blockers": [
                    "unnamed_or_unnumbered_attachment_exists",
                    "proof_purpose_empty_or_irrelevant",
                    "source_authenticity_or_collection_method_unmarked",
                    "catalog_pages_do_not_match_attachment_pages",
                ],
            },
            {
                "id": "lawyer-letter",
                "benchmark_document_type": "lawyer_letter",
                "document_type": "\u5f8b\u5e08\u51fd",
                "product_gap_closed": "Adds authorization, fact, risk, and sending gates to external letters.",
                "required_fields": [
                    "client_identity",
                    "recipient_identity",
                    "authorization_scope",
                    "fact_summary",
                    "rights_claimed",
                    "performance_demand",
                    "reply_deadline",
                    "law_firm_signature_block",
                ],
                "format_requirements": [
                    "title_recipient_body_demands_and_closing_are_clear",
                    "facts_avoid_unverified_conclusions",
                    "demand_has_deadline_method_and_consequence_notice",
                    "closing_has_handling_lawyer_firm_and_date",
                    "sending_version_matches_client_confirmed_version",
                ],
                "pre_generation_blockers": [
                    "client_authorization_scope_unconfirmed",
                    "key_fact_or_amount_unverified",
                    "reply_deadline_unreasonable_or_unenforceable",
                    "letter_may_create_improper_threat_misleading_statement_or_overcommitment",
                ],
            },
            {
                "id": "contract-review-report",
                "benchmark_document_type": "contract_review",
                "document_type": "\u5408\u540c\u5ba1\u67e5\u62a5\u544a",
                "product_gap_closed": "Breaks contract review into risks, clauses, amendment advice, and review conclusion.",
                "required_fields": [
                    "contract_name",
                    "transaction_background",
                    "review_goal",
                    "key_clause_list",
                    "risk_level",
                    "amendment_advice",
                    "open_questions",
                    "review_conclusion",
                ],
                "format_requirements": [
                    "quote_original_location_by_clause_number",
                    "risk_level_reason_and_advice_are_separate",
                    "major_risks_are_prioritized",
                    "open_questions_and_client_confirmations_are_separate",
                    "ending_has_scope_limit_and_lawyer_review_conclusion",
                ],
                "pre_generation_blockers": [
                    "contract_version_or_attachment_incomplete",
                    "review_goal_missing",
                    "transaction_background_or_governing_law_missing",
                    "major_clause_cannot_be_mapped_to_original_location",
                ],
            },
            {
                "id": "settlement-agreement",
                "benchmark_document_type": "settlement_agreement",
                "document_type": "\u548c\u89e3\u534f\u8bae",
                "product_gap_closed": "Adds performance terms, default liability, authorization, and signing checks.",
                "required_fields": [
                    "party_identities",
                    "dispute_background",
                    "settlement_amount_or_obligation",
                    "performance_deadline",
                    "payment_or_delivery_method",
                    "default_liability",
                    "confidentiality_clause",
                    "signing_arrangement",
                ],
                "format_requirements": [
                    "parties_background_obligations_default_and_dispute_resolution_are_chaptered",
                    "amount_deadline_and_account_like_fields_use_structured_placeholders",
                    "one_time_and_installment_performance_are_distinct",
                    "signature_page_matches_attachment_list",
                    "version_number_is_locked_before_final_export",
                ],
                "pre_generation_blockers": [
                    "party_authorization_or_signer_unclear",
                    "performance_obligation_unenforceable_or_acceptance_standard_missing",
                    "default_liability_not_matched_to_settlement_obligation",
                    "withdrawal_preservation_release_or_security_arrangement_path_missing",
                ],
            },
            {
                "id": "legal-opinion",
                "benchmark_document_type": "legal_opinion",
                "document_type": "\u6cd5\u5f8b\u610f\u89c1\u4e66",
                "product_gap_closed": "Adds engagement scope, assumptions, legal basis, analysis, conclusion limits, and delivery checks to opinion drafting.",
                "required_fields": [
                    "client_or_instructing_party",
                    "engagement_scope",
                    "reviewed_materials",
                    "facts_and_assumptions",
                    "legal_issues",
                    "legal_basis",
                    "analysis_and_reasoning",
                    "conclusion_and_limitations",
                ],
                "format_requirements": [
                    "scope_assumptions_basis_analysis_and_conclusion_are_separate",
                    "materials_reviewed_are_listed_before_analysis",
                    "legal_basis_citations_map_to_each_issue",
                    "conclusion_uses_limited_and_conditioned_language",
                    "lawyer_review_and_issue_date_are_present_before_delivery",
                ],
                "pre_generation_blockers": [
                    "engagement_scope_or_reliance_party_unclear",
                    "reviewed_materials_incomplete_or_unverified",
                    "legal_issue_requires_jurisdiction_or_date_confirmation",
                    "conclusion_requested_beyond_available_facts_or_authority",
                ],
            },
        ]
