from __future__ import annotations

import re
from typing import Any

from services import model_catalog
from services.model_catalog import ModelProfile
from services.model_catalog_candidate_patch_plan import ModelCatalogCandidatePatchPlanService
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_default_candidate_selector import (
    COST_RANK,
    TASK_POLICIES,
    ModelDefaultCandidateSelectorService,
)


SENSITIVE_VALUE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization",
    re.IGNORECASE,
)
FORBIDDEN_FIELD_PATTERN = re.compile(
    r"authorization|api[_-]?key|app_ai_key|headers|messages|prompt|raw_output|raw_response|"
    r"response_text|output_text|generated_text|candidate_text|document_text|legal_text|payload",
    re.IGNORECASE,
)
GEMINI_MODEL_ID_PATTERN = re.compile(r"(^|[:/_-])gemini([:/_-]|-\d|\d|\b)")


class ModelCatalogCandidateImpactReplayService:
    """Replay candidate Gemini catalog profiles against the cheap-first selector."""

    def __init__(self, patch_plan_service: ModelCatalogCandidatePatchPlanService | None = None) -> None:
        self.patch_plan_service = patch_plan_service or ModelCatalogCandidatePatchPlanService()

    def build_replay(self, payload: dict[str, Any] | None = None, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        signal_data = signals if isinstance(signals, dict) else {}
        patch_plan = self._patch_plan(data, signal_data)
        forbidden_field_count = self._forbidden_field_count(data)
        profile_sources = [
            *self._profile_sources_from_payload(data),
            *self._profile_sources_from_patch_plan(patch_plan),
        ]
        candidate_rows = [self._candidate_row(source) for source in profile_sources[:80]]
        accepted_profiles = [row["virtual_profile"] for row in candidate_rows if row["virtual_profile"]]
        accepted_profiles = [profile for profile in accepted_profiles if isinstance(profile, ModelProfile)]
        virtual_catalog = (*accepted_profiles, *model_catalog.GEMINI_MODEL_CATALOG)
        baseline_selector = ModelDefaultCandidateSelectorService()
        replay_selector = ModelDefaultCandidateSelectorService(catalog=virtual_catalog)
        task_rows = [
            self._task_impact_row(task, baseline_selector, replay_selector)
            for task in TASK_POLICIES
        ]
        promoted_rows = [row for row in task_rows if row["selected_model_changed"] and row["cheap_first_would_promote"]]
        blocked_rows = [row for row in candidate_rows if row["candidate_status"] == "blocked"]
        review_rows = [row for row in candidate_rows if row["candidate_status"] == "review_required"]
        ready_rows = [row for row in candidate_rows if row["candidate_status"] == "accepted_for_replay"]
        checks = self._checks(candidate_rows, task_rows, forbidden_field_count, blocked_rows, review_rows)
        blocking_checks = [check for check in checks if check["status"] == "fail"]
        warning_checks = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking_checks else ("monitor_only" if not candidate_rows else ("review_required" if warning_checks else "ready"))

        return {
            "id": "model-catalog-candidate-impact-replay",
            "title": "Model catalog candidate impact replay",
            "status": status,
            "method": {
                "type": "model-catalog-candidate-impact-replay",
                "notes": [
                    "Builds an in-memory virtual Gemini catalog from sanitized candidate profiles and candidate patch rows.",
                    "Compares current cheap-first selector output with virtual-catalog selector output for each task.",
                    "Does not edit model_catalog.py, write environment files, call a gateway, or run live probes.",
                    "Candidate impact is replay evidence only; maintainer review is still required before catalog or default changes.",
                ],
            },
            "summary": {
                "candidate_profile_count": len(candidate_rows),
                "accepted_virtual_profile_count": len(ready_rows),
                "review_required_candidate_count": len(review_rows),
                "blocked_candidate_count": len(blocked_rows),
                "task_impact_count": len(task_rows),
                "recommended_change_count": sum(1 for row in task_rows if row["selected_model_changed"]),
                "cheap_first_would_promote_count": len(promoted_rows),
                "high_frequency_change_count": sum(
                    1 for row in task_rows if row["selected_model_changed"] and row["high_frequency"]
                ),
                "forbidden_payload_field_count": forbidden_field_count,
                "patch_plan_status": str(patch_plan.get("status") or "missing"),
                "virtual_catalog_model_count": len(virtual_catalog),
                "baseline_catalog_model_count": len(model_catalog.GEMINI_MODEL_CATALOG),
                "configuration_written": False,
                "catalog_file_written": False,
                "env_file_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
                "secret_value_included": False,
            },
            "candidate_rows": [self._candidate_row_for_api(row) for row in candidate_rows],
            "task_impact_rows": task_rows,
            "selector_delta": {
                "changed_tasks": [row["task"] for row in task_rows if row["selected_model_changed"]],
                "cheap_first_promoted_tasks": [row["task"] for row in promoted_rows],
                "high_frequency_changed_tasks": [
                    row["task"] for row in task_rows if row["selected_model_changed"] and row["high_frequency"]
                ],
            },
            "capability_matrix_coverage": ModelCapabilityMatrixService(
                candidate_selector=replay_selector,
                catalog=virtual_catalog,
            ).build_matrix()["coverage"],
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking_checks],
            "warning_check_ids": [check["id"] for check in warning_checks],
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, promoted_rows, candidate_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "candidate_profiles_sanitized": True,
                "configuration_written": False,
                "catalog_file_written": False,
                "env_file_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "sanitized candidate model ids, lifecycle/cost metadata, selector deltas, task ids, and review actions only",
            },
            "claim_boundary": {
                "automatic_catalog_edit_claimed": False,
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
                "production_quality_claimed": False,
                "twenty_four_hour_completion_claimed": False,
                "hundred_update_completion_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_catalog_candidate_impact_replay.py tests/test_model_default_candidate_selector.py tests/test_model_capability_matrix.py -q",
                "python -m pytest tests/test_model_catalog_candidate_patch_plan.py tests/test_model_ops_readiness.py tests/test_model_ops_cheap_first_priority_queue.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _patch_plan(self, data: dict[str, Any], signals: dict[str, Any]) -> dict[str, Any]:
        for key in ("catalog_candidate_patch_plan", "candidate_patch_plan", "source_patch_plan"):
            value = data.get(key) or signals.get(key)
            if isinstance(value, dict) and isinstance(value.get("summary"), dict):
                return value
        return self.patch_plan_service.build_plan(data, signals=signals)

    def _profile_sources_from_payload(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        sources: list[dict[str, Any]] = []
        value = data.get("candidate_profiles")
        if isinstance(value, list):
            sources.extend(item for item in value if isinstance(item, dict))
        for key in ("candidate_patch_rows", "candidate_patches"):
            rows = data.get(key)
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, dict):
                        sources.append(row)
        return sources

    def _profile_sources_from_patch_plan(self, patch_plan: dict[str, Any]) -> list[dict[str, Any]]:
        rows = patch_plan.get("candidate_patch_rows")
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    def _candidate_row(self, source: dict[str, Any]) -> dict[str, Any]:
        forbidden_count = self._forbidden_field_count(source)
        profile_source = source.get("proposed_profile_stub") if isinstance(source.get("proposed_profile_stub"), dict) else source
        profile, reject_reason = self._profile_from_source(profile_source)
        reason_codes = self._reason_codes(profile, reject_reason, forbidden_count)
        candidate_status = self._candidate_status(profile, reason_codes)
        safe_model_id = profile.id if profile else _safe_text(profile_source.get("id") or source.get("model_id"))
        return {
            "id": f"candidate-impact-{_safe_id(safe_model_id or 'unknown')}",
            "observed_model": _safe_text(source.get("observed_model") or profile_source.get("id") or source.get("model_id")),
            "model_id": safe_model_id,
            "candidate_status": candidate_status,
            "virtual_profile": profile if candidate_status != "blocked" else None,
            "virtual_profile_accepted": profile is not None and candidate_status != "blocked",
            "default_candidate_allowed": self._default_candidate_allowed(profile),
            "cost_tier": profile.cost_tier if profile else "unknown",
            "latency_tier": profile.latency_tier if profile else "unknown",
            "catalog_status": profile.status if profile else "missing",
            "pricing_status": self._pricing_status(profile),
            "capabilities": list(profile.capabilities) if profile else [],
            "reason_codes": reason_codes,
            "recommended_action": self._candidate_action(candidate_status, profile, reason_codes),
        }

    def _candidate_row_for_api(self, row: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in row.items() if key != "virtual_profile"}

    def _profile_from_source(self, source: dict[str, Any]) -> tuple[ModelProfile | None, str | None]:
        model_id = self._candidate_model_id(source.get("id") or source.get("model_id") or source.get("proposed_catalog_id"))
        if not model_id:
            return None, "missing-or-sensitive-model-id"
        if not self._is_gemini_like(model_id):
            return None, "non-gemini-model-id"
        capabilities = self._capabilities(source.get("capabilities"), model_id)
        if not capabilities:
            return None, "missing-capabilities"
        return (
            ModelProfile(
                id=model_id,
                provider=_safe_text(source.get("provider") or "google") or "google",
                family=_safe_text(source.get("family") or "gemini") or "gemini",
                cost_tier=self._safe_choice(source.get("cost_tier"), {"lowest", "low", "medium", "premium", "unknown"}, "unknown"),
                latency_tier=self._safe_choice(
                    source.get("latency_tier"),
                    {"fastest", "fast", "medium", "slower", "unknown"},
                    "unknown",
                ),
                capabilities=tuple(capabilities),
                best_for=tuple(self._safe_string_list(source.get("best_for")) or ["candidate-impact-replay"]),
                notes="Virtual candidate profile for metadata-only selector impact replay.",
                input_usd_per_million_tokens=self._safe_float(source.get("input_usd_per_million_tokens")),
                output_usd_per_million_tokens=self._safe_float(source.get("output_usd_per_million_tokens")),
                output_usd_per_image=self._safe_float(source.get("output_usd_per_image")),
                pricing_note="Virtual replay metadata; maintainers must verify official and gateway pricing before catalog edits.",
                status=self._safe_choice(source.get("status"), {"stable", "preview", "deprecated", "review_required"}, "review_required"),
                context_window_tokens=self._safe_int(source.get("context_window_tokens")),
                pricing_source_url="https://ai.google.dev/gemini-api/docs/pricing",
            ),
            None,
        )

    def _task_impact_row(
        self,
        task: str,
        baseline_selector: ModelDefaultCandidateSelectorService,
        replay_selector: ModelDefaultCandidateSelectorService,
    ) -> dict[str, Any]:
        baseline = baseline_selector.recommendation(task)
        replay = replay_selector.recommendation(task)
        replay_candidate = next(
            (row for row in replay["candidates"] if row["model_id"] == replay["selected_model"]),
            {},
        )
        selected_changed = baseline["selected_model"] != replay["selected_model"]
        return {
            "id": f"candidate-impact-task-{task}",
            "task": task,
            "baseline_model": baseline["selected_model"],
            "replay_model": replay["selected_model"],
            "selected_model_changed": selected_changed,
            "cheap_first_would_promote": selected_changed and replay_candidate.get("default_eligible") is True,
            "high_frequency": bool(replay["high_frequency"]),
            "route_mode": replay["route_mode"],
            "baseline_cost_tier": baseline.get("selected_cost_tier"),
            "replay_cost_tier": replay_candidate.get("cost_tier") or replay.get("selected_cost_tier"),
            "replay_pricing_status": replay_candidate.get("pricing_status") or "unknown",
            "replay_catalog_status": replay_candidate.get("catalog_status") or "unknown",
            "eligible_candidate_count": replay["eligible_candidate_count"],
            "candidate_count": replay["candidate_count"],
            "reason": self._task_reason(selected_changed, replay_candidate, replay),
        }

    def _reason_codes(self, profile: ModelProfile | None, reject_reason: str | None, forbidden_count: int) -> list[str]:
        codes: list[str] = []
        if forbidden_count:
            codes.append("forbidden-payload-fields")
        if reject_reason:
            codes.append(reject_reason)
        if not profile:
            return codes or ["candidate-rejected"]
        if profile.status != "stable":
            codes.append("candidate-lifecycle-review-required")
        if self._pricing_status(profile) not in {"token_priced", "image_priced"}:
            codes.append("candidate-pricing-review-required")
        if profile.cost_tier in {"medium", "premium", "unknown"}:
            codes.append("candidate-cost-review-required")
        if "image" in profile.capabilities:
            codes.append("media-route-explicit-only")
        if self._default_candidate_allowed(profile):
            codes.append("virtual-cheap-first-candidate")
        return _dedupe(codes)

    def _candidate_status(self, profile: ModelProfile | None, reason_codes: list[str]) -> str:
        if not profile or any(code in {"forbidden-payload-fields", "missing-or-sensitive-model-id"} for code in reason_codes):
            return "blocked"
        if self._default_candidate_allowed(profile):
            return "accepted_for_replay"
        return "review_required"

    def _candidate_action(self, status: str, profile: ModelProfile | None, reason_codes: list[str]) -> str:
        if status == "blocked":
            return "discard_candidate_and_resubmit_sanitized_metadata"
        if status == "accepted_for_replay":
            return "review_selector_delta_before_catalog_patch"
        if profile and "image" in profile.capabilities:
            return "keep_media_candidate_explicit_only_until_review"
        if any("pricing" in code for code in reason_codes):
            return "verify_official_and_gateway_pricing_before_replay_promotion"
        if any("lifecycle" in code for code in reason_codes):
            return "confirm_stable_lifecycle_before_default_review"
        return "complete_maintainer_review_before_catalog_or_default_change"

    def _default_candidate_allowed(self, profile: ModelProfile | None) -> bool:
        if not profile:
            return False
        return (
            profile.status == "stable"
            and self._pricing_status(profile) == "token_priced"
            and COST_RANK.get(profile.cost_tier, 99) <= COST_RANK.get("low", 99)
            and "text" in profile.capabilities
            and "json" in profile.capabilities
            and "image" not in profile.capabilities
        )

    def _checks(
        self,
        candidate_rows: list[dict[str, Any]],
        task_rows: list[dict[str, Any]],
        forbidden_field_count: int,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        return [
            {
                "id": "sanitized-candidate-profiles",
                "status": "fail" if forbidden_field_count or blocked_rows else "pass",
                "reason": "Candidate input contains forbidden fields or rejected model ids."
                if forbidden_field_count or blocked_rows
                else "Candidate input is limited to sanitized model metadata.",
            },
            {
                "id": "candidate-profiles-present",
                "status": "pass",
                "reason": f"Replayed {len(candidate_rows)} candidate profiles." if candidate_rows else "No candidate profiles were supplied; replay is monitor-only.",
            },
            {
                "id": "candidate-review-required",
                "status": "warn" if review_rows else "pass",
                "reason": f"{len(review_rows)} candidate profiles need lifecycle, price, media, or capability review."
                if review_rows
                else "No candidate review-only rows are blocking replay evidence.",
            },
            {
                "id": "cheap-first-selector-impact",
                "status": "pass" if not candidate_rows or any(row["cheap_first_would_promote"] for row in task_rows) else "warn",
                "reason": "At least one task would move to a cheap-first virtual candidate."
                if any(row["cheap_first_would_promote"] for row in task_rows)
                else "No candidate replay impact is available yet."
                if not candidate_rows
                else "No task would move to a cheap-first virtual candidate.",
            },
            {
                "id": "no-catalog-or-config-write",
                "status": "pass",
                "reason": "Replay uses in-memory catalog data only and writes no files, configuration, approvals, or traffic state.",
            },
        ]

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        promoted_rows: list[dict[str, Any]],
        candidate_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocked_rows:
            return [
                "Discard blocked candidate payload fields and resubmit sanitized model metadata only.",
                "Do not use blocked candidate rows for catalog patch or default review.",
            ]
        if promoted_rows:
            return [
                "Review official model list, pricing, lifecycle, capabilities, and gateway probe evidence before editing the catalog.",
                "Use the impacted task list to prioritize cheap-first candidate review, not to auto-promote defaults.",
            ]
        if review_rows:
            return [
                "Complete lifecycle, pricing, media-route, and capability review before using candidates as cheap-first defaults.",
                "Keep review-only candidates explicit-only until replay and release evidence pass.",
            ]
        if candidate_rows:
            return ["Candidate replay completed with no selector changes; keep current cheap-first defaults."]
        return ["Submit sanitized candidate profiles or observed Gemini model ids before replaying catalog impact."]

    def _task_reason(self, changed: bool, replay_candidate: dict[str, Any], replay: dict[str, Any]) -> str:
        if changed and replay_candidate.get("default_eligible"):
            return f"{replay['task']} would use {replay['selected_model']} because it is the cheapest eligible virtual candidate."
        if changed:
            return f"{replay['task']} selector changed under the virtual catalog and needs maintainer review."
        return f"{replay['task']} stays on {replay['selected_model']} under the virtual catalog."

    def _pricing_status(self, profile: ModelProfile | None) -> str:
        if not profile:
            return "unknown"
        if profile.output_usd_per_image is not None:
            return "image_priced"
        if profile.input_usd_per_million_tokens is not None and profile.output_usd_per_million_tokens is not None:
            return "token_priced"
        if profile.input_usd_per_million_tokens is not None or profile.output_usd_per_million_tokens is not None:
            return "partial_token_priced"
        return "missing"

    def _candidate_model_id(self, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        text = value.strip().lower()[:180]
        if not text or SENSITIVE_VALUE_PATTERN.search(text):
            return None
        text = text.rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        return re.sub(r"[^a-z0-9_.-]+", "-", text).strip("-") or None

    def _capabilities(self, value: Any, model_id: str) -> list[str]:
        capabilities = self._safe_string_list(value)
        if capabilities:
            return capabilities
        if "image" in model_id:
            return ["image"]
        inferred = ["text", "json"]
        if "flash-lite" in model_id:
            inferred.extend(["vision", "ocr", "classification"])
        if "ground" in model_id:
            inferred.append("grounding")
        if "agent" in model_id:
            inferred.append("agentic")
        return _dedupe(inferred)

    def _safe_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        result: list[str] = []
        for item in value[:40]:
            text = _safe_text(item)
            if text:
                result.append(text)
        return _dedupe(result)

    def _safe_choice(self, value: Any, allowed: set[str], fallback: str) -> str:
        text = _safe_text(value).lower()
        return text if text in allowed else fallback

    def _safe_float(self, value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            return round(max(0.0, float(value)), 6)
        except (TypeError, ValueError):
            return None

    def _safe_int(self, value: Any) -> int | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return None

    def _forbidden_field_count(self, value: Any) -> int:
        return min(20, len(self._forbidden_hits(value)))

    def _forbidden_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if FORBIDDEN_FIELD_PATTERN.search(str(key)):
                    hits.append("forbidden-field")
                    continue
                hits.extend(self._forbidden_hits(child))
                if len(hits) >= 20:
                    return hits[:20]
        elif isinstance(value, list):
            for child in value[:50]:
                hits.extend(self._forbidden_hits(child))
                if len(hits) >= 20:
                    return hits[:20]
        elif isinstance(value, str) and SENSITIVE_VALUE_PATTERN.search(value[:4096]):
            hits.append("sensitive-value")
        return hits[:20]

    def _is_gemini_like(self, model_id: str) -> bool:
        lowered = model_id.lower()
        if "not-gemini" in lowered or "non-gemini" in lowered:
            return False
        return bool(GEMINI_MODEL_ID_PATTERN.search(lowered))


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if SENSITIVE_VALUE_PATTERN.search(text):
        return ""
    return re.sub(r"[\r\n\t]+", " ", text)[:240]


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:96] or "unknown"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
