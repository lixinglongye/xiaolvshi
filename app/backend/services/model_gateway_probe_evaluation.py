from __future__ import annotations

import re
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    canonical_model_id,
    model_profile,
    task_default_model,
)


LOW_RESOURCE_ROLES = ("cheap", "fast", "ocr", "classification")
PASS_STATES = {"pass", "passed", "ok", "success", "ready", "true"}
FAIL_STATES = {"fail", "failed", "error", "blocked", "false"}
FORBIDDEN_PAYLOAD_KEYS = {
    "authorization",
    "api_key",
    "app_ai_key",
    "headers",
    "messages",
    "prompt",
    "raw_output",
    "raw_response",
    "response_text",
    "output",
    "outputs",
    "image_url",
    "image_urls",
    "b64_json",
    "base64",
}
FORBIDDEN_VALUE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("api_key_like", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("bearer_token", re.compile(r"\bbearer\s+[A-Za-z0-9._-]{10,}", re.IGNORECASE)),
    ("email_like", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("url_like", re.compile(r"https?://", re.IGNORECASE)),
    ("data_uri_like", re.compile(r"\bdata:image/|base64,", re.IGNORECASE)),
)


class ModelGatewayProbeEvaluationService:
    """Evaluate maintainer-supplied gateway probe outputs without storing secrets."""

    def template(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "method": {
                "type": "gateway-probe-evaluation-template",
                "notes": [
                    "Paste sanitized /v1/models output, tiny chat probe results, and optional image-generation smoke metadata here.",
                    "Do not include Authorization headers, API keys, prompts, client documents, image URLs, base64 data, or raw model outputs.",
                    "Use the output to choose cheap-first defaults before changing .env.",
                ],
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://docs.newapi.pro/zh/docs/api/ai-model/chat/openai/create-chat-completion",
                    "https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api",
                ],
            },
            "payload_shape": {
                "models_response": {
                    "data": [
                        {"id": "gemini-2.5-flash-lite"},
                        {"id": "models/gemini-2.5-flash"},
                    ]
                },
                "chat_probe_results": {
                    "gemini-2.5-flash-lite": {
                        "status": "pass",
                        "http_status": 200,
                        "json_ok": True,
                        "latency_ms": 1200,
                    }
                },
                "image_probe_results": {
                    "gemini-2.5-flash-image": {
                        "status": "pass",
                        "http_status": 200,
                        "image_count": 1,
                        "latency_ms": 2400,
                    }
                },
            },
            "validation_command": "python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_health_plan.py tests/test_model_catalog.py -q",
        }

    def evaluate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        forbidden_payload_paths = self._forbidden_payload_paths(payload)
        chat_probe_results = self._extract_probe_results(payload.get("chat_probe_results"))
        image_probe_results = self._extract_probe_results(payload.get("image_probe_results"))
        model_ids = self._dedupe_model_ids(
            [
                *self._extract_model_ids(payload),
                *chat_probe_results.keys(),
                *image_probe_results.keys(),
            ]
        )
        rows = [
            self._model_row(
                model_id,
                self._probe_for_model(chat_probe_results, model_id),
                self._probe_for_model(image_probe_results, model_id),
            )
            for model_id in model_ids
        ]
        if not rows:
            return self._not_run(forbidden_payload_paths)

        cheap_candidates = [row for row in rows if self._is_cheap_default_candidate(row)]
        probed_cheap_candidates = [row for row in cheap_candidates if row["chat_probe_status"] == "pass"]
        image_candidates = [row for row in rows if self._is_image_default_candidate(row)]
        probed_image_candidates = [row for row in image_candidates if row["image_probe_status"] == "pass"]
        usable_image_candidates = [row for row in image_candidates if row["image_probe_status"] != "fail"]
        recommended_env = self._recommended_env(
            rows,
            probed_cheap_candidates or cheap_candidates,
            probed_image_candidates or usable_image_candidates,
        )
        checks = self._checks(
            rows,
            cheap_candidates,
            probed_cheap_candidates,
            image_candidates,
            probed_image_candidates,
            recommended_env,
            forbidden_payload_paths,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": self.template()["method"],
            "summary": {
                "observed_model_count": len(rows),
                "known_model_count": sum(1 for row in rows if row["is_known_model"]),
                "unknown_gemini_count": sum(1 for row in rows if row["is_gemini_like"] and not row["is_known_model"]),
                "chat_probe_count": sum(1 for row in rows if row["chat_probe_status"] != "not_supplied"),
                "chat_probe_pass_count": sum(1 for row in rows if row["chat_probe_status"] == "pass"),
                "image_probe_count": sum(1 for row in rows if row["image_probe_status"] != "not_supplied"),
                "image_probe_pass_count": sum(1 for row in rows if row["image_probe_status"] == "pass"),
                "cheap_candidate_count": len(cheap_candidates),
                "probed_cheap_candidate_count": len(probed_cheap_candidates),
                "image_candidate_count": len(image_candidates),
                "probed_image_candidate_count": len(probed_image_candidates),
                "recommended_change_count": sum(1 for row in recommended_env if row["requires_change"]),
                "forbidden_payload_field_count": len(forbidden_payload_paths),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
            },
            "model_rows": rows,
            "recommended_env": recommended_env,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings, recommended_env),
            "privacy_note": (
                "Probe evaluation accepts sanitized model IDs, HTTP status, latency, boolean JSON checks, and image counts only. "
                "Do not submit API keys, bearer tokens, Authorization headers, prompts, image URLs, base64 data, user documents, emails, or raw model outputs."
            ),
        }

    def _not_run(self, forbidden_payload_paths: list[str] | None = None) -> dict[str, Any]:
        forbidden_payload_paths = forbidden_payload_paths or []
        checks = [{"id": "probe-data-present", "status": "warn", "reason": "Submit sanitized model list or chat/image probe results."}]
        if forbidden_payload_paths:
            checks.insert(0, self._forbidden_payload_check(forbidden_payload_paths))
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else "not_run",
            "method": self.template()["method"],
            "summary": {
                "observed_model_count": 0,
                "known_model_count": 0,
                "unknown_gemini_count": 0,
                "chat_probe_count": 0,
                "chat_probe_pass_count": 0,
                "image_probe_count": 0,
                "image_probe_pass_count": 0,
                "cheap_candidate_count": 0,
                "probed_cheap_candidate_count": 0,
                "image_candidate_count": 0,
                "probed_image_candidate_count": 0,
                "recommended_change_count": 0,
                "forbidden_payload_field_count": len(forbidden_payload_paths),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
            },
            "model_rows": [],
            "recommended_env": [],
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": ["Run the gateway health plan dry-run contracts, then submit sanitized results here."],
            "privacy_note": "No probe payload was evaluated.",
        }

    def _extract_model_ids(self, payload: dict[str, Any]) -> list[str]:
        candidates = payload.get("model_ids")
        if isinstance(candidates, list):
            return self._dedupe_model_ids(candidates)
        response = payload.get("models_response")
        if isinstance(response, list):
            return self._dedupe_model_ids(response)
        if not isinstance(response, dict):
            return []
        for key in ("data", "models", "items"):
            value = response.get(key)
            if isinstance(value, list):
                return self._dedupe_model_ids(value)
        return []

    def _dedupe_model_ids(self, rows: list[Any]) -> list[str]:
        seen = set()
        model_ids = []
        for row in rows:
            model_id = ""
            if isinstance(row, dict):
                model_id = _text(row.get("id") or row.get("model") or row.get("name"))
            else:
                model_id = _text(row)
            if not model_id or model_id in seen:
                continue
            seen.add(model_id)
            model_ids.append(model_id)
        return model_ids

    def _extract_probe_results(self, value: Any) -> dict[str, dict[str, Any]]:
        if isinstance(value, dict):
            return {str(model_id): probe for model_id, probe in value.items() if isinstance(probe, dict)}
        if isinstance(value, list):
            rows = {}
            for item in value:
                if not isinstance(item, dict):
                    continue
                model_id = _text(item.get("model") or item.get("model_id") or item.get("id"))
                if model_id:
                    rows[model_id] = item
            return rows
        return {}

    def _probe_for_model(self, probes: dict[str, dict[str, Any]], model_id: str) -> dict[str, Any] | None:
        if model_id in probes:
            return probes[model_id]
        canonical = canonical_model_id(model_id)
        if canonical and canonical in probes:
            return probes[canonical]
        if canonical:
            for probe_model_id, probe in probes.items():
                if canonical_model_id(probe_model_id) == canonical:
                    return probe
        return None

    def _model_row(self, model_id: str, chat_probe: dict[str, Any] | None, image_probe: dict[str, Any] | None) -> dict[str, Any]:
        canonical = canonical_model_id(model_id)
        profile = model_profile(model_id)
        chat_probe_status = self._probe_status(chat_probe)
        image_probe_status = self._image_probe_status(image_probe)
        return {
            "model": model_id,
            "canonical_model": canonical,
            "is_known_model": profile is not None,
            "is_gemini_like": "gemini" in model_id.lower(),
            "provider": profile.provider if profile else "unknown",
            "cost_tier": profile.cost_tier if profile else None,
            "model_status": profile.status if profile else "unknown",
            "capabilities": list(profile.capabilities) if profile else [],
            "chat_probe_status": chat_probe_status,
            "image_probe_status": image_probe_status,
            "http_status": _safe_int((chat_probe or {}).get("http_status"), None),
            "json_ok": bool((chat_probe or {}).get("json_ok")) if chat_probe else None,
            "latency_ms": _safe_int((chat_probe or {}).get("latency_ms"), None),
            "image_http_status": _safe_int((image_probe or {}).get("http_status"), None),
            "image_count": _safe_int((image_probe or {}).get("image_count"), None),
            "image_latency_ms": _safe_int((image_probe or {}).get("latency_ms"), None),
            "output_usd_per_image": profile.output_usd_per_image if profile else None,
            "recommended_for_defaults": False,
            "reason": self._model_reason(model_id, profile, chat_probe_status, image_probe_status),
        }

    def _probe_status(self, probe: dict[str, Any] | None) -> str:
        if not probe:
            return "not_supplied"
        raw = _text(probe.get("status") or probe.get("result")).lower()
        http_status = _safe_int(probe.get("http_status"), None)
        json_ok = probe.get("json_ok")
        if raw in PASS_STATES or (http_status is not None and 200 <= http_status < 300 and json_ok is not False):
            return "pass"
        if raw in FAIL_STATES or (http_status is not None and http_status >= 400) or json_ok is False:
            return "fail"
        return "warn"

    def _image_probe_status(self, probe: dict[str, Any] | None) -> str:
        if not probe:
            return "not_supplied"
        raw = _text(probe.get("status") or probe.get("result")).lower()
        http_status = _safe_int(probe.get("http_status"), None)
        image_count = _safe_int(probe.get("image_count"), None)
        if raw in PASS_STATES or (http_status is not None and 200 <= http_status < 300 and (image_count or 0) > 0):
            return "pass"
        if raw in FAIL_STATES or (http_status is not None and http_status >= 400) or image_count == 0:
            return "fail"
        return "warn"

    def _model_reason(self, model_id: str, profile: Any, chat_probe_status: str, image_probe_status: str) -> str:
        if not profile:
            return "Gateway exposed a Gemini-like pass-through model not yet priced in the local catalog." if "gemini" in model_id.lower() else "Gateway model is not recognized as a local Gemini catalog model."
        if profile.status != "stable":
            return "Model is known but not stable; keep it as an explicit experiment until lifecycle review."
        if "image" in profile.capabilities:
            if image_probe_status == "fail":
                return "Image model is cataloged but failed the supplied image-generation smoke probe."
            if image_probe_status == "pass":
                return "Image model is cataloged, priced per image, and passed the supplied image-generation smoke probe."
            return "Image model is cataloged; run the image-generation smoke probe before using it for unattended image tasks."
        if chat_probe_status == "fail":
            return "Model is cataloged but failed the supplied chat probe."
        if chat_probe_status == "not_supplied":
            return "Model is cataloged; run a tiny chat probe before using it as a default."
        return "Model is cataloged and has a successful supplied chat probe."

    def _is_cheap_default_candidate(self, row: dict[str, Any]) -> bool:
        return (
            row["is_known_model"]
            and row["model_status"] == "stable"
            and COST_TIER_RANK.get(row["cost_tier"] or "unknown", 99) <= COST_TIER_RANK.get("low", 99)
            and "text" in row["capabilities"]
            and row["chat_probe_status"] != "fail"
        )

    def _is_image_default_candidate(self, row: dict[str, Any]) -> bool:
        return (
            row["is_known_model"]
            and row["model_status"] == "stable"
            and COST_TIER_RANK.get(row["cost_tier"] or "unknown", 99) <= COST_TIER_RANK.get("low", 99)
            and "image" in row["capabilities"]
            and row["output_usd_per_image"] is not None
        )

    def _recommended_env(
        self,
        rows: list[dict[str, Any]],
        cheap_candidates: list[dict[str, Any]],
        image_candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        cheapest = self._cheapest(cheap_candidates)
        review = self._best_review(rows) or cheapest
        pdf = self._best_pdf(rows)
        image = self._cheapest_image(image_candidates)
        targets = [
            ("APP_AI_CHEAP_MODEL", "cheap", cheapest),
            ("APP_AI_FAST_MODEL", "fast", cheapest),
            ("APP_OCR_MODEL", "ocr", cheapest),
            ("APP_AI_CLASSIFIER_MODEL", "classification", cheapest),
            ("APP_AI_REVIEW_MODEL", "review", review),
            ("APP_AI_PDF_MODEL", "pdf", pdf),
            ("APP_AI_IMAGE_MODEL", "image", image),
        ]
        result = []
        for env_var, task, row in targets:
            current = task_default_model(task)
            recommended = row["model"] if row else current
            result.append(
                {
                    "env_var": env_var,
                    "task": task,
                    "current_value": current,
                    "recommended_value": recommended,
                    "requires_change": current != recommended,
                    "reason": self._env_reason(task, row),
                }
            )
        return result

    def _cheapest(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        return sorted(rows, key=lambda row: (COST_TIER_RANK.get(row["cost_tier"] or "unknown", 99), row["latency_ms"] or 999999, row["model"]))[0]

    def _cheapest_image(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        return sorted(
            rows,
            key=lambda row: (
                row["image_probe_status"] != "pass",
                row["output_usd_per_image"] or 999999,
                COST_TIER_RANK.get(row["cost_tier"] or "unknown", 99),
                row["image_latency_ms"] or 999999,
                row["model"],
            ),
        )[0]

    def _best_review(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = [
            row
            for row in rows
            if row["is_known_model"]
            and row["model_status"] == "stable"
            and "review" in row["capabilities"]
            and row["chat_probe_status"] != "fail"
            and COST_TIER_RANK.get(row["cost_tier"] or "unknown", 99) <= COST_TIER_RANK.get("medium", 99)
        ]
        return self._cheapest(candidates)

    def _best_pdf(self, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        candidates = [
            row
            for row in rows
            if row["is_known_model"]
            and row["model_status"] == "stable"
            and "long-context" in row["capabilities"]
            and row["chat_probe_status"] != "fail"
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda row: (row["chat_probe_status"] != "pass", COST_TIER_RANK.get(row["cost_tier"] or "unknown", 99), row["model"]))[0]

    def _env_reason(self, task: str, row: dict[str, Any] | None) -> str:
        if not row:
            return "No suitable probed/cataloged model was found; keep the current value and review manually."
        if task == "image":
            if row["image_probe_status"] == "pass":
                return "Recommended from successful image-generation smoke probe."
            return "Recommended from catalog and pricing metadata; run image probe before unattended media use."
        if row["chat_probe_status"] == "pass":
            return f"Recommended from successful gateway probe for {task}."
        return f"Recommended from model list only; run chat probe before promoting for {task}."

    def _checks(
        self,
        rows: list[dict[str, Any]],
        cheap_candidates: list[dict[str, Any]],
        probed_cheap_candidates: list[dict[str, Any]],
        image_candidates: list[dict[str, Any]],
        probed_image_candidates: list[dict[str, Any]],
        recommended_env: list[dict[str, Any]],
        forbidden_payload_paths: list[str],
    ) -> list[dict[str, Any]]:
        failed_probes = [row["model"] for row in rows if row["chat_probe_status"] == "fail"]
        failed_image_probes = [row["model"] for row in rows if row["image_probe_status"] == "fail"]
        unknown_gemini = [row["model"] for row in rows if row["is_gemini_like"] and not row["is_known_model"]]
        image_evidence_present = bool(image_candidates or probed_image_candidates or any(row["image_probe_status"] != "not_supplied" for row in rows))
        checks = [
            self._forbidden_payload_check(forbidden_payload_paths),
            {
                "id": "gateway-model-list-present",
                "status": "pass" if rows else "warn",
                "reason": f"Observed {len(rows)} gateway model rows." if rows else "Submit /v1/models output before changing defaults.",
            },
            {
                "id": "cheap-first-candidate-present",
                "status": "pass" if cheap_candidates else "fail",
                "reason": "At least one known stable low-cost text model is available."
                if cheap_candidates
                else "No known stable low-cost Gemini text model was found in supplied gateway results.",
            },
            {
                "id": "cheap-chat-probe-passed",
                "status": "pass" if probed_cheap_candidates else "warn",
                "reason": "At least one cheap-first candidate passed a chat probe."
                if probed_cheap_candidates
                else "Run a tiny chat probe for the cheap-first candidate before promoting defaults.",
            },
            {
                "id": "image-default-candidate-present",
                "status": "pass" if not image_evidence_present or image_candidates else "fail",
                "reason": "Image probe evaluation is skipped because no sanitized image model/probe metadata was supplied."
                if not image_evidence_present
                else (
                    "At least one known stable low-cost priced image model is available."
                    if image_candidates
                    else "No known stable low-cost priced Gemini image model was found in supplied gateway results."
                ),
            },
            {
                "id": "image-generation-probe-passed",
                "status": "pass" if not image_evidence_present or probed_image_candidates else "warn",
                "reason": "Image probe evaluation is skipped because no sanitized image model/probe metadata was supplied."
                if not image_evidence_present
                else (
                    "At least one image default candidate passed an image-generation smoke probe."
                    if probed_image_candidates
                    else "Run the image-generation smoke probe before unattended media use."
                ),
            },
            {
                "id": "no-failed-probes",
                "status": "warn" if failed_probes else "pass",
                "reason": "No supplied chat probes failed."
                if not failed_probes
                else f"Review failed probes before rollout: {', '.join(failed_probes[:6])}.",
            },
            {
                "id": "no-failed-image-probes",
                "status": "warn" if failed_image_probes else "pass",
                "reason": "No supplied image-generation probes failed."
                if not failed_image_probes
                else f"Review failed image probes before media rollout: {', '.join(failed_image_probes[:6])}.",
            },
            {
                "id": "unknown-gemini-catalog-review",
                "status": "warn" if unknown_gemini else "pass",
                "reason": "All Gemini-like gateway models map to the local catalog."
                if not unknown_gemini
                else f"Add catalog pricing/lifecycle metadata for: {', '.join(unknown_gemini[:6])}.",
            },
            {
                "id": "recommended-env-present",
                "status": "pass" if any(row["recommended_value"] for row in recommended_env) else "warn",
                "reason": "Environment recommendations were generated from probe results.",
            },
        ]
        return checks

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        recommended_env: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [
                "Do not change default models until blocking probe safety or model metadata issues are resolved.",
                "Run /v1/models, tiny chat probes, and optional image smoke probes again after fixing gateway model routing.",
            ]
        actions = []
        changes = [row for row in recommended_env if row["requires_change"]]
        if changes:
            actions.append("Review recommended .env changes before updating defaults: " + ", ".join(row["env_var"] for row in changes[:6]) + ".")
        if warnings:
            actions.append("Resolve warnings before unattended batch runs; explicit experiments can remain manually gated.")
        if not actions:
            actions.append("Gateway probe results support the current cheap-first defaults.")
        actions.append("Never commit raw gateway responses that include API keys, bearer tokens, Authorization headers, prompts, image URLs, base64 data, emails, or model outputs.")
        return actions[:6]

    def _forbidden_payload_check(self, forbidden_payload_paths: list[str]) -> dict[str, Any]:
        return {
            "id": "sanitized-payload-fields",
            "status": "fail" if forbidden_payload_paths else "pass",
            "reason": "Payload contains forbidden raw or secret-bearing fields/values: " + ", ".join(forbidden_payload_paths[:8]) + "."
            if forbidden_payload_paths
            else "Payload contains only allowed sanitized probe metadata fields.",
        }

    def _forbidden_payload_paths(self, value: Any, path: str = "") -> list[str]:
        paths: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = _text(key)
                next_path = f"{path}.{self._safe_path_key(key_text)}" if path else self._safe_path_key(key_text)
                if key_text.lower() in FORBIDDEN_PAYLOAD_KEYS:
                    paths.append(next_path)
                    continue
                paths.extend(self._forbidden_payload_paths(child, next_path))
                if len(paths) >= 12:
                    return paths[:12]
        elif isinstance(value, list):
            for index, child in enumerate(value[:20]):
                paths.extend(self._forbidden_payload_paths(child, f"{path}[{index}]"))
                if len(paths) >= 12:
                    return paths[:12]
        elif isinstance(value, str):
            risk = self._forbidden_value_risk(value)
            if risk:
                paths.append(f"{path or 'value'}#{risk}")
        return paths[:12]

    def _forbidden_value_risk(self, value: str) -> str | None:
        if not value:
            return None
        sample = value[:4096]
        for risk, pattern in FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(sample):
                return risk
        return None

    def _safe_path_key(self, key: str) -> str:
        if key.lower().startswith("sk-") or len(key) > 80:
            return "redacted_key"
        return key


def _safe_int(value: Any, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _text(value: Any) -> str:
    return str(value or "").strip()
