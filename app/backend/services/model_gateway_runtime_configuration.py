from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from core.config import settings
from services.model_catalog import canonical_model_id, model_profile, task_default_model
from services.model_gateway_connection_profile import (
    has_openai_compatible_base_path,
    normalize_openai_compatible_base_url,
)


RUNTIME_ROLE_ENV_MAP: tuple[tuple[str, str, str], ...] = (
    ("cheap", "APP_AI_CHEAP_MODEL", "cheap"),
    ("fast", "APP_AI_FAST_MODEL", "fast"),
    ("classification", "APP_AI_CLASSIFIER_MODEL", "classification"),
    ("ocr", "APP_OCR_MODEL", "ocr"),
    ("review", "APP_AI_REVIEW_MODEL", "review"),
    ("pdf", "APP_AI_PDF_MODEL", "pdf"),
    ("image", "APP_AI_IMAGE_MODEL", "image"),
    ("embedding", "APP_AI_EMBEDDING_MODEL", "embedding"),
    ("agentic", "APP_AI_AGENTIC_MODEL", "agentic"),
    ("grounded-research", "APP_AI_GROUNDED_RESEARCH_MODEL", "grounded-research"),
)
HIGH_FREQUENCY_ROLES = {"cheap", "fast", "classification", "ocr"}


