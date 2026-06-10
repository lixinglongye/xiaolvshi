from __future__ import annotations

from typing import Any

from services.model_catalog import catalog_for_api, canonical_model_id, task_default_model


OFFICIAL_SOURCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "id": "gemini-api-models",
        "title": "Gemini API model list",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "tracked_signal": "Official Gemini model names, lifecycle labels, capabilities, and family availability.",
    },
    {
        "id": "gemini-api-pricing",
        "title": "Gemini API pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
        "tracked_signal": "Official paid-tier token/media pricing used before cheap-first default promotion.",
    },
    {
        "id": "gemini-openai-compatible",
        "title": "Gemini OpenAI compatibility",
        "url": "https://ai.google.dev/gemini-api/docs/openai",
        "tracked_signal": "OpenAI-compatible gateway request boundary for Gemini model names and tool shapes.",
    },
)

TRACKED_LIFECYCLE_SNAPSHOT: tuple[dict[str, Any], ...] = (
    {
        "model_id": "gemini-2.5-flash-lite",
        "official_lifecycle": "stable",
        "default_policy": "cheap_first_text_default",
        "default_allowed_for_high_frequency": True,
        "source_basis": "official_models_and_pricing",
        "required_action": "Keep as the cheapest high-frequency text start while source review remains current.",
    },
    {
        "model_id": "gemini-2.5-flash",
        "official_lifecycle": "stable",
        "default_policy": "balanced_fallback",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_models_and_pricing",
        "required_action": "Use as a balanced fallback after cheap-first checks or explicit review selection.",
    },
    {
        "model_id": "gemini-2.5-pro",
        "official_lifecycle": "stable",
        "default_policy": "premium_exception_review",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_models_and_pricing",
        "required_action": "Keep behind premium exception approval and cost review.",
    },
    {
        "model_id": "gemini-3.1-flash-lite",
        "official_lifecycle": "gateway_observed_review",
        "default_policy": "new_family_review_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "local_gateway_observation_and_official_openai_compatibility_boundary",
        "required_action": "Confirm official model-list lifecycle, pricing, and gateway support before high-volume promotion.",
    },
    {
        "model_id": "gemini-3.5-flash",
        "official_lifecycle": "gateway_observed_review",
        "default_policy": "premium_or_agentic_review",
        "default_allowed_for_high_frequency": False,
        "source_basis": "local_gateway_observation_and_official_openai_compatibility_boundary",
        "required_action": "Keep behind cheap prechecks and maintainer review until official lifecycle/pricing are refreshed.",
    },
    {
        "model_id": "gemini-3-flash-preview",
        "official_lifecycle": "preview",
        "default_policy": "preview_explicit_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_model_lifecycle_review",
        "required_action": "Never promote preview models to default routes without a canary and rollback packet.",
    },
    {
        "model_id": "gemini-3.1-pro",
        "official_lifecycle": "gateway_observed_review",
        "default_policy": "premium_alias_review_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "local_gateway_observation_and_official_openai_compatibility_boundary",
        "required_action": "Canonicalize to an official API name and verify gateway pricing before use.",
    },
    {
        "model_id": "gemini-3.1-pro-preview",
        "official_lifecycle": "preview",
        "default_policy": "preview_premium_explicit_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_model_lifecycle_review",
        "required_action": "Keep preview Pro routes explicit and maintainer-approved.",
    },
    {
        "model_id": "gemini-3.1-pro-preview-customtools",
        "official_lifecycle": "preview",
        "default_policy": "preview_custom_tools_explicit_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_model_lifecycle_review",
        "required_action": "Keep custom-tool preview routes explicit and audited.",
    },
    {
        "model_id": "gemini-2.5-flash-image",
        "official_lifecycle": "stable",
        "default_policy": "explicit_media_route_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_models_and_pricing",
        "required_action": "Use only through image routes with media pricing review.",
    },
    {
        "model_id": "gemini-3.1-flash-image",
        "official_lifecycle": "media_review",
        "default_policy": "explicit_media_route_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_models_and_pricing",
        "required_action": "Keep as explicit image candidate until media route policy is refreshed.",
    },
    {
        "model_id": "gemini-3-pro-image",
        "official_lifecycle": "media_review",
        "default_policy": "premium_media_explicit_only",
        "default_allowed_for_high_frequency": False,
        "source_basis": "official_models_and_pricing",
        "required_action": "Keep premium image generation explicit and operator-approved.",
    },
)

