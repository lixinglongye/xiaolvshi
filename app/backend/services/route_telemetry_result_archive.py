from __future__ import annotations

from typing import Any

from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService
from services.route_telemetry_remediation_plan import RouteTelemetryRemediationPlanService
from services.route_telemetry_repository import RouteTelemetryRepositoryService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService


class RouteTelemetryResultArchiveService:
    """Build metadata-only result archive and cost ledger evidence for route telemetry."""

    def __init__(
        self,
        repository_service: RouteTelemetryRepositoryService | None = None,
        ops_summary_service: RouteTelemetryOpsSummaryService | None = None,
        triage_service: RouteTelemetryTriageQueueService | None = None,
        remediation_service: RouteTelemetryRemediationPlanService | None = None,
    ) -> None:
        self.repository_service = repository_service or RouteTelemetryRepositoryService()
        self.ops_summary_service = ops_summary_service or RouteTelemetryOpsSummaryService(self.repository_service)
        self.triage_service = triage_service or RouteTelemetryTriageQueueService(self.ops_summary_service)
        self.remediation_service = remediation_service or RouteTelemetryRemediationPlanService(self.triage_service)

    def build_archive(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = signals if isinstance(signals, dict) else {}
        repository = _dict(signals.get("route_telemetry_repository")) or self.repository_service.build_repository()
        ops_summary = _dict(signals.get("route_telemetry_ops_summary")) or self.ops_summary_service.build_summary(repository)
        triage = _dict(signals.get("route_telemetry_triage")) or self.triage_service.build_queue(ops_summary)
        remediation = _dict(signals.get("route_telemetry_remediation")) or self.remediation_service.build_plan(triage)

        archive_rows = self._archive_rows(ops_summary)
        cost_ledger_rows = self._cost_ledger_rows(repository)
        release_review_rows = self._release_review_rows(triage, remediation)
        source_statuses = {
            "repository": str(repository.get("status") or "missing"),
            "ops_summary": str(ops_summary.get("status") or "missing"),
            "triage": str(triage.get("status") or "missing"),
            "remediation": str(remediation.get("status") or "missing"),
        }
        status = self._status(source_statuses)
        blocking_ids = self._blocking_ids(ops_summary, triage, remediation)
        warning_ids = self._warning_ids(ops_summary, triage, remediation)
        ops = _dict(ops_summary.get("summary"))
        triage_summary = _dict(triage.get("summary"))
        remediation_summary = _dict(remediation.get("summary"))
        repo_summary = _dict(repository.get("summary"))

        return {
            "id": "route-telemetry-result-archive",
            "title": "Route telemetry result archive and cost ledger",
            "status": status,
            "method": {
                "type": "metadata-only-route-telemetry-result-archive",
                "notes": [
                    "Joins repository aggregates, operations checks, triage actions, and remediation metadata.",
                    "Creates reviewable daily archive rows and model/task cost ledger rows without storing prompts or model outputs.",
                    "Keeps unknown, unpriced, premium, over-budget, and operator-review routes visible for cheap-first maintenance.",
                ],
            },
            "summary": {
                "stored_event_count": _int(repo_summary.get("stored_event_count")),
                "daily_bucket_count": _int(repo_summary.get("daily_bucket_count")),
                "archive_day_count": len(archive_rows),
                "cost_ledger_row_count": len(cost_ledger_rows),
                "release_review_row_count": len(release_review_rows),
                "request_count": _int(ops.get("request_count")),
                "downgrade_count": _int(ops.get("downgrade_count")),
                "over_budget_count": _int(ops.get("over_budget_count")),
                "operator_review_count": _int(ops.get("operator_review_count")),
                "premium_request_count": _int(ops.get("premium_request_count")),
                "unknown_model_count": _int(ops.get("unknown_model_count")),
                "unpriced_model_count": _int(ops.get("unpriced_model_count")),
                "estimated_cost_usd_sum": _float(ops.get("estimated_cost_usd_sum")),
                "blocking_item_count": _int(triage_summary.get("blocking_item_count")),
                "warning_item_count": _int(triage_summary.get("warning_item_count")),
                "remediation_step_count": _int(remediation_summary.get("remediation_step_count")),
                "env_change_count": _int(remediation_summary.get("env_change_count")),
                "manual_review_step_count": _int(remediation_summary.get("manual_review_step_count")),
                "empty_repository": _bool(ops.get("empty_repository")),
                "model_calls": "not_required",
                "network_access": "disabled",
                "configuration_written": False,
                "raw_payload_storage_allowed": False,
            },
            "source_statuses": source_statuses,
            "archive_rows": archive_rows,
            "cost_ledger_rows": cost_ledger_rows,
            "release_review_rows": release_review_rows,
            "blocking_check_ids": blocking_ids,
            "warning_check_ids": warning_ids,
            "recommended_actions": self._recommended_actions(status, ops, triage, remediation),
            "source_boundaries": {
                "repository_source": "route_telemetry_repository daily_buckets and totals",
                "ops_source": "route_telemetry_ops_summary daily_rows and checks",
                "triage_source": "route_telemetry_triage metadata-only actions",
                "remediation_source": "route_telemetry_remediation metadata-only steps",
                "writes_configuration": False,
                "changes_default_routes": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateways": False,
                "imports_public_benchmark_samples": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_storage_allowed": False,
                "returns_raw_events": False,
                "returns_raw_prompts": False,
                "returns_raw_legal_text": False,
                "returns_request_bodies": False,
                "returns_response_bodies": False,
                "returns_headers": False,
                "returns_gateway_responses": False,
                "returns_raw_model_output": False,
                "returns_credentials": False,
                "returns_emails": False,
                "returns_user_identifiers": False,
                "model_calls": False,
                "network_access": False,
                "configuration_written": False,
            },
            "claim_boundary": {
                "claims_production_health": False,
                "claims_default_route_changed": False,
                "claims_public_benchmark_scores": False,
                "allowed_claim": "The repository exposes metadata-only route telemetry archive and cost-ledger evidence for maintainer review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_result_archive.py -q",
                "python -m pytest tests/test_route_telemetry_repository.py tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_remediation_plan.py -q",
            ],
        }

    def _archive_rows(self, ops_summary: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for row in _list(ops_summary.get("daily_rows")):
            if not isinstance(row, dict):
                continue
            rows.append(
                {
                    "day": str(row.get("day") or "unknown"),
                    "request_count": _int(row.get("request_count")),
                    "success_count": _int(row.get("success_count")),
                    "failure_count": _int(row.get("failure_count")),
                    "downgrade_count": _int(row.get("downgrade_count")),
                    "over_budget_count": _int(row.get("over_budget_count")),
                    "operator_review_count": _int(row.get("operator_review_count")),
                    "premium_request_count": _int(row.get("premium_request_count")),
                    "unknown_model_count": _int(row.get("unknown_model_count")),
                    "unpriced_model_count": _int(row.get("unpriced_model_count")),
                    "estimated_cost_usd_sum": _float(row.get("estimated_cost_usd_sum")),
                    "top_reason_codes": _safe_reason_rows(row.get("top_reason_codes")),
                    "reason_code_hotspots": _safe_hotspot_rows(row.get("reason_code_hotspots")),
                    "archive_status": self._row_status(row),
                }
            )
        return rows

    def _cost_ledger_rows(self, repository: dict[str, Any]) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for bucket in _list(repository.get("daily_buckets")):
            if not isinstance(bucket, dict):
                continue
            key = (str(bucket.get("task") or "unknown"), str(bucket.get("resolved_model") or "unknown"))
            row = grouped.setdefault(
                key,
                {
                    "task": key[0],
                    "resolved_model": key[1],
                    "request_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "estimated_cost_usd_sum": 0.0,
                    "unknown_model_count": 0,
                    "unpriced_model_count": 0,
                    "over_budget_count": 0,
                    "operator_review_count": 0,
                    "downgrade_count": 0,
                    "reason_code_counts": {},
                },
            )
            requests = _int(bucket.get("request_count"))
            row["request_count"] += requests
            row["success_count"] += _int(bucket.get("success_count"))
            row["failure_count"] += _int(bucket.get("failure_count"))
            row["estimated_cost_usd_sum"] = round(row["estimated_cost_usd_sum"] + _float(bucket.get("estimated_cost_usd_sum")), 8)
            row["unknown_model_count"] += _int(bucket.get("unknown_model_count"))
            row["unpriced_model_count"] += _int(bucket.get("unpriced_model_count"))
            row["over_budget_count"] += requests if _bool(bucket.get("is_over_budget")) else 0
            row["operator_review_count"] += requests if _bool(bucket.get("requires_operator_review")) else 0
            row["downgrade_count"] += requests if _bool(bucket.get("routed_to_recommended_model")) else 0
            _merge_counts(row["reason_code_counts"], _dict(bucket.get("reason_code_counts")))

        rows = []
        for row in grouped.values():
            cost_status = "priced"
            if row["unknown_model_count"] > 0:
                cost_status = "unknown_model_review"
            elif row["unpriced_model_count"] > 0:
                cost_status = "unpriced_model_review"
            elif row["operator_review_count"] > 0 or row["over_budget_count"] > 0:
                cost_status = "review_required"
            rows.append({**row, "cost_ledger_status": cost_status})
        return sorted(rows, key=lambda item: (-_float(item["estimated_cost_usd_sum"]), str(item["task"]), str(item["resolved_model"])))

    def _release_review_rows(self, triage: dict[str, Any], remediation: dict[str, Any]) -> list[dict[str, Any]]:
        triage_by_id = {str(item.get("id")): item for item in _list(triage.get("triage_items")) if isinstance(item, dict)}
        rows: list[dict[str, Any]] = []
        for step in _list(remediation.get("remediation_steps")):
            if not isinstance(step, dict):
                continue
            source_id = str(step.get("source_triage_item_id") or "")
            triage_item = _dict(triage_by_id.get(source_id))
            rows.append(
                {
                    "id": str(step.get("id") or source_id or "route-telemetry-review"),
                    "severity": str(step.get("severity") or triage_item.get("severity") or "info"),
                    "source_check_id": str(step.get("source_check_id") or triage_item.get("check_id") or "unknown"),
                    "task": str(step.get("task") or "model_ops"),
                    "requires_env_change": _bool(step.get("requires_env_change")),
                    "requires_operator_review": _bool(step.get("requires_operator_review")),
                    "recommended_model": step.get("recommended_model"),
                    "recommended_env_assignment_present": bool(step.get("recommended_env_assignment")),
                    "action": str(step.get("action") or triage_item.get("action") or ""),
                    "release_gate_links": _safe_string_list(step.get("release_gate_links") or triage_item.get("release_gate_links")),
                    "validation_commands": _safe_string_list(step.get("validation_commands") or triage_item.get("validation_commands")),
                }
            )
        if rows:
            return rows
        return [
            {
                "id": "route-telemetry-review-empty",
                "severity": "info",
                "source_check_id": "collect-staging-events",
                "task": "model_ops",
                "requires_env_change": False,
                "requires_operator_review": True,
                "recommended_model": None,
                "recommended_env_assignment_present": False,
                "action": "Collect sanitized staging route events before using archive evidence as production health proof.",
                "release_gate_links": ["route-telemetry-result-archive", "route-telemetry-repository"],
                "validation_commands": ["python -m pytest tests/test_route_telemetry_result_archive.py -q"],
            }
        ]

    def _row_status(self, row: dict[str, Any]) -> str:
        if _int(row.get("failure_count")) or _int(row.get("unknown_model_count")):
            return "review_required"
        if _int(row.get("unpriced_model_count")) or _int(row.get("premium_request_count")):
            return "cost_review_required"
        if _int(row.get("over_budget_count")) or _int(row.get("operator_review_count")):
            return "cheap_first_review"
        return "ready"

    def _status(self, source_statuses: dict[str, str]) -> str:
        values = set(source_statuses.values())
        if "fail" in values:
            return "fail"
        if values & {"warn", "review_required"}:
            return "warn"
        if values == {"ready"} or "ready" in values:
            return "ready"
        return "pass"

    def _blocking_ids(self, ops_summary: dict[str, Any], triage: dict[str, Any], remediation: dict[str, Any]) -> list[str]:
        return _unique(
            [
                *_safe_string_list(ops_summary.get("blocking_check_ids")),
                *_safe_string_list(triage.get("blocking_item_ids")),
                *_safe_string_list(remediation.get("blocking_step_ids")),
            ]
        )

    def _warning_ids(self, ops_summary: dict[str, Any], triage: dict[str, Any], remediation: dict[str, Any]) -> list[str]:
        return _unique(
            [
                *_safe_string_list(ops_summary.get("warning_check_ids")),
                *_safe_string_list(triage.get("warning_item_ids")),
                *_safe_string_list(remediation.get("warning_step_ids")),
            ]
        )

    def _recommended_actions(
        self,
        status: str,
        ops: dict[str, Any],
        triage: dict[str, Any],
        remediation: dict[str, Any],
    ) -> list[str]:
        if _bool(ops.get("empty_repository")):
            return ["Collect sanitized staging route events before treating the archive as production routing evidence."]
        if status == "fail":
            return _safe_string_list(remediation.get("recommended_actions"))[:4] or ["Resolve blocking route telemetry archive rows before default changes."]
        if status == "warn":
            return _safe_string_list(triage.get("recommended_actions"))[:4] or ["Review route telemetry cost ledger warnings before release claims."]
        return ["Route telemetry archive and cost ledger are within cheap-first review guardrails."]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return round(max(0.0, float(value)), 8)
    except (TypeError, ValueError):
        return 0.0


def _bool(value: Any) -> bool:
    return bool(value)


def _safe_string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    return [str(item).strip()[:200] for item in value if str(item).strip()][:20]


def _safe_reason_rows(value: Any) -> list[dict[str, Any]]:
    rows = []
    for item in _list(value):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "reason_code": str(item.get("reason_code") or "unknown")[:100],
                "count": _int(item.get("count")),
                "ratio": _float(item.get("ratio")),
            }
        )
    return rows[:8]


def _safe_hotspot_rows(value: Any) -> list[dict[str, Any]]:
    rows = []
    for item in _list(value):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "reason_code": str(item.get("reason_code") or "unknown")[:100],
                "count": _int(item.get("count")),
                "ratio": _float(item.get("ratio")),
                "severity": str(item.get("severity") or "warn")[:20],
                "label": str(item.get("label") or "")[:160],
            }
        )
    return rows[:8]


def _merge_counts(target: dict[str, int], source: dict[str, Any]) -> None:
    for key, value in source.items():
        safe_key = str(key or "").strip()[:100]
        if not safe_key:
            continue
        target[safe_key] = _int(target.get(safe_key)) + _int(value)


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
