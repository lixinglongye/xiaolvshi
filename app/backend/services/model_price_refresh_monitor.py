from __future__ import annotations

import re
from typing import Any, Iterable

from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    GEMINI_MODEL_CATALOG,
    canonical_model_id,
    model_profile,
    task_default_model,
)
from services.model_cost_forecast import ModelCostForecastService


HIGH_FREQUENCY_TASKS = ("fast", "classification", "ocr")
DEFAULT_ENV_VARS = {
    "fast": "APP_AI_FAST_MODEL",
    "classification": "APP_AI_CLASSIFIER_MODEL",
    "ocr": "APP_OCR_MODEL",
}
PREMIUM_OR_REFRESH_MARKERS = ("pro", "preview", "premium")
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(api[_-]?key|secret|password|passwd)\s*[:=]", re.IGNORECASE),
)


class ModelPriceRefreshMonitorService:
    """Local monitor for Gemini and gateway price refresh drift."""

    def build_monitor(
        self,
        observed_models: Iterable[Any] | None = None,
        cost_forecast: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        forecast = cost_forecast or ModelCostForecastService().build_forecast()

        checks: list[dict[str, Any]] = []
        drift_signals: list[dict[str, Any]] = []

        high_frequency_check, high_frequency_signals = self._check_high_frequency_defaults()
        checks.append(high_frequency_check)
        drift_signals.extend(high_frequency_signals)

        forecast_check, forecast_signals = self._check_forecast_pricing(forecast)
        checks.append(forecast_check)
        drift_signals.extend(forecast_signals)

        observed_check, observed_signals = self._check_observed_models(observed_models or ())
        checks.append(observed_check)
        drift_signals.extend(observed_signals)

        catalog_check, catalog_signals = self._catalog_refresh_watchlist()
        checks.append(catalog_check)
        drift_signals.extend(catalog_signals)

        status = self._aggregate_status(checks)
        warning_count = sum(1 for item in checks if item["status"] == "warn")
        blocking_count = sum(1 for item in checks if item["status"] == "fail")
        missing_price_count = sum(
            1
            for item in drift_signals
            if item.get("signal_type") in {"missing_price_metadata", "unknown_price_metadata"}
        )
        refresh_needed_count = sum(
            1
            for item in drift_signals
            if item.get("requires_price_refresh") is True and item.get("severity") in {"warn", "fail"}
        )

        return {
            "status": status,
            "summary": {
                "check_count": len(checks),
                "blocking_count": blocking_count,
                "warning_count": warning_count,
                "drift_signal_count": len(drift_signals),
                "refresh_needed_count": refresh_needed_count,
                "missing_price_metadata_count": missing_price_count,
                "high_frequency_tasks": list(HIGH_FREQUENCY_TASKS),
                "forecast_profile_count": len(_list(forecast.get("profiles"))),
                "observed_model_count": observed_check["summary"]["observed_model_count"],
            },
            "checks": checks,
            "drift_signals": drift_signals,
            "recommended_actions": self._recommended_actions(checks, drift_signals),
            "privacy_note": [
                "This monitor uses local model catalog and forecast metadata only.",
                "It does not call Gemini, NewAPI, OpenAI, or any other network service.",
                "It does not read, store, or return gateway credentials, prompts, legal documents, client identifiers, or raw model output.",
                "Observed model ids are redacted when they look like credentials or contact data.",
            ],
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_model_price_refresh_monitor.py -q",
                "cd app/backend && python -m compileall services/model_price_refresh_monitor.py tests/test_model_price_refresh_monitor.py",
            ],
        }

    def _check_high_frequency_defaults(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        rows: list[dict[str, Any]] = []
        signals: list[dict[str, Any]] = []

        for task in HIGH_FREQUENCY_TASKS:
            model_id = task_default_model(task)
            profile = model_profile(model_id)
            cost_tier = profile.cost_tier if profile else None
            stable = bool(profile and profile.status == "stable")
            priced = _has_text_price_metadata(profile)
            lowest = cost_tier == "lowest"
            blocked_marker = _has_premium_or_preview_marker(model_id)
            status = "pass"
            reason = f"{task} default remains on the lowest priced known Gemini text model."

            if profile is None:
                status = "fail"
                reason = "High-frequency default is not in the local catalog, so price and stability are unverified."
            elif not priced:
                status = "fail"
                reason = "High-frequency default lacks token price metadata."
            elif not stable:
                status = "fail"
                reason = "High-frequency default is not marked stable."
            elif not lowest or blocked_marker:
                status = "fail"
                reason = "High-frequency default is above the lowest tier or looks premium/preview."

            row = {
                "task": task,
                "env_var": DEFAULT_ENV_VARS[task],
                "default_model": model_id,
                "normalized_model": canonical_model_id(model_id),
                "status": status,
                "cost_tier": cost_tier,
                "max_allowed_cost_tier": "lowest",
                "stable": stable,
                "has_price_metadata": priced,
                "requires_price_refresh": status != "pass",
                "recommended_model": "gemini-2.5-flash-lite",
                "reason": reason,
            }
            rows.append(row)
            if status != "pass":
                signals.append(
                    self._signal(
                        signal_id=f"high-frequency-default-{task}",
                        severity="fail",
                        signal_type="high_frequency_default_drift",
                        model=model_id,
                        reason=reason,
                        action=f"Reset {DEFAULT_ENV_VARS[task]} to gemini-2.5-flash-lite or refresh catalog pricing before using this default.",
                    )
                )

        status = "fail" if any(row["status"] == "fail" for row in rows) else "pass"
        return (
            {
                "id": "high-frequency-default-price-tier",
                "status": status,
                "summary": {
                    "task_count": len(rows),
                    "aligned_count": sum(1 for row in rows if row["status"] == "pass"),
                    "blocking_count": sum(1 for row in rows if row["status"] == "fail"),
                },
                "rows": rows,
                "recommended_action": (
                    "Keep fast, classification, and OCR defaults on gemini-2.5-flash-lite."
                    if status == "pass"
                    else "Restore high-frequency defaults to gemini-2.5-flash-lite before increasing traffic."
                ),
            },
            signals,
        )

    def _check_forecast_pricing(self, forecast: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        rows = _list(forecast.get("profiles"))
        signals: list[dict[str, Any]] = []
        checked_models: set[tuple[str, str, str]] = set()

        if not rows:
            return (
                {
                    "id": "cost-forecast-price-metadata",
                    "status": "warn",
                    "summary": {
                        "forecast_profile_count": 0,
                        "checked_model_count": 0,
                        "missing_price_metadata_count": 0,
                    },
                    "rows": [],
                    "recommended_action": "Regenerate local cost forecast metadata before making price decisions.",
                },
                [
                    self._signal(
                        signal_id="cost-forecast-empty",
                        severity="warn",
                        signal_type="missing_forecast_metadata",
                        model=None,
                        reason="Cost forecast did not include profile rows.",
                        action="Refresh the local forecast fixture before comparing gateway prices.",
                    )
                ],
            )

        checked_rows: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            task = str(row.get("task") or "unknown")
            for role in ("initial_model", "escalation_model", "premium_baseline_model"):
                model_id = str(row.get(role) or "").strip()
                if not model_id:
                    continue
                dedupe_key = (task, role, model_id)
                if dedupe_key in checked_models:
                    continue
                checked_models.add(dedupe_key)
                profile = model_profile(model_id)
                priced = _has_any_price_metadata(profile)
                row_status = "pass" if profile and priced else "warn"
                signal_type = "missing_price_metadata" if profile else "unknown_price_metadata"
                reason = "Forecast model has local price metadata."
                if profile is None:
                    reason = "Forecast model is not in the local catalog; gateway price cannot be estimated locally."
                elif not priced:
                    reason = "Forecast model is known but lacks local price metadata."

                checked_row = {
                    "task": task,
                    "role": role,
                    "model": model_id,
                    "normalized_model": canonical_model_id(model_id),
                    "status": row_status,
                    "has_price_metadata": priced,
                    "cost_tier": profile.cost_tier if profile else None,
                    "catalog_status": profile.status if profile else "unknown",
                    "reason": reason,
                }
                checked_rows.append(checked_row)
                if row_status != "pass":
                    signals.append(
                        self._signal(
                            signal_id=f"forecast-price-{task}-{role}",
                            severity="warn",
                            signal_type=signal_type,
                            model=model_id,
                            reason=reason,
                            action="Refresh model_catalog pricing before relying on this forecast row.",
                        )
                    )

        status = "warn" if signals else "pass"
        return (
            {
                "id": "cost-forecast-price-metadata",
                "status": status,
                "summary": {
                    "forecast_profile_count": len(rows),
                    "checked_model_count": len(checked_rows),
                    "missing_price_metadata_count": sum(
                        1 for row in checked_rows if row["status"] != "pass"
                    ),
                },
                "rows": checked_rows,
                "recommended_action": (
                    "Forecast rows are priced from local catalog metadata."
                    if status == "pass"
                    else "Refresh missing local price metadata before using affected forecast rows."
                ),
            },
            signals,
        )

    def _check_observed_models(self, observed_models: Iterable[Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        rows: list[dict[str, Any]] = []
        signals: list[dict[str, Any]] = []

        for observed in observed_models:
            raw_model = self._model_id_from_observed(observed)
            if not raw_model:
                continue
            if _looks_sensitive(raw_model):
                raw_model = "[redacted-sensitive-model-id]"
            normalized = canonical_model_id(raw_model)
            profile = model_profile(raw_model)
            gemini_like = _is_gemini_like(raw_model) or bool(profile and profile.family == "gemini")
            premium_or_preview = _has_premium_or_preview_marker(raw_model) or bool(
                profile and (profile.cost_tier == "premium" or profile.status == "preview")
            )
            priced = _has_any_price_metadata(profile)
            row_status = "pass"
            reason = "Observed model is known, stable, and priced for local comparisons."
            signal_type = "observed_model_ok"

            if profile is None and gemini_like:
                row_status = "warn"
                reason = "Observed Gemini-like model is unknown locally; price and stability need catalog refresh."
                signal_type = "unknown_gateway_model"
            elif profile is None:
                row_status = "pass"
                reason = "Observed non-Gemini model is ignored by the Gemini price refresh monitor."
                signal_type = "external_model_ignored"
            elif premium_or_preview:
                row_status = "warn"
                reason = "Observed premium or preview Gemini model should be checked against current gateway pricing."
                signal_type = "premium_or_preview_refresh"
            elif not priced:
                row_status = "warn"
                reason = "Observed catalog model lacks local price metadata."
                signal_type = "missing_price_metadata"

            rows.append(
                {
                    "raw_model": raw_model,
                    "normalized_model": normalized,
                    "status": row_status,
                    "is_gemini_like": gemini_like,
                    "cost_tier": profile.cost_tier if profile else None,
                    "catalog_status": profile.status if profile else "unknown",
                    "has_price_metadata": priced,
                    "requires_price_refresh": row_status == "warn",
                    "reason": reason,
                }
            )
            if row_status == "warn":
                signals.append(
                    self._signal(
                        signal_id=f"observed-model-{len(rows)}",
                        severity="warn",
                        signal_type=signal_type,
                        model=raw_model,
                        reason=reason,
                        action="Keep this model explicit-only until local catalog tier, stability, and price metadata are refreshed.",
                    )
                )

        status = "warn" if signals else "pass"
        return (
            {
                "id": "observed-gateway-model-refresh-review",
                "status": status,
                "summary": {
                    "observed_model_count": len(rows),
                    "refresh_review_count": len(signals),
                    "known_model_count": sum(1 for row in rows if row["normalized_model"]),
                },
                "rows": rows,
                "recommended_action": (
                    "Observed models do not require price refresh review."
                    if status == "pass"
                    else "Refresh local catalog metadata for warned observed models before making them defaults."
                ),
            },
            signals,
        )

    def _catalog_refresh_watchlist(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        rows: list[dict[str, Any]] = []
        signals: list[dict[str, Any]] = []

        for profile in GEMINI_MODEL_CATALOG:
            needs_watch = (
                profile.status != "stable"
                or profile.cost_tier == "premium"
                or not _has_any_price_metadata(profile)
            )
            if not needs_watch:
                continue
            missing_price = not _has_any_price_metadata(profile)
            reason_parts: list[str] = []
            if profile.status != "stable":
                reason_parts.append(f"status={profile.status}")
            if profile.cost_tier == "premium":
                reason_parts.append("premium tier")
            if missing_price:
                reason_parts.append("missing price metadata")
            reason = "; ".join(reason_parts)
            rows.append(
                {
                    "model": profile.id,
                    "status": "watch",
                    "cost_tier": profile.cost_tier,
                    "catalog_status": profile.status,
                    "has_price_metadata": not missing_price,
                    "reason": reason,
                }
            )
            signals.append(
                self._signal(
                    signal_id=f"catalog-watch-{profile.id}",
                    severity="info",
                    signal_type="catalog_refresh_watch",
                    model=profile.id,
                    reason=reason,
                    action="Recheck provider or gateway pricing before promoting this model beyond explicit exception use.",
                    requires_price_refresh=missing_price,
                )
            )

        return (
            {
                "id": "catalog-price-refresh-watchlist",
                "status": "pass",
                "summary": {
                    "catalog_model_count": len(GEMINI_MODEL_CATALOG),
                    "watch_model_count": len(rows),
                    "missing_price_metadata_count": sum(1 for row in rows if not row["has_price_metadata"]),
                },
                "rows": rows,
                "recommended_action": "Keep preview, premium, and unpriced catalog entries on the refresh watchlist.",
            },
            signals,
        )

    def _model_id_from_observed(self, observed: Any) -> str:
        if isinstance(observed, str):
            return observed.strip()
        if isinstance(observed, dict):
            for key in ("id", "model", "name"):
                value = observed.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return str(observed or "").strip()

    def _recommended_actions(self, checks: list[dict[str, Any]], drift_signals: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for check in checks:
            if check["status"] in {"fail", "warn"}:
                actions.append(str(check["recommended_action"]))
        for signal in drift_signals:
            if signal["severity"] in {"fail", "warn"}:
                actions.append(str(signal["recommended_action"]))
        if not actions:
            actions.append("No blocking Gemini/NewAPI price refresh drift was found in local metadata.")
        return _dedupe(actions)

    def _aggregate_status(self, checks: list[dict[str, Any]]) -> str:
        if any(item["status"] == "fail" for item in checks):
            return "fail"
        if any(item["status"] == "warn" for item in checks):
            return "warn"
        return "pass"

    def _signal(
        self,
        *,
        signal_id: str,
        severity: str,
        signal_type: str,
        model: str | None,
        reason: str,
        action: str,
        requires_price_refresh: bool = True,
    ) -> dict[str, Any]:
        return {
            "id": signal_id,
            "severity": severity,
            "signal_type": signal_type,
            "model": model,
            "reason": reason,
            "requires_price_refresh": requires_price_refresh,
            "recommended_action": action,
        }


def _has_text_price_metadata(profile: Any) -> bool:
    if profile is None:
        return False
    return (
        profile.input_usd_per_million_tokens is not None
        and profile.output_usd_per_million_tokens is not None
    )


def _has_any_price_metadata(profile: Any) -> bool:
    if profile is None:
        return False
    return any(
        value is not None
        for value in (
            profile.input_usd_per_million_tokens,
            profile.output_usd_per_million_tokens,
            profile.output_usd_per_image,
        )
    )


def _has_premium_or_preview_marker(model_id: str) -> bool:
    parts = {
        part
        for part in (model_id or "").lower().replace("/", "-").replace(":", "-").replace("_", "-").split("-")
        if part
    }
    return any(marker in parts for marker in PREMIUM_OR_REFRESH_MARKERS)


def _is_gemini_like(model_id: str) -> bool:
    value = (model_id or "").strip().lower()
    if not value:
        return False
    candidates = {value, value.rsplit("/", 1)[-1], value.rsplit(":", 1)[-1]}
    return any(candidate.startswith("gemini-") or "gemini-" in candidate for candidate in candidates)


def _looks_sensitive(value: str) -> bool:
    return any(pattern.search(value or "") for pattern in SENSITIVE_VALUE_PATTERNS)


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
