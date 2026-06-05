from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from core.config import settings
from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    canonical_model_id,
    cheap_text_model,
    estimate_token_cost_usd,
    image_model,
    model_profile,
    task_default_model,
)


LOW_RESOURCE_TASKS = ("cheap", "fast", "ocr", "classification")
MEDIA_TASKS = ("image",)
CHEAP_FIRST_ROLES = LOW_RESOURCE_TASKS + MEDIA_TASKS
PROBE_PROMPT_TOKENS = 80
PROBE_COMPLETION_TOKENS = 80


class ModelGatewayHealthPlanService:
    """Build a safe NewAPI/Gemini gateway readiness plan without calling the gateway."""

    def build_plan(self) -> dict[str, Any]:
        base_url = _text(getattr(settings, "app_ai_base_url", None))
        api_key_configured = bool(_text(getattr(settings, "app_ai_key", None)))
        parsed = urlparse(base_url) if base_url else None
        normalized_base_url = self._normalized_base_url(base_url)
        role_rows = self._role_rows()
        checks = self._checks(base_url, parsed, api_key_configured, role_rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        cheap_model = cheap_text_model()
        return {
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": {
                "type": "openai-compatible-gateway-health-plan",
                "notes": [
                    "Builds a configuration and dry-run plan only; it never calls NewAPI, Gemini, or any gateway.",
                    "Checks only base URL shape, API key presence, cheap-first model metadata, and placeholder request contracts.",
                    "Uses Authorization placeholders and never returns API key values, hashes, prompts, documents, or model outputs.",
                ],
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api",
                ],
            },
            "summary": {
                "base_url_configured": bool(base_url),
                "api_key_configured": api_key_configured,
                "normalized_base_url": normalized_base_url or "{{APP_AI_BASE_URL}}",
                "configured_role_count": len(role_rows),
                "known_low_resource_role_count": sum(1 for row in role_rows if row["role"] in LOW_RESOURCE_TASKS and row["is_known_model"]),
                "known_media_role_count": sum(1 for row in role_rows if row["role"] in MEDIA_TASKS and row["is_known_model"]),
                "unknown_role_count": sum(1 for row in role_rows if not row["is_known_model"]),
                "cheap_first_low_cost_count": sum(1 for row in role_rows if row["role"] in CHEAP_FIRST_ROLES and row["cheap_first_aligned"]),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "estimated_probe_cost_usd": estimate_token_cost_usd(cheap_model, PROBE_PROMPT_TOKENS, PROBE_COMPLETION_TOKENS),
            },
            "gateway_config": {
                "base_url_configured": bool(base_url),
                "base_url_display": self._display_base_url(base_url) if base_url else "{{APP_AI_BASE_URL}}",
                "api_key_configured": api_key_configured,
                "api_key_display": "{{APP_AI_KEY}}" if api_key_configured else "not_configured",
                "timeout_seconds": getattr(settings, "app_ai_request_timeout", None),
                "requires_https": True,
            },
            "role_models": role_rows,
            "dry_run_contracts": self._dry_run_contracts(normalized_base_url, cheap_model, image_model()),
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "privacy_note": (
                "Gateway health planning reads configuration presence, base URL shape, model IDs, and pricing metadata only. "
                "It never emits API keys, key fingerprints, user prompts, uploaded documents, emails, or raw model output."
            ),
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
        for role, model in roles:
            canonical = canonical_model_id(model)
            profile = model_profile(model)
            cost_tier = profile.cost_tier if profile else None
            cheap_first_aligned = self._cheap_first_aligned(role, cost_tier)
            is_media_role = role in MEDIA_TASKS
            rows.append(
                {
                    "role": role,
                    "model": model,
                    "canonical_model": canonical,
                    "is_known_model": profile is not None,
                    "cost_tier": cost_tier,
                    "model_status": profile.status if profile else "unknown",
                    "billing_unit": "image" if is_media_role else "tokens",
                    "probe_type": "image-generation" if is_media_role else "chat-json",
                    "cheap_first_aligned": cheap_first_aligned,
                    "estimated_probe_cost_usd": (
                        profile.output_usd_per_image
                        if profile and is_media_role and profile.output_usd_per_image is not None
                        else estimate_token_cost_usd(model, PROBE_PROMPT_TOKENS, PROBE_COMPLETION_TOKENS)
                    ),
                    "output_usd_per_image": profile.output_usd_per_image if profile else None,
                    "reason": self._role_reason(role, profile is not None, cost_tier, cheap_first_aligned),
                }
            )
        return rows

    def _cheap_first_aligned(self, role: str, cost_tier: str | None) -> bool:
        if role in CHEAP_FIRST_ROLES:
            return COST_TIER_RANK.get(cost_tier or "unknown", 99) <= COST_TIER_RANK.get("low", 99)
        if role == "review":
            return COST_TIER_RANK.get(cost_tier or "unknown", 99) <= COST_TIER_RANK.get("medium", 99)
        return True

    def _role_reason(self, role: str, known: bool, cost_tier: str | None, cheap_first_aligned: bool) -> str:
        if not known:
            return "Gateway model is not in the local Gemini catalog; keep as pass-through until pricing is reviewed."
        if role in CHEAP_FIRST_ROLES and not cheap_first_aligned:
            return "High-volume role should use a known lowest/low cost model before gateway rollout."
        if role in MEDIA_TASKS:
            return f"Media role uses a known image model with cost tier {cost_tier or 'unknown'}."
        return f"Role uses a known model with cost tier {cost_tier or 'unknown'}."

    def _checks(
        self,
        base_url: str,
        parsed: Any,
        api_key_configured: bool,
        role_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        insecure_public = bool(parsed and parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"})
        missing_low_cost = [
            row["role"]
            for row in role_rows
            if row["role"] in CHEAP_FIRST_ROLES and not row["cheap_first_aligned"] and row["is_known_model"]
        ]
        unknown_roles = [row["role"] for row in role_rows if not row["is_known_model"]]
        image_rows = [row for row in role_rows if row["role"] == "image"]
        image_row = image_rows[0] if image_rows else None
        image_ready = bool(
            image_row
            and image_row["is_known_model"]
            and image_row["cheap_first_aligned"]
            and image_row.get("output_usd_per_image") is not None
            and image_row["model_status"] == "stable"
        )
        return [
            {
                "id": "base-url-configured",
                "status": "pass" if base_url else "warn",
                "reason": "APP_AI_BASE_URL is configured." if base_url else "Set APP_AI_BASE_URL before running gateway probes.",
            },
            {
                "id": "api-key-configured",
                "status": "pass" if api_key_configured else "warn",
                "reason": "APP_AI_KEY is present in local configuration." if api_key_configured else "Set APP_AI_KEY in local .env or deployment secrets; never commit it.",
            },
            {
                "id": "https-base-url",
                "status": "fail" if insecure_public else ("pass" if parsed and parsed.scheme == "https" else "warn"),
                "reason": "Gateway base URL uses HTTPS."
                if parsed and parsed.scheme == "https"
                else ("Public HTTP gateway URLs are not allowed." if insecure_public else "Use HTTPS for remote gateways; HTTP is only acceptable for localhost tests."),
            },
            {
                "id": "v1-path-shape",
                "status": "pass" if base_url and "/v1" in urlparse(base_url).path.rstrip("/") else "warn",
                "reason": "Base URL includes an OpenAI-compatible /v1 path."
                if base_url and "/v1" in urlparse(base_url).path.rstrip("/")
                else "Use an OpenAI-compatible /v1 base URL such as https://yibuapi.com/v1.",
            },
            {
                "id": "cheap-first-known-models",
                "status": "fail" if missing_low_cost else ("warn" if unknown_roles else "pass"),
                "reason": "High-volume and media roles use known low-cost Gemini models."
                if not missing_low_cost and not unknown_roles
                else (
                    f"High-volume or media roles drifted from low-cost models: {', '.join(missing_low_cost)}."
                    if missing_low_cost
                    else f"Review pricing for unknown gateway role models: {', '.join(unknown_roles)}."
                ),
            },
            {
                "id": "image-probe-priced-model",
                "status": "pass" if image_ready else "fail",
                "reason": "Image probe uses a stable low-cost model with per-image pricing metadata."
                if image_ready
                else "APP_AI_IMAGE_MODEL must be a known stable low-cost image model with per-image pricing before image probes.",
            },
            {
                "id": "dry-run-placeholders",
                "status": "pass",
                "reason": "Dry-run contracts use {{APP_AI_BASE_URL}} and {{APP_AI_KEY}} placeholders only.",
            },
        ]

    def _dry_run_contracts(self, normalized_base_url: str | None, cheap_model: str, image_model_id: str) -> list[dict[str, Any]]:
        base = normalized_base_url or "{{APP_AI_BASE_URL}}"
        chat_url = f"{base.rstrip('/')}/chat/completions"
        images_url = f"{base.rstrip('/')}/images/generations"
        models_url = f"{base.rstrip('/')}/models"
        return [
            {
                "id": "list-models",
                "method": "GET",
                "url": models_url,
                "headers": {"Authorization": "Bearer {{APP_AI_KEY}}"},
                "purpose": "Confirm the OpenAI-compatible gateway responds before any generation request.",
                "expected_success": "HTTP 200 with a model list or gateway-specific compatible model metadata.",
            },
            {
                "id": "cheap-chat-json",
                "method": "POST",
                "url": chat_url,
                "headers": {
                    "Authorization": "Bearer {{APP_AI_KEY}}",
                    "Content-Type": "application/json",
                },
                "body": {
                    "model": cheap_model,
                    "messages": [
                        {"role": "system", "content": "Return compact JSON only."},
                        {"role": "user", "content": "Return {\"ok\":true,\"task\":\"gateway_probe\"}."},
                    ],
                    "temperature": 0,
                    "max_tokens": PROBE_COMPLETION_TOKENS,
                    "response_format": {"type": "json_object"},
                },
                "purpose": "Probe the cheapest configured model with a tiny JSON response budget.",
                "expected_success": "HTTP 200 with JSON content; no client document or user prompt is included.",
            },
            {
                "id": "image-generation-smoke",
                "method": "POST",
                "url": images_url,
                "headers": {
                    "Authorization": "Bearer {{APP_AI_KEY}}",
                    "Content-Type": "application/json",
                },
                "body": {
                    "model": image_model_id,
                    "prompt": "Generate one neutral legal-document placeholder icon on a plain background.",
                    "size": "1024x1024",
                    "n": 1,
                },
                "purpose": "Optionally verify the configured image model after text probes pass, using a non-client placeholder prompt.",
                "expected_success": "HTTP 200 with one generated image reference when the gateway supports OpenAI-compatible image generation.",
            },
        ]

    def _normalized_base_url(self, base_url: str) -> str | None:
        value = base_url.strip().rstrip("/")
        if not value:
            return None
        return value

    def _display_base_url(self, base_url: str) -> str:
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            return base_url.strip()
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

    def _recommended_actions(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        if blocking:
            return [
                "Fix blocking gateway URL or high-volume model configuration before running probes.",
                "Keep real API keys in app/backend/.env or deployment secrets only.",
            ]
        if warnings:
            return [
                "Complete APP_AI_BASE_URL and APP_AI_KEY setup before live gateway tests.",
                "Run list-models first, then the cheap JSON probe, then fixture quick-suite batches.",
            ]
        return [
            "Gateway configuration is ready for a maintainer-run cheap JSON probe.",
            "Keep high-volume tasks on cheap Gemini models before any batch legal fixture run.",
        ]


def _text(value: Any) -> str:
    return str(value or "").strip()
