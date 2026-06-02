"""
In-process model usage counters.

The counters intentionally store only aggregate metadata: task name, model name,
request status, latency, and token counts. Prompts, document text, user content,
API keys, and file names must never be recorded here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Any

from services.model_catalog import estimate_token_cost_usd


@dataclass
class ModelUsageCounter:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    total_latency_ms: int = 0
    last_seen_at: float = 0.0
    tasks: dict[str, int] = field(default_factory=dict)

    def record(
        self,
        *,
        task: str,
        success: bool,
        usage: dict[str, Any] | None = None,
        latency_ms: int | None = None,
    ) -> None:
        self.requests += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1
        self.tasks[task] = self.tasks.get(task, 0) + 1
        self.last_seen_at = time()

        if usage:
            self.prompt_tokens += _safe_int(usage.get("prompt_tokens"))
            self.completion_tokens += _safe_int(usage.get("completion_tokens"))
            self.total_tokens += _safe_int(usage.get("total_tokens"))
        if latency_ms is not None:
            self.total_latency_ms += max(0, int(latency_ms))

    def snapshot(self) -> dict[str, Any]:
        avg_latency_ms = round(self.total_latency_ms / self.requests, 2) if self.requests else 0
        return {
            "requests": self.requests,
            "successes": self.successes,
            "failures": self.failures,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": avg_latency_ms,
            "last_seen_at": self.last_seen_at,
            "tasks": dict(sorted(self.tasks.items())),
        }


class ModelUsageRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._by_model: dict[str, ModelUsageCounter] = {}

    def record(
        self,
        *,
        model: str,
        task: str,
        success: bool,
        usage: dict[str, Any] | None = None,
        latency_ms: int | None = None,
    ) -> None:
        model_key = (model or "unknown").strip() or "unknown"
        task_key = (task or "unknown").strip() or "unknown"
        with self._lock:
            counter = self._by_model.setdefault(model_key, ModelUsageCounter())
            counter.record(task=task_key, success=success, usage=usage, latency_ms=latency_ms)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            models = {
                model: counter.snapshot()
                for model, counter in sorted(self._by_model.items(), key=lambda item: item[0])
            }
            for model, data in models.items():
                data["estimated_cost_usd"] = estimate_token_cost_usd(
                    model,
                    data["prompt_tokens"],
                    data["completion_tokens"],
                )
        totals = {
            "requests": sum(item["requests"] for item in models.values()),
            "successes": sum(item["successes"] for item in models.values()),
            "failures": sum(item["failures"] for item in models.values()),
            "prompt_tokens": sum(item["prompt_tokens"] for item in models.values()),
            "completion_tokens": sum(item["completion_tokens"] for item in models.values()),
            "total_tokens": sum(item["total_tokens"] for item in models.values()),
            "estimated_cost_usd": round(
                sum(item["estimated_cost_usd"] or 0 for item in models.values()),
                8,
            ),
            "priced_model_count": sum(1 for item in models.values() if item["estimated_cost_usd"] is not None),
            "unpriced_model_count": sum(1 for item in models.values() if item["estimated_cost_usd"] is None),
        }
        return {"totals": totals, "models": models}

    def reset(self) -> None:
        with self._lock:
            self._by_model.clear()


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


model_usage_registry = ModelUsageRegistry()
