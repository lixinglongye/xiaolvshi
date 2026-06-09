from __future__ import annotations

from typing import Any

from services.model_gateway_health_plan import ModelGatewayHealthPlanService
from services.model_gateway_probe_evaluation import model_gateway_probe_evaluation_registry
from services.model_gateway_runtime_configuration import ModelGatewayRuntimeConfigurationService
from services.model_ops_newapi_channel_bootstrap import ModelOpsNewapiChannelBootstrapService


PASS_STATUSES = {"pass", "ready", "ok", "success"}
WARN_STATUSES = {"warn", "warning", "not_run", "review_required", "not_supplied"}


class ModelGatewayProbeRunbookGateService:
    """Gate the NewAPI/Gemini gateway probe sequence before cheap-first rollout."""

    def __init__(
        self,
        health_plan_service: ModelGatewayHealthPlanService | None = None,
        runtime_configuration_service: ModelGatewayRuntimeConfigurationService | None = None,
        channel_bootstrap_service: ModelOpsNewapiChannelBootstrapService | None = None,
    ) -> None:
        self.health_plan_service = health_plan_service or ModelGatewayHealthPlanService()
        self.runtime_configuration_service = runtime_configuration_service or ModelGatewayRuntimeConfigurationService()
        self.channel_bootstrap_service = channel_bootstrap_service or ModelOpsNewapiChannelBootstrapService()

    def build_gate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        health_plan = self._source(data, "gateway_health_plan", self.health_plan_service.build_plan())
        runtime_configuration = self._source(
            data,
            "gateway_runtime_configuration",
            self.runtime_configuration_service.build_configuration(data.get("runtime_configuration")),
        )
        channel_bootstrap = self._source(
            data,
            "newapi_channel_bootstrap",
            self.channel_bootstrap_service.build_packet(data.get("channel")),
        )
        probe_evaluation = self._source(
            data,
            "gateway_probe_evaluation",
            data.get("gateway_probe_evaluation") if isinstance(data.get("gateway_probe_evaluation"), dict) else model_gateway_probe_evaluation_registry.latest(),
        )

        steps = self._steps(
            health_plan=health_plan,
            runtime_configuration=runtime_configuration,
            channel_bootstrap=channel_bootstrap,
            probe_evaluation=probe_evaluation,
        )
        checks = self._checks(
            health_plan=health_plan,
            runtime_configuration=runtime_configuration,
            channel_bootstrap=channel_bootstrap,
            probe_evaluation=probe_evaluation,
            steps=steps,
        )
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        ready_steps = [step for step in steps if step["status"] == "ready"]
        blocked_steps = [step for step in steps if step["status"] == "blocked"]
        review_steps = [step for step in steps if step["status"] == "review_required"]
        next_step = next((step for step in steps if step["status"] != "ready"), steps[-1] if steps else None)

        return {
            "id": "model-gateway-probe-runbook-gate",
            "title": "Model gateway probe runbook gate",
            "status": "fail" if blocking else ("warn" if warnings or review_steps else "pass"),
            "method": {
                "type": "metadata-only-gateway-probe-runbook-gate",
                "notes": [
                    "Combines NewAPI channel bootstrap, runtime configuration, gateway health plan, and sanitized probe evaluation into one ordered rollout gate.",
                    "Requires list-models before cheap JSON probes, cheap JSON probes before legal fixture smoke, and fixture smoke before default changes.",
                    "Keeps high-frequency legal workflows on cheap-first Gemini defaults and keeps Pro, preview, unknown, or unpriced models behind review.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, or the network.",
                ],
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/openai",
                    "https://ai.google.dev/gemini-api/docs/models",
                ],
            },
            "summary": {
                "step_count": len(steps),
                "ready_step_count": len(ready_steps),
                "review_step_count": len(review_steps),
                "blocked_step_count": len(blocked_steps),
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
                "next_step_id": next_step["id"] if next_step else None,
                "source_health_status": health_plan.get("status"),
                "source_runtime_status": runtime_configuration.get("status"),
                "source_channel_status": channel_bootstrap.get("status"),
                "source_probe_status": probe_evaluation.get("status"),
                "cheap_probe_pass_count": _summary_int(probe_evaluation, "probed_cheap_candidate_count"),
                "image_probe_pass_count": _summary_int(probe_evaluation, "probed_image_candidate_count"),
                "forbidden_payload_field_count": _summary_int(probe_evaluation, "forbidden_payload_field_count"),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
            },
            "runbook_steps": steps,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings, steps, probe_evaluation),
            "source_summaries": {
                "gateway_health_plan": health_plan.get("summary", {}),
                "gateway_runtime_configuration": runtime_configuration.get("summary", {}),
                "newapi_channel_bootstrap": channel_bootstrap.get("summary", {}),
                "gateway_probe_evaluation": probe_evaluation.get("summary", {}),
            },
            "privacy_boundary": {
                "metadata_only": True,
                "credentials_included": False,
                "credential_material_included": False,
                "authorization_headers_included": False,
                "raw_payload_echoed": False,
                "raw_probe_payload_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "gateway_response_included": False,
                "emails_included": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_key_validated": False,
                "model_inventory_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "pricing_accuracy_claimed": False,
                "legal_quality_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_gateway_probe_runbook_gate.py -q",
                "python -m pytest tests/test_model_gateway_health_plan.py tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_runtime_configuration.py tests/test_model_ops_newapi_channel_bootstrap.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _steps(
        self,
        *,
        health_plan: dict[str, Any],
        runtime_configuration: dict[str, Any],
        channel_bootstrap: dict[str, Any],
        probe_evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            self._step(
                step_id="normalize-runtime-channel",
                title="Normalize runtime channel",
                source_statuses=[channel_bootstrap.get("status"), runtime_configuration.get("status")],
                ready=bool(
                    _summary_bool(channel_bootstrap, "openai_compatible_path")
                    and _summary_bool(runtime_configuration, "openai_compatible_path")
                ),
                blocked=bool(_has_blockers(channel_bootstrap) or _has_blockers(runtime_configuration)),
                action="Keep APP_AI_BASE_URL normalized to the OpenAI-compatible /v1 or Gemini OpenAI-compatible path.",
                evidence_links=["modelops-newapi-channel-bootstrap", "model-gateway-runtime-configuration"],
            ),
            self._step(
                step_id="verify-secret-boundary",
                title="Verify secret boundary",
                source_statuses=[channel_bootstrap.get("status"), runtime_configuration.get("status"), health_plan.get("status")],
                ready=bool(
                    not _has_privacy_leak(channel_bootstrap)
                    and not _has_privacy_leak(runtime_configuration)
                    and not _has_privacy_leak(health_plan)
                ),
                blocked=bool(
                    "channel-secret-redacted" in _blocking_ids(channel_bootstrap)
                    or "runtime-base-url-no-credential-material" in _blocking_ids(runtime_configuration)
                    or "https-base-url" in _blocking_ids(health_plan)
                ),
                action="Keep keys in APP_AI_KEY or deployment secrets only; never paste raw headers, tokens, or gateway responses.",
                evidence_links=["model-gateway-connection-profile", "model-gateway-runtime-configuration", "model-gateway-health-plan"],
            ),
            self._step(
                step_id="list-models-first",
                title="Run list-models first",
                source_statuses=[health_plan.get("status"), probe_evaluation.get("status")],
                ready=_summary_int(probe_evaluation, "observed_model_count") > 0,
                blocked=_has_blockers(health_plan),
                action="Run GET {{APP_AI_BASE_URL}}/models and submit only sanitized model ids or counts.",
                evidence_links=["model-gateway-health-plan", "model-gateway-probe-evaluation"],
            ),
            self._step(
                step_id="cheap-json-probe",
                title="Run cheap JSON probe",
                source_statuses=[probe_evaluation.get("status")],
                ready=_summary_int(probe_evaluation, "probed_cheap_candidate_count") > 0,
                blocked=bool(
                    "cheap-first-candidate-present" in _blocking_ids(probe_evaluation)
                    or _summary_int(probe_evaluation, "forbidden_payload_field_count") > 0
                ),
                action="Probe the cheapest stable Gemini text route with tiny synthetic JSON before any legal fixture smoke.",
                evidence_links=["model-gateway-probe-evaluation", "model-gateway-health-plan"],
            ),
            self._step(
                step_id="optional-image-smoke",
                title="Optional image smoke probe",
                source_statuses=[health_plan.get("status"), probe_evaluation.get("status")],
                ready=bool(
                    _summary_int(probe_evaluation, "image_candidate_count") == 0
                    or _summary_int(probe_evaluation, "probed_image_candidate_count") > 0
                ),
                blocked="image-default-candidate-present" in _blocking_ids(probe_evaluation),
                action="Run image smoke only after text probes pass, using neutral placeholder media and no client content.",
                evidence_links=["model-gateway-probe-evaluation", "model-gateway-health-plan"],
            ),
            self._step(
                step_id="legal-fixture-smoke",
                title="Run legal fixture smoke",
                source_statuses=[probe_evaluation.get("status")],
                ready=bool(
                    _summary_int(probe_evaluation, "probed_cheap_candidate_count") > 0
                    and _summary_int(probe_evaluation, "forbidden_payload_field_count") == 0
                    and not _has_blockers(probe_evaluation)
                ),
                blocked=bool(_has_blockers(probe_evaluation)),
                action="Run only small local synthetic legal fixtures after cheap JSON probe evidence is accepted.",
                evidence_links=["model-gateway-probe-evaluation", "legal-fixture-quick-suite"],
            ),
            self._step(
                step_id="default-change-review",
                title="Default change review",
                source_statuses=[probe_evaluation.get("status")],
                ready=bool(
                    _summary_int(probe_evaluation, "probed_cheap_candidate_count") > 0
                    and _summary_int(probe_evaluation, "recommended_change_count") == 0
                    and not _has_blockers(probe_evaluation)
                ),
                blocked=bool(_summary_int(probe_evaluation, "forbidden_payload_field_count") > 0),
                action="Use recommended env rows only as review input; this gate never writes defaults or shifts traffic.",
                evidence_links=["model-gateway-probe-evaluation", "default-change-queue", "cheap-first-canary-plan"],
            ),
        ]

    def _step(
        self,
        *,
        step_id: str,
        title: str,
        source_statuses: list[Any],
        ready: bool,
        blocked: bool,
        action: str,
        evidence_links: list[str],
    ) -> dict[str, Any]:
        status = "blocked" if blocked else ("ready" if ready else "review_required")
        return {
            "id": step_id,
            "title": title,
            "status": status,
            "source_statuses": [str(status) for status in source_statuses if status],
            "action": action,
            "evidence_links": evidence_links,
        }

    def _checks(
        self,
        *,
        health_plan: dict[str, Any],
        runtime_configuration: dict[str, Any],
        channel_bootstrap: dict[str, Any],
        probe_evaluation: dict[str, Any],
        steps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        blocked_steps = [step["id"] for step in steps if step["status"] == "blocked"]
        review_steps = [step["id"] for step in steps if step["status"] == "review_required"]
        return [
            {
                "id": "runbook-sources-present",
                "status": "pass"
                if all(isinstance(source, dict) and source for source in (health_plan, runtime_configuration, channel_bootstrap, probe_evaluation))
                else "fail",
                "reason": "Gateway health, runtime, channel, and probe signals are attached.",
            },
            {
                "id": "runbook-no-blocked-steps",
                "status": "fail" if blocked_steps else "pass",
                "reason": "No runbook steps are blocked." if not blocked_steps else "Blocked runbook steps: " + ", ".join(blocked_steps) + ".",
            },
            {
                "id": "runbook-review-steps-visible",
                "status": "warn" if review_steps else "pass",
                "reason": "All runbook steps are ready." if not review_steps else "Review runbook steps: " + ", ".join(review_steps) + ".",
            },
            {
                "id": "runbook-cheap-probe-before-fixtures",
                "status": "pass" if _step_ready(steps, "cheap-json-probe") or not _step_ready(steps, "legal-fixture-smoke") else "fail",
                "reason": "Legal fixture smoke cannot be marked ready before cheap JSON probe evidence.",
            },
            {
                "id": "runbook-no-sensitive-probe-fields",
                "status": "fail" if _summary_int(probe_evaluation, "forbidden_payload_field_count") else "pass",
                "reason": "Probe evidence contains no forbidden raw or secret-bearing fields."
                if not _summary_int(probe_evaluation, "forbidden_payload_field_count")
                else "Discard rejected probe evidence and resubmit sanitized ids/status/counts only.",
            },
            {
                "id": "runbook-no-side-effects",
                "status": "pass",
                "reason": "Runbook gate does not call gateways, write configuration, change defaults, or shift traffic.",
            },
        ]

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        steps: list[dict[str, Any]],
        probe_evaluation: dict[str, Any],
    ) -> list[str]:
        if blocking:
            return [
                "Stop gateway rollout until blocked runbook steps are resolved.",
                "Discard any rejected probe payloads and resubmit sanitized model IDs, statuses, HTTP codes, latency, JSON booleans, and image counts only.",
            ]
        next_step = next((step for step in steps if step["status"] != "ready"), None)
        if next_step:
            return [
                f"Next maintainer step: {next_step['action']}",
                "Keep high-frequency legal tasks on cheap-first Gemini defaults while collecting probe evidence.",
            ]
        if _summary_int(probe_evaluation, "recommended_change_count"):
            return ["Review recommended env changes in the default-change queue before changing any runtime default."]
        if warnings:
            return ["Resolve runbook review items before unattended legal fixture or batch runs."]
        return ["Gateway runbook is ready for maintainer-reviewed cheap-first fixture smoke; no defaults are changed by this gate."]

    def _source(self, data: dict[str, Any], key: str, fallback: Any) -> dict[str, Any]:
        value = data.get(key)
        return value if isinstance(value, dict) else (fallback if isinstance(fallback, dict) else {})


