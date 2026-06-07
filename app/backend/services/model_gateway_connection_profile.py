from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

from core.config import settings
from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    canonical_model_id,
    cheap_text_model,
    image_model,
    model_profile,
    task_default_model,
)


SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{8,}|api[_-]?key|authorization|bearer|token|secret|password)",
    re.IGNORECASE,
)
REMOTE_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
OPENAI_COMPATIBLE_PATH_HINTS = ("/v1", "/openai", "/v1beta/openai")
CHEAP_FIRST_ROLES = ("cheap", "fast", "ocr", "classification", "image")


def normalize_openai_compatible_base_url(base_url: str | None) -> str | None:
    """Normalize a remote bare gateway URL to an OpenAI-compatible /v1 base URL."""
    value = str(base_url or "").strip().rstrip("/")
    if not value:
        return None

    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value

    path = parsed.path.rstrip("/")
    normalized = parsed._replace(
        netloc=_netloc_without_credentials(parsed),
        path=path,
        params="",
        query="",
        fragment="",
    )
    if _path_has_openai_compatible_hint(path):
        return urlunparse(normalized).rstrip("/")

    host = (parsed.hostname or "").lower()
    if path in {"", "/"} and host not in REMOTE_LOCAL_HOSTS:
        normalized = normalized._replace(path="/v1")
    return urlunparse(normalized).rstrip("/")


