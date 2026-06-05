from __future__ import annotations

import re
from typing import Any


DEFAULT_MODEL_OPS_API_TIMEOUT_MS = 25_000
DEFAULT_MODEL_OPS_FIRST_LOAD_BUDGET_MS = 2_500
DEFAULT_MODEL_OPS_CACHE_HIT_BUDGET_MS = 750
DEFAULT_MODEL_OPS_CACHE_TTL_SECONDS = 10.0
SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|token)",
    re.IGNORECASE,
)


class ModelOpsPerformanceBudgetService:
    """Build a metadata-only guard for ModelOps loading and timeout behavior."""

    def build_budget(
        self,
        payload: Any = None,
        *,
        cache_ttl_seconds: float = DEFAULT_MODEL_OPS_CACHE_TTL_SECONDS,
    ) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        summary = {
            "first_load_budget_ms": self._safe_int(
                data.get("first_load_budget_ms"),
                DEFAULT_MODEL_OPS_FIRST_LOAD_BUDGET_MS,
            ),
            "cache_hit_budget_ms": self._safe_int(
                data.get("cache_hit_budget_ms"),
                DEFAULT_MODEL_OPS_CACHE_HIT_BUDGET_MS,
            ),
            "frontend_request_timeout_ms": self._safe_int(
                data.get("frontend_request_timeout_ms"),
                DEFAULT_MODEL_OPS_API_TIMEOUT_MS,
            ),
            "backend_cache_ttl_seconds": self._safe_float(data.get("backend_cache_ttl_seconds"), cache_ttl_seconds),
            "models_payload_cache_enabled": bool(data.get("models_payload_cache_enabled", True)),
            "same_origin_fetch_first": bool(data.get("same_origin_fetch_first", True)),
            "duplicate_calibration_fetch_removed": bool(data.get("duplicate_calibration_fetch_removed", True)),
            "frontend_abort_controller_required": bool(data.get("frontend_abort_controller_required", True)),
            "raw_payload_echoed": False,
        }
        observations = self._observations(data.get("observations"))
        checks = self._checks(summary, observations)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": {
                "type": "model-ops-load-performance-budget",
                "notes": [
                    "Tracks ModelOps page load controls for the heavyweight /api/v1/aihub/models payload.",
                    "Requires same-origin fetch before SDK fallback, a frontend request timeout, short backend cache, and no duplicate cheap-first calibration fetch.",
                    "Accepts optional numeric timing observations only; it does not store prompts, documents, users, emails, keys, URLs, raw payloads, or model output.",
                ],
            },
            "summary": {
                **summary,
                "observation_count": len(observations),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
            },
            "observations": observations,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "urls_included": False,
                "output_scope": "numeric timing budgets, cache settings, timeout settings, check ids, and safe observations only",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_performance_budget.py tests/test_model_ops_readiness.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _observations(self, value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        rows: list[dict[str, Any]] = []
        for item in value[:12]:
            if not isinstance(item, dict):
                continue
            metric = self._safe_token(item.get("metric"))
            duration_ms = self._safe_optional_int(item.get("duration_ms"))
            budget_ms = self._safe_optional_int(item.get("budget_ms"))
            if not metric or duration_ms is None:
                continue
            rows.append(
                {
                    "metric": metric,
                    "duration_ms": duration_ms,
                    "budget_ms": budget_ms,
                    "within_budget": budget_ms is None or duration_ms <= budget_ms,
                }
            )
        return rows

    def _checks(self, summary: dict[str, Any], observations: list[dict[str, Any]]) -> list[dict[str, str]]:
        checks = [
            {
                "id": "frontend-timeout-configured",
                "status": "pass" if summary["frontend_request_timeout_ms"] >= 5_000 else "fail",
                "reason": "ModelOps API requests have an explicit frontend timeout guard."
                if summary["frontend_request_timeout_ms"] >= 5_000
                else "Configure a frontend timeout so a slow ModelOps request cannot hang the page.",
            },
            {
                "id": "backend-models-cache-enabled",
                "status": "pass"
                if summary["models_payload_cache_enabled"] and summary["backend_cache_ttl_seconds"] > 0
                else "fail",
                "reason": "The heavyweight /models payload uses a short backend cache."
                if summary["models_payload_cache_enabled"] and summary["backend_cache_ttl_seconds"] > 0
                else "Enable a short backend cache for the heavyweight /models payload.",
            },
            {
                "id": "same-origin-fetch-first",
                "status": "pass" if summary["same_origin_fetch_first"] else "warn",
                "reason": "ModelOps uses same-origin fetch before SDK fallback for local browser loads."
                if summary["same_origin_fetch_first"]
                else "Prefer same-origin fetch before SDK fallback so local loads do not wait for SDK timeouts.",
            },
            {
                "id": "duplicate-calibration-fetch-removed",
                "status": "pass" if summary["duplicate_calibration_fetch_removed"] else "warn",
                "reason": "ModelOps reuses the cheap-first calibration already embedded in /models."
                if summary["duplicate_calibration_fetch_removed"]
                else "Avoid loading cheap-first calibration twice during ModelOps first paint.",
            },
            {
                "id": "frontend-abort-controller",
                "status": "pass" if summary["frontend_abort_controller_required"] else "warn",
                "reason": "Frontend API helpers must cancel timed-out ModelOps requests with AbortController."
                if summary["frontend_abort_controller_required"]
                else "Add AbortController cancellation to prevent late writes after a timeout.",
            },
        ]
        slow_observations = [row for row in observations if row["within_budget"] is False]
        if observations:
            checks.append(
                {
                    "id": "observed-load-within-budget",
                    "status": "warn" if slow_observations else "pass",
                    "reason": f"{len(slow_observations)} submitted ModelOps timing observations exceed budget."
                    if slow_observations
                    else "Submitted ModelOps timing observations are within budget.",
                }
            )
        return checks

    def _recommended_actions(self, blocking: list[dict[str, str]], warnings: list[dict[str, str]]) -> list[str]:
        actions = []
        for check in [*blocking, *warnings]:
            actions.append(f"Review ModelOps performance check: {check['id']}.")
        if not actions:
            actions.append("Keep ModelOps first load guarded by cache, timeout, and duplicate-request regression tests.")
        return actions

    def _safe_int(self, value: Any, default: int) -> int:
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return max(0, value)
        return default

    def _safe_optional_int(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return max(0, value)
        return None

    def _safe_float(self, value: Any, default: float) -> float:
        if isinstance(value, bool):
            return default
        if isinstance(value, (int, float)):
            return round(max(0.0, float(value)), 3)
        return round(max(0.0, default), 3)

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "-")[:80]
        if SENSITIVE_PATTERN.search(raw):
            return "redacted-observation"
        return "".join(char if char.isalnum() or char in "_.:-" else "-" for char in raw).strip("-")
