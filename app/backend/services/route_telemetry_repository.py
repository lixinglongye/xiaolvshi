from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from core.config import settings
from services.model_catalog import estimate_token_cost_usd, model_profile
from services.model_runtime_router import ROUTE_REASON_CODES, RuntimeModelRoute
from services.model_task_inference import TaskInference
from services.route_telemetry_persistence_plan import (
    ALLOWED_FIELDS,
    ROUTE_TELEMETRY_EVENT_TYPE,
    RouteTelemetryPersistencePlanService,
)


BOOLEAN_FIELDS = {
    "routed_to_recommended_model",
    "is_over_budget",
    "requires_operator_review",
    "allow_over_budget_model",
    "is_known_model",
    "success",
    "stream",
    "cache_hit",
}

INTEGER_FIELDS = {
    "estimated_input_tokens",
    "estimated_output_tokens",
    "latency_ms",
    "http_status",
}

FLOAT_FIELDS = {"estimated_cost_usd"}
STRING_LIST_FIELDS = {"reason_codes"}
ROUTE_REASON_CODE_SET = set(ROUTE_REASON_CODES)


@dataclass(frozen=True)
class PersistedRouteEvent:
    event_id: str
    day: str
    task: str
    resolved_model: str
    sanitized_event: dict[str, Any]


