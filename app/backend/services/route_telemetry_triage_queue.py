from __future__ import annotations

from typing import Any

from services.route_telemetry_ops_summary import RouteTelemetryOpsSummaryService


CHECK_GUIDANCE: dict[str, dict[str, str]] = {
    "repository-ready": {
        "title": "Restore route telemetry repository",
        "action": "Fix local route telemetry repository availability before relying on model-ops release evidence.",
        "owner": "engineering",
    },
    "failure-rate": {
        "title": "Investigate route failures",
        "action": "Review gateway error categories, fallback behavior, and retry policy before changing model defaults.",
        "owner": "engineering",
    },
    "over-budget-ratio": {
        "title": "Audit over-budget route pressure",
        "action": "Audit explicit model overrides and route budgets, then restore cheap-first defaults where quality allows.",
        "owner": "model_ops",
    },
    "operator-review-ratio": {
        "title": "Review operator-gated routes",
        "action": "Confirm operator-review routes are intentional exceptions and not hidden default-model drift.",
        "owner": "model_ops",
    },
    "premium-request-ratio": {
        "title": "Reduce premium-model drift",
        "action": "Move routine tasks back to cheap Gemini defaults or document why premium review is required.",
        "owner": "model_ops",
    },
    "unknown-model-count": {
        "title": "Catalog unknown gateway models",
        "action": "Add pricing, lifecycle, and capability metadata before using unknown Gemini-like models in release claims.",
        "owner": "engineering",
    },
    "unpriced-model-count": {
        "title": "Price or exclude unpriced catalog models",
        "action": "Refresh official provider and gateway pricing before using unpriced catalog models in cost or savings evidence.",
        "owner": "engineering",
    },
    "unknown-reason-code-count": {
        "title": "Review unknown route reason codes",
        "action": "Review route reason-code producers and keep telemetry labels on the allowlist before relying on reason-code hotspots.",
        "owner": "model_ops",
    },
}

CHEAP_FIRST_CHECK_IDS = {
    "over-budget-ratio",
    "operator-review-ratio",
    "premium-request-ratio",
    "unknown-model-count",
    "unpriced-model-count",
    "unknown-reason-code-count",
    "daily-route-hotspot",
    "reason-code-hotspot",
}


