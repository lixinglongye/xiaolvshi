from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PASS_THRESHOLD = 80
WARN_THRESHOLD = 60


@dataclass(frozen=True)
class ExpectedTask:
    id: str
    title: str
    output_type: str
    local_check: str
    required_for: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_for"] = list(self.required_for)
        return data


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    title: str
    document_type: str
    matter_type: str
    snippet: str
    expected_tasks: tuple[str, ...]
    expected_fields: dict[str, str]
    expected_risk_labels: tuple[str, ...]
    expected_classification_labels: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["expected_tasks"] = list(self.expected_tasks)
        data["expected_risk_labels"] = list(self.expected_risk_labels)
        data["expected_classification_labels"] = list(self.expected_classification_labels)
        return data


class LegalDocumentBenchmarkFixturesService:
    """Small deterministic Chinese legal-document benchmark fixtures for laptop tests."""

    def build_suite(self) -> dict[str, Any]:
        cases = [case.to_api() for case in self._cases()]
        tasks = [task.to_api() for task in self._expected_tasks()]
        return {
            "status": "ready",
            "summary": {
                "benchmark_case_count": len(cases),
                "expected_task_count": len(tasks),
                "max_snippet_chars": max(len(case["snippet"]) for case in cases),
                "language": "zh-CN",
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "benchmark_cases": cases,
            "expected_tasks": tasks,
            "evaluation_plan": self._evaluation_plan(),
            "privacy_boundary": self._privacy_boundary(),
            "claim_boundary": self._claim_boundary(),
            "privacy_note": (
                "All snippets are synthetic Chinese legal-document fixtures with generic party names only. "
                "Do not add real client documents, identity numbers, phone numbers, emails, addresses, API keys, "
                "or raw model outputs to this fixture file."
            ),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_fixtures.py -q",
            ],
        }

    def evaluate_predictions(self, predictions: dict[str, Any] | None = None) -> dict[str, Any]:
        cases = [case.to_api() for case in self._cases()]
        predictions = predictions or {}
        case_results = [
            self._evaluate_case(case, self._prediction_dict(predictions.get(case["id"])))
            for case in cases
        ]
        if not predictions:
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
            "blocking_case_ids": [result["case_id"] for result in case_results if result["status"] == "fail"],
            "evaluation_plan": self._evaluation_plan(),
            "privacy_boundary": {
                **self._privacy_boundary(),
                "prediction_payload_returned": False,
                "raw_prediction_text_returned": False,
                "raw_model_output_returned": False,
            },
            "claim_boundary": self._claim_boundary(),
        }

    def _evaluate_case(self, case: dict[str, Any], prediction: dict[str, Any]) -> dict[str, Any]:
        if not prediction:
            return {
                "case_id": case["id"],
                "title": case["title"],
                "status": "not_run",
                "score": 0,
                "metric_scores": {
                    "classification": 0,
                    "task_label_coverage": 0,
                    "risk_label_coverage": 0,
                    "field_coverage": 0,
                },
                "missing_tasks": case["expected_tasks"],
                "missing_risk_labels": case["expected_risk_labels"],
                "missing_fields": sorted(case["expected_fields"]),
            }

        classification_score = self._classification_score(case, prediction)
        task_score = self._coverage_score(case["expected_tasks"], prediction.get("task_labels"))
        risk_score = self._coverage_score(case["expected_risk_labels"], prediction.get("risk_labels"))
        field_score = self._field_score(case["expected_fields"], prediction.get("extracted_fields"))
        score = round(
            (classification_score * 0.25)
            + (task_score * 0.25)
            + (risk_score * 0.25)
            + (field_score * 0.25)
        )
        return {
            "case_id": case["id"],
            "title": case["title"],
            "status": self._score_status(score),
            "score": score,
            "metric_scores": {
                "classification": classification_score,
                "task_label_coverage": task_score,
                "risk_label_coverage": risk_score,
                "field_coverage": field_score,
            },
            "missing_tasks": self._missing_labels(case["expected_tasks"], prediction.get("task_labels")),
            "missing_risk_labels": self._missing_labels(case["expected_risk_labels"], prediction.get("risk_labels")),
            "missing_fields": self._missing_fields(case["expected_fields"], prediction.get("extracted_fields")),
        }

    def _classification_score(self, case: dict[str, Any], prediction: dict[str, Any]) -> int:
        observed_type = str(prediction.get("document_type") or "").strip()
        observed_labels = self._label_set(prediction.get("classification_labels"))
        if observed_type == case["document_type"] and set(case["expected_classification_labels"]).issubset(observed_labels):
            return 100
        if observed_type == case["document_type"]:
            return 70
        return 0

    def _field_score(self, expected_fields: dict[str, str], observed_fields: Any) -> int:
        observed = self._prediction_dict(observed_fields)
        if not expected_fields:
            return 100
        matched = 0
        for field, expected_value in expected_fields.items():
            observed_value = str(observed.get(field) or "")
            if expected_value and expected_value in observed_value:
                matched += 1
        return round((matched / len(expected_fields)) * 100)

    def _coverage_score(self, expected_labels: list[str], observed_labels: Any) -> int:
        if not expected_labels:
            return 100
        observed = self._label_set(observed_labels)
        matched = sum(1 for label in expected_labels if label in observed)
        return round((matched / len(expected_labels)) * 100)

    def _missing_labels(self, expected_labels: list[str], observed_labels: Any) -> list[str]:
        observed = self._label_set(observed_labels)
        return [label for label in expected_labels if label not in observed]

    def _missing_fields(self, expected_fields: dict[str, str], observed_fields: Any) -> list[str]:
        observed = self._prediction_dict(observed_fields)
        missing = []
        for field, expected_value in expected_fields.items():
            if expected_value not in str(observed.get(field) or ""):
                missing.append(field)
        return missing

    def _suite_status(self, score: int, case_results: list[dict[str, Any]]) -> str:
        if any(result["status"] == "fail" for result in case_results):
            return "fail"
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

    def _prediction_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _evaluation_plan(self) -> dict[str, Any]:
        return {
            "type": "local-fixture-label-and-field-evaluation",
            "model_call_policy": "never_call_external_models",
            "network_access": "disabled",
            "resource_profile": {
                "max_cases": 5,
                "max_snippet_chars": 500,
                "parallelism": 1,
                "storage": "in-memory dictionaries only",
            },
            "steps": [
                {
                    "order": 1,
                    "id": "classify-document",
                    "check": "Compare document_type and classification_labels against expected labels.",
                },
                {
                    "order": 2,
                    "id": "extract-key-fields",
                    "check": "Compare expected string fragments in extracted_fields.",
                },
                {
                    "order": 3,
                    "id": "tag-risks",
                    "check": "Compare deterministic risk_labels coverage.",
                },
                {
                    "order": 4,
                    "id": "summarize-score",
                    "check": "Average classification, task label, risk label, and field coverage scores.",
                },
            ],
            "metrics": {
                "classification": "25 percent",
                "task_label_coverage": "25 percent",
                "risk_label_coverage": "25 percent",
                "field_coverage": "25 percent",
            },
            "pass_thresholds": {
                "pass": PASS_THRESHOLD,
                "warn": WARN_THRESHOLD,
                "fail": 0,
            },
        }

    def _privacy_boundary(self) -> dict[str, Any]:
        return {
            "fixture_source": "synthetic_inline_fixtures",
            "returns_synthetic_fixture_snippets": True,
            "maintenance_ui_renders_raw_fixture_snippets": False,
            "real_client_documents_included": False,
            "identity_numbers_included": False,
            "phone_numbers_included": False,
            "emails_included": False,
            "addresses_included": False,
            "prompts_included": False,
            "raw_model_outputs_included": False,
            "gateway_payloads_included": False,
            "credentials_included": False,
            "model_calls": False,
            "network_access": False,
            "dataset_downloads": False,
        }

    def _claim_boundary(self) -> dict[str, Any]:
        return {
            "public_benchmark_score_claimed": False,
            "live_model_accuracy_claimed": False,
            "production_accuracy_claimed": False,
            "real_client_document_coverage_claimed": False,
            "universal_document_support_claimed": False,
            "legal_advice_claimed": False,
            "allowed_claim": "Tiny synthetic local fixture smoke tests for deterministic document labels and fields.",
        }

    def _expected_tasks(self) -> tuple[ExpectedTask, ...]:
        return (
            ExpectedTask(
                id="document_classification",
                title="文书类型分类",
                output_type="document_type + classification_labels",
                local_check="Exact match against the synthetic case document_type and label set.",
                required_for=("contract", "civil_complaint", "lawyer_letter", "settlement_agreement"),
            ),
            ExpectedTask(
                id="party_extraction",
                title="主体抽取",
                output_type="extracted_fields.parties",
                local_check="Expected party names must appear in the extracted field value.",
                required_for=("contract", "civil_complaint", "lawyer_letter", "settlement_agreement"),
            ),
            ExpectedTask(
                id="amount_or_claim_extraction",
                title="金额或诉请抽取",
                output_type="extracted_fields.amount_or_claim",
                local_check="Expected amount, demand, or relief fragment must appear in extracted fields.",
                required_for=("contract", "civil_complaint", "lawyer_letter"),
            ),
            ExpectedTask(
                id="deadline_extraction",
                title="期限抽取",
                output_type="extracted_fields.deadline",
                local_check="Expected deadline fragment must appear when the fixture contains a deadline.",
                required_for=("contract", "lawyer_letter", "settlement_agreement"),
            ),
            ExpectedTask(
                id="risk_labeling",
                title="风险标签",
                output_type="risk_labels",
                local_check="Expected risk labels must be present in the prediction risk label list.",
                required_for=("contract", "civil_complaint", "lawyer_letter", "settlement_agreement"),
            ),
        )

    def _cases(self) -> tuple[BenchmarkCase, ...]:
        return (
            BenchmarkCase(
                id="fixture-contract-payment-small",
                title="服务合同付款与违约责任片段",
                document_type="contract",
                matter_type="service_contract",
                snippet=(
                    "甲方A公司委托乙方B公司提供年度系统维护服务，服务费为120000元。"
                    "甲方应在验收后15日内付款。合同约定乙方逾期响应每次扣减服务费2%，"
                    "但未约定数据泄露责任、服务级别附件和提前解约后的费用结算方式。"
                ),
                expected_tasks=(
                    "document_classification",
                    "party_extraction",
                    "amount_or_claim_extraction",
                    "deadline_extraction",
                    "risk_labeling",
                ),
                expected_fields={
                    "parties": "A公司;B公司",
                    "amount_or_claim": "120000元",
                    "deadline": "验收后15日",
                },
                expected_risk_labels=(
                    "missing_data_liability",
                    "missing_service_level_attachment",
                    "termination_fee_gap",
                ),
                expected_classification_labels=("service_contract", "payment_clause"),
            ),
            BenchmarkCase(
                id="fixture-civil-complaint-loan-small",
                title="民间借贷起诉状事实与诉请片段",
                document_type="civil_complaint",
                matter_type="private_lending_dispute",
                snippet=(
                    "原告张某诉称，被告李某于2026年1月5日借款80000元并出具借条，"
                    "约定2026年4月5日前归还。到期后李某仅归还10000元。原告诉请"
                    "判令被告返还剩余借款70000元并承担逾期利息，证据包括借条、转账凭证和聊天记录。"
                ),
                expected_tasks=(
                    "document_classification",
                    "party_extraction",
                    "amount_or_claim_extraction",
                    "deadline_extraction",
                    "risk_labeling",
                ),
                expected_fields={
                    "parties": "张某;李某",
                    "amount_or_claim": "70000元",
                    "deadline": "2026年4月5日",
                    "evidence": "借条;转账凭证;聊天记录",
                },
                expected_risk_labels=(
                    "interest_basis_needed",
                    "partial_repayment_dispute",
                    "evidence_chain_review",
                ),
                expected_classification_labels=("loan_dispute", "civil_claims"),
            ),
            BenchmarkCase(
                id="fixture-lawyer-letter-rent-small",
                title="租金催收律师函片段",
                document_type="lawyer_letter",
                matter_type="lease_payment_collection",
                snippet=(
                    "某律师事务所受C公司委托，就D商户拖欠2026年3月至5月租金合计45000元事宜发函。"
                    "函件要求D商户在收到本函后7日内支付欠付租金及违约金，并提示逾期将提起诉讼。"
                    "附件列明租赁合同、付款记录和催告截图。"
                ),
                expected_tasks=(
                    "document_classification",
                    "party_extraction",
                    "amount_or_claim_extraction",
                    "deadline_extraction",
                    "risk_labeling",
                ),
                expected_fields={
                    "parties": "C公司;D商户",
                    "amount_or_claim": "45000元",
                    "deadline": "收到本函后7日",
                    "evidence": "租赁合同;付款记录;催告截图",
                },
                expected_risk_labels=(
                    "payment_overdue",
                    "litigation_escalation",
                    "penalty_basis_review",
                ),
                expected_classification_labels=("lawyer_letter", "rent_collection"),
            ),
            BenchmarkCase(
                id="fixture-labor-settlement-small",
                title="劳动解除补偿协议片段",
                document_type="settlement_agreement",
                matter_type="labor_termination",
                snippet=(
                    "E公司与员工王某协商解除劳动关系，约定公司在2026年6月30日前一次性支付补偿金30000元。"
                    "王某确认工资已结清，但协议未写明社保缴纳截止日、竞业限制是否继续有效，"
                    "也未说明双方保密义务的违约后果。"
                ),
                expected_tasks=(
                    "document_classification",
                    "party_extraction",
                    "amount_or_claim_extraction",
                    "deadline_extraction",
                    "risk_labeling",
                ),
                expected_fields={
                    "parties": "E公司;王某",
                    "amount_or_claim": "30000元",
                    "deadline": "2026年6月30日",
                },
                expected_risk_labels=(
                    "social_insurance_cutoff_missing",
                    "non_compete_status_unclear",
                    "confidentiality_remedy_gap",
                ),
                expected_classification_labels=("labor_termination", "settlement_payment"),
            ),
        )
