from __future__ import annotations

from typing import Any


REQUIRED_SIGNAL_KEYS = (
    "model_ops_readiness",
    "cheap_first_calibration",
    "gemini_variant_matrix",
    "gemini_cheap_first_route_preflight",
    "catalog_source_audit",
    "route_quality_budget",
    "cheap_first_escalation_budget",
    "failure_upgrade_budget",
    "price_refresh_monitor",
    "model_ops_performance_budget",
    "legal_fixture_cheap_first_benchmark_gate",
    "legal_fixture_cheap_first_default_promotion_packet",
    "legal_fixture_cheap_first_regression_budget",
    "legal_benchmark_risk_bridge",
    "user_need_release_bridge",
)


class ModelOpsCheapFirstReleaseDecisionService:
    """Combine existing ModelOps signals into one cheap-first release decision."""

    def build_decision(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        checks = [
            self._check_signal(
                "model-ops-readiness-review",
                "model_ops_readiness",
                data.get("model_ops_readiness"),
                fail_reason="ModelOps readiness has required missing or blocking release signals.",
                warn_reason="ModelOps readiness requires maintainer review before default changes.",
            ),
            self._check_signal(
                "cheap-first-calibration",
                "cheap_first_calibration",
                data.get("cheap_first_calibration"),
                fail_reason="Cheap-first calibration is failing or missing.",
                warn_reason="Cheap-first calibration needs maintainer review.",
            ),
            self._check_signal(
                "gemini-variant-matrix-review",
                "gemini_variant_matrix",
                data.get("gemini_variant_matrix"),
                fail_reason="Gemini variant matrix is failing or missing.",
                warn_reason="Gemini variant matrix has catalog-review or unpriced-model warnings.",
            ),
            self._check_signal(
                "gemini-cheap-first-route-preflight-review",
                "gemini_cheap_first_route_preflight",
                data.get("gemini_cheap_first_route_preflight"),
                fail_reason="Gemini cheap-first route preflight has unknown, blocked, or unsafe default-route findings.",
                warn_reason="Gemini cheap-first route preflight needs maintainer review for preview, premium, media, alias, or pricing boundaries.",
            ),
            self._check_signal(
                "catalog-source-audit-review",
                "catalog_source_audit",
                data.get("catalog_source_audit"),
                fail_reason="Gemini catalog source audit has blocking source/default drift.",
                warn_reason="Gemini catalog source audit has source or pricing watchlist warnings.",
            ),
            self._check_signal(
                "route-quality-budget-review",
                "route_quality_budget",
                data.get("route_quality_budget"),
                fail_reason="Route quality budget has blocking cheap-first quality gaps.",
                warn_reason="Route quality budget has maintainer-review warnings.",
            ),
            self._check_signal(
                "cheap-first-escalation-budget-review",
                "cheap_first_escalation_budget",
                data.get("cheap_first_escalation_budget"),
                fail_reason="Cheap-first escalation budget has runaway retry, wasted spend, or premium-review blockers.",
                warn_reason="Cheap-first escalation budget needs maintainer review before default changes.",
            ),
            self._check_signal(
                "failure-upgrade-budget-review",
                "failure_upgrade_budget",
                data.get("failure_upgrade_budget"),
                fail_reason="Failure upgrade budget has unsafe retry, premium quota, or attempt-budget blockers.",
                warn_reason="Failure upgrade budget needs maintainer review before default changes.",
            ),
            self._check_signal(
                "price-refresh-review",
                "price_refresh_monitor",
                data.get("price_refresh_monitor"),
                fail_reason="Gemini/NewAPI price refresh monitor has blocking drift.",
                warn_reason="Gemini/NewAPI price refresh monitor needs price or model metadata review.",
            ),
            self._check_signal(
                "performance-budget-review",
                "model_ops_performance_budget",
                data.get("model_ops_performance_budget"),
                fail_reason="ModelOps performance budget has blocking load or timeout regressions.",
                warn_reason="ModelOps performance budget has observation or timeout warnings.",
            ),
            self._check_signal(
                "legal-fixture-cheap-first-benchmark-gate",
                "legal_fixture_cheap_first_benchmark_gate",
                data.get("legal_fixture_cheap_first_benchmark_gate"),
                fail_reason="Legal fixture cheap-first benchmark gate has blocked fixture, document, fact-consistency, or calibration evidence.",
                warn_reason="Legal fixture benchmark evidence needs fixture, document, fact-consistency, or calibration review before default promotion.",
            ),
            self._check_signal(
                "legal-fixture-default-promotion-packet",
                "legal_fixture_cheap_first_default_promotion_packet",
                data.get("legal_fixture_cheap_first_default_promotion_packet"),
                fail_reason="Legal fixture default promotion packet is blocked by fixture, document, fact-consistency, or calibration evidence.",
                warn_reason="Legal fixture default promotion packet is not ready or still needs maintainer review.",
            ),
            self._check_signal(
                "legal-fixture-cheap-first-regression-budget",
                "legal_fixture_cheap_first_regression_budget",
                data.get("legal_fixture_cheap_first_regression_budget"),
                fail_reason="Legal fixture regression budget is blocked by fixture regression, document runbook, benchmark gate, or promotion packet evidence.",
                warn_reason="Legal fixture regression budget needs baseline/current cheap-first fixture results or maintainer review before default promotion.",
            ),
            self._check_signal(
                "legal-benchmark-risk-bridge",
                "legal_benchmark_risk_bridge",
                data.get("legal_benchmark_risk_bridge"),
                fail_reason="Legal benchmark risk bridge has blocked legal route evidence.",
                warn_reason="Legal benchmark risk bridge requires review for public benchmark license, premium exception, or route watchlist evidence.",
            ),
            self._check_signal(
                "user-need-release-bridge",
                "user_need_release_bridge",
                data.get("user_need_release_bridge"),
                fail_reason="User-need release bridge has high-priority implementation or Gemini route blockers.",
                warn_reason="User-need release bridge requires review for public benchmark license, premium exception, partial coverage, or lower-priority blocker evidence.",
            ),
        ]
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "fail" if blocking else ("review_required" if warnings else "pass")
        release_decision = self._release_decision(status)
        warning_ids = [item for check in warnings for item in check["source_warning_ids"]]
        blocking_ids = [item for check in blocking for item in check["source_blocking_ids"]]

        return {
            "status": status,
            "release_decision": release_decision,
            "method": {
                "type": "model-ops-cheap-first-release-decision",
                "notes": [
                    "Consumes existing ModelOps evidence instead of re-running model, gateway, pricing, or benchmark checks.",
                    "Treats ModelOps readiness as the aggregate upstream release signal and does not feed this packet back into readiness.",
                    "Requires metadata-only legal fixture benchmark, default-promotion packet, and legal benchmark route-risk evidence before promoting legal-task defaults.",
                    "Requires a low-resource legal fixture regression budget so cheap-first legal defaults are reviewed against baseline/current fixture drift before default changes.",
                    "Requires user-need release bridge evidence so product priorities, implementation gaps, and Gemini route coverage stay attached to cheap-first default decisions.",
                    "Blocks cheap-first default changes only when a required source signal fails.",
                    "Keeps catalog-review, unpriced-model, legal fixture not-run/not-ready, legal benchmark watchlist, performance-observation, and other warn states as maintainer review.",
                    "Does not call Gemini, NewAPI, OpenAI, Google, or any gateway.",
                ],
            },
            "summary": {
                "required_signal_count": len(REQUIRED_SIGNAL_KEYS),
                "attached_signal_count": sum(1 for key in REQUIRED_SIGNAL_KEYS if isinstance(data.get(key), dict)),
                "passing_signal_count": sum(1 for check in checks if check["status"] == "pass"),
                "warning_signal_count": len(warnings),
                "blocking_signal_count": len(blocking),
                "source_warning_id_count": len(warning_ids),
                "source_blocking_id_count": len(blocking_ids),
                "current_cheap_first_default_allowed": status != "fail",
                "default_change_allowed": status == "pass",
                "default_promotion_blocked": bool(blocking),
                "maintainer_review_required": bool(warnings),
                "newapi_called": False,
                "raw_payload_echoed": False,
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "source_blocking_ids": blocking_ids,
            "source_warning_ids": warning_ids,
            "promotion_policy": {
                "current_default_action": release_decision["current_default_action"],
                "default_change_policy": release_decision["default_change_policy"],
                "premium_exception_policy": "Premium, Pro, preview, and unknown Gemini-like models require explicit exception evidence before default promotion.",
                "unknown_model_policy": "Unknown Gemini-like ids can stay explicit-only but cannot become high-frequency defaults without catalog source and pricing review.",
                "legal_fixture_policy": "Legal fixture, document benchmark, fact-consistency, and calibration evidence can support legal-task defaults only through the metadata-only benchmark gate and promotion packet.",
                "legal_fixture_regression_policy": "Baseline/current legal fixture regression budget evidence must be ready or reviewed before cheap-first legal default changes.",
                "legal_benchmark_policy": "Legal benchmark route-risk bridge must be pass before new legal-task defaults are promoted; watchlist or license-review evidence requires maintainer review.",
                "user_need_policy": "High-priority user needs with blocked implementation or route evidence block default changes; license, premium exception, partial coverage, and medium or low priority blockers require maintainer review.",
            },
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "network_called": False,
                "output_scope": "source signal statuses, check ids, counts, and cheap-first release decision metadata only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "public_benchmark_scores_included": False,
                "external_adoption_included": False,
                "twenty_four_hour_completion_claimed": False,
                "production_accuracy_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_readiness.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_modelops_legal_fixture_default_promotion_packet.py tests/test_model_ops_legal_benchmark_risk_bridge.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _check_signal(
        self,
        check_id: str,
        source_key: str,
        value: Any,
        *,
        fail_reason: str,
        warn_reason: str,
    ) -> dict[str, Any]:
        data = value if isinstance(value, dict) else {}
        source_status = str(data.get("status") or "").strip().lower()
        source_blocking_ids = self._list(data.get("blocking_check_ids"))
        source_warning_ids = self._list(data.get("warning_check_ids"))
        if not data:
            status = "fail"
            decision_effect = "blocks_default_changes"
            reason = fail_reason
        elif source_status in {"fail", "failed", "blocked", "error"} or source_blocking_ids:
            status = "fail"
            decision_effect = "blocks_default_changes"
            reason = fail_reason
        elif source_status in {
            "warn",
            "warning",
            "review_required",
            "manual_review",
            "needs_review",
            "not_ready",
            "not_run",
            "ready_with_watchlist",
            "ready_for_maintainer_review",
        } or source_warning_ids:
            status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = warn_reason
        elif source_status in {"pass", "ready", "ok", "success"}:
            status = "pass"
            decision_effect = "supports_current_defaults"
            reason = "Source signal supports keeping current cheap-first defaults."
        else:
            status = "warn"
            decision_effect = "requires_maintainer_review"
            reason = "Source signal has an unrecognized status and needs maintainer review."

        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        return {
            "id": check_id,
            "source_key": source_key,
            "status": status,
            "source_status": source_status or "missing",
            "decision_effect": decision_effect,
            "source_blocking_ids": source_blocking_ids,
            "source_warning_ids": source_warning_ids,
            "source_summary": {
                "blocking_count": self._safe_int(summary.get("blocking_count") or summary.get("blocking_check_count")),
                "warning_count": self._safe_int(summary.get("warning_count") or summary.get("warning_check_count")),
                "catalog_review_count": self._safe_int(summary.get("catalog_review_count")),
                "missing_pricing_count": self._safe_int(summary.get("missing_pricing_count")),
                "slow_observation_count": self._safe_int(summary.get("slow_observation_count")),
                "not_run_count": self._safe_int(summary.get("not_run_count")),
                "not_ready_count": self._safe_int(summary.get("not_ready_count")),
                "ready_for_review_count": self._safe_int(summary.get("ready_for_review_count")),
                "review_required_count": self._safe_int(summary.get("review_required_count")),
                "blocked_count": self._safe_int(summary.get("blocked_count")),
                "selected_fixture_count": self._safe_int(summary.get("selected_fixture_count")),
                "evaluated_fixture_count": self._safe_int(summary.get("evaluated_fixture_count")),
                "default_evidence_allowed_count": self._safe_int(summary.get("default_evidence_allowed_count")),
                "promotion_item_count": self._safe_int(summary.get("promotion_item_count")),
                "linked_calibration_task_count": self._safe_int(summary.get("linked_calibration_task_count")),
                "calibration_blocking_count": self._safe_int(summary.get("calibration_blocking_count")),
                "calibration_warning_count": self._safe_int(summary.get("calibration_warning_count")),
                "document_benchmark_failed_case_count": self._safe_int(summary.get("document_benchmark_failed_case_count")),
                "document_benchmark_blocking_case_count": self._safe_int(
                    summary.get("document_benchmark_blocking_case_count")
                ),
                "fact_consistency_blocking_case_count": self._safe_int(
                    summary.get("fact_consistency_blocking_case_count")
                ),
                "route_review_count": self._safe_int(summary.get("route_review_count")),
                "user_need_review_count": self._safe_int(summary.get("user_need_review_count")),
                "need_count": self._safe_int(summary.get("need_count")),
                "high_priority_need_count": self._safe_int(summary.get("high_priority_need_count")),
                "implementation_blocked_count": self._safe_int(summary.get("implementation_blocked_count")),
                "high_priority_implementation_blocked_count": self._safe_int(
                    summary.get("high_priority_implementation_blocked_count")
                ),
                "route_unmapped_need_count": self._safe_int(summary.get("route_unmapped_need_count")),
                "high_priority_route_blocked_count": self._safe_int(summary.get("high_priority_route_blocked_count")),
                "high_priority_route_protected_count": self._safe_int(
                    summary.get("high_priority_route_protected_count")
                ),
                "public_benchmark_review_need_count": self._safe_int(
                    summary.get("public_benchmark_review_need_count")
                ),
                "premium_exception_review_need_count": self._safe_int(
                    summary.get("premium_exception_review_need_count")
                ),
                "default_change_blocked_need_count": self._safe_int(
                    summary.get("default_change_blocked_need_count")
                ),
                "default_change_review_need_count": self._safe_int(
                    summary.get("default_change_review_need_count")
                ),
                "premium_exception_route_count": self._safe_int(summary.get("premium_exception_route_count")),
                "benchmark_license_watch_count": self._safe_int(summary.get("benchmark_license_watch_count")),
                "default_change_queue_item_count": self._safe_int(summary.get("default_change_queue_item_count")),
            },
            "reason": reason,
        }

    def _release_decision(self, status: str) -> dict[str, str]:
        if status == "fail":
            return {
                "status": "blocked",
                "label": "block cheap-first default changes",
                "current_default_action": "hold_current_defaults_and_fix_blockers",
                "default_change_policy": "do_not_promote_new_defaults_until_blocking_checks_pass",
            }
        if status == "review_required":
            return {
                "status": "review_required",
                "label": "maintainer review before default changes",
                "current_default_action": "keep_current_cheap_first_defaults",
                "default_change_policy": "allow_explicit_only_experiments_but_require_review_before_default_promotion",
            }
        return {
            "status": "ready",
            "label": "keep cheap-first defaults",
            "current_default_action": "keep_current_cheap_first_defaults",
            "default_change_policy": "default_changes_may_proceed_after_standard_release_validation",
        }

    def _recommended_actions(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        if blocking:
            actions.append("Resolve blocking ModelOps cheap-first signals before changing default models.")
            actions.extend(f"Fix blocking signal: {check['source_key']}." for check in blocking)
        if warnings:
            actions.append("Keep current cheap-first defaults and complete maintainer review before promoting new Gemini variants.")
            actions.extend(f"Review warning signal: {check['source_key']}." for check in warnings)
        if not actions:
            actions.append("Keep current cheap-first defaults and rerun this packet before any model default change.")
        return self._dedupe(actions)

    def _list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if str(item).strip()]

    def _safe_int(self, value: Any) -> int:
        if isinstance(value, bool):
            return 0
        if isinstance(value, int):
            return max(0, value)
        return 0

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result