HIGH_FREQUENCY_TEXT_TASKS = ("cheap", "fast", "classification", "ocr")
NEW_FAMILY_REVIEW_TASKS = ("agentic", "grounded-research")
DEFAULT_REVIEW_TASKS = HIGH_FREQUENCY_TEXT_TASKS + NEW_FAMILY_REVIEW_TASKS
BLOCKED_DEFAULT_LIFECYCLES = {"preview", "deprecated", "shutdown", "retired"}
REVIEW_LIFECYCLES = {"gateway_observed_review", "media_review", "review_required", "unknown"}


class ModelOpsGeminiOfficialLifecycleDriftGateService:
    """Build metadata-only evidence that prevents unsafe Gemini lifecycle drift."""

    def build_gate(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        signals = signals if isinstance(signals, dict) else {}
        catalog_rows = self._catalog_rows(signals)
        catalog_by_id = {str(row.get("id") or ""): row for row in catalog_rows}
        snapshot_rows = self._snapshot_rows(signals)
        snapshot_by_id = {row["model_id"]: row for row in snapshot_rows}
        default_rows = self._default_rows(catalog_by_id, snapshot_by_id, signals)
        lifecycle_rows = self._lifecycle_rows(catalog_by_id, snapshot_rows)
        drift_rows = [row for row in lifecycle_rows if row["drift_status"] != "aligned"]
        checks = self._checks(default_rows, lifecycle_rows, drift_rows)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-gemini-official-lifecycle-drift-gate",
            "title": "ModelOps Gemini official lifecycle drift gate",
            "status": status,
            "method": {
                "type": "metadata-only-gemini-official-lifecycle-drift-gate",
                "notes": [
                    "Compares local catalog/default roles with a maintainer-reviewed Gemini lifecycle snapshot.",
                    "Keeps stable Flash-Lite as the only high-frequency cheap-first default without extra review.",
                    "Treats gateway-observed, preview, media, and premium Gemini names as explicit-review candidates.",
                    "Does not call Gemini, Google, NewAPI, OpenAI, gateways, app AI endpoints, models, or the network.",
                ],
                "source_urls": [row["url"] for row in OFFICIAL_SOURCE_ROWS],
            },
            "summary": {
                "tracked_model_count": len(snapshot_rows),
                "catalog_model_count": len(catalog_rows),
                "default_task_count": len(default_rows),
                "high_frequency_task_count": len(HIGH_FREQUENCY_TEXT_TASKS),
                "stable_flash_lite_default_count": sum(1 for row in default_rows if row["stable_flash_lite_aligned"]),
                "review_default_count": sum(1 for row in default_rows if row["requires_review"]),
                "blocked_default_count": sum(1 for row in default_rows if row["blocked_default"]),
                "lifecycle_drift_count": len(drift_rows),
                "preview_catalog_count": sum(1 for row in lifecycle_rows if row["official_lifecycle"] == "preview"),
                "gateway_observed_review_count": sum(
                    1 for row in lifecycle_rows if row["official_lifecycle"] == "gateway_observed_review"
                ),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "official_source_rows": [dict(row) for row in OFFICIAL_SOURCE_ROWS],
            "lifecycle_rows": lifecycle_rows,
            "default_task_rows": default_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(default_rows, drift_rows, status),
            "privacy_boundary": {
                "metadata_only": True,
                "source_urls_returned": True,
                "model_ids_returned": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "headers_included": False,
                "request_bodies_included": False,
                "response_bodies_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "official source URLs, lifecycle labels, local catalog ids, configured role names, checks, and maintainer actions only",
            },
            "claim_boundary": {
                "official_source_refresh_completed": False,
                "all_gemini_models_supported_claimed": False,
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "production_quality_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claim": "The repository exposes metadata-only Gemini lifecycle drift evidence before default promotion.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_official_lifecycle_drift_gate.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _catalog_rows(self, signals: dict[str, Any]) -> list[dict[str, Any]]:
        rows = signals.get("catalog_rows")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
        return catalog_for_api()

    def _snapshot_rows(self, signals: dict[str, Any]) -> list[dict[str, Any]]:
        merged = {str(row["model_id"]): dict(row) for row in TRACKED_LIFECYCLE_SNAPSHOT}
        overrides = signals.get("official_lifecycle_snapshot")
        if isinstance(overrides, list):
            for item in overrides:
                if not isinstance(item, dict):
                    continue
                model_id = str(item.get("model_id") or "").strip()
                if not model_id:
                    continue
                base = dict(merged.get(model_id, {}))
                base.update(item)
                merged[model_id] = self._normalize_snapshot_row(base)
        return [self._normalize_snapshot_row(row) for row in merged.values()]

    def _normalize_snapshot_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "model_id": str(row.get("model_id") or ""),
            "official_lifecycle": str(row.get("official_lifecycle") or "unknown"),
            "default_policy": str(row.get("default_policy") or "review_required"),
            "default_allowed_for_high_frequency": bool(row.get("default_allowed_for_high_frequency")),
            "source_basis": str(row.get("source_basis") or "maintainer_snapshot"),
            "required_action": str(row.get("required_action") or "Review official lifecycle and pricing before promotion."),
        }

    def _default_rows(
        self,
        catalog_by_id: dict[str, dict[str, Any]],
        snapshot_by_id: dict[str, dict[str, Any]],
        signals: dict[str, Any],
    ) -> list[dict[str, Any]]:
        configured = signals.get("task_defaults") if isinstance(signals.get("task_defaults"), dict) else {}
        rows: list[dict[str, Any]] = []
        for task in DEFAULT_REVIEW_TASKS:
            default_model = str(configured.get(task) or task_default_model(task))
            canonical = canonical_model_id(default_model)
            catalog_row = catalog_by_id.get(canonical or "", {})
            snapshot = snapshot_by_id.get(canonical or "", {})
            official_lifecycle = str(snapshot.get("official_lifecycle") or "unknown")
            default_policy = str(snapshot.get("default_policy") or "review_required")
            cost_tier = str(catalog_row.get("cost_tier") or "unknown")
            catalog_status = str(catalog_row.get("status") or "unknown")
            stable_flash_lite = (
                canonical == "gemini-2.5-flash-lite"
                and official_lifecycle == "stable"
                and catalog_status == "stable"
                and cost_tier in {"lowest", "low"}
            )
            high_frequency = task in HIGH_FREQUENCY_TEXT_TASKS
            blocked_default = official_lifecycle in BLOCKED_DEFAULT_LIFECYCLES or (
                high_frequency and not stable_flash_lite
            )
            requires_review = (
                not blocked_default
                and (
                    official_lifecycle in REVIEW_LIFECYCLES
                    or default_policy not in {"cheap_first_text_default", "balanced_fallback"}
                    or (high_frequency and not stable_flash_lite)
                )
            )
            rows.append(
                {
                    "task": task,
                    "default_model": default_model,
                    "canonical_model": canonical,
                    "catalog_status": catalog_status,
                    "cost_tier": cost_tier,
                    "official_lifecycle": official_lifecycle,
                    "default_policy": default_policy,
                    "high_frequency": high_frequency,
                    "stable_flash_lite_aligned": stable_flash_lite,
                    "requires_review": requires_review,
                    "blocked_default": blocked_default,
                    "recommended_action": self._default_action(task, stable_flash_lite, requires_review, blocked_default),
                }
            )
        return rows

    def _lifecycle_rows(
        self,
        catalog_by_id: dict[str, dict[str, Any]],
        snapshot_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for snapshot in snapshot_rows:
            model_id = snapshot["model_id"]
            catalog_row = catalog_by_id.get(model_id, {})
            catalog_status = str(catalog_row.get("status") or "missing")
            configured_roles = [str(role) for role in catalog_row.get("configured_roles") or []]
            official_lifecycle = str(snapshot["official_lifecycle"])
            drift_status = self._drift_status(official_lifecycle, catalog_status, configured_roles)
            rows.append(
                {
                    "model_id": model_id,
                    "catalog_status": catalog_status,
                    "cost_tier": str(catalog_row.get("cost_tier") or "missing"),
                    "configured_roles": configured_roles,
                    "official_lifecycle": official_lifecycle,
                    "default_policy": str(snapshot["default_policy"]),
                    "default_allowed_for_high_frequency": bool(snapshot["default_allowed_for_high_frequency"]),
                    "source_basis": str(snapshot["source_basis"]),
                    "drift_status": drift_status,
                    "required_action": str(snapshot["required_action"]),
                }
            )
        return rows

    def _drift_status(self, official_lifecycle: str, catalog_status: str, configured_roles: list[str]) -> str:
        if official_lifecycle in {"deprecated", "shutdown", "retired"}:
            return "blocked_default_drift" if configured_roles or catalog_status not in {"deprecated", "retired"} else "aligned"
        if official_lifecycle == "preview" and catalog_status == "stable":
            return "catalog_marks_preview_stable"
        if official_lifecycle in REVIEW_LIFECYCLES and catalog_status == "stable":
            return "catalog_marks_review_model_stable"
        if catalog_status == "missing":
            return "snapshot_model_missing_from_catalog"
        return "aligned"

    def _checks(
        self,
        default_rows: list[dict[str, Any]],
        lifecycle_rows: list[dict[str, Any]],
        drift_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        high_frequency_drifts = [
            row["task"] for row in default_rows if row["high_frequency"] and not row["stable_flash_lite_aligned"]
        ]
        blocked_defaults = [row["task"] for row in default_rows if row["blocked_default"]]
        review_defaults = [row["task"] for row in default_rows if row["requires_review"]]
        preview_default_models = [
            row["default_model"] for row in default_rows if row["official_lifecycle"] in BLOCKED_DEFAULT_LIFECYCLES
        ]
        missing_catalog = [row["model_id"] for row in lifecycle_rows if row["catalog_status"] == "missing"]
        drift_model_ids = [row["model_id"] for row in drift_rows]
        return [
            {
                "id": "official-source-boundary-linked",
                "status": "pass" if len(OFFICIAL_SOURCE_ROWS) >= 3 else "fail",
                "reason": "Gemini model, pricing, and OpenAI-compatible official source URLs are attached.",
            },
            {
                "id": "high-frequency-text-defaults-stable-flash-lite",
                "status": "fail" if high_frequency_drifts else "pass",
                "reason": "High-frequency text defaults remain on stable Gemini 2.5 Flash-Lite."
                if not high_frequency_drifts
                else "High-frequency lifecycle drift detected for: " + ", ".join(high_frequency_drifts),
            },
            {
                "id": "preview-deprecated-shutdown-defaults-blocked",
                "status": "fail" if preview_default_models or blocked_defaults else "pass",
                "reason": "Preview, deprecated, shutdown, and retired lifecycle labels are blocked from defaults."
                if not preview_default_models and not blocked_defaults
                else "Blocked lifecycle default detected for: " + ", ".join(sorted(set(blocked_defaults))),
            },
            {
                "id": "review-lifecycle-defaults-visible",
                "status": "warn" if review_defaults else "pass",
                "reason": "No default task uses a lifecycle-review Gemini model."
                if not review_defaults
                else "Default task review still required for: " + ", ".join(review_defaults),
            },
            {
                "id": "catalog-lifecycle-drift-visible",
                "status": "warn" if drift_rows else "pass",
                "reason": "Local catalog lifecycle labels align with tracked Gemini lifecycle snapshot."
                if not drift_rows
                else "Catalog lifecycle drift visible for: " + ", ".join(drift_model_ids),
            },
            {
                "id": "tracked-snapshot-models-cataloged",
                "status": "warn" if missing_catalog else "pass",
                "reason": "All tracked Gemini lifecycle snapshot rows are represented in the local catalog."
                if not missing_catalog
                else "Snapshot model rows missing from catalog: " + ", ".join(missing_catalog),
            },
            {
                "id": "openai-compatible-gateway-boundary",
                "status": "pass",
                "reason": "OpenAI-compatible Gemini gateway support is treated as metadata-only until sanitized probes are attached.",
            },
        ]

    def _default_action(
        self,
        task: str,
        stable_flash_lite: bool,
        requires_review: bool,
        blocked_default: bool,
    ) -> str:
        if blocked_default:
            return f"Move {task} back to stable Gemini 2.5 Flash-Lite or attach a maintainer-approved migration packet."
        if requires_review:
            return f"Keep {task} behind lifecycle, pricing, and gateway support review before default promotion."
        if stable_flash_lite:
            return f"Keep {task} on stable Gemini 2.5 Flash-Lite for cheap-first routing."
        return f"Review {task} default lifecycle before release."

    def _recommended_actions(
        self,
        default_rows: list[dict[str, Any]],
        drift_rows: list[dict[str, Any]],
        status: str,
    ) -> list[str]:
        actions: list[str] = []
        for row in default_rows:
            if row["blocked_default"] or row["requires_review"]:
                actions.append(str(row["recommended_action"]))
        for row in drift_rows:
            actions.append(f"Review catalog lifecycle for {row['model_id']}: {row['drift_status']}.")
        if not actions:
            actions.append("Gemini lifecycle drift gate is passing; keep the official source review attached to releases.")
        if status == "blocked":
            actions.insert(0, "Do not promote Gemini/NewAPI default changes until blocked lifecycle drift is resolved.")
        return list(dict.fromkeys(actions))
