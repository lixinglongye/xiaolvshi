from __future__ import annotations

import re
from typing import Any

from services.legal_fixture_evidence_bundle import LegalFixtureEvidenceBundleService
from services.legal_fixture_model_matrix import LegalFixtureModelMatrixService
from services.legal_fixture_quick_suite import LegalFixtureQuickSuiteService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.model_budget import COST_TIER_RANK


FORBIDDEN_OUTPUT_KEYS = {
    "input_excerpt",
    "output_text",
    "generated_text",
    "raw_output",
    "raw_response",
    "prompt",
    "messages",
    "authorization",
    "api_key",
    "headers",
}
SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
    re.IGNORECASE,
)


class ModelOpsLegalFixtureCheapFirstBenchmarkGateService:
    """Gate cheap-first Gemini default evidence against small legal fixtures."""

    def __init__(
        self,
        quick_suite_service: LegalFixtureQuickSuiteService | None = None,
        model_matrix_service: LegalFixtureModelMatrixService | None = None,
        run_report_service: LegalFixtureRunReportService | None = None,
        evidence_bundle_service: LegalFixtureEvidenceBundleService | None = None,
    ) -> None:
        self.quick_suite_service = quick_suite_service or LegalFixtureQuickSuiteService()
        self.model_matrix_service = model_matrix_service or LegalFixtureModelMatrixService()
        self.run_report_service = run_report_service or LegalFixtureRunReportService()
        self.evidence_bundle_service = evidence_bundle_service or LegalFixtureEvidenceBundleService()

    def build_gate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        quick_suite = self.quick_suite_service.build_suite()
        model_matrix = self.model_matrix_service.build_matrix()
        run_report = self.run_report_service.build_report(payload)
        evidence_bundle = self.evidence_bundle_service.build_bundle(payload)
        matrix_by_fixture = {
            row["fixture_id"]: row
            for row in model_matrix.get("fixtures", [])
            if isinstance(row, dict) and row.get("fixture_id")
        }
        report_by_fixture = {
            row["fixture_id"]: row
            for row in run_report.get("fixture_reports", [])
            if isinstance(row, dict) and row.get("fixture_id")
        }
        source_by_fixture = self._source_by_fixture(quick_suite)
        gate_rows = [
            self._gate_row(fixture, matrix_by_fixture.get(fixture["fixture_id"]), report_by_fixture.get(fixture["fixture_id"]), source_by_fixture)
            for fixture in quick_suite.get("selected_fixtures", [])
            if isinstance(fixture, dict)
        ]
        blocking_rows = [row for row in gate_rows if row["gate_status"] == "blocked"]
        warning_rows = [row for row in gate_rows if row["gate_status"] in {"review_required", "not_run"}]
        passing_rows = [row for row in gate_rows if row["gate_status"] == "pass"]
        raw_input_field_count = self._raw_input_field_count(payload)

        return {
            "status": self._status(gate_rows, blocking_rows, warning_rows),
            "method": {
                "type": "modelops-legal-fixture-cheap-first-benchmark-gate",
                "notes": [
                    "Joins the laptop-safe quick suite, fixture model matrix, run report, and evidence bundle into one default-change gate.",
                    "Cheap Gemini fixture results can support default retention only after selected fixtures pass smoke checks without high-priority actions.",
                    "The gate returns metadata only and never calls NewAPI, Gemini, OpenAI, Google, a gateway, or the network.",
                ],
            },
            "summary": {
                "selected_fixture_count": len(gate_rows),
                "evaluated_fixture_count": sum(1 for row in gate_rows if row["run_report_status"] != "not_run"),
                "pass_count": len(passing_rows),
                "review_required_count": sum(1 for row in gate_rows if row["gate_status"] == "review_required"),
                "blocked_count": len(blocking_rows),
                "not_run_count": sum(1 for row in gate_rows if row["gate_status"] == "not_run"),
                "default_evidence_allowed_count": sum(1 for row in gate_rows if row["default_change_evidence_allowed"]),
                "cheap_first_model_count": sum(1 for row in gate_rows if row["cheap_first_model"]),
                "premium_escalation_candidate_count": sum(1 for row in gate_rows if row["premium_escalation_candidate"]),
                "license_review_source_count": sum(
                    1
                    for row in gate_rows
                    for state in row["public_source_sampling_states"]
                    if state == "license_review_required"
                ),
                "quick_suite_status": quick_suite["status"],
                "model_matrix_status": model_matrix["status"],
                "run_report_status": run_report["status"],
                "evidence_bundle_status": evidence_bundle["status"],
                "estimated_cheap_first_cost_usd": quick_suite["summary"]["estimated_cheap_first_cost_usd"],
                "max_parallel_requests": quick_suite["summary"]["max_parallel_requests"],
                "raw_input_field_count": raw_input_field_count,
                "raw_fixture_text_returned": False,
                "raw_model_output_returned": False,
                "newapi_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "gate_rows": gate_rows,
            "blocking_fixture_ids": [row["fixture_id"] for row in blocking_rows],
            "review_fixture_ids": [row["fixture_id"] for row in warning_rows],
            "default_evidence_fixture_ids": [row["fixture_id"] for row in passing_rows],
            "routing_policy": {
                "default_strategy": "cheap_first_gemini_with_fixture_gate",
                "cheap_first_models": sorted({row["cheap_first_model"] for row in gate_rows if row["cheap_first_model"]}),
                "default_evidence_requires": [
                    "selected fixture smoke status pass",
                    "no high priority improvement actions",
                    "known low-cost cheap-first model ladder",
                    "release evidence bundle reviewed",
                ],
                "blocked_actions": [
                    "do not promote a new default from failed or not-run fixture evidence",
                    "do not convert premium escalation candidates into defaults",
                    "do not claim public benchmark scores from metadata-only source mappings",
                ],
                "max_parallel_requests": quick_suite["summary"]["max_parallel_requests"],
                "configuration_write_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
            },
            "recommended_actions": self._recommended_actions(blocking_rows, warning_rows, passing_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_expected_signal_counts": True,
                "returns_raw_fixture_text": False,
                "returns_fixture_excerpt": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "network_called": False,
                "newapi_called": False,
                "output_scope": "fixture ids, expected signal counts, model ids, cost tiers, gate status, and release actions only",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "public_benchmark_scores_claimed": False,
                "external_dataset_execution_claimed": False,
                "live_gateway_quality_claimed": False,
                "production_legal_accuracy_claimed": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_legal_fixture_quick_suite.py tests/test_legal_fixture_model_matrix.py tests/test_legal_fixture_run_report.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _gate_row(
        self,
        fixture: dict[str, Any],
        matrix_row: dict[str, Any] | None,
        report_row: dict[str, Any] | None,
        source_by_fixture: dict[str, list[dict[str, str]]],
    ) -> dict[str, Any]:
        cheap_first = self._cheap_first_candidate(matrix_row)
        report_row = report_row or {}
        reason_codes = self._reason_codes(fixture, matrix_row, report_row, cheap_first, source_by_fixture)
        gate_status = self._gate_status(report_row, reason_codes)
        return {
            "id": f"{fixture['fixture_id']}-cheap-first-benchmark-gate",
            "fixture_id": fixture["fixture_id"],
            "title": fixture["title"],
            "matter_type": fixture["matter_type"],
            "task": fixture["task"],
            "cheap_first_model": cheap_first.get("model") if cheap_first else fixture.get("model"),
            "cheap_first_cost_tier": cheap_first.get("cost_tier") if cheap_first else fixture.get("model_cost_tier"),
            "cheap_first_known_model": bool(cheap_first and cheap_first.get("known_model")),
            "estimated_request_cost_usd": fixture["estimated_request_cost_usd"],
            "expected_signal_count": len(fixture.get("expected_signals", [])),
            "expected_task_count": len(fixture.get("expected_tasks", [])),
            "linked_case_count": len(fixture.get("linked_case_ids", [])),
            "public_source_ids": fixture.get("public_source_ids", []),
            "public_source_sampling_states": [
                source["sampling_state"]
                for source in source_by_fixture.get(str(fixture["fixture_id"]), [])
            ],
            "model_matrix_status": (matrix_row or {}).get("status", "missing"),
            "run_report_status": report_row.get("smoke_status", "not_run"),
            "run_report_score": report_row.get("score"),
            "matched_signal_count": report_row.get("matched_signal_count", 0),
            "missing_signal_count": report_row.get("missing_signal_count", len(fixture.get("expected_signals", []))),
            "missing_task_count": report_row.get("missing_task_count", len(fixture.get("expected_tasks", []))),
            "high_priority_action_count": report_row.get("high_priority_action_count", 0),
            "premium_escalation_candidate": self._has_premium_candidate(matrix_row),
            "gate_status": gate_status,
            "release_action": self._release_action(gate_status, report_row),
            "default_change_evidence_allowed": gate_status == "pass",
            "reason_codes": reason_codes,
            "validation_targets": [
                "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
                "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
            ],
            "raw_fixture_text_returned": False,
            "raw_model_output_returned": False,
            "gateway_called": False,
        }

    def _source_by_fixture(self, quick_suite: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
        rows: dict[str, list[dict[str, str]]] = {}
        for source in quick_suite.get("public_source_mapping", []):
            if not isinstance(source, dict):
                continue
            for fixture_id in source.get("local_fixture_ids", []):
                rows.setdefault(str(fixture_id), []).append(
                    {
                        "source_id": str(source.get("source_id") or ""),
                        "sampling_state": str(source.get("sampling_state") or "unknown"),
                    }
                )
        return rows

    def _cheap_first_candidate(self, matrix_row: dict[str, Any] | None) -> dict[str, Any] | None:
        for candidate in (matrix_row or {}).get("candidate_ladder", []):
            if isinstance(candidate, dict) and candidate.get("role") == "cheap_first":
                return candidate
        return None

    def _has_premium_candidate(self, matrix_row: dict[str, Any] | None) -> bool:
        return any(
            isinstance(candidate, dict) and candidate.get("cost_tier") == "premium"
            for candidate in (matrix_row or {}).get("candidate_ladder", [])
        )

    def _reason_codes(
        self,
        fixture: dict[str, Any],
        matrix_row: dict[str, Any] | None,
        report_row: dict[str, Any],
        cheap_first: dict[str, Any] | None,
        source_by_fixture: dict[str, list[dict[str, str]]],
    ) -> list[str]:
        codes: list[str] = []
        if not report_row or report_row.get("smoke_status") == "not_run":
            codes.append("fixture-not-run")
        if (matrix_row or {}).get("status") != "pass":
            codes.append("fixture-model-ladder-review")
        if not cheap_first:
            codes.append("missing-cheap-first-model")
        elif not cheap_first.get("known_model"):
            codes.append("unknown-cheap-first-model")
        elif COST_TIER_RANK.get(str(cheap_first.get("cost_tier") or "unknown"), 99) <= COST_TIER_RANK.get("low", 99):
            codes.append("known-low-cost-gemini-cheap-first")
        else:
            codes.append("cheap-first-cost-tier-review")
        if report_row.get("smoke_status") == "fail":
            codes.append("fixture-smoke-failed")
        if report_row.get("smoke_status") == "warn":
            codes.append("fixture-smoke-warning")
        if int(report_row.get("high_priority_action_count") or 0) > 0:
            codes.append("high-priority-fixture-improvement")
        if int(report_row.get("missing_signal_count") or 0) > 0:
            codes.append("missing-expected-signals")
        if self._has_premium_candidate(matrix_row):
            codes.append("premium-escalation-candidate")
        if any(
            source["sampling_state"] == "license_review_required"
            for source in source_by_fixture.get(str(fixture["fixture_id"]), [])
        ):
            codes.append("public-source-license-review")
        return _dedupe(codes) or ["fixture-gate-ready"]

    def _gate_status(self, report_row: dict[str, Any], reason_codes: list[str]) -> str:
        if not report_row or "fixture-not-run" in reason_codes:
            return "not_run"
        blocking = {"fixture-smoke-failed", "high-priority-fixture-improvement", "missing-cheap-first-model"}
        if any(code in blocking for code in reason_codes):
            return "blocked"
        review = {
            "fixture-model-ladder-review",
            "unknown-cheap-first-model",
            "cheap-first-cost-tier-review",
            "fixture-smoke-warning",
            "missing-expected-signals",
        }
        if any(code in review for code in reason_codes):
            return "review_required"
        return "pass"

    def _release_action(self, gate_status: str, report_row: dict[str, Any]) -> str:
        if gate_status == "pass":
            return "allow_cheap_first_fixture_evidence_for_default_retention"
        if gate_status == "blocked":
            return "block_default_change_until_selected_fixture_is_fixed"
        if gate_status == "not_run":
            return "run_selected_cheap_first_fixtures_before_default_change"
        next_step = str(report_row.get("recommended_next_step") or "review_fixture_warning")
        return f"review_fixture_before_default_change:{next_step}"

    def _status(
        self,
        gate_rows: list[dict[str, Any]],
        blocking_rows: list[dict[str, Any]],
        warning_rows: list[dict[str, Any]],
    ) -> str:
        if blocking_rows:
            return "blocked"
        if gate_rows and all(row["gate_status"] == "pass" for row in gate_rows):
            return "ready"
        if gate_rows and all(row["gate_status"] == "not_run" for row in gate_rows):
            return "not_run"
        if warning_rows:
            return "ready_with_watchlist"
        return "not_run"

    def _raw_input_field_count(self, payload: dict[str, Any] | None) -> int:
        if not isinstance(payload, dict):
            return 0
        return self._count_forbidden(payload)

    def _count_forbidden(self, value: Any) -> int:
        if isinstance(value, dict):
            count = 0
            for key, child in value.items():
                key_text = str(key).lower()
                if key_text in FORBIDDEN_OUTPUT_KEYS:
                    count += 1
                    continue
                count += self._count_forbidden(child)
            return count
        if isinstance(value, list):
            return sum(self._count_forbidden(item) for item in value[:50])
        if isinstance(value, str) and SENSITIVE_PATTERN.search(value):
            return 1
        return 0

    def _recommended_actions(
        self,
        blocking_rows: list[dict[str, Any]],
        warning_rows: list[dict[str, Any]],
        passing_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking_rows:
            return [
                f"{row['fixture_id']}: fix blocked cheap-first fixture evidence before changing defaults."
                for row in blocking_rows[:4]
            ]
        if warning_rows:
            return [
                "Run or review selected cheap-first fixtures before treating the result as default-change evidence.",
                "Keep public benchmark mappings metadata-only until license review passes.",
            ]
        if passing_rows:
            return [
                "Selected legal fixtures passed the cheap-first gate; keep defaults cheap-first and archive the evidence bundle.",
                "Do not promote premium escalation candidates into defaults from this gate alone.",
            ]
        return ["Prepare selected fixture observations before evaluating the cheap-first benchmark gate."]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
