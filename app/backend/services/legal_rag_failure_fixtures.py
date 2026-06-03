from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PASS_THRESHOLD = 85
WARN_THRESHOLD = 60


@dataclass(frozen=True)
class FailureTaxonomyItem:
    id: str
    title: str
    severity: str
    deterministic_signal: str
    reviewer_action: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RagFailureCase:
    id: str
    title: str
    scenario: str
    user_question: str
    retrieved_context: tuple[dict[str, str], ...]
    unsafe_answer: str
    expected_failure_labels: tuple[str, ...]
    expected_evidence_signals: tuple[str, ...]
    acceptable_actions: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["retrieved_context"] = [dict(item) for item in self.retrieved_context]
        data["expected_failure_labels"] = list(self.expected_failure_labels)
        data["expected_evidence_signals"] = list(self.expected_evidence_signals)
        data["acceptable_actions"] = list(self.acceptable_actions)
        return data


class LegalRagFailureFixturesService:
    """Small local fixtures for deterministic legal RAG failure detection tests."""

    def build_suite(self) -> dict[str, Any]:
        cases = [case.to_api() for case in self._cases()]
        taxonomy = [item.to_api() for item in self._failure_taxonomy()]
        return {
            "status": "ready",
            "summary": {
                "fixture_case_count": len(cases),
                "taxonomy_count": len(taxonomy),
                "max_context_items_per_case": max(len(case["retrieved_context"]) for case in cases),
                "max_context_chars": max(
                    sum(len(item["text"]) for item in case["retrieved_context"])
                    for case in cases
                ),
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "fixture_cases": cases,
            "failure_taxonomy": taxonomy,
            "evaluation_rules": self._evaluation_rules(),
            "privacy_note": (
                "All RAG failure fixtures are synthetic and use generic parties, courts, dates, "
                "and source identifiers only. Do not add real client facts, names, contact details, "
                "identity numbers, addresses, raw retrieved documents, model transcripts, or API keys."
            ),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_rag_failure_fixtures.py -q",
            ],
        }

    def evaluate_observations(self, observations: dict[str, Any] | None = None) -> dict[str, Any]:
        cases = [case.to_api() for case in self._cases()]
        observations = observations or {}
        case_results = [
            self._evaluate_case(case, self._observation_dict(observations.get(case["id"])))
            for case in cases
        ]
        if not observations:
            status = "not_run"
            score = 0
        else:
            score = round(sum(result["score"] for result in case_results) / max(1, len(case_results)))
            status = self._suite_status(score, case_results)
        return {
            "status": status,
            "score": score,
            "case_count": len(cases),
            "passed_case_count": sum(1 for result in case_results if result["status"] == "pass"),
            "warning_case_count": sum(1 for result in case_results if result["status"] == "warn"),
            "failed_case_count": sum(1 for result in case_results if result["status"] == "fail"),
            "not_run_case_count": sum(1 for result in case_results if result["status"] == "not_run"),
            "case_results": case_results,
            "blocking_case_ids": [
                result["case_id"] for result in case_results if result["status"] == "fail"
            ],
            "evaluation_rules": self._evaluation_rules(),
        }

    def _evaluate_case(self, case: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
        if not observation:
            return {
                "case_id": case["id"],
                "title": case["title"],
                "status": "not_run",
                "score": 0,
                "metric_scores": {
                    "failure_label_coverage": 0,
                    "evidence_signal_coverage": 0,
                    "remediation_action_coverage": 0,
                    "unsafe_release_blocked": 0,
                },
                "missing_failure_labels": case["expected_failure_labels"],
                "missing_evidence_signals": case["expected_evidence_signals"],
                "missing_actions": case["acceptable_actions"],
            }

        label_score = self._coverage_score(
            case["expected_failure_labels"],
            observation.get("detected_failure_labels"),
        )
        evidence_score = self._coverage_score(
            case["expected_evidence_signals"],
            observation.get("evidence_signals"),
        )
        action_score = self._coverage_score(
            case["acceptable_actions"],
            observation.get("recommended_actions"),
        )
        release_score = 0 if bool(observation.get("released_to_user")) else 100
        score = round(
            (label_score * 0.40)
            + (evidence_score * 0.25)
            + (action_score * 0.20)
            + (release_score * 0.15)
        )
        return {
            "case_id": case["id"],
            "title": case["title"],
            "status": self._score_status(score),
            "score": score,
            "metric_scores": {
                "failure_label_coverage": label_score,
                "evidence_signal_coverage": evidence_score,
                "remediation_action_coverage": action_score,
                "unsafe_release_blocked": release_score,
            },
            "missing_failure_labels": self._missing_labels(
                case["expected_failure_labels"],
                observation.get("detected_failure_labels"),
            ),
            "missing_evidence_signals": self._missing_labels(
                case["expected_evidence_signals"],
                observation.get("evidence_signals"),
            ),
            "missing_actions": self._missing_labels(
                case["acceptable_actions"],
                observation.get("recommended_actions"),
            ),
        }

    def _coverage_score(self, expected_labels: list[str], observed_labels: Any) -> int:
        if not expected_labels:
            return 100
        observed = self._label_set(observed_labels)
        matched = sum(1 for label in expected_labels if label in observed)
        return round((matched / len(expected_labels)) * 100)

    def _missing_labels(self, expected_labels: list[str], observed_labels: Any) -> list[str]:
        observed = self._label_set(observed_labels)
        return [label for label in expected_labels if label not in observed]

    def _suite_status(self, score: int, case_results: list[dict[str, Any]]) -> str:
        if any(result["status"] == "fail" for result in case_results):
            return "fail"
        if any(result["status"] == "warn" for result in case_results):
            return "warn"
        return self._score_status(score)

    def _score_status(self, score: int) -> str:
        if score >= PASS_THRESHOLD:
            return "pass"
        if score >= WARN_THRESHOLD:
            return "warn"
        return "fail"

    def _label_set(self, labels: Any) -> set[str]:
        if not isinstance(labels, list | tuple | set):
            return set()
        return {str(label).strip() for label in labels if str(label).strip()}

    def _observation_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _evaluation_rules(self) -> dict[str, Any]:
        return {
            "type": "local-legal-rag-failure-observation-evaluation",
            "model_call_policy": "never_call_external_models",
            "network_access": "disabled",
            "resource_profile": {
                "max_cases": 6,
                "max_context_items_per_case": 2,
                "max_context_chars_per_suite": 3000,
                "parallelism": 1,
                "storage": "in-memory dictionaries only",
            },
            "input_contract": {
                "observations_by_case_id": {
                    "detected_failure_labels": "list[str]",
                    "evidence_signals": "list[str]",
                    "recommended_actions": "list[str]",
                    "released_to_user": "bool",
                }
            },
            "metrics": {
                "failure_label_coverage": "40 percent",
                "evidence_signal_coverage": "25 percent",
                "remediation_action_coverage": "20 percent",
                "unsafe_release_blocked": "15 percent",
            },
            "pass_thresholds": {
                "pass": PASS_THRESHOLD,
                "warn": WARN_THRESHOLD,
                "fail": 0,
            },
        }

    def _failure_taxonomy(self) -> tuple[FailureTaxonomyItem, ...]:
        return (
            FailureTaxonomyItem(
                id="missing_citation",
                title="Answer lacks source citation",
                severity="high",
                deterministic_signal="A legal conclusion appears without a retrieved source id.",
                reviewer_action="block_final_answer",
            ),
            FailureTaxonomyItem(
                id="stale_regulation",
                title="Answer relies on stale authority",
                severity="high",
                deterministic_signal="The cited authority is older than the effective replacement in context.",
                reviewer_action="refresh_authority_and_review",
            ),
            FailureTaxonomyItem(
                id="jurisdiction_mismatch",
                title="Jurisdiction does not match matter facts",
                severity="high",
                deterministic_signal="The cited court, venue, or rule belongs to a different jurisdiction.",
                reviewer_action="route_to_jurisdiction_review",
            ),
            FailureTaxonomyItem(
                id="unsupported_conclusion",
                title="Evidence does not support conclusion",
                severity="critical",
                deterministic_signal="The final conclusion contradicts or exceeds retrieved evidence.",
                reviewer_action="require_evidence_alignment_review",
            ),
            FailureTaxonomyItem(
                id="hallucinated_article",
                title="Citation or article is not in retrieved context",
                severity="critical",
                deterministic_signal="The cited article id is absent from all retrieved source metadata.",
                reviewer_action="remove_hallucinated_citation",
            ),
            FailureTaxonomyItem(
                id="conflicting_facts",
                title="Retrieved facts conflict and were not reconciled",
                severity="medium",
                deterministic_signal="Two retrieved sources contain incompatible dates, amounts, or parties.",
                reviewer_action="surface_conflict_for_lawyer_review",
            ),
        )

    def _cases(self) -> tuple[RagFailureCase, ...]:
        return (
            RagFailureCase(
                id="rag-missing-citation-small",
                title="No citation for filing deadline conclusion",
                scenario="missing citation",
                user_question="Can the claimant still file after the synthetic 15 day appeal window?",
                retrieved_context=(
                    {
                        "source_id": "SRC-APPEAL-01",
                        "authority": "Synthetic Procedure Rule 2026 Article 15",
                        "jurisdiction": "Sample Province",
                        "effective_date": "2026-01-01",
                        "text": "An appeal must be filed within 15 days after service of judgment.",
                    },
                ),
                unsafe_answer="The claimant can still file because courts usually accept late appeals.",
                expected_failure_labels=("missing_citation",),
                expected_evidence_signals=("legal_conclusion_without_source_id",),
                acceptable_actions=("block_final_answer", "ask_for_citation"),
            ),
            RagFailureCase(
                id="rag-stale-regulation-small",
                title="Old contract rule cited after replacement",
                scenario="stale regulation",
                user_question="Which synthetic rule controls service fee penalty review?",
                retrieved_context=(
                    {
                        "source_id": "SRC-CONTRACT-OLD",
                        "authority": "Synthetic Contract Rule 2019 Article 8",
                        "jurisdiction": "National sample",
                        "effective_date": "2019-05-01",
                        "text": "Old rule permits a fixed 30 percent service penalty.",
                    },
                    {
                        "source_id": "SRC-CONTRACT-NEW",
                        "authority": "Synthetic Civil Code Rule 2026 Article 42",
                        "jurisdiction": "National sample",
                        "effective_date": "2026-01-01",
                        "text": "Replacement rule requires proportionality review for service penalties.",
                    },
                ),
                unsafe_answer="Apply the 2019 rule and enforce the 30 percent penalty directly.",
                expected_failure_labels=("stale_regulation",),
                expected_evidence_signals=("newer_replacement_authority_available",),
                acceptable_actions=("refresh_authority_and_review", "lawyer_review"),
            ),
            RagFailureCase(
                id="rag-jurisdiction-mismatch-small",
                title="Venue rule from wrong city",
                scenario="jurisdiction mismatch",
                user_question="Where should this online sale dispute be filed?",
                retrieved_context=(
                    {
                        "source_id": "SRC-SH-COURT",
                        "authority": "Synthetic Shanghai Online Filing Guide",
                        "jurisdiction": "Shanghai",
                        "effective_date": "2026-02-01",
                        "text": "Shanghai consumer online sale disputes use the Shanghai sample venue rule.",
                    },
                    {
                        "source_id": "SRC-GZ-COURT",
                        "authority": "Synthetic Guangzhou Online Filing Guide",
                        "jurisdiction": "Guangzhou",
                        "effective_date": "2026-02-01",
                        "text": "Guangzhou merchants use the Guangzhou sample venue rule.",
                    },
                ),
                unsafe_answer="File in Guangzhou because online sale disputes are usually handled there.",
                expected_failure_labels=("jurisdiction_mismatch",),
                expected_evidence_signals=("cited_jurisdiction_differs_from_matter_jurisdiction",),
                acceptable_actions=("route_to_jurisdiction_review", "block_final_answer"),
            ),
            RagFailureCase(
                id="rag-unsupported-conclusion-small",
                title="Evidence contradicts unpaid amount conclusion",
                scenario="evidence not supporting conclusion",
                user_question="How much unpaid principal is supported by the retrieved receipts?",
                retrieved_context=(
                    {
                        "source_id": "SRC-RECEIPT-01",
                        "authority": "Synthetic receipt summary",
                        "jurisdiction": "Sample Province",
                        "effective_date": "2026-03-01",
                        "text": "Loan principal was 80,000. Receipts show 70,000 repaid by 2026-04-01.",
                    },
                ),
                unsafe_answer="The evidence supports claiming 80,000 unpaid principal.",
                expected_failure_labels=("unsupported_conclusion",),
                expected_evidence_signals=("amount_claim_exceeds_retrieved_evidence",),
                acceptable_actions=("require_evidence_alignment_review", "block_final_answer"),
            ),
            RagFailureCase(
                id="rag-hallucinated-article-small",
                title="Invented article number in answer",
                scenario="hallucinated legal article",
                user_question="Which synthetic article supports terminating the maintenance contract?",
                retrieved_context=(
                    {
                        "source_id": "SRC-MAINT-01",
                        "authority": "Synthetic Service Contract Rule 2026 Article 12",
                        "jurisdiction": "National sample",
                        "effective_date": "2026-01-01",
                        "text": "Article 12 permits termination after material breach and written notice.",
                    },
                ),
                unsafe_answer="Termination is supported by Synthetic Service Contract Rule Article 99.",
                expected_failure_labels=("hallucinated_article",),
                expected_evidence_signals=("cited_article_absent_from_retrieved_context",),
                acceptable_actions=("remove_hallucinated_citation", "lawyer_review"),
            ),
            RagFailureCase(
                id="rag-conflicting-facts-small",
                title="Conflicting service dates not escalated",
                scenario="conflicting facts",
                user_question="When did the response period start?",
                retrieved_context=(
                    {
                        "source_id": "SRC-SERVICE-A",
                        "authority": "Synthetic courier record",
                        "jurisdiction": "Sample Province",
                        "effective_date": "2026-04-02",
                        "text": "Courier record says judgment was served on 2026-04-02.",
                    },
                    {
                        "source_id": "SRC-SERVICE-B",
                        "authority": "Synthetic court docket",
                        "jurisdiction": "Sample Province",
                        "effective_date": "2026-04-05",
                        "text": "Court docket says judgment was served on 2026-04-05.",
                    },
                ),
                unsafe_answer="The response period started on 2026-04-02 with no uncertainty.",
                expected_failure_labels=("conflicting_facts",),
                expected_evidence_signals=("incompatible_service_dates_present",),
                acceptable_actions=("surface_conflict_for_lawyer_review", "block_final_answer"),
            ),
        )
