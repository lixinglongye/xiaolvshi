from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.legal_fixture_gateway_manifest import LegalFixtureGatewayManifestService
from services.model_catalog import estimate_token_cost_usd, model_profile


@dataclass(frozen=True)
class FixtureRunStep:
    step_id: str
    order: int
    phase: str
    batch_id: str
    fixture_id: str
    title: str
    task: str
    model: str
    model_cost_tier: str | None
    endpoint_path: str
    run_condition: str
    prompt_tokens_estimate: int
    completion_tokens_budget: int
    estimated_request_cost_usd: float | None
    max_parallel_requests: int
    smoke_route: str
    observation_target: str
    improvement_target: str
    required_response_fields: tuple[str, ...]
    command_hint: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_response_fields"] = list(self.required_response_fields)
        return data


class LegalFixtureRunPlanService:
    """Create a cheap-first local run plan from safe fixture gateway manifests."""

    def __init__(self, manifest_service: LegalFixtureGatewayManifestService | None = None) -> None:
        self.manifest_service = manifest_service or LegalFixtureGatewayManifestService()

    def build_plan(self) -> dict[str, Any]:
        manifest = self.manifest_service.build_manifest()
        cheap_steps = [
            self._step(row, phase="cheap_first", order=index + 1)
            for index, row in enumerate(manifest["requests"])
        ]
        escalation_steps = [
            self._step(row, phase="escalation_if_needed", order=len(cheap_steps) + index + 1)
            for index, row in enumerate(manifest["requests"])
            if row["cheap_first_policy"]["escalate_to_model"]
        ]
        steps = cheap_steps + escalation_steps
        batches = self._batches(steps)
        priced_steps = [step for step in steps if step.estimated_request_cost_usd is not None]
        unknown_steps = [step for step in steps if step.estimated_request_cost_usd is None]
        min_cost = sum(step.estimated_request_cost_usd or 0.0 for step in cheap_steps)
        max_cost = sum(step.estimated_request_cost_usd or 0.0 for step in steps)
        return {
            "status": "warn" if unknown_steps else "ready",
            "method": {
                "type": "cheap-first-legal-fixture-run-plan",
                "notes": [
                    "Builds a local execution plan only; it never calls NewAPI, Gemini, or app AI endpoints.",
                    "Run cheap_first batches before any escalation_if_needed batch.",
                    "Use one request at a time on low-resource laptops; submit smoke results before escalating.",
                ],
            },
            "summary": {
                "fixture_count": manifest["summary"]["request_count"],
                "batch_count": len(batches),
                "total_step_count": len(steps),
                "cheap_first_step_count": len(cheap_steps),
                "escalation_step_count": len(escalation_steps),
                "priced_step_count": len(priced_steps),
                "unknown_model_step_count": len(unknown_steps),
                "estimated_min_cost_usd": round(min_cost, 8),
                "estimated_max_cost_usd": round(max_cost, 8),
                "max_parallel_requests": 1,
            },
            "batches": batches,
            "steps": [step.to_api() for step in steps],
            "warning_step_ids": [step.step_id for step in unknown_steps],
            "recommended_actions": self._recommended_actions(escalation_steps, unknown_steps),
            "privacy_note": (
                "The plan references synthetic fixture prompts and credential placeholders only. "
                "Do not commit real gateway keys, client documents, emails, or raw model outputs."
            ),
        }

    def _step(self, row: dict[str, Any], *, phase: str, order: int) -> FixtureRunStep:
        model = row["cheap_trial_model"]
        run_condition = "always"
        if phase == "escalation_if_needed":
            model = row["recommended_model"]
            run_condition = "only when the matching cheap_first step fails fixture smoke coverage"
        body = dict(row["openai_request_body"])
        body["model"] = model
        task = str(row["app_request_body"]["task"])
        prompt_tokens = self._prompt_tokens(body)
        completion_tokens = int(body.get("max_tokens") or 0)
        profile = model_profile(model)
        cost = estimate_token_cost_usd(model, prompt_tokens, completion_tokens)
        batch_id = f"{phase}:{task}:{model}"
        step_id = f"{phase}:{row['fixture_id']}"
        success_target = row["cheap_first_policy"]["post_success_to"]
        failure_target = row["cheap_first_policy"]["post_failure_to"]
        route = row["smoke_observation_template"][row["fixture_id"]]["route"]
        return FixtureRunStep(
            step_id=step_id,
            order=order,
            phase=phase,
            batch_id=batch_id,
            fixture_id=row["fixture_id"],
            title=row["title"],
            task=task,
            model=model,
            model_cost_tier=profile.cost_tier if profile else None,
            endpoint_path=row["endpoint_path"],
            run_condition=run_condition,
            prompt_tokens_estimate=prompt_tokens,
            completion_tokens_budget=completion_tokens,
            estimated_request_cost_usd=cost,
            max_parallel_requests=1,
            smoke_route=route,
            observation_target=success_target,
            improvement_target=failure_target,
            required_response_fields=tuple(row["expected_response_contract"]["required_fields"]),
            command_hint=(
                "POST {{APP_AI_BASE_URL}}/v1/chat/completions with Authorization: "
                "Bearer {{APP_AI_KEY}}; paste normalized JSON output into fixture-smoke."
            ),
        )

    def _prompt_tokens(self, body: dict[str, Any]) -> int:
        text = " ".join(str(message.get("content", "")) for message in body.get("messages", []))
        return max(1, round(len(text) / 4))

    def _batches(self, steps: list[FixtureRunStep]) -> list[dict[str, Any]]:
        batches: dict[str, list[FixtureRunStep]] = {}
        for step in steps:
            batches.setdefault(step.batch_id, []).append(step)

        rows: list[dict[str, Any]] = []
        for batch_id, batch_steps in batches.items():
            first = batch_steps[0]
            rows.append(
                {
                    "batch_id": batch_id,
                    "phase": first.phase,
                    "task": first.task,
                    "model": first.model,
                    "model_cost_tier": first.model_cost_tier,
                    "step_ids": [step.step_id for step in batch_steps],
                    "fixture_ids": [step.fixture_id for step in batch_steps],
                    "max_parallel_requests": 1,
                    "estimated_batch_cost_usd": self._batch_cost(batch_steps),
                    "run_after": "fixture smoke scoring" if first.phase == "escalation_if_needed" else "none",
                }
            )
        return sorted(rows, key=lambda item: (item["phase"] != "cheap_first", item["batch_id"]))

    def _batch_cost(self, steps: list[FixtureRunStep]) -> float | None:
        if any(step.estimated_request_cost_usd is None for step in steps):
            return None
        return round(sum(step.estimated_request_cost_usd or 0.0 for step in steps), 8)

    def _recommended_actions(
        self,
        escalation_steps: list[FixtureRunStep],
        unknown_steps: list[FixtureRunStep],
    ) -> list[str]:
        actions = [
            "Run cheap_first batches serially on a low-resource laptop, then submit outputs to /fixture-smoke.",
            "Escalate only the fixtures that fail smoke coverage or keep high-priority improvement actions.",
            "Attach fixture smoke scores to release-readiness evidence before changing default models.",
        ]
        if escalation_steps:
            actions.append("Review escalation_if_needed batches before spending on balanced or premium models.")
        if unknown_steps:
            actions.append("Map unknown gateway model names into the local Gemini catalog to restore cost estimates.")
        return actions
