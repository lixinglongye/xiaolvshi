from __future__ import annotations

import json
import time
from typing import Any

import httpx
from openai import AsyncOpenAI

from core.config import settings
from services.model_catalog import cheap_text_model, task_default_model
from services.model_gateway_connection_profile import normalize_openai_compatible_base_url
from services.model_gateway_probe_evaluation import ModelGatewayProbeEvaluationService

MAX_CHAT_PROBE_MODELS = 3
PROBE_MAX_TOKENS = 32
STATIC_JSON_PROBE_MESSAGES = (
    {"role": "system", "content": "Return compact JSON only."},
    {"role": "user", "content": 'Return {"ok":true,"task":"gateway_probe"}.'},
)


class ModelGatewayLiveProbeService:
    """Run an opt-in NewAPI/Gemini gateway probe and return sanitized metadata only."""

    async def run(self, payload: dict[str, Any] | None = None, *, client: Any | None = None) -> dict[str, Any]:
        payload = payload or {}
        execute = bool(payload.get("execute"))
        requested_models = self._dedupe_model_ids(payload.get("models") or payload.get("model_ids") or [])
        max_models = _safe_int(payload.get("max_models"), MAX_CHAT_PROBE_MODELS)
        max_models = max(1, min(max_models, MAX_CHAT_PROBE_MODELS))

        dry_run = self._dry_run(requested_models=requested_models, max_models=max_models)
        if not execute:
            return dry_run

        base_url = str(getattr(settings, "app_ai_base_url", "") or "").strip()
        api_key = str(getattr(settings, "app_ai_key", "") or "").strip()
        if client is None and (not base_url or not api_key):
            result = self._blocked_not_configured(dry_run)
            return result

        probe_client = client or self._build_client(base_url=base_url, api_key=api_key)
        model_ids: list[str] = []
        models_probe = await self._list_models(probe_client)
        if models_probe["status"] == "pass":
            model_ids = self._dedupe_model_ids(models_probe.get("model_ids") or [])

        probe_models = self._probe_models(requested_models=requested_models, observed_models=model_ids, max_models=max_models)
        chat_probe_results: dict[str, dict[str, Any]] = {}
        for model_id in probe_models:
            chat_probe_results[model_id] = await self._probe_chat_model(probe_client, model_id)

        evaluation_payload = {
            "model_ids": self._dedupe_model_ids([*model_ids, *probe_models]),
            "chat_probe_results": chat_probe_results,
        }
        evaluation = ModelGatewayProbeEvaluationService().evaluate(evaluation_payload)
        live_checks = self._live_checks(models_probe, chat_probe_results, evaluation)
        blocking = [check for check in live_checks if check["status"] == "fail"]
        warnings = [check for check in live_checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else ("warn" if warnings or evaluation["status"] != "pass" else "pass"),
            "method": self._method(executed=True),
            "summary": {
                "execute_requested": True,
                "gateway_called": True,
                "raw_outputs_returned": False,
                "raw_prompts_returned": False,
                "model_list_status": models_probe["status"],
                "observed_model_count": len(model_ids),
                "chat_probe_count": len(chat_probe_results),
                "chat_probe_pass_count": sum(1 for row in chat_probe_results.values() if row.get("status") == "pass"),
                "evaluation_status": evaluation["status"],
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
            },
            "model_list_probe": {
                "status": models_probe["status"],
                "http_status": models_probe.get("http_status"),
                "latency_ms": models_probe.get("latency_ms"),
                "model_count": len(model_ids),
                "error_category": models_probe.get("error_category", ""),
            },
            "chat_probe_results": chat_probe_results,
            "evaluation": evaluation,
            "checks": live_checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._actions(blocking, warnings, evaluation),
            "privacy_note": (
                "Live probe uses a static non-client JSON prompt and returns only model IDs, pass/fail status, "
                "HTTP status, JSON parse booleans, and latency. It never returns API keys, Authorization headers, "
                "raw gateway responses, prompts, user documents, or model output text."
            ),
        }

    def _dry_run(self, *, requested_models: list[str], max_models: int) -> dict[str, Any]:
        base_url = str(getattr(settings, "app_ai_base_url", "") or "").strip()
        api_key_configured = bool(str(getattr(settings, "app_ai_key", "") or "").strip())
        probe_models = self._probe_models(requested_models=requested_models, observed_models=[], max_models=max_models)
        checks = [
            {
                "id": "execute-flag",
                "status": "warn",
                "reason": "Set execute=true to run the live probe; dry-run mode makes no network calls.",
            },
            {
                "id": "base-url-configured",
                "status": "pass" if base_url else "warn",
                "reason": "APP_AI_BASE_URL is configured." if base_url else "Set APP_AI_BASE_URL before live probing.",
            },
            {
                "id": "api-key-configured",
                "status": "pass" if api_key_configured else "warn",
                "reason": "APP_AI_KEY is configured in local secrets." if api_key_configured else "Set APP_AI_KEY in local secrets; never commit it.",
            },
        ]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "dry_run",
            "method": self._method(executed=False),
            "summary": {
                "execute_requested": False,
                "gateway_called": False,
                "raw_outputs_returned": False,
                "raw_prompts_returned": False,
                "configured_base_url": self._display_base_url(base_url),
                "api_key_configured": api_key_configured,
                "planned_chat_probe_count": len(probe_models),
                "max_chat_probe_models": max_models,
                "warning_check_count": len(warnings),
            },
            "planned_probes": {
                "list_models": True,
                "chat_models": probe_models,
                "chat_prompt_kind": "static_json_contract",
                "max_tokens": PROBE_MAX_TOKENS,
                "temperature": 0,
            },
            "checks": checks,
            "blocking_check_ids": [],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": [
                "Review planned cheap-first models, then rerun with execute=true from a maintainer environment.",
                "Keep APP_AI_KEY in local secrets only; never paste it into requests, docs, tests, or commits.",
            ],
            "privacy_note": "Dry-run mode returns the live probe contract and does not call any gateway.",
        }

    def _method(self, *, executed: bool) -> dict[str, Any]:
        return {
            "type": "openai-compatible-live-gateway-probe",
            "mode": "live" if executed else "dry-run",
            "notes": [
                "Default mode is dry-run and never calls NewAPI, Gemini, or any gateway.",
                "Live mode is opt-in with execute=true and requires APP_AI_BASE_URL plus APP_AI_KEY in local secrets.",
                "Live mode records only sanitized metadata and feeds that into gateway probe evaluation.",
            ],
            "source_urls": [
                "https://ai.google.dev/gemini-api/docs/openai",
                "https://ai.google.dev/gemini-api/docs/models",
            ],
        }

    def _build_client(self, *, base_url: str, api_key: str) -> AsyncOpenAI:
        normalized_base_url = normalize_openai_compatible_base_url(base_url) or base_url.rstrip("/")
        return AsyncOpenAI(
            api_key=api_key,
            base_url=normalized_base_url,
            http_client=httpx.AsyncClient(
                timeout=httpx.Timeout(float(getattr(settings, "app_ai_request_timeout", 360)), connect=30.0),
                trust_env=False,
            ),
        )

    async def _list_models(self, client: Any) -> dict[str, Any]:
        started_at = time.monotonic()
        try:
            response = await client.models.list()
            model_ids = self._extract_model_ids(response)
            return {
                "status": "pass",
                "http_status": 200,
                "latency_ms": _latency_ms(started_at),
                "model_ids": model_ids,
            }
        except Exception as exc:  # pragma: no cover - exercised by fake client tests
            return {
                "status": "fail",
                "http_status": _http_status(exc),
                "latency_ms": _latency_ms(started_at),
                "model_ids": [],
                "error_category": _error_category(exc),
            }

    async def _probe_chat_model(self, client: Any, model_id: str) -> dict[str, Any]:
        started_at = time.monotonic()
        try:
            response = await client.chat.completions.create(
                model=model_id,
                messages=list(STATIC_JSON_PROBE_MESSAGES),
                temperature=0,
                max_tokens=PROBE_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            content = _response_text(response)
            return {
                "status": "pass" if _json_ok(content) else "warn",
                "http_status": 200,
                "json_ok": _json_ok(content),
                "latency_ms": _latency_ms(started_at),
            }
        except Exception as exc:
            return {
                "status": "fail",
                "http_status": _http_status(exc),
                "json_ok": False,
                "latency_ms": _latency_ms(started_at),
                "error_category": _error_category(exc),
            }

    def _probe_models(self, *, requested_models: list[str], observed_models: list[str], max_models: int) -> list[str]:
        candidates = requested_models or [
            cheap_text_model(),
            task_default_model("fast"),
            task_default_model("classification"),
            *[model_id for model_id in observed_models if "gemini" in model_id.lower() and "flash" in model_id.lower()],
        ]
        return self._dedupe_model_ids(candidates)[:max_models]

    def _extract_model_ids(self, response: Any) -> list[str]:
        data = getattr(response, "data", None)
        if data is None and isinstance(response, dict):
            data = response.get("data") or response.get("models") or response.get("items")
        if data is None:
            data = response
        return self._dedupe_model_ids(data if isinstance(data, (list, tuple)) else [])

    def _dedupe_model_ids(self, rows: Any) -> list[str]:
        seen = set()
        result: list[str] = []
        if not isinstance(rows, (list, tuple)):
            return result
        for row in rows:
            model_id = ""
            if isinstance(row, dict):
                model_id = str(row.get("id") or row.get("model") or row.get("name") or "").strip()
            else:
                model_id = str(getattr(row, "id", row) or "").strip()
            if not model_id or model_id in seen:
                continue
            seen.add(model_id)
            result.append(model_id)
        return result

    def _live_checks(
        self,
        models_probe: dict[str, Any],
        chat_probe_results: dict[str, dict[str, Any]],
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        chat_failures = [model_id for model_id, row in chat_probe_results.items() if row.get("status") == "fail"]
        return [
            {
                "id": "list-models-live-probe",
                "status": "pass" if models_probe["status"] == "pass" else "warn",
                "reason": "Gateway model list endpoint responded."
                if models_probe["status"] == "pass"
                else "Model list probe failed; chat probe metadata can still be evaluated if supplied.",
            },
            {
                "id": "cheap-chat-live-probe",
                "status": "pass" if chat_probe_results and not chat_failures else "fail",
                "reason": "All selected cheap-first chat probes completed."
                if chat_probe_results and not chat_failures
                else "At least one selected cheap-first chat probe failed.",
            },
            {
                "id": "sanitized-evaluation",
                "status": "fail" if "sanitized-payload-fields" in evaluation.get("blocking_check_ids", []) else "pass",
                "reason": "Live probe output passed the sanitized metadata evaluator.",
            },
        ]

    def _actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        evaluation: dict[str, Any],
    ) -> list[str]:
        if blocking:
            return [
                "Do not change model defaults from this probe; fix gateway errors and rerun with cheap-first models.",
                "Check APP_AI_BASE_URL, APP_AI_KEY, gateway model aliases, and rate limits without exposing credentials.",
            ]
        actions = ["Review sanitized gateway evaluation before changing defaults."]
        if warnings:
            actions.append("Resolve model-list or catalog warnings before unattended fixture batches.")
        actions.extend(evaluation.get("recommended_actions", [])[:2])
        return actions[:5]

    def _blocked_not_configured(self, dry_run: dict[str, Any]) -> dict[str, Any]:
        result = dict(dry_run)
        result["status"] = "blocked"
        result["summary"] = {**dry_run["summary"], "execute_requested": True, "gateway_called": False}
        result["blocking_check_ids"] = ["live-probe-configured"]
        result["checks"] = [
            *dry_run["checks"],
            {
                "id": "live-probe-configured",
                "status": "fail",
                "reason": "Live probe requires APP_AI_BASE_URL and APP_AI_KEY in local secrets.",
            },
        ]
        result["recommended_actions"] = [
            "Configure APP_AI_BASE_URL and APP_AI_KEY locally, then rerun with execute=true.",
            "Never paste or commit API keys; keep them in .env or deployment secrets.",
        ]
        return result

    def _display_base_url(self, base_url: str) -> str:
        if not base_url:
            return "{{APP_AI_BASE_URL}}"
        return normalize_openai_compatible_base_url(base_url) or base_url.rstrip("/")


def _response_text(response: Any) -> str:
    try:
        choice = (getattr(response, "choices", None) or [])[0]
        message = getattr(choice, "message", None)
        return str(getattr(message, "content", "") or "")
    except (IndexError, TypeError):
        return ""


def _json_ok(value: str) -> bool:
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(decoded, dict) and decoded.get("ok") is True


def _latency_ms(started_at: float) -> int:
    return int((time.monotonic() - started_at) * 1000)


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _http_status(exc: Exception) -> int | None:
    value = getattr(exc, "status_code", None)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _error_category(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    if "auth" in name or _http_status(exc) in {401, 403}:
        return "auth"
    if "rate" in name or _http_status(exc) == 429:
        return "rate_limit"
    if "timeout" in name:
        return "timeout"
    if "connect" in name or "connection" in name:
        return "connection"
    return "provider_error"
