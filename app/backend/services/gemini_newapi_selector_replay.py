from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.gemini_newapi_model_selector import GeminiNewapiModelSelectorService


COST_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3, "unverified": 99}


@dataclass(frozen=True)
class SelectorReplayScenario:
    id: str
    task: str
    explicit_model: str | None
    observed_models: tuple[str, ...]
    expected_decision: str
    max_cost_tier: str
    expected_selector_status: str
    rationale: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["observed_models"] = list(self.observed_models)
        return data


class GeminiNewapiSelectorReplayService:
    """Replay Gemini/NewAPI selector scenarios without calling the gateway."""

    def __init__(self, selector_service: GeminiNewapiModelSelectorService | None = None) -> None:
        self.selector_service = selector_service or GeminiNewapiModelSelectorService()

    def run_replay(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        scenarios = self._scenarios(data.get("scenarios"))
        results = [self._run_scenario(scenario) for scenario in scenarios]
        failed = [item for item in results if item["status"] == "fail"]
        warnings = [item for item in results if item["status"] == "warn"]

        return {
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "summary": {
                "scenario_count": len(results),
                "pass_count": sum(1 for item in results if item["status"] == "pass"),
                "warn_count": len(warnings),
                "fail_count": len(failed),
                "cheap_first_pass_count": sum(
                    1 for item in results if item["actual"]["decision"] == "cheap_first_ready" and item["status"] == "pass"
                ),
                "balanced_route_count": sum(1 for item in results if item["actual"]["decision"] == "balanced_after_precheck"),
                "premium_exception_count": sum(1 for item in results if item["actual"]["premium_exception"] is True),
                "catalog_review_count": sum(1 for item in results if item["actual"]["selector_status"] == "needs_catalog_review"),
                "raw_payload_echoed": False,
            },
            "method": {
                "type": "deterministic-gemini-newapi-selector-replay",
                "notes": [
                    "Replays selector scenarios without NewAPI calls.",
                    "Checks selected model, canonical id, cost tier, decision, and catalog-review status.",
                    "Keeps prompts, legal text, model output, credentials, and emails out of the replay payload.",
                ],
            },
            "replay_results": results,
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "newapi_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "metadata-only selector replay scenarios, model ids, cost tiers, decisions, checks, and warnings",
            },
            "validation_commands": [
                "python -m pytest tests/test_gemini_newapi_selector_replay.py -q",
                "python -m pytest tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_cheap_first_policy.py tests/test_model_catalog.py -q",
                "npm run typecheck",
                "npm run build",
            ],
        }

    def _run_scenario(self, scenario: SelectorReplayScenario) -> dict[str, Any]:
        payload = {
            "tasks": [scenario.task],
            "observed_models": list(scenario.observed_models),
        }
        if scenario.explicit_model:
            payload["explicit_models"] = {scenario.task: scenario.explicit_model}
        selector = self.selector_service.build_selector(payload)
        recommendation = selector["task_recommendations"][0]
        checks = [
            self._check_decision(recommendation.get("decision"), scenario.expected_decision),
            self._check_cost_tier(recommendation.get("cost_tier"), scenario.max_cost_tier),
            self._check_selector_status(selector.get("status"), scenario.expected_selector_status),
            self._check_premium_exception(recommendation, scenario),
        ]
        failed = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "id": scenario.id,
            "status": "fail" if failed else ("warn" if warnings else "pass"),
            "scenario": scenario.to_api(),
            "actual": {
                "selected_model": recommendation.get("selected_model"),
                "canonical_model": recommendation.get("canonical_model"),
                "decision": recommendation.get("decision"),
                "cost_tier": recommendation.get("cost_tier"),
                "route_mode": recommendation.get("route_mode"),
                "premium_exception": recommendation.get("premium_exception"),
                "selector_status": selector.get("status"),
                "warnings": list(recommendation.get("warnings") or []),
                "catalog_review_count": selector["summary"].get("catalog_review_count", 0),
            },
            "checks": checks,
            "recommended_action": self._recommended_action(failed, warnings, scenario),
        }

    def _check_decision(self, actual: str | None, expected: str) -> dict[str, Any]:
        return {
            "id": "decision",
            "status": "pass" if actual == expected else "fail",
            "expected": expected,
            "actual": actual,
            "reason": "Selector decision matches the expected cheap-first scenario."
            if actual == expected
            else "Selector decision drifted from the expected cheap-first behavior.",
        }

    def _check_cost_tier(self, actual: str | None, max_cost_tier: str) -> dict[str, Any]:
        actual_value = actual or "unverified"
        actual_rank = COST_RANK.get(actual_value, COST_RANK["unverified"])
        max_rank = COST_RANK.get(max_cost_tier, COST_RANK["unverified"])
        if actual_value == "unverified":
            status = "warn"
        else:
            status = "pass" if actual_rank <= max_rank else "fail"
        return {
            "id": "cost-tier",
            "status": status,
            "expected": f"<= {max_cost_tier}",
            "actual": actual_value,
            "reason": "Selected model stays within the scenario cost ceiling."
            if status == "pass"
            else (
                "Selector returned an unpriced or uncataloged model; keep it explicit-only."
                if status == "warn"
                else "Selected model exceeds the scenario cost ceiling."
            ),
        }

    def _check_selector_status(self, actual: str | None, expected: str) -> dict[str, Any]:
        return {
            "id": "selector-status",
            "status": "pass" if actual == expected else "fail",
            "expected": expected,
            "actual": actual,
            "reason": "Catalog-review status matches the scenario expectation."
            if actual == expected
            else "Catalog-review status changed for this scenario.",
        }

    def _check_premium_exception(
        self,
        recommendation: dict[str, Any],
        scenario: SelectorReplayScenario,
    ) -> dict[str, Any]:
        premium = bool(recommendation.get("premium_exception"))
        expected = scenario.expected_decision == "premium_exception_required"
        return {
            "id": "premium-exception",
            "status": "pass" if premium == expected else "fail",
            "expected": expected,
            "actual": premium,
            "reason": "Premium exception flag matches selector replay expectations."
            if premium == expected
            else "Premium exception flag drifted and may allow expensive defaults.",
        }

    def _recommended_action(
        self,
        failed: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        scenario: SelectorReplayScenario,
    ) -> str:
        if failed:
            return f"Review Gemini/NewAPI selector scenario {scenario.id}; failing checks: {', '.join(item['id'] for item in failed)}."
        if warnings:
            return f"Keep scenario {scenario.id} explicit-only until catalog price and stability review completes."
        return "Selector scenario is aligned with cheap-first expectations."

    def _scenarios(self, raw_scenarios: Any) -> list[SelectorReplayScenario]:
        if not isinstance(raw_scenarios, list):
            return list(self._default_scenarios())
        scenarios = []
        for index, item in enumerate(raw_scenarios[:20], start=1):
            if not isinstance(item, dict):
                continue
            task = self._safe_token(item.get("task")) or "fast"
            scenarios.append(
                SelectorReplayScenario(
                    id=self._safe_token(item.get("id")) or f"submitted-selector-scenario-{index}",
                    task=task,
                    explicit_model=self._safe_model_id(item.get("explicit_model")),
                    observed_models=tuple(
                        self._safe_model_id(model)
                        for model in (item.get("observed_models") if isinstance(item.get("observed_models"), list) else [])
                        if self._safe_model_id(model)
                    ),
                    expected_decision=self._safe_enum(item.get("expected_decision")) or "cheap_first_ready",
                    max_cost_tier=self._safe_enum(item.get("max_cost_tier")) or "premium",
                    expected_selector_status=self._safe_enum(item.get("expected_selector_status")) or "ready",
                    rationale="Submitted metadata-only selector scenario; maintainer rationale is not echoed.",
                )
            )
        return scenarios or list(self._default_scenarios())

    def _default_scenarios(self) -> tuple[SelectorReplayScenario, ...]:
        return (
            SelectorReplayScenario(
                id="fast-default-flash-lite",
                task="fast",
                explicit_model=None,
                observed_models=(),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                expected_selector_status="ready",
                rationale="High-volume fast tasks should stay on Flash-Lite.",
            ),
            SelectorReplayScenario(
                id="classification-default-flash-lite",
                task="classification",
                explicit_model=None,
                observed_models=(),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                expected_selector_status="ready",
                rationale="Classification should stay cheap-first unless validation fails.",
            ),
            SelectorReplayScenario(
                id="ocr-default-flash-lite",
                task="ocr",
                explicit_model=None,
                observed_models=(),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                expected_selector_status="ready",
                rationale="OCR assist can run over many pages and should start cheap.",
            ),
            SelectorReplayScenario(
                id="review-balanced-after-precheck",
                task="review",
                explicit_model=None,
                observed_models=(),
                expected_decision="balanced_after_precheck",
                max_cost_tier="low",
                expected_selector_status="ready",
                rationale="Legal review uses cheap precheck, then balanced Flash.",
            ),
            SelectorReplayScenario(
                id="document-generation-balanced-after-precheck",
                task="document-generation",
                explicit_model=None,
                observed_models=(),
                expected_decision="balanced_after_precheck",
                max_cost_tier="low",
                expected_selector_status="ready",
                rationale="Draft generation starts with templates and cheap checks before balanced Flash.",
            ),
            SelectorReplayScenario(
                id="large-pdf-premium-exception",
                task="large-pdf",
                explicit_model=None,
                observed_models=(),
                expected_decision="premium_exception_required",
                max_cost_tier="premium",
                expected_selector_status="ready",
                rationale="Large PDF is an explicit premium exception path.",
            ),
            SelectorReplayScenario(
                id="final-review-premium-exception",
                task="final-review",
                explicit_model=None,
                observed_models=(),
                expected_decision="premium_exception_required",
                max_cost_tier="premium",
                expected_selector_status="ready",
                rationale="Final legal review is an explicit premium exception path.",
            ),
            SelectorReplayScenario(
                id="unknown-gemini-like-catalog-review",
                task="fast",
                explicit_model=None,
                observed_models=("google/gemini-3.2-flash-lite",),
                expected_decision="cheap_first_ready",
                max_cost_tier="lowest",
                expected_selector_status="needs_catalog_review",
                rationale="Unknown Gemini-like observed ids must not become defaults until catalog review.",
            ),
            SelectorReplayScenario(
                id="fast-explicit-pro-premium-exception",
                task="fast",
                explicit_model="google/gemini-2.5-pro",
                observed_models=(),
                expected_decision="premium_exception_required",
                max_cost_tier="premium",
                expected_selector_status="ready",
                rationale="Explicit Pro on high-volume routes must be treated as premium exception evidence.",
            ),
        )

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace("_", "-")[:80]
        if not raw or any(marker in raw for marker in ("sk-", "@", "password", "secret")):
            return ""
        return "".join(char if char.isalnum() or char in "-:." else "-" for char in raw).strip("-")

    def _safe_enum(self, value: Any) -> str:
        raw = str(value or "").strip().lower()[:80]
        if not raw or any(marker in raw for marker in ("sk-", "@", "password", "secret")):
            return ""
        return "".join(char if char.isalnum() or char in "-_:." else "_" for char in raw).strip("_-")

    def _safe_model_id(self, value: Any) -> str:
        raw = str(value or "").strip().lower()[:120]
        if not raw or any(marker in raw for marker in ("sk-", "@", "password", "secret")):
            return ""
        return "".join(char if char.isalnum() or char in "-_./:" else "-" for char in raw).strip("-")
