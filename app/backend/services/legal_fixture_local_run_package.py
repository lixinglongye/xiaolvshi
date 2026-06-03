from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.legal_fixture_gateway_manifest import LegalFixtureGatewayManifestService
from services.legal_fixture_quick_suite import LegalFixtureQuickSuiteService
from services.legal_fixture_run_plan import LegalFixtureRunPlanService


DEFAULT_PACKAGE_FIXTURE_LIMIT = 2


class LegalFixtureLocalRunPackageService:
    """Bundle the smallest manual gateway fixture run into one safe payload."""

    def __init__(
        self,
        quick_suite_service: LegalFixtureQuickSuiteService | None = None,
        manifest_service: LegalFixtureGatewayManifestService | None = None,
        run_plan_service: LegalFixtureRunPlanService | None = None,
    ) -> None:
        self.quick_suite_service = quick_suite_service or LegalFixtureQuickSuiteService()
        self.manifest_service = manifest_service or LegalFixtureGatewayManifestService()
        self.run_plan_service = run_plan_service or LegalFixtureRunPlanService()

    def build_package(self, fixture_limit: int = DEFAULT_PACKAGE_FIXTURE_LIMIT) -> dict[str, Any]:
        limit = self._fixture_limit(fixture_limit)
        quick_suite = self.quick_suite_service.build_suite(limit)
        manifest = self.manifest_service.build_manifest()
        run_plan = self.run_plan_service.build_plan()
        selected_ids = [row["fixture_id"] for row in quick_suite["selected_fixtures"]]
        manifest_by_id = {row["fixture_id"]: row for row in manifest["requests"]}
        cheap_steps_by_id = {
            step["fixture_id"]: step
            for step in run_plan["steps"]
            if step["phase"] == "cheap_first" and step["fixture_id"] in selected_ids
        }
        request_files = [
            self._request_file(index, fixture_id, manifest_by_id[fixture_id], cheap_steps_by_id[fixture_id])
            for index, fixture_id in enumerate(selected_ids, start=1)
            if fixture_id in manifest_by_id and fixture_id in cheap_steps_by_id
        ]
        run_steps = [self._run_step(index, row) for index, row in enumerate(request_files, start=1)]
        observation_template = self._observation_template(request_files, manifest_by_id)
        run_report_payload = self._run_report_payload(request_files, observation_template)
        checks = self._checks(quick_suite, run_plan, request_files)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else ("warn" if warnings else "ready"),
            "method": {
                "type": "local-legal-fixture-run-package",
                "notes": [
                    "Combines quick-suite, gateway manifest, and run-plan data into one manual local run payload.",
                    "Produces request JSON and shell command templates only; it never calls a gateway or app AI endpoint.",
                    "Defaults to two cheap-first fixtures and max_parallel_requests=1 for low-resource machines.",
                ],
            },
            "summary": {
                "requested_fixture_limit": limit,
                "selected_fixture_count": len(selected_ids),
                "request_file_count": len(request_files),
                "run_step_count": len(run_steps),
                "max_parallel_requests": 1,
                "estimated_cheap_first_cost_usd": round(
                    sum(row["estimated_request_cost_usd"] or 0.0 for row in request_files),
                    8,
                ),
                "unknown_cost_request_count": sum(
                    1 for row in request_files if row["estimated_request_cost_usd"] is None
                ),
                "follow_up_endpoint_count": len(self._follow_up_endpoints()),
            },
            "environment": {
                "required_env": ["APP_AI_BASE_URL", "APP_AI_KEY"],
                "base_url_rule": "Set APP_AI_BASE_URL to an OpenAI-compatible /v1 base URL, for example https://example-gateway.test/v1.",
                "secret_policy": "Use local environment variables only; do not paste keys into request files, docs, issues, or commits.",
            },
            "request_files": request_files,
            "run_steps": run_steps,
            "observation_template": observation_template,
            "run_report_payload_template": run_report_payload,
            "follow_up_endpoints": self._follow_up_endpoints(),
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "validation_commands": [
                "python -m pytest tests/test_legal_fixture_local_run_package.py tests/test_legal_fixture_quick_suite.py -q",
                "python -m pytest tests/test_legal_fixture_gateway_manifest.py tests/test_legal_fixture_run_plan.py -q",
            ],
            "privacy_note": (
                "The package contains synthetic fixture prompts, model IDs, request budgets, and placeholders only. "
                "Do not commit API keys, Authorization headers with real tokens, client documents, emails, public benchmark raw examples, or raw model outputs."
            ),
        }

    def _fixture_limit(self, value: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = DEFAULT_PACKAGE_FIXTURE_LIMIT
        return max(1, min(parsed, 4))

    def _request_file(
        self,
        index: int,
        fixture_id: str,
        manifest_row: dict[str, Any],
        cheap_step: dict[str, Any],
    ) -> dict[str, Any]:
        body = deepcopy(manifest_row["openai_request_body"])
        body["model"] = cheap_step["model"]
        file_name = f"{index:02d}-{fixture_id}.request.json"
        return {
            "file_name": file_name,
            "fixture_id": fixture_id,
            "title": manifest_row["title"],
            "phase": "cheap_first",
            "task": cheap_step["task"],
            "model": cheap_step["model"],
            "model_cost_tier": cheap_step["model_cost_tier"],
            "endpoint_url": "{{APP_AI_BASE_URL}}/chat/completions",
            "body": body,
            "prompt_tokens_estimate": cheap_step["prompt_tokens_estimate"],
            "completion_tokens_budget": cheap_step["completion_tokens_budget"],
            "estimated_request_cost_usd": cheap_step["estimated_request_cost_usd"],
            "response_capture": {
                "gateway_json_path": "choices[0].message.content",
                "normalized_observation_path": f"observations.{fixture_id}.output_text",
                "raw_output_policy": "Keep raw gateway output local and ephemeral; paste only normalized JSON/text into the observation template.",
            },
        }

    def _run_step(self, index: int, request_file: dict[str, Any]) -> dict[str, Any]:
        file_name = request_file["file_name"]
        return {
            "order": index,
            "step_id": f"local-run-{index:02d}-{request_file['fixture_id']}",
            "fixture_id": request_file["fixture_id"],
            "title": request_file["title"],
            "run_condition": "always; cheap_first phase only",
            "max_parallel_requests": 1,
            "request_file_name": file_name,
            "endpoint_url": request_file["endpoint_url"],
            "command_templates": {
                "powershell": (
                    '$headers = @{ Authorization = "Bearer " + $env:APP_AI_KEY; "Content-Type" = "application/json" }; '
                    f'$body = Get-Content -Raw .\\{file_name}; '
                    'Invoke-RestMethod -Method Post -Uri ($env:APP_AI_BASE_URL.TrimEnd("/") + "/chat/completions") -Headers $headers -Body $body'
                ),
                "curl": (
                    f'curl -sS -X POST "$APP_AI_BASE_URL/chat/completions" '
                    f'-H "Authorization: Bearer $APP_AI_KEY" -H "Content-Type: application/json" --data-binary "@{file_name}"'
                ),
            },
            "next_local_action": (
                "Copy choices[0].message.content into observation_template for this fixture, then POST the combined "
                "payload to fixture-smoke and fixture-run-report."
            ),
        }

    def _observation_template(
        self,
        request_files: list[dict[str, Any]],
        manifest_by_id: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        rows: dict[str, Any] = {}
        for request_file in request_files:
            fixture_id = request_file["fixture_id"]
            rows.update(deepcopy(manifest_by_id[fixture_id]["smoke_observation_template"]))
        return rows

    def _run_report_payload(
        self,
        request_files: list[dict[str, Any]],
        observation_template: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "observations": observation_template,
            "run_metadata": {
                row["fixture_id"]: {
                    "phase": row["phase"],
                    "model": row["model"],
                    "estimated_cost_usd": row["estimated_request_cost_usd"],
                    "http_status": "<fill locally>",
                    "latency_ms": "<fill locally>",
                }
                for row in request_files
            },
        }

    def _checks(
        self,
        quick_suite: dict[str, Any],
        run_plan: dict[str, Any],
        request_files: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "request-files-present",
                "status": "pass" if request_files else "fail",
                "reason": f"Prepared {len(request_files)} cheap-first request files.",
            },
            {
                "id": "quick-suite-ready",
                "status": "pass" if quick_suite["status"] == "ready" else "warn",
                "reason": f"Quick suite status is {quick_suite['status']}.",
            },
            {
                "id": "run-plan-ready",
                "status": "pass" if run_plan["status"] == "ready" else "warn",
                "reason": f"Fixture run plan status is {run_plan['status']}.",
            },
            {
                "id": "serial-execution",
                "status": "pass",
                "reason": "Every generated command is intended for one-at-a-time execution with max_parallel_requests=1.",
            },
            {
                "id": "placeholder-secrets-only",
                "status": "pass",
                "reason": "Commands read APP_AI_KEY from the local environment and request files contain no Authorization header.",
            },
        ]

    def _follow_up_endpoints(self) -> list[str]:
        return [
            "/api/v1/maintenance/legal-review-benchmark/local-response-normalizer",
            "/api/v1/maintenance/legal-review-benchmark/local-run-review",
            "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
            "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
            "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
        ]

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return ["Fix package blockers before running gateway fixture requests."]
        actions = [
            "Run only the generated cheap-first request files first, one at a time.",
            "Submit normalized observations to fixture-smoke before any escalation.",
            "Submit the same payload to fixture-run-report and fixture-evidence-bundle before changing default models.",
        ]
        if warnings:
            actions.append("Review warnings before relying on cost estimates or release-readiness evidence.")
        return actions