class ModelGatewayRuntimeConfigurationService:
    """Expose safe runtime gateway configuration evidence without returning secrets."""

    def build_configuration(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        raw_base_url = _first_text(data.get("base_url"), data.get("url"), getattr(settings, "app_ai_base_url", None))
        normalized_base_url = normalize_openai_compatible_base_url(raw_base_url)
        api_key_configured = _payload_key_present(data) or bool(_text(getattr(settings, "app_ai_key", None)))
        role_rows = self._role_rows()
        checks = self._checks(raw_base_url, normalized_base_url, api_key_configured, role_rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]

        return {
            "id": "model-gateway-runtime-configuration",
            "title": "Model gateway runtime configuration",
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": {
                "type": "metadata-only-openai-compatible-runtime-configuration",
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://ai.google.dev/gemini-api/docs/pricing",
                ],
                "notes": [
                    "Verifies that runtime setup can use a normalized OpenAI-compatible base URL before provider calls.",
                    "Keeps API key material in APP_AI_KEY or deployment secrets and returns only placeholder display values.",
                    "Pins high-frequency legal workflow roles to catalog-known Flash-Lite or lowest/low-cost Gemini defaults.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
            },
            "summary": {
                "base_url_configured": bool(raw_base_url),
                "api_key_configured": api_key_configured,
                "normalized_base_url": normalized_base_url or "{{APP_AI_BASE_URL}}",
                "openai_compatible_path": has_openai_compatible_base_path(urlparse(normalized_base_url or "").path),
                "remote_gateway": _is_remote_gateway(normalized_base_url or raw_base_url),
                "runtime_env_var_count": 2 + len(role_rows),
                "role_count": len(role_rows),
                "known_role_count": sum(1 for row in role_rows if row["known_catalog_model"]),
                "high_frequency_role_count": sum(1 for row in role_rows if row["high_frequency_role"]),
                "cheap_first_ready_count": sum(1 for row in role_rows if row["cheap_first_ready"]),
                "review_required_role_count": sum(1 for row in role_rows if row["runtime_action"] == "review_required"),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
                "traffic_shifted": False,
            },
            "runtime_env": {
                "base_url_env": "APP_AI_BASE_URL",
                "base_url_display": normalized_base_url or "{{APP_AI_BASE_URL}}",
                "api_key_env": "APP_AI_KEY",
                "api_key_display": "{{APP_AI_KEY}}" if api_key_configured else "not_configured",
                "client_base_url_source": "normalize_openai_compatible_base_url(APP_AI_BASE_URL)",
                "timeout_env": "APP_AI_REQUEST_TIMEOUT",
                "timeout_seconds": getattr(settings, "app_ai_request_timeout", None),
            },
            "role_rows": role_rows,
            "runtime_probe_sequence": [
                {
                    "step": "list-models",
                    "method": "GET",
                    "url": "{{APP_AI_BASE_URL}}/models",
                    "model": None,
                    "required_before": "cheap-json-probe",
                    "payload_boundary": "no request body; key placeholder remains local",
                },
                {
                    "step": "cheap-json-probe",
                    "method": "POST",
                    "url": "{{APP_AI_BASE_URL}}/chat/completions",
                    "model": task_default_model("fast"),
                    "required_before": "legal-fixture-smoke",
                    "payload_boundary": "tiny synthetic JSON prompt only; no client legal text or documents",
                },
                {
                    "step": "legal-fixture-smoke",
                    "method": "POST",
                    "url": "{{APP_AI_BASE_URL}}/chat/completions",
                    "model": task_default_model("fast"),
                    "required_before": "batch-runs",
                    "payload_boundary": "small local benchmark fixtures only after list-models and cheap probe pass",
                },
            ],
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "configuration_policy": {
                "key_storage": "APP_AI_KEY or deployment secret only",
                "base_url_storage": "APP_AI_BASE_URL with normalized /v1 or Gemini OpenAI-compatible /openai path",
                "high_frequency_default_policy": "Flash-Lite or known lowest/low-cost stable Gemini catalog model first",
                "premium_exception_policy": "Pro, preview, unknown, media, or unpriced models require explicit review before defaults",
                "yibuapi_base_url_example": "https://yibuapi.com/v1",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "credentials_included": False,
                "credential_material_included": False,
                "authorization_headers_included": False,
                "raw_payload_echoed": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "gateway_response_included": False,
                "emails_included": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
            },
            "claim_boundary": {
                "actual_key_validated": False,
                "live_gateway_execution_claimed": False,
                "model_inventory_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "pricing_accuracy_claimed": False,
            },
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "validation_commands": [
                "python -m pytest tests/test_model_gateway_runtime_configuration.py tests/test_model_gateway_connection_profile.py tests/test_model_gateway_health_plan.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _role_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for role, env_name, task in RUNTIME_ROLE_ENV_MAP:
            model_id = task_default_model(task)
            canonical = canonical_model_id(model_id)
            profile = model_profile(model_id)
            cost_tier = profile.cost_tier if profile else "unknown"
            high_frequency = role in HIGH_FREQUENCY_ROLES
            cheap_first_ready = bool(
                profile
                and profile.status == "stable"
                and (
                    not high_frequency
                    or profile.cost_tier in {"lowest", "low"}
                    or "flash-lite" in profile.id
                )
            )
            review_required = bool(not profile or profile.status != "stable" or (high_frequency and not cheap_first_ready))
            rows.append(
                {
                    "role": role,
                    "task": task,
                    "env_name": env_name,
                    "configured_model": model_id,
                    "canonical_model": canonical,
                    "known_catalog_model": profile is not None,
                    "cost_tier": cost_tier,
                    "model_status": profile.status if profile else "unknown",
                    "high_frequency_role": high_frequency,
                    "cheap_first_ready": cheap_first_ready,
                    "runtime_action": "review_required" if review_required else "ready",
                    "reason": self._role_reason(role, model_id, profile, high_frequency, cheap_first_ready),
                }
            )
        return rows

    def _role_reason(
        self,
        role: str,
        model_id: str,
        profile: Any,
        high_frequency: bool,
        cheap_first_ready: bool,
    ) -> str:
        if not profile:
            return f"{role} uses gateway-specific model {model_id}; keep explicit-only until catalog and pricing review."
        if high_frequency and not cheap_first_ready:
            return f"{role} is high-frequency and must stay on a stable lowest/low-cost Gemini default."
        return f"{role} maps to stable catalog model {profile.id} with cost tier {profile.cost_tier}."

    def _checks(
        self,
        raw_base_url: str,
        normalized_base_url: str | None,
        api_key_configured: bool,
        role_rows: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        parsed = urlparse(raw_base_url) if raw_base_url else None
        insecure_remote = bool(parsed and parsed.scheme == "http" and (parsed.hostname or "") not in {"localhost", "127.0.0.1", "::1"})
        credential_url = bool(parsed and (parsed.username or parsed.password or parsed.query))
        openai_path = has_openai_compatible_base_path(urlparse(normalized_base_url or "").path)
        high_frequency_drift = [
            row["role"] for row in role_rows if row["high_frequency_role"] and not row["cheap_first_ready"]
        ]
        unknown_roles = [row["role"] for row in role_rows if not row["known_catalog_model"]]

        return [
            {
                "id": "runtime-base-url-configured",
                "status": "pass" if raw_base_url else "warn",
                "reason": "APP_AI_BASE_URL or supplied URL is present." if raw_base_url else "Set APP_AI_BASE_URL before live gateway use.",
            },
            {
                "id": "runtime-base-url-openai-compatible",
                "status": "pass" if openai_path else "warn",
                "reason": "Runtime base URL has an OpenAI-compatible path." if openai_path else "Use /v1 or Gemini /v1beta/openai before live calls.",
            },
            {
                "id": "runtime-base-url-no-credential-material",
                "status": "fail" if credential_url else "pass",
                "reason": "Gateway URL contains no credentials or query secrets." if not credential_url else "Move URL credentials or query tokens into APP_AI_KEY/deployment secrets.",
            },
            {
                "id": "runtime-remote-https",
                "status": "fail" if insecure_remote else ("pass" if parsed and parsed.scheme == "https" else "warn"),
                "reason": "Remote runtime gateway uses HTTPS." if parsed and parsed.scheme == "https" else ("Remote HTTP gateways are blocked." if insecure_remote else "Use HTTPS for remote gateways; localhost HTTP is development-only."),
            },
            {
                "id": "runtime-api-key-placeholder",
                "status": "pass" if api_key_configured else "warn",
                "reason": "APP_AI_KEY is configured but redacted as a placeholder." if api_key_configured else "Set APP_AI_KEY locally or in deployment secrets; never commit it.",
            },
            {
                "id": "runtime-cheap-first-role-defaults",
                "status": "fail" if high_frequency_drift else ("warn" if unknown_roles else "pass"),
                "reason": "High-frequency runtime roles are cheap-first and catalog-known."
                if not high_frequency_drift and not unknown_roles
                else (
                    f"High-frequency role drift: {', '.join(high_frequency_drift)}."
                    if high_frequency_drift
                    else f"Gateway-specific role models need review: {', '.join(unknown_roles)}."
                ),
            },
            {
                "id": "runtime-probe-order",
                "status": "pass",
                "reason": "List-models must pass before cheap JSON probes, and cheap probes before legal fixture smoke runs.",
            },
        ]

    def _recommended_actions(self, blocking: list[dict[str, str]], warnings: list[dict[str, str]]) -> list[str]:
        if blocking:
            return [
                "Remove credential material from APP_AI_BASE_URL and keep secrets only in APP_AI_KEY or deployment secrets.",
                "Restore high-frequency runtime roles to stable Flash-Lite or known low-cost Gemini defaults.",
            ]
        actions = [
            "Keep APP_AI_KEY outside git and pass it through local .env or deployment secret managers only.",
            "Run list-models first, then the cheap JSON probe, before any legal fixture or batch run.",
        ]
        if warnings:
            actions.insert(0, "Complete APP_AI_BASE_URL and APP_AI_KEY setup before claiming live gateway readiness.")
        return actions


def _payload_key_present(data: dict[str, Any]) -> bool:
    return any(_text(data.get(name)) for name in ("key", "api_key", "token"))


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _is_remote_gateway(value: str) -> bool:
    parsed = urlparse(value or "")
    host = (parsed.hostname or "").lower()
    return bool(parsed.scheme in {"http", "https"} and host not in {"", "localhost", "127.0.0.1", "::1"})
