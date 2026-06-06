from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


PASS_THRESHOLD = 90
WARN_THRESHOLD = 70
MAX_CASES = 4
AMOUNT_TOLERANCE = 0.01


FORBIDDEN_INPUT_KEYS = {
    "generated_text",
    "raw_output",
    "raw_response",
    "output_text",
    "prompt",
    "messages",
    "headers",
    "authorization",
    "api_key",
    "document_text",
    "fixture_text",
}

SENSITIVE_VALUE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AmountExpectation:
    id: str
    value: float
    currency: str
    formula: str


@dataclass(frozen=True)
class DeadlineExpectation:
    id: str
    value: str
    rule: str


@dataclass(frozen=True)
class ContradictionPair:
    id: str
    fact_ids: tuple[str, str]


@dataclass(frozen=True)
class LegalDocumentFactConsistencyCase:
    id: str
    title: str
    document_type: str
    matter_type: str
    amount_expectations: tuple[AmountExpectation, ...]
    deadline_expectations: tuple[DeadlineExpectation, ...]
    required_fact_ids: tuple[str, ...]
    contradiction_pairs: tuple[ContradictionPair, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["amount_expectations"] = [asdict(item) for item in self.amount_expectations]
        data["deadline_expectations"] = [asdict(item) for item in self.deadline_expectations]
        data["required_fact_ids"] = list(self.required_fact_ids)
        data["contradiction_pairs"] = [
            {"id": item.id, "fact_ids": list(item.fact_ids)}
            for item in self.contradiction_pairs
        ]
        return data


class LegalDocumentFactConsistencyBenchmarkService:
    """Deterministic fact consistency checks for structured legal document outputs."""

    def build_suite(self) -> dict[str, Any]:
        cases = [case.to_api() for case in self._cases()]
        return {
            "status": "ready",
            "summary": {
                "case_count": len(cases),
                "check_count": 5,
                "max_cases": MAX_CASES,
                "language": "zh-CN",
                "data_source": "synthetic_structured_expectations",
                "model_calls": "not_required",
                "network_access": "disabled",
                "external_datasets": "disabled",
                "amount_tolerance": AMOUNT_TOLERANCE,
            },
            "benchmark_cases": cases,
            "checks": [
                {
                    "id": "amount_consistency",
                    "target": "amounts",
                    "local_check": "Observed amount IDs must match deterministic expected values.",
                    "weight": 25,
                    "hard_fail": True,
                },
                {
                    "id": "deadline_consistency",
                    "target": "deadlines",
                    "local_check": "Observed deadline IDs must match deterministic expected ISO dates.",
                    "weight": 20,
                    "hard_fail": True,
                },
                {
                    "id": "required_fact_presence",
                    "target": "facts",
                    "local_check": "Required fact IDs must be present in structured candidate output.",
                    "weight": 20,
                },
                {
                    "id": "contradiction_exclusion",
                    "target": "facts",
                    "local_check": "Mutually exclusive fact IDs must not both be asserted.",
                    "weight": 20,
                    "hard_fail": True,
                },
                {
                    "id": "raw_input_exclusion",
                    "target": "payload",
                    "local_check": "Raw prompts, generated text, credentials, and client identifiers are rejected.",
                    "weight": 15,
                    "hard_fail": True,
                },
            ],
            "resource_policy": {
                "profile": "laptop_safe",
                "max_cases": MAX_CASES,
                "parallelism": 1,
                "storage": "in_memory_only",
                "external_datasets": "disabled",
                "external_model_calls": "disabled",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_case_ids": True,
                "returns_expected_amount_values": True,
                "returns_expected_deadline_values": True,
                "returns_raw_document_text": False,
                "returns_generated_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_called": False,
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_fact_consistency_benchmark.py -q",
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
        blocking_case_ids = [
            result["case_id"]
            for result in case_results
            if result["status"] == "fail" or result["hard_consistency_block"]
        ]
        return {
            "status": status,
            "score": score,
            "case_count": len(case_results),
            "passed_case_count": sum(1 for result in case_results if result["status"] == "pass"),
            "warning_case_count": sum(1 for result in case_results if result["status"] == "warn"),
            "failed_case_count": sum(1 for result in case_results if result["status"] == "fail"),
            "not_run_case_count": sum(1 for result in case_results if result["status"] == "not_run"),
            "amount_mismatch_count": sum(len(result["mismatched_amount_ids"]) for result in case_results),
            "deadline_mismatch_count": sum(len(result["mismatched_deadline_ids"]) for result in case_results),
            "contradiction_count": sum(len(result["contradiction_pair_ids"]) for result in case_results),
            "raw_input_field_count": sum(result["raw_input_field_count"] for result in case_results),
            "blocking_case_ids": blocking_case_ids,
            "case_results": case_results,
            "privacy_boundary": {
                "metadata_only": True,
                "returns_raw_document_text": False,
                "returns_generated_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_credentials": False,
                "model_calls": False,
                "network_called": False,
            },
        }

    def _evaluate_case(self, case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
        if not output:
            return {
                "case_id": case["id"],
                "title": case["title"],
                "status": "not_run",
                "score": 0,
                "metric_scores": self._metric_scores(0, 0, 0, 0, 100),
                "missing_amount_ids": [item["id"] for item in case["amount_expectations"]],
                "mismatched_amount_ids": [],
                "missing_deadline_ids": [item["id"] for item in case["deadline_expectations"]],
                "mismatched_deadline_ids": [],
                "missing_fact_ids": list(case["required_fact_ids"]),
                "contradiction_pair_ids": [],
                "raw_input_field_count": 0,
                "hard_consistency_block": False,
                "reason_codes": ["fact-consistency-not-run"],
            }

        raw_input_field_count = self._raw_input_field_count(output)
        amount_result = self._amount_result(case["amount_expectations"], output.get("amounts"))
        deadline_result = self._deadline_result(case["deadline_expectations"], output.get("deadlines"))
        fact_ids = self._fact_ids(output.get("facts"))
        missing_fact_ids = [fact_id for fact_id in case["required_fact_ids"] if fact_id not in fact_ids]
        contradiction_pair_ids = self._contradiction_pair_ids(case["contradiction_pairs"], fact_ids)
        amount_score = self._coverage_score(
            len(case["amount_expectations"]),
            len(case["amount_expectations"]) - len(amount_result["missing"]) - len(amount_result["mismatched"]),
        )
        deadline_score = self._coverage_score(
            len(case["deadline_expectations"]),
            len(case["deadline_expectations"]) - len(deadline_result["missing"]) - len(deadline_result["mismatched"]),
        )
        fact_score = self._coverage_score(len(case["required_fact_ids"]), len(case["required_fact_ids"]) - len(missing_fact_ids))
        contradiction_score = 0 if contradiction_pair_ids else 100
        privacy_score = 0 if raw_input_field_count else 100
        score = round((amount_score + deadline_score + fact_score + contradiction_score + privacy_score) / 5)
        hard_consistency_block = bool(
            raw_input_field_count
            or amount_result["mismatched"]
            or deadline_result["mismatched"]
            or contradiction_pair_ids
        )
        reason_codes = self._reason_codes(
            output_present=True,
            amount_result=amount_result,
            deadline_result=deadline_result,
            missing_fact_ids=missing_fact_ids,
            contradiction_pair_ids=contradiction_pair_ids,
            raw_input_field_count=raw_input_field_count,
            score=score,
        )
        return {
            "case_id": case["id"],
            "title": case["title"],
            "status": "fail" if hard_consistency_block else self._score_status(score),
            "score": score,
            "metric_scores": self._metric_scores(amount_score, deadline_score, fact_score, contradiction_score, privacy_score),
            "missing_amount_ids": amount_result["missing"],
            "mismatched_amount_ids": amount_result["mismatched"],
            "missing_deadline_ids": deadline_result["missing"],
            "mismatched_deadline_ids": deadline_result["mismatched"],
            "missing_fact_ids": missing_fact_ids,
            "contradiction_pair_ids": contradiction_pair_ids,
            "raw_input_field_count": raw_input_field_count,
            "hard_consistency_block": hard_consistency_block,
            "reason_codes": reason_codes,
        }

    def _amount_result(self, expected: list[dict[str, Any]], observed: Any) -> dict[str, list[str]]:
        observed_amounts = self._value_map(observed)
        missing: list[str] = []
        mismatched: list[str] = []
        for item in expected:
            amount_id = str(item["id"])
            if amount_id not in observed_amounts:
                missing.append(amount_id)
                continue
            observed_value = self._number(observed_amounts[amount_id])
            if observed_value is None or abs(observed_value - float(item["value"])) > AMOUNT_TOLERANCE:
                mismatched.append(amount_id)
        return {"missing": missing, "mismatched": mismatched}

    def _deadline_result(self, expected: list[dict[str, Any]], observed: Any) -> dict[str, list[str]]:
        observed_deadlines = self._value_map(observed)
        missing: list[str] = []
        mismatched: list[str] = []
        for item in expected:
            deadline_id = str(item["id"])
            if deadline_id not in observed_deadlines:
                missing.append(deadline_id)
                continue
            expected_value = self._date_str(item["value"])
            observed_value = self._date_str(observed_deadlines[deadline_id])
            if not observed_value or observed_value != expected_value:
                mismatched.append(deadline_id)
        return {"missing": missing, "mismatched": mismatched}

    def _contradiction_pair_ids(self, pairs: list[dict[str, Any]], fact_ids: set[str]) -> list[str]:
        contradiction_ids: list[str] = []
        for pair in pairs:
            pair_ids = [str(item) for item in pair.get("fact_ids", [])]
            if len(pair_ids) == 2 and pair_ids[0] in fact_ids and pair_ids[1] in fact_ids:
                contradiction_ids.append(str(pair.get("id") or ":".join(pair_ids)))
        return contradiction_ids

    def _reason_codes(
        self,
        *,
        output_present: bool,
        amount_result: dict[str, list[str]],
        deadline_result: dict[str, list[str]],
        missing_fact_ids: list[str],
        contradiction_pair_ids: list[str],
        raw_input_field_count: int,
        score: int,
    ) -> list[str]:
        codes: list[str] = []
        if not output_present:
            codes.append("fact-consistency-not-run")
        if amount_result["missing"]:
            codes.append("amount-missing")
        if amount_result["mismatched"]:
            codes.append("amount-mismatch")
        if deadline_result["missing"]:
            codes.append("deadline-missing")
        if deadline_result["mismatched"]:
            codes.append("deadline-mismatch")
        if missing_fact_ids:
            codes.append("required-fact-missing")
        if contradiction_pair_ids:
            codes.append("fact-contradiction")
        if raw_input_field_count:
            codes.append("raw-or-sensitive-input-rejected")
        if score >= PASS_THRESHOLD and not codes:
            codes.append("fact-consistency-ready")
        return codes or ["fact-consistency-review"]

    def _value_map(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, child in value.items():
                if isinstance(child, dict):
                    result[str(key)] = child.get("value")
                else:
                    result[str(key)] = child
            return result
        if isinstance(value, list | tuple):
            result: dict[str, Any] = {}
            for item in value:
                if isinstance(item, dict) and item.get("id"):
                    result[str(item["id"])] = item.get("value")
            return result
        return {}

    def _fact_ids(self, value: Any) -> set[str]:
        if isinstance(value, dict):
            return {str(key) for key, child in value.items() if child is True or child == "present"}
        if isinstance(value, list | tuple | set):
            return {str(item.get("id") if isinstance(item, dict) else item) for item in value if str(item).strip()}
        return set()

    def _raw_input_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            count = 0
            for key, child in value.items():
                if str(key).lower() in FORBIDDEN_INPUT_KEYS:
                    count += 1
                    continue
                count += self._raw_input_field_count(child)
            return count
        if isinstance(value, list):
            return sum(self._raw_input_field_count(item) for item in value[:100])
        if isinstance(value, str) and SENSITIVE_VALUE_PATTERN.search(value):
            return 1
        return 0

    def _coverage_score(self, expected_count: int, matched_count: int) -> int:
        if expected_count <= 0:
            return 100
        return max(0, round((matched_count / expected_count) * 100))

    def _metric_scores(
        self,
        amount: int,
        deadline: int,
        facts: int,
        contradiction: int,
        privacy: int,
    ) -> dict[str, int]:
        return {
            "amount_consistency": amount,
            "deadline_consistency": deadline,
            "required_fact_presence": facts,
            "contradiction_exclusion": contradiction,
            "raw_input_exclusion": privacy,
        }

    def _number(self, value: Any) -> float | None:
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip().replace(",", "")
            try:
                return float(stripped)
            except ValueError:
                return None
        return None

    def _date_str(self, value: Any) -> str | None:
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, str):
            stripped = value.strip()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stripped):
                return stripped
        return None

    def _output_dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _suite_status(self, score: int, case_results: list[dict[str, Any]]) -> str:
        if any(result["hard_consistency_block"] or result["status"] == "fail" for result in case_results):
            return "fail"
        return self._score_status(score)

    def _score_status(self, score: int) -> str:
        if score >= PASS_THRESHOLD:
            return "pass"
        if score >= WARN_THRESHOLD:
            return "warn"
        return "fail"

    def _cases(self) -> tuple[LegalDocumentFactConsistencyCase, ...]:
        return (
            LegalDocumentFactConsistencyCase(
                id="fact-lease-arrears-mini",
                title="Lease arrears amount and cure deadline",
                document_type="lawyer_letter",
                matter_type="lease_payment_collection",
                amount_expectations=(
                    AmountExpectation("monthly_rent", 4800, "CNY", "given monthly rent"),
                    AmountExpectation("arrears_total", 9600, "CNY", "monthly_rent * 2"),
                ),
                deadline_expectations=(
                    DeadlineExpectation("cure_due_date", "2026-04-08", "2026-04-01 + 7 days"),
                ),
                required_fact_ids=("lease_exists", "two_month_arrears", "written_notice_required"),
                contradiction_pairs=(
                    ContradictionPair("paid-vs-unpaid", ("arrears_fully_paid", "two_month_arrears")),
                ),
            ),
            LegalDocumentFactConsistencyCase(
                id="fact-maintenance-settlement-mini",
                title="Maintenance fee settlement total and installment facts",
                document_type="settlement_agreement",
                matter_type="maintenance_fee_settlement",
                amount_expectations=(
                    AmountExpectation("repair_fee", 4200, "CNY", "invoice repair fee"),
                    AmountExpectation("material_fee", 800, "CNY", "invoice material fee"),
                    AmountExpectation("settlement_total", 5000, "CNY", "repair_fee + material_fee"),
                ),
                deadline_expectations=(
                    DeadlineExpectation("first_installment_due", "2026-05-15", "signed date + 15 days"),
                    DeadlineExpectation("final_installment_due", "2026-06-15", "first due date + 31 days"),
                ),
                required_fact_ids=("two_installments", "mutual_release_after_full_payment", "late_fee_reserved"),
                contradiction_pairs=(
                    ContradictionPair("release-before-payment", ("release_effective_immediately", "mutual_release_after_full_payment")),
                ),
            ),
            LegalDocumentFactConsistencyCase(
                id="fact-service-contract-sla-mini",
                title="Service contract fee, delivery deadline, and SLA risk",
                document_type="contract_review",
                matter_type="service_contract_review",
                amount_expectations=(
                    AmountExpectation("service_fee", 120000, "CNY", "contract service fee"),
                    AmountExpectation("advance_payment", 36000, "CNY", "service_fee * 30%"),
                ),
                deadline_expectations=(
                    DeadlineExpectation("acceptance_due_date", "2026-07-30", "project delivery + 10 days"),
                ),
                required_fact_ids=("acceptance_standard_missing", "data_confidentiality_gap", "fault_response_gap"),
                contradiction_pairs=(
                    ContradictionPair("sla-present-vs-gap", ("fault_response_sla_complete", "fault_response_gap")),
                ),
            ),
            LegalDocumentFactConsistencyCase(
                id="fact-evidence-catalog-overtime-mini",
                title="Overtime evidence catalog hours and wage base",
                document_type="evidence_catalog",
                matter_type="labor_overtime_dispute",
                amount_expectations=(
                    AmountExpectation("monthly_wage_base", 9000, "CNY", "payroll wage base"),
                    AmountExpectation("claimed_overtime_hours", 18, "hour", "attendance records total"),
                ),
                deadline_expectations=(
                    DeadlineExpectation("evidence_exchange_due", "2026-03-20", "court notice deadline"),
                ),
                required_fact_ids=("attendance_record_attached", "payroll_record_attached", "original_carrier_pending"),
                contradiction_pairs=(
                    ContradictionPair("original-carrier", ("original_carrier_verified", "original_carrier_pending")),
                ),
            ),
        )
