from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Any

from services.model_runtime_router import RuntimeModelRoute
from services.model_task_inference import TaskInference


@dataclass
class RouteBucket:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    auto_inferred: int = 0
    explicit_task: int = 0
    downgraded_to_recommended: int = 0
    over_budget_requested: int = 0
    operator_review_requested: int = 0
    allowed_over_budget: int = 0
    unknown_price_model: int = 0
    stream_requests: int = 0
    last_seen_at: float = 0.0
    models: dict[str, int] = field(default_factory=dict)

    def record(
        self,
        *,
        model: str,
        inference_source: str,
        downgraded: bool,
        over_budget: bool,
        operator_review: bool,
        allowed_over_budget: bool,
        unknown_price: bool,
        stream: bool,
        success: bool,
    ) -> None:
        self.requests += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1
        if inference_source == "auto":
            self.auto_inferred += 1
        else:
            self.explicit_task += 1
        if downgraded:
            self.downgraded_to_recommended += 1
        if over_budget:
            self.over_budget_requested += 1
        if operator_review:
            self.operator_review_requested += 1
        if allowed_over_budget:
            self.allowed_over_budget += 1
        if unknown_price:
            self.unknown_price_model += 1
        if stream:
            self.stream_requests += 1
        self.models[model] = self.models.get(model, 0) + 1
        self.last_seen_at = time()

    def snapshot(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "successes": self.successes,
            "failures": self.failures,
            "auto_inferred": self.auto_inferred,
            "explicit_task": self.explicit_task,
            "downgraded_to_recommended": self.downgraded_to_recommended,
            "over_budget_requested": self.over_budget_requested,
            "operator_review_requested": self.operator_review_requested,
            "allowed_over_budget": self.allowed_over_budget,
            "unknown_price_model": self.unknown_price_model,
            "stream_requests": self.stream_requests,
            "last_seen_at": self.last_seen_at,
            "models": dict(sorted(self.models.items())),
        }


class ModelRouteTelemetryRegistry:
    """Aggregate runtime route decisions without storing prompts or documents."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._totals = RouteBucket()
        self._by_task: dict[str, RouteBucket] = {}
        self._by_inference_source: dict[str, RouteBucket] = {}
        self._version = 0

    def record(
        self,
        *,
        route: RuntimeModelRoute,
        task_inference: TaskInference,
        success: bool,
        stream: bool = False,
    ) -> None:
        task = (route.task or "unknown").strip() or "unknown"
        source = (task_inference.source or "unknown").strip() or "unknown"
        model = (route.resolved_model or "unknown").strip() or "unknown"
        downgraded = bool(route.routed_to_recommended_model)
        over_budget = bool(route.is_over_budget)
        operator_review = bool(route.requires_operator_review)
        reason_codes = set(getattr(route, "reason_codes", ()) or ())
        allowed_over_budget = bool(route.allow_over_budget_model and "explicit_over_budget_allowed" in reason_codes)
        unknown_price = not bool(route.is_known_model) or "unknown_catalog_model" in reason_codes

        with self._lock:
            buckets = [
                self._totals,
                self._by_task.setdefault(task, RouteBucket()),
                self._by_inference_source.setdefault(source, RouteBucket()),
            ]
            for bucket in buckets:
                bucket.record(
                    model=model,
                    inference_source=source,
                    downgraded=downgraded,
                    over_budget=over_budget,
                    operator_review=operator_review,
                    allowed_over_budget=allowed_over_budget,
                    unknown_price=unknown_price,
                    stream=stream,
                    success=success,
                )
            self._version += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            version = self._version
            totals = self._totals.snapshot()
            by_task = {
                task: bucket.snapshot()
                for task, bucket in sorted(self._by_task.items(), key=lambda item: item[0])
            }
            by_inference_source = {
                source: bucket.snapshot()
                for source, bucket in sorted(self._by_inference_source.items(), key=lambda item: item[0])
            }
        return {
            "status": "ready",
            "method": {
                "type": "aggregate-runtime-route-telemetry",
                "notes": [
                    "Records model routing decisions after deterministic task inference and budget enforcement.",
                    "Stores aggregate task, model, inference-source, downgrade, and success counters only.",
                    "Does not store prompts, documents, file names, API keys, users, emails, or raw model output.",
                ],
            },
            "summary": _summary(totals),
            "version": version,
            "totals": totals,
            "by_task": by_task,
            "by_inference_source": by_inference_source,
        }

    def reset(self) -> None:
        with self._lock:
            self._totals = RouteBucket()
            self._by_task.clear()
            self._by_inference_source.clear()
            self._version += 1

    @property
    def version(self) -> int:
        with self._lock:
            return self._version


def _summary(totals: dict[str, Any]) -> dict[str, Any]:
    requests = max(0, int(totals.get("requests") or 0))
    downgraded = max(0, int(totals.get("downgraded_to_recommended") or 0))
    auto = max(0, int(totals.get("auto_inferred") or 0))
    over_budget = max(0, int(totals.get("over_budget_requested") or 0))
    failures = max(0, int(totals.get("failures") or 0))
    return {
        "request_count": requests,
        "auto_inferred_ratio": _ratio(auto, requests),
        "downgrade_ratio": _ratio(downgraded, requests),
        "over_budget_request_ratio": _ratio(over_budget, requests),
        "failure_rate": _ratio(failures, requests),
        "operator_review_request_count": totals.get("operator_review_requested", 0),
        "allowed_over_budget_count": totals.get("allowed_over_budget", 0),
        "unknown_price_model_count": totals.get("unknown_price_model", 0),
    }


def _ratio(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(value / total, 4)


model_route_telemetry_registry = ModelRouteTelemetryRegistry()