class RouteTelemetryTriageQueueService:
    """Convert persisted route telemetry ops checks into an actionable queue."""

    def __init__(self, ops_summary_service: RouteTelemetryOpsSummaryService | None = None) -> None:
        self.ops_summary_service = ops_summary_service or RouteTelemetryOpsSummaryService()

    def build_queue(self, ops_summary: dict[str, Any] | None = None) -> dict[str, Any]:
        summary_payload = ops_summary if isinstance(ops_summary, dict) else self.ops_summary_service.build_summary()
        source_summary = _dict(summary_payload.get("summary"))
        items = self._items_from_checks(summary_payload)
        items.extend(self._daily_hotspots(summary_payload))
        items.extend(self._reason_code_hotspots(summary_payload))
        if _bool(source_summary.get("empty_repository")):
            items.append(self._empty_repository_item(summary_payload))

        triage_items = sorted(items, key=lambda item: (-_int(item.get("priority")), str(item.get("id"))))
        blocking = [item for item in triage_items if item["severity"] == "fail"]
        warnings = [item for item in triage_items if item["severity"] == "warn"]
        info = [item for item in triage_items if item["severity"] == "info"]
        status = self._status(blocking, warnings, source_summary)

        return {
            "status": status,
            "method": {
                "type": "route-telemetry-triage-queue",
                "notes": [
                    "Consumes RouteTelemetryOpsSummaryService output only.",
                    "Turns failures, premium drift, over-budget pressure, operator review load, unknown models, and unknown reason-code hotspots into maintainer actions.",
                    "Does not read prompts, legal text, request bodies, response bodies, credentials, emails, or raw model outputs.",
                ],
            },
            "summary": {
                "triage_item_count": len(triage_items),
                "blocking_item_count": len(blocking),
                "warning_item_count": len(warnings),
                "info_item_count": len(info),
                "cheap_first_action_count": sum(1 for item in triage_items if item["check_id"] in CHEAP_FIRST_CHECK_IDS),
                "highest_priority": max((_int(item.get("priority")) for item in triage_items), default=0),
                "source_status": str(summary_payload.get("status") or "missing"),
                "source_request_count": _int(source_summary.get("request_count")),
                "empty_repository": _bool(source_summary.get("empty_repository")),
            },
            "triage_items": triage_items,
            "blocking_item_ids": [item["id"] for item in blocking],
            "warning_item_ids": [item["id"] for item in warnings],
            "recommended_actions": self._recommended_actions(status, triage_items),
            "privacy_boundary": {
                "source": "route_telemetry_ops_summary checks and daily rows",
                "raw_payload_storage_allowed": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "credentials_included": False,
                "raw_model_output_included": False,
            },
            "release_guardrails": [
                "Do not treat an empty triage queue as production health proof when no route events exist.",
                "Blocking triage items should be reviewed before changing Gemini/NewAPI defaults.",
                "Keep raw prompts, legal text, gateway payloads, credentials, emails, and model outputs outside triage evidence.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_triage_queue.py -q",
                "python -m pytest tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_repository.py -q",
            ],
        }

    def _items_from_checks(self, summary_payload: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for check in _list(summary_payload.get("checks")):
            if not isinstance(check, dict) or str(check.get("status")) == "pass":
                continue
            check_id = str(check.get("id") or "unknown-check")
            guidance = CHECK_GUIDANCE.get(
                check_id,
                {
                    "title": f"Review {check_id}",
                    "action": "Review route telemetry operations evidence before changing model defaults.",
                    "owner": "engineering",
                },
            )
            severity = "fail" if str(check.get("status")) == "fail" else "warn"
            threshold = check.get("fail_threshold") if severity == "fail" else check.get("warn_threshold")
            items.append(
                {
                    "id": f"route-telemetry-{check_id}",
                    "title": guidance["title"],
                    "severity": severity,
                    "priority": self._priority(severity, check_id),
                    "check_id": check_id,
                    "metric": check_id,
                    "value": check.get("value", 0),
                    "threshold": threshold,
                    "reason": str(check.get("reason") or guidance["title"]),
                    "action": guidance["action"],
                    "owner": guidance["owner"],
                    "release_gate_links": [
                        "route-telemetry-triage-queue",
                        "route-telemetry-ops-summary",
                        "route-telemetry-repository",
                    ],
                    "evidence_paths": [
                        "app/backend/services/route_telemetry_triage_queue.py",
                        "app/backend/services/route_telemetry_ops_summary.py",
                    ],
                    "validation_commands": [
                        "python -m pytest tests/test_route_telemetry_triage_queue.py -q",
                    ],
                }
            )
        return items

    def _daily_hotspots(self, summary_payload: dict[str, Any]) -> list[dict[str, Any]]:
        thresholds = _dict(summary_payload.get("thresholds"))
        items: list[dict[str, Any]] = []
        for row in _list(summary_payload.get("daily_rows")):
            if not isinstance(row, dict):
                continue
            metrics = [
                ("failure_rate", "fail_failure_rate", "warn_failure_rate", "daily failure rate"),
                ("over_budget_ratio", "fail_over_budget_ratio", "warn_over_budget_ratio", "daily over-budget ratio"),
                ("operator_review_ratio", "fail_operator_review_ratio", "warn_operator_review_ratio", "daily operator-review ratio"),
                ("premium_request_ratio", "fail_premium_ratio", "warn_premium_ratio", "daily premium ratio"),
            ]
            breached = []
            severity = "pass"
            for field, fail_key, warn_key, label in metrics:
                value = _float(row.get(field))
                if value >= _float(thresholds.get(fail_key)):
                    severity = "fail"
                    breached.append(f"{label} {round(value * 100)}%")
                elif value >= _float(thresholds.get(warn_key)) and severity != "fail":
                    severity = "warn"
                    breached.append(f"{label} {round(value * 100)}%")
            if severity == "pass":
                continue
            day = str(row.get("day") or "unknown")
            items.append(
                {
                    "id": f"route-telemetry-daily-hotspot-{day}",
                    "title": f"Review route telemetry hotspot for {day}",
                    "severity": severity,
                    "priority": self._priority(severity, "daily-route-hotspot") - 5,
                    "check_id": "daily-route-hotspot",
                    "metric": "daily ratios",
                    "value": _int(row.get("request_count")),
                    "threshold": "ops-summary thresholds",
                    "reason": "; ".join(breached) or "Daily route telemetry exceeded cheap-first thresholds.",
                    "action": "Inspect that day's task/model mix and move routine routes back to cheap-first defaults.",
                    "owner": "model_ops",
                    "release_gate_links": [
                        "route-telemetry-triage-queue",
                        "route-telemetry-ops-summary",
                    ],
                    "evidence_paths": [
                        "app/backend/services/route_telemetry_triage_queue.py",
                        "docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md",
                    ],
                    "validation_commands": [
                        "python -m pytest tests/test_route_telemetry_triage_queue.py -q",
                    ],
                }
            )
        return items

    def _reason_code_hotspots(self, summary_payload: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in _list(summary_payload.get("daily_rows")):
            if not isinstance(row, dict):
                continue
            day = str(row.get("day") or "unknown")
            reason_counts = _dict(row.get("reason_code_counts"))
            for hotspot in _list(row.get("reason_code_hotspots")):
                if not isinstance(hotspot, dict):
                    continue
                code = str(hotspot.get("reason_code") or "unknown_reason_code")
                severity = "fail" if str(hotspot.get("severity")) == "fail" else "warn"
                ratio = _float(hotspot.get("ratio"))
                count = _int(hotspot.get("count"))
                items.append(
                    {
                        "id": f"route-telemetry-reason-code-hotspot-{day}-{_slug(code)}",
                        "title": f"Review route reason-code hotspot: {code}",
                        "severity": severity,
                        "priority": self._priority(severity, "reason-code-hotspot") - 2,
                        "check_id": "reason-code-hotspot",
                        "metric": "reason_code_ratio",
                        "value": ratio,
                        "threshold": "reason-code hotspot thresholds",
                        "reason": f"{code} appeared {count} times on {day} ({round(ratio * 100)}% of persisted requests).",
                        "action": _reason_code_action(code),
                        "owner": "model_ops",
                        "reason_code": code,
                        "reason_code_counts": reason_counts,
                        "hotspot_ratio": ratio,
                        "source_day": day,
                        "release_gate_links": [
                            "route-telemetry-triage-queue",
                            "route-telemetry-ops-summary",
                            "route-telemetry-repository",
                        ],
                        "evidence_paths": [
                            "app/backend/services/route_telemetry_triage_queue.py",
                            "app/backend/services/route_telemetry_ops_summary.py",
                            "docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md",
                        ],
                        "validation_commands": [
                            "python -m pytest tests/test_route_telemetry_triage_queue.py -q",
                        ],
                    }
                )
        return items

    def _empty_repository_item(self, summary_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "route-telemetry-collect-staging-events",
            "title": "Collect staging route events",
            "severity": "info",
            "priority": 40,
            "check_id": "collect-staging-events",
            "metric": "source_request_count",
            "value": _int(_dict(summary_payload.get("summary")).get("request_count")),
            "threshold": "more than zero persisted route events",
            "reason": "No persisted route events exist yet, so production routing health is unproven.",
            "action": "Run a small sanitized staging batch through the route telemetry repository before making production health claims.",
            "owner": "model_ops",
            "release_gate_links": [
                "route-telemetry-triage-queue",
                "route-telemetry-repository",
            ],
            "evidence_paths": [
                "app/backend/services/route_telemetry_triage_queue.py",
                "docs/ROUTE_TELEMETRY_TRIAGE_QUEUE.md",
            ],
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_triage_queue.py -q",
            ],
        }

    def _priority(self, severity: str, check_id: str) -> int:
        base = 90 if severity == "fail" else 65
        if check_id == "failure-rate":
            return base + 8
        if check_id in {"premium-request-ratio", "over-budget-ratio"}:
            return base + 6
        if check_id == "reason-code-hotspot":
            return base + 5
        if check_id in {"unknown-model-count", "unpriced-model-count", "unknown-reason-code-count"}:
            return base + 4
        return base

    def _status(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]], source_summary: dict[str, Any]) -> str:
        if blocking:
            return "fail"
        if warnings:
            return "warn"
        return "ready" if _bool(source_summary.get("empty_repository")) else "pass"

    def _recommended_actions(self, status: str, triage_items: list[dict[str, Any]]) -> list[str]:
        actionable = [item for item in triage_items if item["severity"] in {"fail", "warn"}]
        if actionable:
            return [str(item["action"]) for item in actionable[:3]]
        if status == "ready":
            return ["Collect sanitized staging route events before claiming production routing health."]
        return ["No route telemetry triage actions are currently blocking cheap-first model operations."]


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
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _bool(value: Any) -> bool:
    return bool(value)


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-")[:80] or "unknown"


def _reason_code_action(code: str) -> str:
    return {
        "over_task_budget": "Audit task budgets and explicit model overrides, then move routine routes back under cheap-first limits.",
        "operator_review_required": "Confirm operator-review routes are intentional exceptions and document the quality or safety reason.",
        "routed_to_recommended_model": "Review repeated downgrades to ensure user-facing quality remains acceptable under cheap-first defaults.",
        "resolved_to_recommended_model": "Review recommendation resolution pressure before promoting or removing model defaults.",
        "unknown_catalog_model": "Catalog the model lifecycle, capabilities, and pricing before using these routes in release evidence.",
        "unverified_price_tier": "Refresh official provider and gateway pricing before relying on cost or savings claims.",
        "gateway_passthrough": "Review gateway passthrough routes and bind them to known catalog models where possible.",
        "unknown_reason_code": "Fix reason-code producers or extend the allowlist before treating these telemetry labels as evidence.",
    }.get(code, "Review this route reason-code hotspot before changing model defaults.")
