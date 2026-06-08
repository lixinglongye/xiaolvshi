from __future__ import annotations

from typing import Any

from services import model_catalog
from services.gemini_newapi_observed_model_extraction import extract_observed_model_ids
from services.model_catalog import ModelProfile, canonical_model_id, model_profile, task_default_model
from services.model_default_candidate_selector import COST_RANK, TASK_POLICIES


class ModelOpsObservedGatewayModelFitMatrixService:
    """Score observed OpenAI-compatible gateway models against cheap-first task needs."""

    def build_matrix(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        extraction = extract_observed_model_ids(data, max_candidates=120, max_model_ids=80)
        model_rows = [self._model_row(model_id) for model_id in extraction["observed_models"]]
        task_rows = [self._task_row(task, model_rows) for task in TASK_POLICIES]
        checks = self._checks(task_rows, model_rows, extraction)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-observed-gateway-model-fit-matrix",
            "title": "Observed gateway model fit matrix",
            "status": "blocked" if blocking else ("review_required" if warnings else "ready"),
            "method": {
                "type": "metadata-only-observed-gateway-model-fit-matrix",
                "notes": [
                    "Maps sanitized NewAPI/Gemini/OpenAI-compatible model-list ids to local Gemini catalog capability and pricing metadata.",
                    "Finds the cheapest observed gateway candidate per task before any default or route change.",
                    "Keeps Pro, preview, unpriced, unknown, external, and media variants explicit-review unless policy allows them.",
                    "Does not call NewAPI, Gemini, Google, OpenAI, gateways, app AI endpoints, or the network.",
                ],
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://ai.google.dev/gemini-api/docs/models",
                    "https://ai.google.dev/gemini-api/docs/pricing",
                    "https://docs.newapi.pro/zh/docs/guide/feature-guide/user/api",
                ],
            },
            "summary": {
                "observed_model_candidate_count": extraction["summary"]["candidate_count"],
                "accepted_observed_model_count": extraction["summary"]["accepted_model_count"],
                "rejected_sensitive_observed_model_count": extraction["summary"]["rejected_sensitive_count"],
                "rejected_invalid_observed_model_count": extraction["summary"].get("rejected_invalid_count", 0),
                "known_gemini_model_count": sum(1 for row in model_rows if row["known_catalog_model"]),
                "unknown_gemini_like_count": sum(1 for row in model_rows if row["gemini_like"] and not row["known_catalog_model"]),
                "external_model_count": sum(1 for row in model_rows if not row["gemini_like"]),
                "default_allowed_model_count": sum(1 for row in model_rows if row["default_allowed_without_review"]),
                "explicit_review_model_count": sum(1 for row in model_rows if row["explicit_review_required"]),
                "task_count": len(task_rows),
                "covered_task_count": sum(1 for row in task_rows if row["gateway_fit_status"] in {"cheap_fit", "balanced_fit", "premium_exception_fit", "media_fit"}),
                "cheap_first_task_count": sum(1 for row in task_rows if row["high_frequency"]),
                "cheap_first_covered_count": sum(1 for row in task_rows if row["high_frequency"] and row["gateway_fit_status"] == "cheap_fit"),
                "missing_task_count": sum(1 for row in task_rows if row["gateway_fit_status"] == "missing"),
                "review_task_count": sum(1 for row in task_rows if row["review_required"]),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "raw_payload_echoed": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "credentials_included": False,
            },
            "task_fit_rows": task_rows,
            "observed_model_rows": model_rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "source_summaries": {
                "observed_model_extraction": extraction["summary"],
            },
            "coverage_policy": {
                "cheap_first_rule": "High-frequency tasks need an observed stable Flash-Lite or equivalent lowest-cost catalog model with task-required capabilities.",
                "balanced_rule": "Review/document-generation tasks can use stable low-cost review-capable models after deterministic or cheap prechecks.",
                "premium_exception_rule": "PDF, complex, Pro, preview, unknown, and unpriced routes are review-only unless explicit premium evidence is approved.",
                "media_rule": "Image routes require image pricing metadata and remain explicit media operations, not bulk text defaults.",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "output_scope": "sanitized model ids, canonical ids, task names, capability labels, cost tiers, fit states, and checks only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_gateway_inventory_claimed": False,
                "automatic_default_change_claimed": False,
                "pricing_accuracy_claimed": False,
                "production_quality_claimed": False,
                "public_benchmark_score_claimed": False,
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, task_rows),
            "validation_commands": [
                "python -m pytest tests/test_modelops_observed_gateway_model_fit_matrix.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_gemini_newapi_observed_model_extraction.py tests/test_model_default_candidate_selector.py tests/test_model_catalog.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _model_row(self, observed_model: str) -> dict[str, Any]:
        canonical = canonical_model_id(observed_model)
        profile = model_profile(observed_model) if observed_model else None
        gemini_like = _is_gemini_like(observed_model)
        reason_codes = _model_reason_codes(profile, gemini_like)
        return {
            "id": f"observed-gateway-model-{_slug(observed_model)}",
            "observed_model": observed_model,
            "canonical_model": canonical,
            "known_catalog_model": bool(profile),
            "gemini_like": gemini_like,
            "model_family": profile.family if profile else ("gemini" if gemini_like else "external"),
            "cost_tier": profile.cost_tier if profile else "unknown",
            "latency_tier": profile.latency_tier if profile else "unknown",
            "lifecycle_status": profile.status if profile else "unknown",
            "capabilities": list(profile.capabilities) if profile else [],
            "task_coverage": _covered_tasks(profile),
            "default_allowed_without_review": _default_allowed_model(profile),
            "explicit_review_required": bool(reason_codes),
            "reason_codes": reason_codes or ["observed_model_fit_ready"],
            "recommended_action": _model_action(reason_codes, gemini_like),
        }

    def _task_row(self, task: str, model_rows: list[dict[str, Any]]) -> dict[str, Any]:
        policy = TASK_POLICIES[task]
        configured_default = task_default_model(task)
        configured_canonical = canonical_model_id(configured_default)
        candidates = [row for row in model_rows if task in row["task_coverage"]]
        default_candidates = [row for row in candidates if self._task_default_allowed(row, policy)]
        cheapest = _sort_gateway_candidates(default_candidates)[0] if default_candidates else None
        review_candidates = [row for row in candidates if row not in default_candidates]
        status = self._task_status(task, cheapest, review_candidates)
        review_required = status in {"review_only", "missing"}
        reason_codes = self._task_reason_codes(task, policy, configured_canonical, candidates, cheapest, review_candidates)
        return {
            "id": f"observed-gateway-task-fit-{task}",
            "task": task,
            "route_mode": policy.route_mode,
            "high_frequency": policy.high_frequency,
            "price_mode": policy.price_mode,
            "required_capabilities": list(policy.required_capabilities),
            "preferred_capabilities": list(policy.preferred_capabilities),
            "max_default_cost_tier": policy.max_default_cost_tier,
            "configured_default_model": configured_default,
            "configured_default_canonical": configured_canonical,
            "configured_default_observed": bool(
                configured_canonical and any(row["canonical_model"] == configured_canonical for row in candidates)
            ),
            "gateway_candidate_count": len(candidates),
            "default_allowed_candidate_count": len(default_candidates),
            "review_only_candidate_count": len(review_candidates),
            "cheapest_gateway_model": cheapest["observed_model"] if cheapest else None,
            "cheapest_canonical_model": cheapest["canonical_model"] if cheapest else None,
            "cheapest_cost_tier": cheapest["cost_tier"] if cheapest else None,
            "gateway_fit_status": status,
            "default_allowed_without_review": bool(cheapest),
            "review_required": review_required,
            "reason_codes": reason_codes or ["task_gateway_fit_ready"],
            "next_action": self._task_action(status, task, policy, cheapest),
        }

    def _task_default_allowed(self, row: dict[str, Any], policy: Any) -> bool:
        profile = model_profile(row.get("canonical_model"))
        if not profile:
            return False
        if profile.status != "stable":
            return False
        if _tier_rank(profile.cost_tier) > _tier_rank(policy.max_default_cost_tier):
            return False
        if policy.price_mode == "image":
            return profile.output_usd_per_image is not None
        if policy.price_mode == "embedding":
            return profile.input_usd_per_million_tokens is not None
        return profile.input_usd_per_million_tokens is not None and profile.output_usd_per_million_tokens is not None

    def _task_status(self, task: str, cheapest: dict[str, Any] | None, review_candidates: list[dict[str, Any]]) -> str:
        if cheapest and TASK_POLICIES[task].price_mode == "image":
            return "media_fit"
        if cheapest and TASK_POLICIES[task].route_mode == "premium_exception":
            return "premium_exception_fit"
        if cheapest and TASK_POLICIES[task].high_frequency:
            return "cheap_fit"
        if cheapest:
            return "balanced_fit"
        if review_candidates:
            return "review_only"
        return "missing"

    def _task_reason_codes(
        self,
        task: str,
        policy: Any,
        configured_canonical: str | None,
        candidates: list[dict[str, Any]],
        cheapest: dict[str, Any] | None,
        review_candidates: list[dict[str, Any]],
    ) -> list[str]:
        codes: list[str] = []
        if not candidates:
            codes.append("gateway_task_capability_missing")
        if candidates and not cheapest:
            codes.append("gateway_candidates_review_only")
        if (
            policy.high_frequency
            and cheapest
            and policy.price_mode == "text"
            and "flash-lite" not in str(cheapest.get("canonical_model") or "")
        ):
            codes.append("high_frequency_not_flash_lite")
        if configured_canonical and candidates and not any(row["canonical_model"] == configured_canonical for row in candidates):
            codes.append("configured_default_not_observed")
        if review_candidates:
            codes.append("review_only_candidates_present")
        if task in {"pdf"} and cheapest:
            codes.append("premium_exception_requires_operator_review")
        return codes

    def _checks(
        self,
        task_rows: list[dict[str, Any]],
        model_rows: list[dict[str, Any]],
        extraction: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rejected_sensitive = int(extraction["summary"]["rejected_sensitive_count"])
        high_frequency_gaps = [
            row["task"]
            for row in task_rows
            if row["high_frequency"] and row["gateway_fit_status"] != "cheap_fit"
        ]
        missing_tasks = [row["task"] for row in task_rows if row["gateway_fit_status"] == "missing"]
        review_models = [
            row["observed_model"]
            for row in model_rows
            if row["explicit_review_required"]
        ]
        return [
            _check(
                "observed-models-present",
                "pass" if model_rows else "warn",
                "At least one sanitized observed gateway model is available for fit scoring.",
                [str(len(model_rows))],
            ),
            _check(
                "sensitive-observed-model-values",
                "fail" if rejected_sensitive else "pass",
                "Sensitive observed model values are rejected and never echoed.",
                [str(rejected_sensitive)],
            ),
            _check(
                "high-frequency-cheap-fit",
                "fail" if high_frequency_gaps else "pass",
                "High-frequency tasks have observed cheap-first gateway coverage.",
                high_frequency_gaps,
            ),
            _check(
                "task-capability-coverage",
                "warn" if missing_tasks else "pass",
                "Every task policy has at least one observed capable gateway model.",
                missing_tasks,
            ),
            _check(
                "review-only-model-boundary",
                "warn" if review_models else "pass",
                "Unknown, external, preview, premium, or unpriced observed models remain review-only.",
                review_models[:12],
            ),
            _check(
                "metadata-only-boundary",
                "pass",
                "The fit matrix is metadata-only and does not call gateways or write configuration.",
                [],
            ),
        ]

    def _task_action(self, status: str, task: str, policy: Any, cheapest: dict[str, Any] | None) -> str:
        if status == "missing":
            return f"Add or verify an observed gateway model with {', '.join(policy.required_capabilities)} for {task}."
        if status == "review_only":
            return f"Review observed {task} candidates for lifecycle, pricing, and capability evidence before default use."
        if status == "cheap_fit":
            return f"Keep {cheapest['canonical_model']} as the observed cheap-first candidate for {task}."
        if status == "media_fit":
            return f"Keep {cheapest['canonical_model']} explicit for image/media routes with per-image pricing review."
        if status == "premium_exception_fit":
            return f"Use {cheapest['canonical_model']} only as an operator-approved premium exception for {task}."
        return f"Use {cheapest['canonical_model']} after deterministic or cheap prechecks for {task}."

    def _recommended_actions(
        self,
        blocking: list[str],
        warnings: list[str],
        task_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if "sensitive-observed-model-values" in blocking:
            actions.extend(
                [
                "Remove sensitive model-list values and rerun the sanitized gateway model fit matrix.",
                "Do not promote observed gateway models while sensitive values are present.",
                ]
            )
        missing = [row["task"] for row in task_rows if row["gateway_fit_status"] == "missing"]
        high_frequency = [
            row["task"]
            for row in task_rows
            if row["high_frequency"] and row["gateway_fit_status"] != "cheap_fit"
        ]
        if high_frequency:
            actions.append(
                "Verify Flash-Lite text coverage and input-priced embedding coverage for high-frequency tasks before batch or default route changes."
            )
        if missing:
            actions.append(f"Collect sanitized gateway model-list evidence for missing tasks: {', '.join(missing)}.")
        unresolved_blocking = [check_id for check_id in blocking if check_id != "sensitive-observed-model-values"]
        if unresolved_blocking and not high_frequency and not missing:
            actions.append(f"Resolve blocking observed gateway fit checks: {', '.join(unresolved_blocking)}.")
        if warnings:
            actions.append("Keep review-only observed models explicit until catalog pricing and lifecycle evidence is added.")
        actions.append("Use this matrix with cheap-first route preflight before changing APP_AI_* defaults.")
        return actions


def _covered_tasks(profile: ModelProfile | None) -> list[str]:
    if not profile:
        return []
    tasks = []
    for task, policy in TASK_POLICIES.items():
        if all(capability in profile.capabilities for capability in policy.required_capabilities):
            tasks.append(task)
    return tasks


def _default_allowed_model(profile: ModelProfile | None) -> bool:
    if not profile or profile.status != "stable":
        return False
    capabilities = set(profile.capabilities)
    if "embedding" in capabilities:
        return (
            profile.cost_tier == "lowest"
            and profile.input_usd_per_million_tokens is not None
            and "multimodal" not in capabilities
        )
    if profile.output_usd_per_image is not None and "image" in profile.capabilities:
        return profile.cost_tier in {"lowest", "low"}
    return (
        profile.cost_tier in {"lowest", "low"}
        and profile.input_usd_per_million_tokens is not None
        and profile.output_usd_per_million_tokens is not None
    )


def _model_reason_codes(profile: ModelProfile | None, gemini_like: bool) -> list[str]:
    if not profile:
        return ["unknown_gemini_like_model"] if gemini_like else ["external_non_gemini_model"]
    codes: list[str] = []
    if profile.status != "stable":
        codes.append(f"lifecycle_{profile.status}")
    if profile.cost_tier == "premium":
        codes.append("premium_model")
    if profile.input_usd_per_million_tokens is None and profile.output_usd_per_image is None:
        codes.append("pricing_missing")
    if "embedding" in profile.capabilities and "multimodal" in profile.capabilities:
        codes.append("multimodal_embedding_review")
    if "image" in profile.capabilities:
        codes.append("media_model_explicit_only")
    return codes


def _model_action(reason_codes: list[str], gemini_like: bool) -> str:
    if not reason_codes:
        return "Allow as a task-scoped observed gateway candidate when task policy also fits."
    if "unknown_gemini_like_model" in reason_codes:
        return "Catalog price, lifecycle, and capability metadata before default or batch use."
    if not gemini_like:
        return "Ignore for Gemini cheap-first defaults unless a separate external-provider policy is approved."
    return "Keep explicit-review until blockers are resolved."


def _sort_gateway_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            _tier_rank(str(row.get("cost_tier") or "unknown")),
            0 if "flash-lite" in str(row.get("canonical_model") or "") else 1,
            str(row.get("canonical_model") or row.get("observed_model") or ""),
        ),
    )


def _check(check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "reason": reason if not evidence else f"{reason} Evidence: {', '.join(evidence[:8])}.",
        "evidence_count": len(evidence),
        "evidence": evidence[:12],
    }


def _is_gemini_like(value: str) -> bool:
    token = str(value or "").lower()
    return "gemini-" in token


def _tier_rank(cost_tier: str) -> int:
    return COST_RANK.get(cost_tier, 99)


def _slug(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "-" for ch in str(value).lower())
    return "-".join(part for part in safe.split("-") if part)[:96] or "unknown"