def _status_ready(value: Any) -> bool:
    return str(value or "").lower() in PASS_STATUSES


def _blocking_ids(value: dict[str, Any]) -> list[str]:
    ids = value.get("blocking_check_ids")
    return [str(item) for item in ids] if isinstance(ids, list) else []


def _has_blockers(value: dict[str, Any]) -> bool:
    return str(value.get("status") or "").lower() == "fail" or bool(_blocking_ids(value))


def _has_privacy_leak(value: dict[str, Any]) -> bool:
    boundary = value.get("privacy_boundary")
    if not isinstance(boundary, dict):
        return False
    for key in (
        "credentials_included",
        "credential_material_included",
        "authorization_headers_included",
        "raw_payload_echoed",
        "raw_probe_payload_included",
        "prompts_included",
        "raw_legal_text_included",
        "raw_model_output_included",
        "gateway_response_included",
        "emails_included",
    ):
        if boundary.get(key):
            return True
    return False


def _summary_bool(value: dict[str, Any], key: str) -> bool:
    summary = value.get("summary") if isinstance(value.get("summary"), dict) else {}
    return bool(summary.get(key))


def _summary_int(value: dict[str, Any], key: str) -> int:
    summary = value.get("summary") if isinstance(value.get("summary"), dict) else {}
    try:
        return max(0, int(summary.get(key) or 0))
    except (TypeError, ValueError):
        return 0


def _step_ready(steps: list[dict[str, Any]], step_id: str) -> bool:
    return any(step.get("id") == step_id and step.get("status") == "ready" for step in steps)
