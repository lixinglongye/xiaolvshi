from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.legal_fixture_prompt_pack import LegalFixturePromptPackService


@dataclass(frozen=True)
class GatewayFixtureRequest:
    fixture_id: str
    title: str
    recommended_model: str
    cheap_trial_model: str
    endpoint_path: str
    gateway_base_url_placeholder: str
    auth_header_placeholder: str
    cheap_first_policy: dict[str, Any]
    openai_request_body: dict[str, Any]
    app_request_body: dict[str, Any]
    smoke_observation_template: dict[str, Any]
    expected_response_contract: dict[str, Any]

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class LegalFixtureGatewayManifestService:
    """Build safe request manifests for running legal fixtures through OpenAI-compatible gateways."""

    def __init__(self, prompt_pack_service: LegalFixturePromptPackService | None = None) -> None:
        self.prompt_pack_service = prompt_pack_service or LegalFixturePromptPackService()

    def build_manifest(self) -> dict[str, Any]:
        prompt_pack = self.prompt_pack_service.build_pack()
        rows = [self._request_row(prompt) for prompt in prompt_pack["prompts"]]
        warnings = [row.fixture_id for row in rows if row.recommended_model != row.cheap_trial_model]
        return {
            "status": "ready",
            "method": {
                "type": "openai-compatible-legal-fixture-request-manifest",
                "notes": [
                    "Produces request bodies only; it never calls a gateway.",
                    "Use environment variables for APP_AI_BASE_URL and APP_AI_KEY. The manifest contains placeholders only.",
                    "Run cheap_trial_model first, then escalate to recommended_model only when smoke coverage fails.",
                ],
            },
            "summary": {
                "request_count": len(rows),
                "cheap_first_request_count": len(rows),
                "escalation_candidate_count": len(warnings),
                "prompt_pack_status": prompt_pack["status"],
            },
            "requests": [row.to_api() for row in rows],
            "warning_fixture_ids": warnings,
            "recommended_actions": self._recommended_actions(warnings),
            "privacy_note": (
                "The manifest includes synthetic fixture prompts only and uses credential placeholders. "
                "Do not paste real client documents, API keys, emails, or raw model outputs into committed manifests."
            ),
        }

    def _request_row(self, prompt: dict[str, Any]) -> GatewayFixtureRequest:
        cheap_model = str(prompt["cheap_trial_model"])
        recommended_model = str(prompt["recommended_model"])
        request_body = self._openai_request_body(prompt, model=cheap_model)
        return GatewayFixtureRequest(
            fixture_id=str(prompt["fixture_id"]),
            title=str(prompt["title"]),
            recommended_model=recommended_model,
            cheap_trial_model=cheap_model,
            endpoint_path="/v1/chat/completions",
            gateway_base_url_placeholder="{{APP_AI_BASE_URL}}",
            auth_header_placeholder="Bearer {{APP_AI_KEY}}",
            cheap_first_policy={
                "first_attempt_model": cheap_model,
                "escalate_to_model": recommended_model if recommended_model != cheap_model else None,
                "escalation_trigger": "fixture smoke status is fail or high-priority improvement actions remain",
                "post_success_to": "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
                "post_failure_to": "/api/v1/maintenance/legal-review-benchmark/fixture-improvements",
            },
            openai_request_body=request_body,
            app_request_body=self._app_request_body(prompt, model=cheap_model),
            smoke_observation_template={
                prompt["fixture_id"]: {
                    "route": prompt["expected_route"],
                    "output_text": "<paste model JSON string or normalized report text here>",
                    "structured_outputs": {},
                }
            },
            expected_response_contract={
                "content_type": "json_object",
                "required_fields": prompt["output_schema"]["required"],
                "follow_up_endpoints": prompt["follow_up_endpoints"],
            },
        )

    def _openai_request_body(self, prompt: dict[str, Any], *, model: str) -> dict[str, Any]:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt["system_prompt"]},
                {"role": "user", "content": prompt["user_prompt"]},
            ],
            "temperature": prompt["request_parameters"]["temperature"],
            "max_tokens": prompt["request_parameters"]["max_tokens"],
            "response_format": prompt["request_parameters"]["response_format"],
            "stream": False,
        }

    def _app_request_body(self, prompt: dict[str, Any], *, model: str) -> dict[str, Any]:
        return {
            "model": model,
            "task": prompt["recommended_task"],
            "messages": [
                {"role": "system", "content": prompt["system_prompt"]},
                {"role": "user", "content": prompt["user_prompt"]},
            ],
            "temperature": prompt["request_parameters"]["temperature"],
            "max_tokens": prompt["request_parameters"]["max_tokens"],
            "response_format": prompt["request_parameters"]["response_format"],
            "allow_over_budget_model": False,
        }

    def _recommended_actions(self, warning_fixture_ids: list[str]) -> list[str]:
        actions = [
            "Run each openai_request_body against {{APP_AI_BASE_URL}}/v1/chat/completions with a local APP_AI_KEY.",
            "Submit normalized model output to the smoke_observation_template for deterministic fixture scoring.",
        ]
        if warning_fixture_ids:
            actions.append("Only escalate warning fixtures to recommended_model after cheap model smoke coverage fails.")
        return actions