class ModelGatewayConnectionProfileService:
    """Build safe NewAPI/Gemini connection evidence without returning secrets."""

    def build_profile(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        raw_base_url = _first_text(
            data.get("base_url"),
            data.get("url"),
            data.get("endpoint"),
            getattr(settings, "app_ai_base_url", None),
        )
        payload_supplied_key = any(_text(data.get(name)) for name in ("key", "api_key", "token"))
        api_key_configured = payload_supplied_key or bool(_text(getattr(settings, "app_ai_key", None)))
        parsed = urlparse(raw_base_url) if raw_base_url else None
        normalized_base_url = normalize_openai_compatible_base_url(raw_base_url)
        role_rows = self._role_rows()
        checks = self._checks(raw_base_url, normalized_base_url, parsed, api_key_configured, role_rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        normalized = bool(raw_base_url and normalized_base_url and normalized_base_url != raw_base_url.rstrip("/"))

        return {
            "id": "model-gateway-connection-profile",
            "title": "Model gateway connection profile",
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": {
                "type": "metadata-only-openai-compatible-connection-profile",
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api",
                ],
                "notes": [
                    "Normalizes OpenAI-compatible gateway base URL shape before runtime client setup.",
                    "Treats remote bare hosts such as https://yibuapi.com as https://yibuapi.com/v1.",
                    "Never calls NewAPI, Gemini, OpenAI, Google, gateways, or the network.",
                    "Never returns API key values, hashes, Authorization headers, prompts, documents, or model outputs.",
                ],
            },
            "summary": {
                "base_url_configured": bool(raw_base_url),
                "api_key_configured": api_key_configured,
                "normalized_base_url": normalized_base_url or "{{APP_AI_BASE_URL}}",
                "base_url_was_normalized": normalized,
                "remote_bare_url_normalized_to_v1": normalized
                and normalized_base_url is not None
                and normalized_base_url.endswith("/v1"),
                "v1_compatible_path": _path_has_openai_compatible_hint(urlparse(normalized_base_url or "").path),
                "configured_role_count": len(role_rows),
                "cheap_first_role_count": len([row for row in role_rows if row["role"] in CHEAP_FIRST_ROLES]),
                "cheap_first_ready_count": sum(1 for row in role_rows if row["cheap_first_ready"]),
                "unknown_role_count": sum(1 for row in role_rows if not row["is_known_model"]),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
            },
            "connection": {
                "base_url_display": _display_url(raw_base_url) if raw_base_url else "{{APP_AI_BASE_URL}}",
                "normalized_base_url_display": normalized_base_url or "{{APP_AI_BASE_URL}}",
                "api_key_display": "{{APP_AI_KEY}}" if api_key_configured else "not_configured",
                "runtime_base_url_source": "normalized_openai_compatible_base_url",
                "timeout_seconds": getattr(settings, "app_ai_request_timeout", None),
                "runtime_client_uses_normalized_base_url": True,
            },
            "role_models": role_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_env": {
                "APP_AI_BASE_URL": normalized_base_url or "https://yibuapi.com/v1",
                "APP_AI_KEY": "{{APP_AI_KEY}}",
                "APP_AI_CHEAP_MODEL": cheap_text_model(),
                "APP_AI_FAST_MODEL": task_default_model("fast"),
                "APP_AI_CLASSIFIER_MODEL": task_default_model("classification"),
                "APP_OCR_MODEL": task_default_model("ocr"),
                "APP_AI_IMAGE_MODEL": image_model(),
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "credential_material_included": False,
                "authorization_headers_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "output_scope": "URL shape, placeholder names, boolean key presence, model ids, cost tiers, and readiness labels only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_api_key_validated": False,
                "account_access_claimed": False,
                "configuration_written": False,
                "default_model_changed": False,
                "traffic_shifted": False,
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, normalized),
            "validation_commands": [
                "python -m pytest tests/test_model_gateway_connection_profile.py tests/test_model_gateway_health_plan.py tests/test_aihub_runtime_routing.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _role_rows(self) -> list[dict[str, Any]]:
        roles = (
            ("cheap", cheap_text_model()),
            ("fast", task_default_model("fast")),
            ("ocr", task_default_model("ocr")),
            ("classification", task_default_model("classification")),
            ("review", task_default_model("review")),
            ("grounded-research", task_default_model("grounded-research")),
            ("agentic", task_default_model("agentic")),
            ("pdf", task_default_model("pdf")),
            ("image", image_model()),
        )
        rows = []
        for role, model_id in roles:
            profile = model_profile(model_id)
            cost_tier = profile.cost_tier if profile else None
            cheap_first_ready = self._cheap_first_ready(role, profile is not None, cost_tier, profile.status if profile else None)
            rows.append(
                {
                    "role": role,
                    "model": model_id,
                    "canonical_model": canonical_model_id(model_id),
                    "is_known_model": profile is not None,
                    "cost_tier": cost_tier,
                    "model_status": profile.status if profile else "unknown",
                    "cheap_first_role": role in CHEAP_FIRST_ROLES,
                    "cheap_first_ready": cheap_first_ready,
                    "default_allowed_without_review": cheap_first_ready,
                    "reason": self._role_reason(role, profile is not None, cost_tier, cheap_first_ready),
                }
            )
        return rows

    def _cheap_first_ready(self, role: str, known: bool, cost_tier: str | None, status: str | None) -> bool:
        if not known or status != "stable":
            return False
        if role in CHEAP_FIRST_ROLES:
            return COST_TIER_RANK.get(cost_tier or "unknown", 99) <= COST_TIER_RANK.get("low", 99)
        if role == "review":
            return COST_TIER_RANK.get(cost_tier or "unknown", 99) <= COST_TIER_RANK.get("medium", 99)
        return True

    def _role_reason(self, role: str, known: bool, cost_tier: str | None, cheap_first_ready: bool) -> str:
        if not known:
            return "Model is not in the local Gemini catalog; keep pass-through explicit-only until pricing review."
        if role in CHEAP_FIRST_ROLES and not cheap_first_ready:
            return "Cheap-first role must stay on a known stable lowest/low cost model."
        return f"Role is mapped to a known Gemini model with cost tier {cost_tier or 'unknown'}."

    def _checks(
        self,
        raw_base_url: str,
        normalized_base_url: str | None,
        parsed: Any,
        api_key_configured: bool,
        role_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        insecure_remote = bool(
            parsed
            and parsed.scheme == "http"
            and (parsed.hostname or "").lower() not in REMOTE_LOCAL_HOSTS
        )
        url_credentials = _url_has_credentials(raw_base_url)
        unknown_roles = [row["role"] for row in role_rows if not row["is_known_model"]]
        cheap_first_drift = [
            row["role"]
            for row in role_rows
            if row["cheap_first_role"] and row["is_known_model"] and not row["cheap_first_ready"]
        ]
        return [
            {
                "id": "base-url-configured",
                "status": "pass" if raw_base_url else "warn",
                "reason": "APP_AI_BASE_URL or provided channel URL is configured."
                if raw_base_url
                else "Set APP_AI_BASE_URL to an OpenAI-compatible gateway URL such as https://yibuapi.com/v1.",
            },
            {
                "id": "base-url-no-credentials",
                "status": "fail" if url_credentials else "pass",
                "reason": "Gateway URL does not include credential material."
                if not url_credentials
                else "Move credentials from the URL into APP_AI_KEY or deployment secrets; never include them in APP_AI_BASE_URL.",
            },
            {
                "id": "remote-https",
                "status": "fail" if insecure_remote else ("pass" if parsed and parsed.scheme == "https" else "warn"),
                "reason": "Remote gateway uses HTTPS."
                if parsed and parsed.scheme == "https"
                else ("Public HTTP gateway URLs are blocked." if insecure_remote else "Use HTTPS for remote gateways; localhost HTTP is only for local proxies."),
            },
            {
                "id": "openai-compatible-v1-base-url",
                "status": "pass" if _path_has_openai_compatible_hint(urlparse(normalized_base_url or "").path) else "warn",
                "reason": "Runtime client will use an OpenAI-compatible /v1 or /openai base path."
                if _path_has_openai_compatible_hint(urlparse(normalized_base_url or "").path)
                else "Use a /v1 or Gemini OpenAI-compatible /openai base path before live calls.",
            },
            {
                "id": "api-key-configured",
                "status": "pass" if api_key_configured else "warn",
                "reason": "API key material is present but redacted from this profile."
                if api_key_configured
                else "Set APP_AI_KEY in local .env or deployment secrets; do not commit it.",
            },
            {
                "id": "cheap-first-role-models",
                "status": "fail" if cheap_first_drift else ("warn" if unknown_roles else "pass"),
                "reason": "Cheap-first roles use known stable low-cost Gemini models."
                if not cheap_first_drift and not unknown_roles
                else (
                    f"Cheap-first roles drifted from low-cost models: {', '.join(cheap_first_drift)}."
                    if cheap_first_drift
                    else f"Review pricing for unknown role models: {', '.join(unknown_roles)}."
                ),
            },
            {
                "id": "runtime-normalization-boundary",
                "status": "pass" if not url_credentials else "fail",
                "reason": "Runtime normalization changes only URL path shape and never handles key values."
                if not url_credentials
                else "Runtime normalization rejected credential-bearing URL input.",
            },
        ]

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        normalized: bool,
    ) -> list[str]:
        if blocking:
            return [
                "Remove credentials from APP_AI_BASE_URL and keep the key only in APP_AI_KEY or deployment secrets.",
                "Use HTTPS for remote OpenAI-compatible gateways before enabling live calls.",
            ]
        actions = []
        if normalized:
            actions.append("Persist the normalized /v1 base URL in deployment secrets when promoting this gateway.")
        if warnings:
            actions.append("Complete APP_AI_BASE_URL and APP_AI_KEY setup, then run sanitized list-models and cheap JSON probes.")
        actions.append("Keep high-volume work on stable Flash-Lite/low-cost Gemini defaults before benchmark batches.")
        return actions


def _path_has_openai_compatible_hint(path: str) -> bool:
    normalized = (path or "").rstrip("/").lower()
    return any(normalized == hint or normalized.startswith(f"{hint}/") for hint in OPENAI_COMPATIBLE_PATH_HINTS)


def has_openai_compatible_base_path(path: str) -> bool:
    return _path_has_openai_compatible_hint(path)


def _display_url(value: str) -> str:
    if not value:
        return ""
    return normalize_openai_compatible_base_url(value) or value.strip()


def _url_has_credentials(value: str) -> bool:
    parsed = urlparse(value or "")
    if parsed.username or parsed.password:
        return True
    return bool(SENSITIVE_PATTERN.search(parsed.query or ""))


def _netloc_without_credentials(parsed: Any) -> str:
    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return host if parsed.port is None else f"{host}:{parsed.port}"


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _text(value: Any) -> str:
    return str(value or "").strip()
