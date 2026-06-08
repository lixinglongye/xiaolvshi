from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from services.model_catalog import canonical_model_id, model_profile, task_default_model
from services.model_gateway_connection_profile import ModelGatewayConnectionProfileService
from services.model_gateway_runtime_configuration import ModelGatewayRuntimeConfigurationService
from services.model_ops_observed_gemini_coverage_gap_queue import ModelOpsObservedGeminiCoverageGapQueueService
from services.model_ops_observed_gemini_model_intake_queue import ModelOpsObservedGeminiModelIntakeQueueService
from services.model_ops_observed_gemini_premium_exception_review import (
    ModelOpsObservedGeminiPremiumExceptionReviewService,
)


SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{8,}|api[_-]?key|authorization|bearer|token|secret|password|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)",
    re.IGNORECASE,
)
BOOTSTRAP_ROLE_TASKS: tuple[tuple[str, str, str], ...] = (
    ("cheap", "APP_AI_CHEAP_MODEL", "cheap"),
    ("fast", "APP_AI_FAST_MODEL", "fast"),
    ("classification", "APP_AI_CLASSIFIER_MODEL", "classification"),
    ("ocr", "APP_OCR_MODEL", "ocr"),
    ("review", "APP_AI_REVIEW_MODEL", "review"),
    ("pdf", "APP_AI_PDF_MODEL", "pdf"),
    ("agentic", "APP_AI_AGENTIC_MODEL", "agentic"),
    ("grounded-research", "APP_AI_GROUNDED_RESEARCH_MODEL", "grounded-research"),
)
HIGH_FREQUENCY_ROLES = {"cheap", "fast", "classification", "ocr"}


