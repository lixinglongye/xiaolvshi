from __future__ import annotations

from typing import Any

from services.legal_fixture_run_plan import LegalFixtureRunPlanService
from services.model_budget import COST_TIER_RANK, TASK_GROUPS
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_catalog import model_profile
from services.model_fallback_chains import ModelFallbackChainService


class LegalFixtureModelMatrixService:
    """Build fixture-level Gemini/NewAPI model candidate ladders for cheap-first testing."""

    def __init__(
        self,
        run_plan_service: LegalFixtureRunPlanService | None = None,
        capability_matrix_service: ModelCapabilityMatrixService | None = None,
        fallback_chain_service: ModelFallbackChainService | None = None,
    ) -> None:
        self.run_plan_service = run_plan_service or LegalFixtureRunPlanService()
        self.capability_matrix_service = capability_matrix_service or ModelCapabilityMatrixService()
        self.fallback_chain_service = fallback_chain_service or ModelFallbackChainService()

    def build_matrix(self) -> dict[str, Any]:
        run_plan = self.run_plan_service.build_plan()
        capability_rows = {
            row["task"]: row
            for row in self.capability_matrix_service.build_matrix()["tasks"]
        }
        fallback_rows = {
            row["task"]: row
            for row in self.fallback_chain_service.build_chains()["chains"]
        }
        rows = [
            self._fixture_row(step, capability_rows.get(step["task"]), fallback_rows.get(step["task"]))
            for step in run_plan["steps"]
            if step["phase"] == "cheap_first"
        ]
        warnings = [row["fixture_id"] for row in rows if row["status"] != "pass"]
        return {
            "status": "warn" if warnings else "ready",
            "method": {
                "type": "legal-fixture-gemini-model-matrix",
                "notes": [
                    "Builds model candidate ladders only; it never calls NewAPI, Gemini, or app AI endpoints.",
                    "Every fixture starts from the cheap-first run-plan step.",
                    "Premium candidates remain explicit fixture-scoped escalation paths, never global defaults.",
                ],
            },
            "summary": {
                "fixture_count": len(rows),
                "pass_count": sum(1 for row in rows if row["status"] == "pass"),
                "warning_count": len(warnings),
                "cheap_first_candidate_count": sum(1 for row in rows for item in row["candidate_ladder"] if item["role"] == "cheap_first"),
                "premium_candidate_count": sum(1 for row in rows for item in row["candidate_ladder"] if item["cost_tier"] == "premium"),
                "operator_review_candidate_count": sum(
                    1
                    for row in rows
                    for item in row["candidate_ladder"]
                    if item["requires_operator_review"]
                ),
                "unknown_candidate_count": sum(1 for row in rows for item in row["candidate_ladder"] if not item["known_model"]),
            },
            "fixtures": rows,
            "warning_fixture_ids": warnings,
            "recommended_actions": self._recommended_actions(rows),
            "privacy_note": (
                "The matrix stores model IDs, fixture IDs, cost tiers, and routing notes only. "
                "It does not contain API keys, prompts, raw documents, or model outputs."
            ),
        }

    def _fixture_row(
        self,
        cheap_step: dict[str, Any],
        capability_row: dict[str, Any] | None,
        fallback_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        task = str(cheap_step["task"])
        ladder = self._candidate_ladder(cheap_step, capability_row, fallback_row)
        checks = self._checks(task, ladder)
        failed = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "fixture_id": cheap_step["fixture_id"],
            "title": cheap_step["title"],
            "task": task,
            "smoke_route": cheap_step["smoke_route"],
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "budget_mode": TASK_GROUPS.get(task, {}).get("budget_mode", "explicit"),
            "max_cost_tier": TASK_GROUPS.get(task, {}).get("max_cost_tier", "premium"),
            "runtime_default_model": capability_row.get("runtime_default_model") if capability_row else None,
            "capability_recommended_model": capability_row.get("recommended_model") if capability_row else None,
            "candidate_ladder": ladder,
            "checks": checks,
            "recommended_action": self._fixture_action(failed, warnings),
        }

    def _candidate_ladder(
        self,
        cheap_step: dict[str, Any],
        capability_row: dict[str, Any] | None,
        fallback_row: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def add(role: str, model: str | None, source: str, trigger: str, requires_review: bool = False) -> None:
            if not model:
                return
            key = (role, model)
            if key in seen:
                return
            seen.add(key)
            candidates.append(self._candidate(role, model, source, trigger, cheap_step["task"], requires_review))

        add("cheap_first", cheap_step["model"], "fixture_run_plan", "always")
        if capability_row:
            add(
                "task_recommended",
                capability_row.get("recommended_model"),
                "capability_matrix",
                "use when cheap-first fixture smoke needs review",
            )

        for step in (fallback_row or {}).get("steps", []):
            role = "premium_exception" if step["cost_tier"] == "premium" else "fallback"
            add(role, step["resolved_model"], "fallback_chain", step["trigger"], bool(step["requires_operator_review"]))

        for candidate in (capability_row or {}).get("candidates", [])[:3]:
            add(
                "capability_candidate",
                candidate["model_id"],
                "capability_matrix",
                "manual candidate for fixture-specific experiments",
            )

        candidates.sort(
            key=lambda item: (
                self._role_rank(item["role"]),
                COST_TIER_RANK.get(str(item.get("cost_tier") or "unknown"), 99),
                item["model"],
            )
        )
        return candidates

    def _candidate(
        self,
        role: str,
        model: str,
        source: str,
        trigger: str,
        task: str,
        requires_review: bool,
    ) -> dict[str, Any]:
        profile = model_profile(model)
        cost_tier = profile.cost_tier if profile else "unknown"
        max_tier = str(TASK_GROUPS.get(task, {}).get("max_cost_tier", "premium"))
        over_budget = COST_TIER_RANK.get(cost_tier, 99) > COST_TIER_RANK.get(max_tier, 99)
        premium_requires_review = cost_tier == "premium" and task not in {"pdf", "image"}
        return {
            "role": role,
            "model": model,
            "known_model": profile is not None,
            "provider": profile.provider if profile else "gateway",
            "family": profile.family if profile else "unknown",
            "status": profile.status if profile else "unknown",
            "cost_tier": cost_tier,
            "latency_tier": profile.latency_tier if profile else "unknown",
            "context_window_tokens": profile.context_window_tokens if profile else None,
            "input_usd_per_million_tokens": profile.input_usd_per_million_tokens if profile else None,
            "output_usd_per_million_tokens": profile.output_usd_per_million_tokens if profile else None,
            "over_fixture_budget": over_budget,
            "requires_operator_review": requires_review or premium_requires_review,
            "source": source,
            "trigger": trigger,
        }

    def _checks(self, task: str, ladder: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cheap_first = next((item for item in ladder if item["role"] == "cheap_first"), None)
        premium_without_review = [
            item
            for item in ladder
            if item["cost_tier"] == "premium"
            and not item["requires_operator_review"]
            and task not in {"pdf", "image"}
        ]
        unknown_default = cheap_first and not cheap_first["known_model"]
        return [
            {
                "id": "cheap-first-start",
                "status": "pass" if cheap_first else "fail",
                "reason": "Fixture has a cheap-first starting model." if cheap_first else "Fixture has no cheap-first model.",
            },
            {
                "id": "known-cheap-first",
                "status": "warn" if unknown_default else "pass",
                "reason": "Cheap-first model has local catalog pricing." if not unknown_default else "Cheap-first model is gateway-specific; verify price before using it as a default.",
            },
            {
                "id": "premium-review-boundary",
                "status": "pass" if not premium_without_review else "fail",
                "reason": "Premium candidates outside explicit PDF/image exceptions require operator review."
                if not premium_without_review
                else "A premium candidate can run without operator review.",
            },
        ]

    def _fixture_action(self, failed: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
        if failed:
            return f"Fix model ladder before fixture runs: {', '.join(item['id'] for item in failed)}."
        if warnings:
            return f"Review model ladder warning: {', '.join(item['id'] for item in warnings)}."
        return "Fixture model ladder is aligned with cheap-first policy."

    def _recommended_actions(self, rows: list[dict[str, Any]]) -> list[str]:
        warning_rows = [row for row in rows if row["status"] != "pass"]
        if warning_rows:
            return [
                f"Review fixture model ladder for {row['fixture_id']}: {row['recommended_action']}"
                for row in warning_rows[:8]
            ]
        return [
            "Use cheap_first candidates for fixture-run-plan batches.",
            "Use task_recommended or fallback candidates only after fixture-run-report marks a selected fixture for review.",
        ]

    def _role_rank(self, role: str) -> int:
        return {
            "cheap_first": 0,
            "task_recommended": 1,
            "fallback": 2,
            "capability_candidate": 3,
            "premium_exception": 4,
        }.get(role, 9)