class RouteTelemetryRepositoryService:
    """Persist sanitized model route telemetry locally and expose daily aggregates."""

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        plan_service: RouteTelemetryPersistencePlanService | None = None,
    ) -> None:
        base = Path(storage_dir) if storage_dir is not None else Path(settings.local_storage_dir) / "model_ops" / "route_telemetry"
        self.storage_dir = base
        self.events_path = self.storage_dir / "events.jsonl"
        self.aggregates_path = self.storage_dir / "daily_aggregates.json"
        self.plan_service = plan_service or RouteTelemetryPersistencePlanService()

    def build_repository(self) -> dict[str, Any]:
        events = self._read_events()
        aggregates = self._aggregate(events)
        return self._response(
            status="ready",
            plan=self.plan_service.build_plan([]),
            accepted=[],
            rejected=[],
            stored_events=events,
            aggregates=aggregates,
        )

    def append_route_decision(
        self,
        *,
        route: RuntimeModelRoute,
        task_inference: TaskInference,
        success: bool,
        stream: bool = False,
        usage: dict[str, int] | None = None,
        latency_ms: int | None = None,
        error_category: str = "",
    ) -> dict[str, Any]:
        """Persist one sanitized route decision without prompt or response bodies."""
        event = self.build_route_decision_event(
            route=route,
            task_inference=task_inference,
            success=success,
            stream=stream,
            usage=usage,
            latency_ms=latency_ms,
            error_category=error_category,
        )
        return self.append_events([event])

    def build_route_decision_event(
        self,
        *,
        route: RuntimeModelRoute,
        task_inference: TaskInference,
        success: bool,
        stream: bool = False,
        usage: dict[str, int] | None = None,
        latency_ms: int | None = None,
        error_category: str = "",
    ) -> dict[str, Any]:
        usage = usage if isinstance(usage, dict) else {}
        input_tokens = _safe_int(usage.get("prompt_tokens"))
        output_tokens = _safe_int(usage.get("completion_tokens"))
        return {
            "event_id": f"route-{uuid4().hex}",
            "event_type": ROUTE_TELEMETRY_EVENT_TYPE,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "route_id": f"{route.task}:{route.resolved_model}",
            "task": route.task,
            "inference_source": task_inference.source,
            "requested_model": route.requested_resolved_model,
            "resolved_model": route.resolved_model,
            "gateway": "configured-aihub",
            "provider": _provider_family(route.resolved_model),
            "routed_to_recommended_model": route.routed_to_recommended_model,
            "is_over_budget": route.is_over_budget,
            "requires_operator_review": route.requires_operator_review,
            "reason_codes": list(route.reason_codes),
            "allow_over_budget_model": route.allow_over_budget_model,
            "is_known_model": route.is_known_model,
            "estimated_input_tokens": input_tokens,
            "estimated_output_tokens": output_tokens,
            "estimated_cost_usd": _estimated_route_cost(route.resolved_model, input_tokens, output_tokens),
            "latency_ms": _safe_int(latency_ms),
            "success": success,
            "error_category": _safe_error_category(error_category),
            "stream": stream,
            "cache_hit": False,
            "http_status": 200 if success else 500,
        }

    def append_events(self, events: Iterable[dict[str, Any]] | None) -> dict[str, Any]:
        candidates = [event for event in events or [] if isinstance(event, dict)]
        plan = self.plan_service.build_plan(candidates)
        accepted: list[PersistedRouteEvent] = []
        rejected: list[dict[str, Any]] = []

        existing = self._read_events()
        existing_ids = {str(event.get("event_id") or "") for event in existing}
        for event, check in zip(candidates, plan["persistence_checks"]):
            if not check.get("allowed_to_persist"):
                rejected.append(
                    {
                        "event_index": check.get("event_index"),
                        "status": "rejected",
                        "reason_codes": list(check.get("failures") or []),
                    }
                )
                continue

            sanitized = self._sanitize_event(event)
            event_id = str(sanitized.get("event_id") or "").strip()
            if not event_id:
                rejected.append(
                    {
                        "event_index": check.get("event_index"),
                        "status": "rejected",
                        "reason_codes": ["missing_event_id_after_sanitization"],
                    }
                )
                continue
            if event_id in existing_ids:
                rejected.append(
                    {
                        "event_index": check.get("event_index"),
                        "event_id": event_id,
                        "status": "duplicate",
                        "reason_codes": ["duplicate_event_id"],
                    }
                )
                continue

            persisted = PersistedRouteEvent(
                event_id=event_id,
                day=self._day(sanitized.get("timestamp")),
                task=str(sanitized.get("task") or "unknown"),
                resolved_model=str(sanitized.get("resolved_model") or "unknown"),
                sanitized_event=sanitized,
            )
            accepted.append(persisted)
            existing_ids.add(event_id)

        if accepted:
            self._append_events(accepted)

        stored_events = self._read_events()
        aggregates = self._aggregate(stored_events)
        self._write_aggregates(aggregates)
        status = "fail" if plan["status"] == "fail" and not accepted else ("warn" if rejected or plan["status"] == "warn" else "pass")
        return self._response(
            status=status,
            plan=plan,
            accepted=[item.sanitized_event for item in accepted],
            rejected=rejected,
            stored_events=stored_events,
            aggregates=aggregates,
        )

    def _response(
        self,
        *,
        status: str,
        plan: dict[str, Any],
        accepted: list[dict[str, Any]],
        rejected: list[dict[str, Any]],
        stored_events: list[dict[str, Any]],
        aggregates: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "method": {
                "type": "privacy-safe-local-route-telemetry-repository",
                "notes": [
                    "Stores only allowed route telemetry fields after persistence-plan validation.",
                    "Rejects events containing prompts, raw legal text, client contact details, credentials, headers, request bodies, or model outputs.",
                    "Aggregates by day, task, resolved model, inference source, downgrade, over-budget, operator-review, and success flags.",
                ],
            },
            "summary": {
                "stored_event_count": len(stored_events),
                "accepted_event_count": len(accepted),
                "rejected_event_count": len(rejected),
                "daily_bucket_count": len(aggregates["daily_buckets"]),
                "raw_payload_storage_allowed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "storage_mode": "local_jsonl",
            },
            "storage": {
                "events_path": str(self.events_path),
                "aggregates_path": str(self.aggregates_path),
                "retention": plan["retention_policy"],
            },
            "accepted_events": accepted,
            "rejected_events": rejected,
            "daily_buckets": aggregates["daily_buckets"],
            "totals": aggregates["totals"],
            "persistence_plan_status": plan["status"],
            "recommended_actions": self._recommended_actions(status, plan, rejected),
            "privacy_boundary": {
                "allowed_fields": list(ALLOWED_FIELDS),
                "raw_payload_storage_allowed": False,
                "duplicate_event_policy": "reject_duplicate_event_id",
                "forbidden_content": [
                    "api keys",
                    "emails",
                    "passwords",
                    "prompts",
                    "raw legal text",
                    "raw model output",
                    "headers",
                    "request bodies",
                    "response bodies",
                ],
            },
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_repository.py -q",
                "python -m pytest tests/test_route_telemetry_persistence_plan.py tests/test_model_route_telemetry.py -q",
            ],
        }

    def _sanitize_event(self, event: dict[str, Any]) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}
        for field in ALLOWED_FIELDS:
            if field not in event:
                continue
            value = event.get(field)
            if field in BOOLEAN_FIELDS:
                sanitized[field] = bool(value)
            elif field in INTEGER_FIELDS:
                sanitized[field] = _safe_int(value)
            elif field in FLOAT_FIELDS:
                sanitized[field] = _safe_float(value)
            elif field in STRING_LIST_FIELDS:
                sanitized[field] = _safe_string_list(value)
            else:
                sanitized[field] = _safe_string(value)
        sanitized["event_type"] = sanitized.get("event_type") or ROUTE_TELEMETRY_EVENT_TYPE
        sanitized["day"] = self._day(sanitized.get("timestamp"))
        return sanitized

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        return rows

    def _append_events(self, events: list[PersistedRouteEvent]) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event.sanitized_event, ensure_ascii=True, sort_keys=True) + "\n")

    def _write_aggregates(self, aggregates: dict[str, Any]) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.aggregates_path.write_text(json.dumps(aggregates, ensure_ascii=True, sort_keys=True, indent=2), encoding="utf-8")

    def _aggregate(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        buckets: dict[tuple[str, str, str, str, bool, bool, bool, bool], dict[str, Any]] = {}
        totals = {
            "request_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "downgrade_count": 0,
            "over_budget_count": 0,
            "operator_review_count": 0,
            "unknown_model_count": 0,
            "unpriced_model_count": 0,
            "reason_code_counts": {},
            "estimated_cost_usd_sum": 0.0,
        }
        for event in events:
            success = bool(event.get("success"))
            downgraded = bool(event.get("routed_to_recommended_model"))
            over_budget = bool(event.get("is_over_budget"))
            operator_review = bool(event.get("requires_operator_review"))
            known = bool(event.get("is_known_model"))
            model = str(event.get("resolved_model") or "unknown")
            unpriced_model = known and _is_token_unpriced_catalog_model(model)
            cost = _safe_float(event.get("estimated_cost_usd"))
            reason_codes = _safe_string_list(event.get("reason_codes"))
            key = (
                str(event.get("day") or self._day(event.get("timestamp"))),
                str(event.get("task") or "unknown"),
                model,
                str(event.get("inference_source") or "unknown"),
                downgraded,
                over_budget,
                operator_review,
                success,
            )
            bucket = buckets.setdefault(
                key,
                {
                    "day": key[0],
                    "task": key[1],
                    "resolved_model": key[2],
                    "inference_source": key[3],
                    "routed_to_recommended_model": key[4],
                    "is_over_budget": key[5],
                    "requires_operator_review": key[6],
                    "success": key[7],
                    "request_count": 0,
                    "success_count": 0,
                    "failure_count": 0,
                    "unknown_model_count": 0,
                    "unpriced_model_count": 0,
                    "reason_code_counts": {},
                    "estimated_cost_usd_sum": 0.0,
                },
            )
            bucket["request_count"] += 1
            bucket["success_count"] += 1 if success else 0
            bucket["failure_count"] += 0 if success else 1
            bucket["unknown_model_count"] += 0 if known else 1
            bucket["unpriced_model_count"] += 1 if unpriced_model else 0
            _increment_reason_counts(bucket["reason_code_counts"], reason_codes)
            bucket["estimated_cost_usd_sum"] = round(bucket["estimated_cost_usd_sum"] + cost, 8)

            totals["request_count"] += 1
            totals["success_count"] += 1 if success else 0
            totals["failure_count"] += 0 if success else 1
            totals["downgrade_count"] += 1 if downgraded else 0
            totals["over_budget_count"] += 1 if over_budget else 0
            totals["operator_review_count"] += 1 if operator_review else 0
            totals["unknown_model_count"] += 0 if known else 1
            totals["unpriced_model_count"] += 1 if unpriced_model else 0
            _increment_reason_counts(totals["reason_code_counts"], reason_codes)
            totals["estimated_cost_usd_sum"] = round(totals["estimated_cost_usd_sum"] + cost, 8)

        return {
            "totals": totals,
            "daily_buckets": sorted(buckets.values(), key=lambda item: (item["day"], item["task"], item["resolved_model"])),
        }

    def _day(self, timestamp: Any) -> str:
        value = str(timestamp or "").strip()
        if value:
            try:
                normalized = value.replace("Z", "+00:00")
                return datetime.fromisoformat(normalized).date().isoformat()
            except ValueError:
                return value[:10] if len(value) >= 10 else "unknown"
        return datetime.now(timezone.utc).date().isoformat()

    def _recommended_actions(self, status: str, plan: dict[str, Any], rejected: list[dict[str, Any]]) -> list[str]:
        if status == "ready":
            return ["Repository is ready; append sanitized route telemetry events after plan validation passes."]
        if rejected:
            return ["Review rejected or duplicate route telemetry events before relying on durable aggregate counters."]
        if status == "pass":
            return ["Persisted route telemetry events are sanitized and daily aggregate counters are current."]
        return plan.get("recommended_actions") or ["Review route telemetry repository warnings."]


def _safe_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        return ""
    return str(value).strip()[:200]


def _safe_string_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        safe = _safe_reason_code(item)
        if safe and safe not in result:
            result.append(safe)
        if len(result) >= 12:
            break
    return result


def _safe_reason_code(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")[:80]
    if not text:
        return ""
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    code = "".join(char for char in text if char in allowed).strip("_")
    if not code:
        return ""
    return code if code in ROUTE_REASON_CODE_SET else "unknown_reason_code"


def _increment_reason_counts(target: dict[str, int], reason_codes: list[str]) -> None:
    for code in reason_codes:
        target[code] = int(target.get(code, 0)) + 1


def _safe_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return round(max(0.0, float(value)), 8)
    except (TypeError, ValueError):
        return 0.0


def _provider_family(model: str) -> str:
    normalized = (model or "").lower()
    if "gemini" in normalized:
        return "google"
    if "gpt" in normalized or "openai" in normalized:
        return "openai"
    if "qwen" in normalized:
        return "qwen"
    return "unknown"


def _estimated_route_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    estimated = estimate_token_cost_usd(model, input_tokens, output_tokens)
    return _safe_float(estimated)


def _is_token_unpriced_catalog_model(model: str) -> bool:
    profile = model_profile(model)
    return bool(
        profile
        and profile.input_usd_per_million_tokens is None
        and profile.output_usd_per_million_tokens is None
    )


def _safe_error_category(value: Any) -> str:
    text = _safe_string(value).lower()
    if not text:
        return ""
    if "timeout" in text:
        return "timeout"
    if "rate" in text or "429" in text:
        return "rate_limit"
    if "auth" in text or "key" in text or "401" in text or "403" in text:
        return "auth_or_access"
    if "quota" in text or "billing" in text:
        return "quota_or_billing"
    return "runtime_error"
