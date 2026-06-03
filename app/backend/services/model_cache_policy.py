from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_cost_forecast import ModelCostForecastService
from services.model_request_policy import resolve_generation_request_policy


@dataclass(frozen=True)
class ModelCacheRule:
    task: str
    cache_mode: str
    ttl_seconds: int
    expected_hit_rate: float
    key_material: tuple[str, ...]
    privacy_boundary: str
    rationale: str
    enabled_by_default: bool = True

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["key_material"] = list(self.key_material)
        return data


CACHE_RULES: tuple[ModelCacheRule, ...] = (
    ModelCacheRule(
        task="fast",
        cache_mode="hashed-exact-request",
        ttl_seconds=6 * 60 * 60,
        expected_hit_rate=0.12,
        key_material=("task", "canonical_model", "response_format", "normalized_message_hash"),
        privacy_boundary="Store only deterministic hashes and aggregate counters; never store prompt text.",
        rationale="Preflight, routing, and light extraction requests often repeat in batch workflows.",
    ),
    ModelCacheRule(
        task="classification",
        cache_mode="hashed-material-fingerprint",
        ttl_seconds=24 * 60 * 60,
        expected_hit_rate=0.18,
        key_material=("task", "canonical_model", "schema_version", "material_fingerprint_hash"),
        privacy_boundary="Use a material fingerprint hash and schema version, not raw document text.",
        rationale="Document and evidence classification is deterministic and high-volume.",
    ),
    ModelCacheRule(
        task="ocr",
        cache_mode="hashed-page-image",
        ttl_seconds=7 * 24 * 60 * 60,
        expected_hit_rate=0.15,
        key_material=("task", "canonical_model", "page_image_hash", "ocr_prompt_version"),
        privacy_boundary="Use image/page hashes; never store scanned page images in the model cache.",
        rationale="OCR fallback may retry the same page after extraction failures or re-imports.",
    ),
    ModelCacheRule(
        task="review",
        cache_mode="template-and-rubric-only",
        ttl_seconds=2 * 60 * 60,
        expected_hit_rate=0.04,
        key_material=("task", "canonical_model", "rubric_version", "redacted_fact_pattern_hash"),
        privacy_boundary="Cache only redacted rubric patterns; user-specific legal facts stay out of cache entries.",
        rationale="Routine review can reuse rubric scaffolding but should not cache full legal fact narratives.",
    ),
    ModelCacheRule(
        task="pdf",
        cache_mode="disabled-user-document",
        ttl_seconds=0,
        expected_hit_rate=0.0,
        key_material=("task", "document_hash", "analysis_mode"),
        privacy_boundary="Large PDF analysis remains disabled by default because source documents may contain sensitive facts.",
        rationale="PDF review is a premium exception; cost is controlled by explicit routing rather than shared cache reuse.",
        enabled_by_default=False,
    ),
)


class ModelCachePolicyService:
    """Describe safe cache boundaries for repeated Gemini/NewAPI model work."""

    def build_policy(self, cost_forecast: dict[str, Any] | None = None) -> dict[str, Any]:
        cost_forecast = cost_forecast or ModelCostForecastService().build_forecast()
        forecast_by_task = {
            str(row.get("task")): row
            for row in _list(cost_forecast.get("profiles"))
            if isinstance(row, dict)
        }
        rows = [self._row(rule, forecast_by_task.get(rule.task)) for rule in CACHE_RULES]
        warnings = [row for row in rows if row["status"] == "warn"]
        blocking = [row for row in rows if row["status"] == "fail"]
        return {
            "status": self._status(rows),
            "method": {
                "type": "hashed-model-cache-policy",
                "notes": [
                    "Describes cache eligibility and safe key material; it does not store cache entries.",
                    "Only hashes, schema versions, task labels, model ids, and aggregate counters are allowed as cache metadata.",
                    "PDF document analysis is disabled by default because user documents may contain sensitive facts.",
                ],
            },
            "summary": {
                "rule_count": len(rows),
                "enabled_rule_count": sum(1 for row in rows if row["enabled_by_default"]),
                "estimated_monthly_savings_usd": round(
                    sum(row["estimated_monthly_savings_usd"] or 0.0 for row in rows),
                    6,
                ),
                "warning_count": len(warnings),
                "blocking_count": len(blocking),
            },
            "rules": rows,
            "blocking_check_ids": [row["id"] for row in blocking],
            "warning_check_ids": [row["id"] for row in warnings],
            "recommended_actions": self._recommended_actions(rows),
        }

    def _row(self, rule: ModelCacheRule, forecast_row: dict[str, Any] | None) -> dict[str, Any]:
        request_policy = resolve_generation_request_policy(task=rule.task)
        deterministic = request_policy.effective_temperature <= 0.2
        forecast_cost = _float(forecast_row.get("cheap_first_monthly_cost_usd")) if forecast_row else None
        estimated_savings = (
            round(max(0.0, forecast_cost * rule.expected_hit_rate), 6)
            if forecast_cost is not None and rule.enabled_by_default
            else 0.0
        )
        status = self._row_status(rule, deterministic, forecast_cost)
        data = rule.to_api()
        data.update(
            {
                "id": f"cache-policy-{rule.task}",
                "status": status,
                "deterministic_request_policy": deterministic,
                "request_temperature": request_policy.effective_temperature,
                "forecast_monthly_cost_usd": forecast_cost,
                "estimated_monthly_savings_usd": estimated_savings,
                "reason": self._reason(rule, deterministic, forecast_cost, status),
            }
        )
        return data

    def _row_status(self, rule: ModelCacheRule, deterministic: bool, forecast_cost: float | None) -> str:
        if not rule.enabled_by_default:
            return "pass"
        if forecast_cost is None:
            return "warn"
        if not deterministic:
            return "fail"
        if not rule.key_material:
            return "fail"
        return "pass"

    def _reason(
        self,
        rule: ModelCacheRule,
        deterministic: bool,
        forecast_cost: float | None,
        status: str,
    ) -> str:
        if not rule.enabled_by_default:
            return "Cache is intentionally disabled for this task; keep premium/document-sensitive paths explicit."
        if forecast_cost is None:
            return "Monthly cost forecast is missing, so cache savings cannot be estimated."
        if not deterministic:
            return "Request policy temperature is too high for safe exact-result reuse."
        if status == "pass":
            return f"{rule.task} can use {rule.cache_mode} with hashed metadata only."
        return "Review cache policy before enabling this task."

    def _status(self, rows: list[dict[str, Any]]) -> str:
        if any(row["status"] == "fail" for row in rows):
            return "fail"
        if any(row["status"] == "warn" for row in rows):
            return "warn"
        return "pass"

    def _recommended_actions(self, rows: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for row in rows:
            if row["status"] == "pass":
                continue
            if not row["deterministic_request_policy"]:
                actions.append(f"Lower {row['task']} temperature before enabling hashed cache reuse.")
            elif row["forecast_monthly_cost_usd"] is None:
                actions.append(f"Add {row['task']} to cost forecast before estimating cache savings.")
            else:
                actions.append(f"Review cache policy for {row['task']}.")
        if not actions:
            actions.append("Cache policy is safe to use with hash-only metadata for eligible tasks.")
        return actions


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
