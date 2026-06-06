from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


PASS_THRESHOLD = 85
WARN_THRESHOLD = 60
MAX_CASES = 7
MAX_SNIPPET_CHARS = 420


SENSITIVE_TEXT_PATTERNS: dict[str, re.Pattern[str]] = {
    "api_key": re.compile(r"\bsk-[A-Za-z0-9]{12,}\b"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "mobile_phone": re.compile(r"\b1[3-9]\d{9}\b"),
    "identity_number": re.compile(r"\b\d{17}[\dXx]\b"),
}


@dataclass(frozen=True)
class LegalDocumentBenchmarkCase:
    id: str
    title: str
    document_type: str
    matter_type: str
    snippet: str
    required_sections: tuple[str, ...]
    expected_citations: tuple[str, ...]
    expected_risk_labels: tuple[str, ...]
    banned_pii_categories: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_sections"] = list(self.required_sections)
        data["expected_citations"] = list(self.expected_citations)
        data["expected_risk_labels"] = list(self.expected_risk_labels)
        data["banned_pii_categories"] = list(self.banned_pii_categories)
        return data


class LegalDocumentBenchmarkSuiteService:
    """Laptop-safe deterministic fixtures for legal-document output checks."""

    def build_suite(self) -> dict[str, Any]:
        cases = [case.to_api() for case in self._cases()]
        return {
            "status": "ready",
            "summary": {
                "case_count": len(cases),
                "check_count": 4,
                "max_cases": MAX_CASES,
                "max_snippet_chars": max(len(case["snippet"]) for case in cases),
                "language": "zh-CN",
                "model_calls": "not_required",
                "network_access": "disabled",
                "data_source": "synthetic_inline_fixtures",
            },
            "benchmark_cases": cases,
            "checks": [
                {
                    "id": "document_structure",
                    "target": "sections",
                    "local_check": "Required section ids must be present in the candidate output.",
                    "weight": 25,
                },
                {
                    "id": "citation_presence",
                    "target": "citations",
                    "local_check": "Expected legal or evidence citation strings must be present exactly.",
                    "weight": 25,
                },
                {
                    "id": "pii_exclusion",
                    "target": "pii_findings + generated_text",
                    "local_check": "Candidate outputs must not contain API keys, emails, mobile phones, or identity numbers.",
                    "weight": 25,
                    "hard_fail": True,
                },
                {
                    "id": "risk_labeling",
                    "target": "risk_labels",
                    "local_check": "Expected deterministic risk labels must be present.",
                    "weight": 25,
                },
            ],
            "resource_policy": {
                "profile": "laptop_safe",
                "max_cases": MAX_CASES,
                "max_snippet_chars": MAX_SNIPPET_CHARS,
                "parallelism": 1,
                "storage": "in_memory_only",
                "external_datasets": "disabled",
                "external_model_calls": "disabled",
            },
            "fixture_content_boundary": {
                "allowed": [
                    "synthetic short legal-document snippets",
                    "generic party placeholders such as A company, B merchant, or staff C",
                    "deterministic expected structure, citation, PII, and risk labels",
                ],
                "disallowed": [
                    "real_client_documents",
                    "real_person_names",
                    "identity_numbers",
                    "phone_numbers",
                    "emails",
                    "addresses",
                    "api_keys",
                    "raw_model_outputs",
                    "downloaded_public_dataset_rows",
                ],
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py -q",
            ],
        }

    def evaluate_outputs(self, outputs: dict[str, Any] | None = None) -> dict[str, Any]:
        outputs = outputs or {}
        case_results = [
            self._evaluate_case(case.to_api(), self._output_dict(outputs.get(case.id)))
            for case in self._cases()
        ]
        if not outputs:
            status = "not_run"
            score = 0
        else:
            score = round(sum(result["score"] for result in case_results) / max(1, len(case_results)))
            status = self._suite_status(score, case_results)
        return {
            "status": status,
            "score": score,
            "case_count": len(case_results),
            "passed_case_count": sum(1 for result in case_results if result["status"] == "pass"),
            "warning_case_count": sum(1 for result in case_results if result["status"] == "warn"),
            "failed_case_count": sum(1 for result in case_results if result["status"] == "fail"),
            "not_run_case_count": sum(1 for result in case_results if result["status"] == "not_run"),
            "case_results": case_results,
            "blocking_case_ids": [
                result["case_id"]
                for result in case_results
                if result["status"] == "fail" or result["hard_pii_block"]
            ],
        }

    def _evaluate_case(self, case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
        if not output:
            return {
                "case_id": case["id"],
                "title": case["title"],
                "status": "not_run",
                "score": 0,
                "metric_scores": {
                    "document_structure": 0,
                    "citation_presence": 0,
                    "pii_exclusion": 0,
                    "risk_labeling": 0,
                },
                "missing_sections": case["required_sections"],
                "missing_citations": case["expected_citations"],
                "missing_risk_labels": case["expected_risk_labels"],
                "pii_findings": [],
                "hard_pii_block": False,
            }

        pii_findings = self._pii_findings(output)
        structure_score = self._coverage_score(case["required_sections"], self._section_ids(output.get("sections")))
        citation_score = self._coverage_score(case["expected_citations"], output.get("citations"))
        pii_score = 0 if pii_findings else 100
        risk_score = self._coverage_score(case["expected_risk_labels"], output.get("risk_labels"))
        score = round((structure_score + citation_score + pii_score + risk_score) / 4)
        hard_pii_block = bool(pii_findings)
        return {
            "case_id": case["id"],
            "title": case["title"],
            "status": "fail" if hard_pii_block else self._score_status(score),
            "score": score,
            "metric_scores": {
                "document_structure": structure_score,
                "citation_presence": citation_score,
                "pii_exclusion": pii_score,
                "risk_labeling": risk_score,
            },
            "missing_sections": self._missing_labels(case["required_sections"], self._section_ids(output.get("sections"))),
            "missing_citations": self._missing_labels(case["expected_citations"], output.get("citations")),
            "missing_risk_labels": self._missing_labels(case["expected_risk_labels"], output.get("risk_labels")),
            "pii_findings": pii_findings,
            "hard_pii_block": hard_pii_block,
        }

    def _coverage_score(self, expected: list[str], observed: Any) -> int:
        if not expected:
            return 100
        observed_labels = self._label_set(observed)
        matched = sum(1 for label in expected if label in observed_labels)
        return round((matched / len(expected)) * 100)

    def _missing_labels(self, expected: list[str], observed: Any) -> list[str]:
        observed_labels = self._label_set(observed)
        return [label for label in expected if label not in observed_labels]

    def _section_ids(self, sections: Any) -> list[str]:
        if isinstance(sections, dict):
            return [str(key) for key in sections]
        if isinstance(sections, list | tuple | set):
            ids = []
            for section in sections:
                if isinstance(section, dict):
                    ids.append(str(section.get("id") or section.get("type") or section.get("title") or ""))
                else:
                    ids.append(str(section))
            return ids
        return []

    def _label_set(self, labels: Any) -> set[str]:
        if not isinstance(labels, list | tuple | set):
            return set()
        return {str(label).strip() for label in labels if str(label).strip()}

    def _pii_findings(self, output: dict[str, Any]) -> list[str]:
        findings = set()
        declared = output.get("pii_findings")
        if isinstance(declared, list | tuple | set):
            findings.update(str(item).strip() for item in declared if str(item).strip())
        if output.get("pii_detected") is True:
            findings.add("pii_detected")
        generated_text = str(output.get("generated_text") or "")
        for category, pattern in SENSITIVE_TEXT_PATTERNS.items():
            if pattern.search(generated_text):
                findings.add(category)
        return sorted(findings)

    def _output_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _suite_status(self, score: int, case_results: list[dict[str, Any]]) -> str:
        if any(result["hard_pii_block"] or result["status"] == "fail" for result in case_results):
            return "fail"
        return self._score_status(score)

    def _score_status(self, score: int) -> str:
        if score >= PASS_THRESHOLD:
            return "pass"
        if score >= WARN_THRESHOLD:
            return "warn"
        return "fail"

    def _cases(self) -> tuple[LegalDocumentBenchmarkCase, ...]:
        return (
            LegalDocumentBenchmarkCase(
                id="ldoc-civil-complaint-mini",
                title="\u6c11\u4e8b\u8d77\u8bc9\u72b6\u7ed3\u6784\u4e0e\u8bc1\u636e\u5f15\u7528\u7247\u6bb5",
                document_type="civil_complaint",
                matter_type="sales_payment_dispute",
                snippet=(
                    "\u6c11\u4e8b\u8d77\u8bc9\u72b6\uff1a\u539f\u544aA\u516c\u53f8\u8bf7\u6c42\u5224\u4ee4"
                    "\u88ab\u544aB\u516c\u53f8\u652f\u4ed8\u8d27\u6b3e32000\u5143\u3002"
                    "\u4e8b\u5b9e\u8bb0\u8f7d\u5408\u540c\u7b7e\u8ba2\u3001\u9001\u8d27\u548c\u5bf9\u8d26\u8fc7\u7a0b\uff0c"
                    "\u8bc1\u636e\u5f15\u7528\u4e3a\u8bc1\u636e1\u300a\u4e70\u5356\u5408\u540c\u300b\u548c"
                    "\u8bc1\u636e2\u300a\u5bf9\u8d26\u5355\u300b\uff0c\u62df\u63f4\u5f15"
                    "\u300a\u6c11\u4e8b\u8bc9\u8bbc\u6cd5\u300b\u7b2c122\u6761\u3002"
                ),
                required_sections=("title", "parties", "claims", "facts_and_reasons", "evidence", "court_tail"),
                expected_citations=(
                    "\u8bc1\u636e1\u300a\u4e70\u5356\u5408\u540c\u300b",
                    "\u300a\u6c11\u4e8b\u8bc9\u8bbc\u6cd5\u300b\u7b2c122\u6761",
                ),
                expected_risk_labels=(
                    "jurisdiction_confirmation",
                    "evidence_reference_check",
                    "claim_amount_proof",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
            LegalDocumentBenchmarkCase(
                id="ldoc-lawyer-letter-mini",
                title="\u5f8b\u5e08\u51fd\u671f\u9650\u4e0e\u5f15\u7528\u7247\u6bb5",
                document_type="lawyer_letter",
                matter_type="lease_payment_collection",
                snippet=(
                    "\u5f8b\u5e08\u51fd\uff1a\u53d7C\u516c\u53f8\u59d4\u6258\uff0c\u5c31D\u5546\u6237"
                    "\u903e\u671f\u672a\u4ed8\u79df\u91d118000\u5143\u53d1\u51fd\u3002"
                    "\u51fd\u4ef6\u8981\u6c42\u6536\u51fd\u540e7\u65e5\u5185\u4ed8\u6b3e\uff0c"
                    "\u5e76\u5f15\u7528\u79df\u8d41\u5408\u540c\u7b2c4\u6761\u3001"
                    "\u9644\u4ef6\u4e00\u300a\u79df\u91d1\u660e\u7ec6\u300b\u3002"
                ),
                required_sections=("title", "authorization", "facts", "demand", "deadline", "legal_consequence"),
                expected_citations=(
                    "\u79df\u8d41\u5408\u540c\u7b2c4\u6761",
                    "\u9644\u4ef6\u4e00\u300a\u79df\u91d1\u660e\u7ec6\u300b",
                ),
                expected_risk_labels=(
                    "service_deadline_unclear",
                    "penalty_basis_review",
                    "delivery_method_check",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
            LegalDocumentBenchmarkCase(
                id="ldoc-defense-answer-mini",
                title="\u7b54\u8fa9\u72b6\u6297\u8fa9\u4e0e\u8bc1\u636e\u53cd\u9a73\u7247\u6bb5",
                document_type="defense_answer",
                matter_type="sales_payment_defense",
                snippet=(
                    "\u7b54\u8fa9\u72b6\uff1a\u88ab\u544aB\u516c\u53f8\u5bf9A\u516c\u53f8"
                    "\u8d27\u6b3e\u8bf7\u6c42\u63d0\u51fa\u90e8\u5206\u6297\u8fa9\u3002"
                    "\u7b54\u8fa9\u610f\u89c1\u8bb0\u8f7d\u5df2\u4ed8\u6b3e12000\u5143\uff0c"
                    "\u5bf9\u539f\u544a\u8bc1\u636e1\u300a\u4e70\u5356\u5408\u540c\u300b"
                    "\u771f\u5b9e\u6027\u65e0\u5f02\u8bae\uff0c\u4f46\u5bf9\u8bc1\u636e2\u300a\u5bf9\u8d26\u5355\u300b"
                    "\u6570\u989d\u63d0\u51fa\u53cd\u9a73\uff0c\u5e76\u9700\u6838\u5bf9\u7b54\u8fa9\u671f\u9650\u3002"
                ),
                required_sections=(
                    "title",
                    "case_caption",
                    "respondent_identity",
                    "defense_points",
                    "facts_and_reasons",
                    "evidence_rebuttal",
                ),
                expected_citations=(
                    "\u539f\u544a\u8bc1\u636e1\u300a\u4e70\u5356\u5408\u540c\u300b",
                    "\u8bc1\u636e2\u300a\u5bf9\u8d26\u5355\u300b",
                ),
                expected_risk_labels=(
                    "answer_deadline_review",
                    "admission_waiver_check",
                    "evidence_rebuttal_gap",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
            LegalDocumentBenchmarkCase(
                id="ldoc-contract-review-mini",
                title="\u5408\u540c\u5ba1\u67e5\u98ce\u9669\u6807\u7b7e\u7247\u6bb5",
                document_type="contract_review",
                matter_type="service_contract_review",
                snippet=(
                    "\u5408\u540c\u5ba1\u67e5\u610f\u89c1\uff1aE\u516c\u53f8\u4e0eF\u670d\u52a1\u5546"
                    "\u62df\u7b7e\u8ba2\u7cfb\u7edf\u8fd0\u7ef4\u5408\u540c\uff0c\u670d\u52a1\u8d39120000\u5143\u3002"
                    "\u8349\u6848\u6709\u4ea4\u4ed8\u6e05\u5355\u548c\u9a8c\u6536\u8282\u70b9\uff0c"
                    "\u4f46\u672a\u5199\u660e\u6570\u636e\u4fdd\u5bc6\u8d23\u4efb\u548c\u6545\u969c\u54cd\u5e94\u65f6\u9650\uff0c"
                    "\u9700\u5bf9\u7167\u9644\u4ef6\u4e8c\u300a\u670d\u52a1\u7ea7\u522b\u300b\u548c"
                    "\u7b2c8\u6761\u8fdd\u7ea6\u8d23\u4efb\u3002"
                ),
                required_sections=("title", "parties", "subject", "payment", "delivery_acceptance", "risk_opinion"),
                expected_citations=(
                    "\u9644\u4ef6\u4e8c\u300a\u670d\u52a1\u7ea7\u522b\u300b",
                    "\u7b2c8\u6761\u8fdd\u7ea6\u8d23\u4efb",
                ),
                expected_risk_labels=(
                    "missing_data_confidentiality",
                    "acceptance_standard_unclear",
                    "fault_response_gap",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
            LegalDocumentBenchmarkCase(
                id="ldoc-evidence-catalog-mini",
                title="\u8bc1\u636e\u76ee\u5f55\u771f\u5b9e\u6027\u4e0e\u8bc1\u660e\u76ee\u7684\u7247\u6bb5",
                document_type="evidence_catalog",
                matter_type="labor_overtime_dispute",
                snippet=(
                    "\u8bc1\u636e\u76ee\u5f55\uff1aE-001\u300a\u8003\u52e4\u8bb0\u5f55\u300b"
                    "\u8bc1\u660e\u52a0\u73ed\u65f6\u95f4\uff0cE-002\u300a\u5de5\u8d44\u8868\u300b"
                    "\u8bc1\u660e\u5de5\u8d44\u57fa\u6570\uff0cE-003\u300a\u5fae\u4fe1\u6c9f\u901a\u622a\u56fe\u300b"
                    "\u5f85\u6838\u9a8c\u539f\u59cb\u8f7d\u4f53\u3002\u9700\u6807\u660e\u6765\u6e90\u3001"
                    "\u9875\u7801\u3001\u8bc1\u660e\u76ee\u7684\u548c\u539f\u4ef6\u6838\u5bf9\u72b6\u6001\u3002"
                ),
                required_sections=("title", "case_caption", "evidence_list", "proof_purpose", "source_status", "authenticity_note"),
                expected_citations=(
                    "E-001\u300a\u8003\u52e4\u8bb0\u5f55\u300b",
                    "E-003\u300a\u5fae\u4fe1\u6c9f\u901a\u622a\u56fe\u300b",
                ),
                expected_risk_labels=(
                    "missing_original_carrier",
                    "proof_purpose_unclear",
                    "source_authenticity_review",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
            LegalDocumentBenchmarkCase(
                id="ldoc-settlement-agreement-mini",
                title="\u548c\u89e3\u534f\u8bae\u4ed8\u6b3e\u4e0e\u64a4\u8bc9\u6761\u4ef6\u7247\u6bb5",
                document_type="settlement_agreement",
                matter_type="maintenance_fee_settlement",
                snippet=(
                    "\u548c\u89e3\u534f\u8bae\uff1aG\u516c\u53f8\u4e0eH\u4f9b\u5e94\u5546"
                    "\u5c31\u7ef4\u4fee\u8d39\u4e89\u8bae\u8fbe\u6210\u5206\u671f\u4ed8\u6b3e\u5b89\u6392\uff0c"
                    "\u9996\u671f20000\u5143\uff0c\u4f59\u6b3e\u4e24\u671f\u652f\u4ed8\u3002"
                    "\u534f\u8bae\u7ea6\u5b9a\u5c65\u884c\u5b8c\u6bd5\u540e\u4e92\u4e0d\u8ffd\u7a76\uff0c"
                    "\u4f46\u9700\u4fdd\u7559\u903e\u671f\u8fdd\u7ea6\u91d1\u3001\u64a4\u8bc9\u8282\u70b9"
                    "\u548c\u4fdd\u5bc6\u6761\u6b3e\u3002"
                ),
                required_sections=("title", "parties", "settlement_amount", "payment_schedule", "release_scope", "breach_clause", "execution_tail"),
                expected_citations=(
                    "\u7b2c3\u6761\u4ed8\u6b3e\u5b89\u6392",
                    "\u7b2c5\u6761\u8fdd\u7ea6\u8d23\u4efb",
                ),
                expected_risk_labels=(
                    "release_scope_overbroad",
                    "payment_schedule_review",
                    "withdrawal_condition_check",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
            LegalDocumentBenchmarkCase(
                id="ldoc-legal-opinion-mini",
                title="\u6cd5\u5f8b\u610f\u89c1\u4e66\u5047\u8bbe\u4e0e\u7ed3\u8bba\u9650\u5236\u7247\u6bb5",
                document_type="legal_opinion",
                matter_type="equity_repurchase_opinion",
                snippet=(
                    "\u6cd5\u5f8b\u610f\u89c1\u4e66\uff1a\u53d7I\u57fa\u91d1\u54a8\u8be2\uff0c"
                    "\u5c31J\u9879\u76ee\u80a1\u6743\u56de\u8d2d\u6761\u6b3e\u6548\u529b\u51fa\u5177\u610f\u89c1\u3002"
                    "\u6750\u6599\u5305\u62ec\u6295\u8d44\u534f\u8bae\u7b2c6\u6761\u3001"
                    "\u8865\u5145\u534f\u8bae\u548c\u8463\u4e8b\u4f1a\u51b3\u8bae\u3002"
                    "\u610f\u89c1\u9700\u533a\u5206\u4e8b\u5b9e\u5047\u8bbe\u3001\u6cd5\u5f8b\u4f9d\u636e\u3001"
                    "\u98ce\u9669\u8bc4\u7ea7\u548c\u7ed3\u8bba\u9650\u5236\u3002"
                ),
                required_sections=("title", "engagement_scope", "facts_assumptions", "legal_basis", "analysis", "conclusion", "limitations"),
                expected_citations=(
                    "\u6295\u8d44\u534f\u8bae\u7b2c6\u6761",
                    "\u8463\u4e8b\u4f1a\u51b3\u8bae",
                ),
                expected_risk_labels=(
                    "assumption_boundary_required",
                    "authority_basis_check",
                    "conclusion_limitation_needed",
                ),
                banned_pii_categories=("identity_number", "mobile_phone", "email", "api_key"),
            ),
        )