class ModelOpsNewapiChannelBootstrapService:
    """Build a safe NewAPI-compatible Gemini channel bootstrap packet."""

    def __init__(
        self,
        connection_profile_service: ModelGatewayConnectionProfileService | None = None,
        runtime_configuration_service: ModelGatewayRuntimeConfigurationService | None = None,
        intake_queue_service: ModelOpsObservedGeminiModelIntakeQueueService | None = None,
        coverage_gap_queue_service: ModelOpsObservedGeminiCoverageGapQueueService | None = None,
        premium_exception_review_service: ModelOpsObservedGeminiPremiumExceptionReviewService | None = None,
    ) -> None:
        self.connection_profile_service = connection_profile_service or ModelGatewayConnectionProfileService()
        self.runtime_configuration_service = runtime_configuration_service or ModelGatewayRuntimeConfigurationService()
        self.intake_queue_service = intake_queue_service or ModelOpsObservedGeminiModelIntakeQueueService()
        self.coverage_gap_queue_service = coverage_gap_queue_service or ModelOpsObservedGeminiCoverageGapQueueService()
        self.premium_exception_review_service = (
            premium_exception_review_service or ModelOpsObservedGeminiPremiumExceptionReviewService()
        )

    def build_packet(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        sanitized = self._sanitized_payload(data)
        connection_profile = self.connection_profile_service.build_profile(sanitized)
        runtime_configuration = self.runtime_configuration_service.build_configuration(sanitized)
        observed_payload = {"observed_models": self._observed_models(data)}
        intake_queue = self.intake_queue_service.build_queue(observed_payload)
        coverage_gap_queue = self.coverage_gap_queue_service.build_queue(observed_payload)
        premium_exception_review = self.premium_exception_review_service.build_review(observed_payload)
        role_rows = self._role_rows()
        setup_steps = self._setup_steps(connection_profile, runtime_configuration, premium_exception_review)
        checks = self._checks(
            sanitized=sanitized,
            connection_profile=connection_profile,
            runtime_configuration=runtime_configuration,
            premium_exception_review=premium_exception_review,
            role_rows=role_rows,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        key_configured = bool(_text(data.get("key")) or _text(data.get("api_key")) or _text(data.get("token")))

        return {
            "id": "modelops-newapi-channel-bootstrap",
            "title": "ModelOps NewAPI channel cheap-first bootstrap",
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": {
                "type": "metadata-only-newapi-channel-cheap-first-bootstrap",
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://ai.google.dev/gemini-api/docs/models",
                    "https://ai.google.dev/gemini-api/docs/pricing",
                ],
                "notes": [
                    "Normalizes a NewAPI or other OpenAI-compatible channel URL before runtime configuration.",
                    "Converts key presence into an APP_AI_KEY placeholder only; it never returns or stores the key.",
                    "Pins high-frequency legal workflow routes to cheap-first Gemini defaults before any premium exception.",
                    "Uses observed model ids only as sanitized metadata for intake, coverage-gap, and premium-review evidence.",
                ],
            },
            "summary": {
                "channel_url_configured": bool(sanitized.get("url")),
                "channel_key_present": key_configured,
                "normalized_base_url": connection_profile["connection"]["normalized_base_url_display"],
                "remote_bare_url_normalized_to_v1": bool(
                    connection_profile["summary"].get("remote_bare_url_normalized_to_v1")
                ),
                "openai_compatible_path": bool(runtime_configuration["summary"].get("openai_compatible_path")),
                "recommended_env_count": len(self._recommended_env(connection_profile)),
                "cheap_first_role_count": sum(1 for row in role_rows if row["cheap_first_role"]),
                "cheap_first_ready_count": sum(1 for row in role_rows if row["cheap_first_ready"]),
                "premium_exception_review_count": _int(
                    _dict(premium_exception_review.get("summary")).get("premium_exception_review_count")
                ),
                "observed_model_count": _int(_dict(intake_queue.get("summary")).get("observed_model_count")),
                "coverage_gap_count": _int(_dict(coverage_gap_queue.get("summary")).get("gap_item_count")),
                "setup_step_count": len(setup_steps),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
                "traffic_shifted": False,
            },
            "channel": {
                "type": _text(data.get("_type")) or "newapi_channel_conn",
                "url_display": self._display_url(_text(sanitized.get("url"))),
                "normalized_base_url_display": connection_profile["connection"]["normalized_base_url_display"],
                "api_key_env": "APP_AI_KEY",
                "api_key_display": "{{APP_AI_KEY}}" if key_configured else "not_configured",
                "base_url_env": "APP_AI_BASE_URL",
                "base_url_source": "normalize_openai_compatible_base_url(channel.url)",
                "provider_family": self._provider_family(_text(sanitized.get("url"))),
            },
            "recommended_env": self._recommended_env(connection_profile),
            "role_rows": role_rows,
            "setup_steps": setup_steps,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "source_summaries": {
                "gateway_connection_profile": connection_profile.get("summary", {}),
                "gateway_runtime_configuration": runtime_configuration.get("summary", {}),
                "observed_gemini_model_intake_queue": intake_queue.get("summary", {}),
                "observed_gemini_coverage_gap_queue": coverage_gap_queue.get("summary", {}),
                "observed_gemini_premium_exception_review": premium_exception_review.get("summary", {}),
            },
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "credential_material_included": False,
                "authorization_headers_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "prompts_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_key_validated": False,
                "model_inventory_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "pricing_accuracy_claimed": False,
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, key_configured),
            "validation_commands": [
                "python -m pytest tests/test_model_ops_newapi_channel_bootstrap.py -q",
                "python -m pytest tests/test_model_gateway_connection_profile.py tests/test_model_gateway_runtime_configuration.py tests/test_model_ops_observed_gemini_premium_exception_review.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _sanitized_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        url = _first_text(data.get("url"), data.get("base_url"), data.get("endpoint"))
        return {
            "_type": _text(data.get("_type")) or "newapi_channel_conn",
            "url": url,
            "base_url": url,
            "key": "{{APP_AI_KEY}}" if _text(data.get("key")) else "",
            "api_key": "{{APP_AI_KEY}}" if _text(data.get("api_key")) else "",
            "token": "{{APP_AI_KEY}}" if _text(data.get("token")) else "",
        }

    def _observed_models(self, data: dict[str, Any]) -> list[Any]:
        observed = data.get("observed_models")
        if isinstance(observed, list):
            return observed
        models_response = data.get("models_response")
        if isinstance(models_response, dict):
            rows = models_response.get("data")
            if isinstance(rows, list):
                return [row.get("id") for row in rows if isinstance(row, dict)]
        return [
            task_default_model("cheap"),
            task_default_model("fast"),
            task_default_model("review"),
            task_default_model("agentic"),
            task_default_model("grounded-research"),
            task_default_model("pdf"),
        ]

    def _role_rows(self) -> list[dict[str, Any]]:
        rows = []
        for role, env_name, task in BOOTSTRAP_ROLE_TASKS:
            model_id = task_default_model(task)
            canonical = canonical_model_id(model_id)
            profile = model_profile(model_id)
            cheap_first_role = role in HIGH_FREQUENCY_ROLES
            cheap_first_ready = bool(
                profile and profile.status == "stable" and (not cheap_first_role or profile.cost_tier in {"lowest", "low"})
            )
            rows.append(
                {
                    "role": role,
                    "task": task,
                    "env_name": env_name,
                    "recommended_model": model_id,
                    "canonical_model": canonical,
                    "known_catalog_model": profile is not None,
                    "cost_tier": profile.cost_tier if profile else "unknown",
                    "model_status": profile.status if profile else "unknown",
                    "cheap_first_role": cheap_first_role,
                    "cheap_first_ready": cheap_first_ready,
                    "default_allowed_without_review": cheap_first_ready,
                    "reason": (
                        f"{role} stays on stable cheap-first model {model_id}."
                        if cheap_first_ready
                        else f"{role} requires review before using {model_id} as a default."
                    ),
                }
            )
        return rows

    def _recommended_env(self, connection_profile: dict[str, Any]) -> dict[str, str]:
        return {
            "APP_AI_BASE_URL": str(_dict(connection_profile.get("connection")).get("normalized_base_url_display") or "https://yibuapi.com/v1"),
            "APP_AI_KEY": "{{APP_AI_KEY}}",
            "APP_AI_CHEAP_MODEL": task_default_model("cheap"),
            "APP_AI_FAST_MODEL": task_default_model("fast"),
            "APP_AI_CLASSIFIER_MODEL": task_default_model("classification"),
            "APP_OCR_MODEL": task_default_model("ocr"),
            "APP_AI_REVIEW_MODEL": task_default_model("review"),
            "APP_AI_PDF_MODEL": task_default_model("pdf"),
            "APP_AI_AGENTIC_MODEL": task_default_model("agentic"),
            "APP_AI_GROUNDED_RESEARCH_MODEL": task_default_model("grounded-research"),
        }

    def _setup_steps(
        self,
        connection_profile: dict[str, Any],
        runtime_configuration: dict[str, Any],
        premium_exception_review: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "normalize-channel-url",
                "title": "Normalize channel URL",
                "action": "Set APP_AI_BASE_URL to the normalized OpenAI-compatible /v1 URL.",
                "status": "ready" if connection_profile["summary"].get("v1_compatible_path") else "review_required",
                "evidence_links": ["model-gateway-connection-profile"],
            },
            {
                "id": "store-key-outside-git",
                "title": "Store key outside git",
                "action": "Store the channel key as APP_AI_KEY in local .env or deployment secrets only.",
                "status": "ready" if connection_profile["summary"].get("api_key_configured") else "review_required",
                "evidence_links": ["model-gateway-connection-profile", "model-gateway-runtime-configuration"],
            },
            {
                "id": "pin-cheap-first-defaults",
                "title": "Pin cheap-first defaults",
                "action": "Keep high-frequency legal workflow roles on Flash-Lite or known low-cost Gemini defaults.",
                "status": "ready" if runtime_configuration["summary"].get("cheap_first_ready_count", 0) >= 4 else "review_required",
                "evidence_links": ["model-gateway-runtime-configuration", "gemini-cheap-first-route-preflight"],
            },
            {
                "id": "review-premium-exceptions",
                "title": "Review premium exceptions",
                "action": "Keep Pro, preview, and premium variants explicit-only until maintainer/cost-owner approval.",
                "status": "review_required"
                if _int(_dict(premium_exception_review.get("summary")).get("premium_exception_review_count"))
                else "ready",
                "evidence_links": ["modelops-observed-gemini-premium-exception-review"],
            },
        ]

    def _checks(
        self,
        *,
        sanitized: dict[str, Any],
        connection_profile: dict[str, Any],
        runtime_configuration: dict[str, Any],
        premium_exception_review: dict[str, Any],
        role_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        parsed_url = urlparse(_text(sanitized.get("url")))
        url_secret_material = bool(
            parsed_url.username
            or parsed_url.password
            or parsed_url.query
            and SENSITIVE_PATTERN.search(parsed_url.query)
        )
        high_frequency_drift = [row["role"] for row in role_rows if row["cheap_first_role"] and not row["cheap_first_ready"]]
        return [
            {
                "id": "channel-url-openai-compatible",
                "status": "pass" if runtime_configuration["summary"].get("openai_compatible_path") else "warn",
                "reason": "Channel URL is normalized to an OpenAI-compatible base path.",
                "evidence": [str(connection_profile["connection"].get("normalized_base_url_display"))],
            },
            {
                "id": "channel-secret-redacted",
                "status": "fail" if url_secret_material else "pass",
                "reason": "Channel secret material is represented only by APP_AI_KEY placeholders.",
                "evidence": ["APP_AI_KEY"],
            },
            {
                "id": "cheap-first-defaults-ready",
                "status": "fail" if high_frequency_drift else "pass",
                "reason": "High-frequency roles use cheap-first stable Gemini defaults.",
                "evidence": high_frequency_drift or [row["env_name"] for row in role_rows if row["cheap_first_role"]],
            },
            {
                "id": "premium-explicit-only",
                "status": "warn"
                if _int(_dict(premium_exception_review.get("summary")).get("premium_exception_review_count"))
                else "pass",
                "reason": "Premium or Pro observed variants stay explicit-only behind maintainer review.",
                "evidence": _list(premium_exception_review.get("premium_exception_review_model_ids")),
            },
            {
                "id": "no-live-bootstrap-side-effects",
                "status": "pass",
                "reason": "Bootstrap packet does not write configuration, call gateways, call the network, or shift traffic.",
                "evidence": ["configuration_written:false", "gateway_called:false", "network_called:false"],
            },
        ]

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        key_configured: bool,
    ) -> list[str]:
        if blocking:
            return [
                "Remove secret material from channel URLs or payload metadata before any review.",
                "Restore cheap-first Gemini defaults before using this channel for routine legal workflows.",
            ]
        actions = [
            "Set APP_AI_BASE_URL to the normalized channel URL and APP_AI_KEY through local or deployment secrets.",
            "Run list-models, then a tiny cheap JSON probe, before any legal fixture smoke run.",
            "Keep Pro, preview, and premium variants explicit-only until maintainer and cost-owner approval.",
        ]
        if warnings and not key_configured:
            actions.insert(0, "Add APP_AI_KEY locally before claiming live NewAPI channel readiness.")
        return actions

    def _display_url(self, value: str) -> str:
        parsed = urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            return value or "{{APP_AI_BASE_URL}}"
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return parsed._replace(netloc=netloc, params="", query="", fragment="").geturl().rstrip("/")

    def _provider_family(self, url: str) -> str:
        host = (urlparse(url).hostname or "").lower()
        if "yibuapi" in host:
            return "newapi-yibuapi"
        if "googleapis" in host or "generativelanguage" in host:
            return "google-gemini-openai-compatible"
        return "openai-compatible-gateway" if host else "not_configured"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _text(value: Any) -> str:
    return str(value or "").strip()
