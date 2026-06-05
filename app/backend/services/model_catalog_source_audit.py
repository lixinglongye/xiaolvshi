from __future__ import annotations

from typing import Any

from services.model_catalog import GEMINI_MODEL_CATALOG, catalog_for_api, canonical_model_id, task_default_model


OFFICIAL_GEMINI_SOURCE_REFERENCES = (
    {
        "id": "google-gemini-pricing",
        "title": "Gemini Developer API pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
        "review_purpose": "Refresh paid-tier token and image pricing before changing defaults.",
    },
    {
        "id": "google-gemini-models",
        "title": "Gemini API model list",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "review_purpose": "Check model availability, lifecycle, capabilities, and naming before catalog promotion.",
    },
)
HIGH_FREQUENCY_TASKS = ("fast", "classification", "ocr")
HIGH_FREQUENCY_ROLE_NAMES = {"cheap", "fast", "ocr", "classification", "classifier"}
SOURCE_HOST = "https://ai.google.dev/"


class ModelCatalogSourceAuditService:
    """Audit local Gemini catalog source and default-role metadata without network calls."""

    def build_audit(self) -> dict[str, Any]:
        rows = [self._catalog_row(item) for item in catalog_for_api()]
        checks = self._checks(rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "fail" if blocking else ("warn" if warnings else "pass")
        high_frequency_defaults = [
            {
                "task": task,
                "default_model": task_default_model(task),
                "canonical_model": canonical_model_id(task_default_model(task)),
            }
            for task in HIGH_FREQUENCY_TASKS
        ]

        return {
            "status": status,
            "method": {
                "type": "gemini-catalog-source-audit",
                "notes": [
                    "Audits local Gemini catalog metadata, source URLs, pricing coverage, and default-role posture.",
                    "Keeps high-frequency defaults on catalog-known stable Flash-Lite models unless release evidence changes.",
                    "Does not call Gemini, NewAPI, OpenAI, Google, or any gateway.",
                ],
                "source_urls": [item["url"] for item in OFFICIAL_GEMINI_SOURCE_REFERENCES],
            },
            "summary": {
                "catalog_model_count": len(rows),
                "source_reference_count": len(OFFICIAL_GEMINI_SOURCE_REFERENCES),
                "source_url_present_count": sum(1 for row in rows if row["source_url_present"]),
                "official_source_url_count": sum(1 for row in rows if row["official_source_url"]),
                "priced_model_count": sum(1 for row in rows if row["pricing_status"] != "missing"),
                "missing_pricing_count": sum(1 for row in rows if row["pricing_status"] == "missing"),
                "stable_model_count": sum(1 for row in rows if row["catalog_status"] == "stable"),
                "preview_model_count": sum(1 for row in rows if row["catalog_status"] == "preview"),
                "high_frequency_default_count": len(high_frequency_defaults),
                "high_frequency_aligned_count": sum(
                    1 for item in high_frequency_defaults if self._high_frequency_default_is_aligned(item["default_model"])
                ),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "raw_payload_echoed": False,
            },
            "source_references": list(OFFICIAL_GEMINI_SOURCE_REFERENCES),
            "high_frequency_defaults": high_frequency_defaults,
            "catalog_rows": rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings, rows),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "network_called": False,
                "output_scope": "catalog model ids, official source URLs, pricing/source status, default roles, and check ids only",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_catalog_source_audit.py tests/test_model_catalog.py -q",
                "python -m pytest tests/test_model_ops_readiness.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _catalog_row(self, item: dict[str, Any]) -> dict[str, Any]:
        model_id = str(item.get("id") or "")
        pricing = item.get("pricing") if isinstance(item.get("pricing"), dict) else {}
        source_url = str(pricing.get("source_url") or "")
        pricing_status = self._pricing_status(pricing)
        configured_roles = [str(role) for role in item.get("configured_roles") or []]
        is_flash_lite = "flash-lite" in model_id
        is_stable = str(item.get("status") or "") == "stable"
        is_premium_or_preview = str(item.get("cost_tier") or "") == "premium" or not is_stable or "pro" in model_id
        return {
            "model_id": model_id,
            "catalog_status": str(item.get("status") or "unknown"),
            "cost_tier": str(item.get("cost_tier") or "unknown"),
            "latency_tier": str(item.get("latency_tier") or "unknown"),
            "capability_count": len(item.get("capabilities") or []),
            "best_for_count": len(item.get("best_for") or []),
            "configured_roles": configured_roles,
            "source_url": source_url,
            "source_url_present": bool(source_url),
            "official_source_url": source_url.startswith(SOURCE_HOST),
            "pricing_status": pricing_status,
            "high_frequency_default_allowed": is_flash_lite
            and is_stable
            and str(item.get("cost_tier") or "") in {"lowest", "low"}
            and pricing_status == "token_priced",
            "default_requires_review": any(role in HIGH_FREQUENCY_ROLE_NAMES for role in configured_roles)
            and is_premium_or_preview,
            "review_note": self._review_note(model_id, pricing_status, is_premium_or_preview),
        }

    def _checks(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        missing_source = [row for row in rows if not row["source_url_present"] or not row["official_source_url"]]
        missing_pricing = [row for row in rows if row["pricing_status"] == "missing"]
        aligned_defaults = [
            task
            for task in HIGH_FREQUENCY_TASKS
            if self._high_frequency_default_is_aligned(task_default_model(task))
        ]
        preview_default_rows = [row for row in rows if row["default_requires_review"]]
        return [
            {
                "id": "official-source-url-present",
                "status": "pass" if not missing_source else "fail",
                "reason": "Every catalog model points to an official Gemini source URL."
                if not missing_source
                else "One or more catalog models are missing official Gemini source URLs.",
            },
            {
                "id": "high-frequency-defaults-cheap-first",
                "status": "pass" if len(aligned_defaults) == len(HIGH_FREQUENCY_TASKS) else "fail",
                "reason": "Fast, classification, and OCR defaults resolve to stable Flash-Lite catalog models."
                if len(aligned_defaults) == len(HIGH_FREQUENCY_TASKS)
                else "High-frequency defaults must stay on stable Flash-Lite catalog models.",
            },
            {
                "id": "stable-defaults-not-preview-or-premium",
                "status": "pass" if not preview_default_rows else "fail",
                "reason": "High-frequency configured defaults do not point at preview or premium catalog rows."
                if not preview_default_rows
                else "Preview or premium model rows are configured for high-frequency defaults and require review.",
            },
            {
                "id": "pricing-metadata-watchlist",
                "status": "pass" if not missing_pricing else "warn",
                "reason": "Catalog pricing metadata is present for every model."
                if not missing_pricing
                else "Some catalog models lack local price metadata and must stay on the source-review watchlist.",
            },
            {
                "id": "catalog-shape-complete",
                "status": "pass"
                if all(row["capability_count"] > 0 and row["best_for_count"] > 0 for row in rows)
                else "fail",
                "reason": "Every catalog model has capability and intended-use metadata."
                if all(row["capability_count"] > 0 and row["best_for_count"] > 0 for row in rows)
                else "Every catalog model must include capabilities and intended-use metadata.",
            },
        ]

    def _high_frequency_default_is_aligned(self, model_id: str) -> bool:
        canonical = canonical_model_id(model_id)
        if not canonical or "flash-lite" not in canonical:
            return False
        for profile in GEMINI_MODEL_CATALOG:
            if profile.id == canonical:
                return profile.status == "stable" and profile.cost_tier in {"lowest", "low"}
        return False

    def _pricing_status(self, pricing: dict[str, Any]) -> str:
        if pricing.get("output_usd_per_image") is not None:
            return "image_priced"
        if pricing.get("input_usd_per_million_tokens") is not None and pricing.get("output_usd_per_million_tokens") is not None:
            return "token_priced"
        if pricing.get("input_usd_per_million_tokens") is not None or pricing.get("output_usd_per_million_tokens") is not None:
            return "partial_token_priced"
        return "missing"

    def _review_note(self, model_id: str, pricing_status: str, premium_or_preview: bool) -> str:
        if pricing_status == "missing":
            return "Keep explicit-only until provider and gateway price metadata are reviewed."
        if premium_or_preview:
            return "Requires operator review before use as a default."
        if "flash-lite" in model_id:
            return "Eligible cheap-first candidate when the gateway exposes this catalog id or accepted prefixes."
        return "Use after cheap-first checks or for explicit task routes."

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        rows: list[dict[str, Any]],
    ) -> list[str]:
        actions = []
        if blocking:
            actions.append("Restore catalog source URLs and cheap-first defaults before changing Gemini route defaults.")
        if warnings:
            missing = [row["model_id"] for row in rows if row["pricing_status"] == "missing"]
            if missing:
                actions.append("Refresh local price metadata or keep explicit-only for: " + ", ".join(missing[:6]) + ".")
        if not actions:
            actions.append("Keep official Gemini source review attached to catalog changes and rerun ModelOps readiness.")
        return actions
