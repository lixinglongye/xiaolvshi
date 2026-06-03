from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


ValidationState = Literal["pass", "fail", "not_run", "waived"]


@dataclass(frozen=True)
class ReleaseCheck:
    id: str
    title: str
    category: str
    required: bool
    owner: str
    evidence_paths: tuple[str, ...]
    validation_command: str | None = None
    manual_note: str | None = None

    def to_api(self, validation_state: ValidationState) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_paths"] = list(self.evidence_paths)
        data["validation_state"] = validation_state
        data["blocks_release"] = self.required and validation_state not in {"pass", "waived"}
        return data


class ReleaseReadinessService:
    """Evaluates maintainer release readiness without running shell commands."""

    def evaluate(self, validation_results: dict[str, str] | None = None) -> dict[str, Any]:
        results = validation_results or {}
        checks = [check.to_api(self._state(results.get(check.id))) for check in self._checks()]
        blocking = [check for check in checks if check["blocks_release"]]
        failed = [check for check in checks if check["validation_state"] == "fail"]
        not_run = [check for check in checks if check["validation_state"] == "not_run"]

        if failed:
            status = "blocked"
        elif blocking:
            status = "manual_validation_required"
        else:
            status = "ready_for_release_candidate"

        return {
            "status": status,
            "release_allowed": status == "ready_for_release_candidate",
            "required_check_count": sum(1 for check in checks if check["required"]),
            "passed_or_waived_required_count": sum(
                1 for check in checks if check["required"] and check["validation_state"] in {"pass", "waived"}
            ),
            "blocking_check_ids": [check["id"] for check in blocking],
            "failed_check_ids": [check["id"] for check in failed],
            "not_run_check_ids": [check["id"] for check in not_run],
            "checks": checks,
            "summary": self._summary(status, blocking, failed),
        }

    def default_validation_commands(self) -> list[dict[str, str]]:
        return [
            {
                "check_id": check.id,
                "command": check.validation_command,
            }
            for check in self._checks()
            if check.validation_command
        ]

    def _checks(self) -> list[ReleaseCheck]:
        return [
            ReleaseCheck(
                id="backend-tests",
                title="Backend regression tests",
                category="tests",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/tests/test_model_catalog.py",
                    "app/backend/tests/test_model_capability_matrix.py",
                    "app/backend/tests/test_report_quality_gate.py",
                    "app/backend/tests/test_citation_audit.py",
                    "app/backend/tests/test_evidence_audit.py",
                    "app/backend/tests/test_release_decision.py",
                    "app/backend/tests/test_feedback_triage.py",
                ),
                validation_command="python -m pytest tests -q",
            ),
            ReleaseCheck(
                id="frontend-typecheck",
                title="Frontend TypeScript check",
                category="tests",
                required=True,
                owner="frontend",
                evidence_paths=(
                    "app/frontend/src/lib/deepReviewApi.ts",
                    "app/frontend/src/pages/DeepReportPage.tsx",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                    "app/frontend/src/pages/AdminPage.tsx",
                ),
                validation_command="npm run typecheck",
            ),
            ReleaseCheck(
                id="frontend-build",
                title="Frontend production build",
                category="tests",
                required=True,
                owner="frontend",
                evidence_paths=("app/frontend/package.json", "app/frontend/vite.config.ts"),
                validation_command="npm run build",
            ),
            ReleaseCheck(
                id="secret-scan",
                title="Secret and credential scan",
                category="security",
                required=True,
                owner="security_privacy_owner",
                evidence_paths=("README.md", "app/backend/.env.example"),
                validation_command="rg -n \"APP_AI_KEY=.*s[k]-|\\\\bs[k]-[A-Za-z0-9]{20,}\" . --glob '!app/frontend/node_modules/**'",
                manual_note="The command should return no matches for real keys or passwords.",
            ),
            ReleaseCheck(
                id="deep-review-release-decision",
                title="Deep-review release decision coverage",
                category="legal_quality",
                required=True,
                owner="legal_review_owner",
                evidence_paths=(
                    "app/backend/services/release_decision.py",
                    "app/backend/tests/test_release_decision.py",
                    "docs/DEEP_REVIEW_RELEASE_DECISION.md",
                ),
                validation_command="python -m pytest tests/test_release_decision.py -q",
            ),
            ReleaseCheck(
                id="model-capability-matrix",
                title="Gemini model capability matrix coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_capability_matrix.py",
                    "app/backend/services/model_catalog.py",
                    "app/backend/tests/test_model_capability_matrix.py",
                    "docs/AI_MODEL_STRATEGY.md",
                ),
                validation_command="python -m pytest tests/test_model_capability_matrix.py tests/test_model_catalog.py tests/test_model_budget.py -q",
            ),
            ReleaseCheck(
                id="model-configuration-audit",
                title="Model configuration audit coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_configuration_audit.py",
                    "app/backend/tests/test_model_configuration_audit.py",
                    "docs/MODEL_CONFIGURATION_AUDIT.md",
                ),
                validation_command="python -m pytest tests/test_model_configuration_audit.py tests/test_model_catalog.py tests/test_model_budget.py -q",
            ),
            ReleaseCheck(
                id="model-default-optimization",
                title="Model default optimization coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_default_optimization.py",
                    "app/backend/tests/test_model_default_optimization.py",
                    "docs/MODEL_DEFAULT_OPTIMIZATION.md",
                ),
                validation_command="python -m pytest tests/test_model_default_optimization.py tests/test_model_capability_matrix.py -q",
            ),
            ReleaseCheck(
                id="model-gateway-compatibility",
                title="Model gateway compatibility coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_gateway_compatibility.py",
                    "app/backend/tests/test_model_gateway_compatibility.py",
                    "docs/MODEL_GATEWAY_COMPATIBILITY.md",
                ),
                validation_command="python -m pytest tests/test_model_gateway_compatibility.py tests/test_model_catalog.py -q",
            ),
            ReleaseCheck(
                id="model-gateway-health-plan",
                title="Model gateway health plan coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_gateway_health_plan.py",
                    "app/backend/tests/test_model_gateway_health_plan.py",
                    "docs/MODEL_GATEWAY_HEALTH_PLAN.md",
                ),
                validation_command="python -m pytest tests/test_model_gateway_health_plan.py tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py -q",
            ),
            ReleaseCheck(
                id="model-gateway-probe-evaluation",
                title="Model gateway probe evaluation coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_gateway_probe_evaluation.py",
                    "app/backend/tests/test_model_gateway_probe_evaluation.py",
                    "docs/MODEL_GATEWAY_PROBE_EVALUATION.md",
                ),
                validation_command="python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_gateway_health_plan.py tests/test_model_catalog.py -q",
            ),
            ReleaseCheck(
                id="model-lifecycle-policy",
                title="Gemini model lifecycle policy coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_lifecycle_policy.py",
                    "app/backend/tests/test_model_lifecycle_policy.py",
                    "docs/MODEL_LIFECYCLE_POLICY.md",
                ),
                validation_command="python -m pytest tests/test_model_lifecycle_policy.py tests/test_model_catalog.py tests/test_model_ops_readiness.py -q",
            ),
            ReleaseCheck(
                id="model-ops-readiness",
                title="Model operations readiness coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_ops_readiness.py",
                    "app/backend/tests/test_model_ops_readiness.py",
                    "docs/MODEL_OPS_READINESS.md",
                ),
                validation_command="python -m pytest tests/test_model_ops_readiness.py -q",
            ),
            ReleaseCheck(
                id="model-runtime-router",
                title="Runtime model router coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_runtime_router.py",
                    "app/backend/tests/test_model_runtime_router.py",
                    "app/backend/tests/test_aihub_runtime_routing.py",
                    "docs/MODEL_RUNTIME_ROUTER.md",
                ),
                validation_command="python -m pytest tests/test_model_runtime_router.py tests/test_aihub_runtime_routing.py -q",
            ),
            ReleaseCheck(
                id="model-reasoning-policy",
                title="Gemini reasoning effort policy coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_reasoning_policy.py",
                    "app/backend/tests/test_model_reasoning_policy.py",
                    "docs/MODEL_REASONING_POLICY.md",
                ),
                validation_command="python -m pytest tests/test_model_reasoning_policy.py tests/test_aihub_runtime_routing.py -q",
            ),
            ReleaseCheck(
                id="model-request-policy",
                title="Generation request parameter policy coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_request_policy.py",
                    "app/backend/tests/test_model_request_policy.py",
                    "docs/MODEL_REQUEST_POLICY.md",
                ),
                validation_command="python -m pytest tests/test_model_request_policy.py tests/test_aihub_runtime_routing.py -q",
            ),
            ReleaseCheck(
                id="model-request-cost-bounds",
                title="Model request cost bounds coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_request_cost_bounds.py",
                    "app/backend/tests/test_model_request_cost_bounds.py",
                    "docs/MODEL_REQUEST_COST_BOUNDS.md",
                ),
                validation_command="python -m pytest tests/test_model_request_cost_bounds.py tests/test_model_request_policy.py -q",
            ),
            ReleaseCheck(
                id="model-cache-policy",
                title="Model cache policy coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_cache_policy.py",
                    "app/backend/tests/test_model_cache_policy.py",
                    "docs/MODEL_CACHE_POLICY.md",
                ),
                validation_command="python -m pytest tests/test_model_cache_policy.py tests/test_model_ops_readiness.py -q",
            ),
            ReleaseCheck(
                id="model-route-telemetry",
                title="Model route telemetry coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_route_telemetry.py",
                    "app/backend/tests/test_model_route_telemetry.py",
                    "docs/MODEL_ROUTE_TELEMETRY.md",
                ),
                validation_command="python -m pytest tests/test_model_route_telemetry.py tests/test_aihub_runtime_routing.py -q",
            ),
            ReleaseCheck(
                id="model-route-guardrails",
                title="Model route guardrail coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_route_guardrails.py",
                    "app/backend/tests/test_model_route_guardrails.py",
                    "docs/MODEL_ROUTE_GUARDRAILS.md",
                ),
                validation_command="python -m pytest tests/test_model_route_guardrails.py -q",
            ),
            ReleaseCheck(
                id="model-task-inference",
                title="Model task inference coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_task_inference.py",
                    "app/backend/tests/test_model_task_inference.py",
                    "docs/MODEL_TASK_INFERENCE.md",
                ),
                validation_command="python -m pytest tests/test_model_task_inference.py -q",
            ),
            ReleaseCheck(
                id="model-callsite-audit",
                title="Model callsite task audit coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_callsite_audit.py",
                    "app/backend/tests/test_model_callsite_audit.py",
                    "docs/MODEL_CALLSITE_AUDIT.md",
                ),
                validation_command="python -m pytest tests/test_model_callsite_audit.py -q",
            ),
            ReleaseCheck(
                id="model-escalation-policy",
                title="Cheap-first model escalation policy coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_escalation_policy.py",
                    "app/backend/tests/test_model_escalation_policy.py",
                    "docs/MODEL_ESCALATION_POLICY.md",
                ),
                validation_command="python -m pytest tests/test_model_escalation_policy.py -q",
            ),
            ReleaseCheck(
                id="model-cost-forecast",
                title="Model cost forecast coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_cost_forecast.py",
                    "app/backend/tests/test_model_cost_forecast.py",
                    "docs/MODEL_COST_FORECAST.md",
                ),
                validation_command="python -m pytest tests/test_model_cost_forecast.py -q",
            ),
            ReleaseCheck(
                id="model-cost-guardrails",
                title="Model cost guardrail coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_cost_guardrails.py",
                    "app/backend/tests/test_model_cost_guardrails.py",
                    "docs/MODEL_COST_GUARDRAILS.md",
                ),
                validation_command="python -m pytest tests/test_model_cost_guardrails.py -q",
            ),
            ReleaseCheck(
                id="model-routing-replay",
                title="Model routing replay coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_routing_replay.py",
                    "app/backend/tests/test_model_routing_replay.py",
                    "docs/MODEL_ROUTING_REPLAY.md",
                ),
                validation_command="python -m pytest tests/test_model_routing_replay.py -q",
            ),
            ReleaseCheck(
                id="model-fallback-chains",
                title="Model fallback chain coverage",
                category="model_ops",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/model_fallback_chains.py",
                    "app/backend/tests/test_model_fallback_chains.py",
                    "docs/MODEL_FALLBACK_CHAINS.md",
                ),
                validation_command="python -m pytest tests/test_model_fallback_chains.py -q",
            ),
            ReleaseCheck(
                id="document-preflight",
                title="Document preflight routing coverage",
                category="legal_quality",
                required=True,
                owner="legal_review_owner",
                evidence_paths=(
                    "app/backend/services/document_preflight.py",
                    "app/backend/services/document_strategy.py",
                    "app/backend/tests/test_document_preflight.py",
                    "docs/DOCUMENT_PREFLIGHT.md",
                ),
                validation_command="python -m pytest tests/test_document_preflight.py -q",
            ),
            ReleaseCheck(
                id="extraction-quality",
                title="Extraction quality audit coverage",
                category="tests",
                required=True,
                owner="engineering",
                evidence_paths=(
                    "app/backend/services/extraction_quality.py",
                    "app/backend/tests/test_extraction_quality.py",
                    "docs/EXTRACTION_QUALITY_AUDIT.md",
                ),
                validation_command="python -m pytest tests/test_extraction_quality.py -q",
            ),
            ReleaseCheck(
                id="privacy-redaction",
                title="Privacy redaction coverage",
                category="security",
                required=True,
                owner="security_privacy_owner",
                evidence_paths=(
                    "app/backend/services/privacy_redaction.py",
                    "app/backend/tests/test_privacy_redaction.py",
                    "docs/PRIVACY_REDACTION.md",
                ),
                validation_command="python -m pytest tests/test_privacy_redaction.py -q",
            ),
            ReleaseCheck(
                id="instruction-injection-audit",
                title="Instruction injection audit coverage",
                category="security",
                required=True,
                owner="security_privacy_owner",
                evidence_paths=(
                    "app/backend/services/instruction_injection_audit.py",
                    "app/backend/tests/test_instruction_injection_audit.py",
                    "docs/INSTRUCTION_INJECTION_AUDIT.md",
                ),
                validation_command="python -m pytest tests/test_instruction_injection_audit.py -q",
            ),
            ReleaseCheck(
                id="feedback-triage",
                title="Feedback triage coverage",
                category="maintenance",
                required=True,
                owner="support_ops",
                evidence_paths=(
                    "app/backend/services/feedback_triage.py",
                    "app/backend/tests/test_feedback_triage.py",
                    "docs/FEEDBACK_TRIAGE.md",
                ),
                validation_command="python -m pytest tests/test_feedback_triage.py -q",
            ),
            ReleaseCheck(
                id="feedback-roadmap-alignment",
                title="Feedback roadmap alignment coverage",
                category="maintenance",
                required=True,
                owner="product_maintainer",
                evidence_paths=(
                    "app/backend/services/feedback_roadmap_alignment.py",
                    "app/backend/tests/test_feedback_roadmap_alignment.py",
                    "docs/FEEDBACK_ROADMAP_ALIGNMENT.md",
                ),
                validation_command="python -m pytest tests/test_feedback_roadmap_alignment.py -q",
            ),
            ReleaseCheck(
                id="user-needs-radar",
                title="User needs radar coverage",
                category="maintenance",
                required=True,
                owner="product_maintainer",
                evidence_paths=(
                    "app/backend/services/user_needs_radar.py",
                    "app/backend/tests/test_user_needs_radar.py",
                    "docs/USER_NEEDS_RADAR.md",
                ),
                validation_command="python -m pytest tests/test_user_needs_radar.py -q",
            ),
            ReleaseCheck(
                id="legal-review-benchmark",
                title="Legal review benchmark coverage",
                category="legal_quality",
                required=True,
                owner="legal_review_owner",
                evidence_paths=(
                    "app/backend/services/legal_review_benchmark.py",
                    "app/backend/services/legal_research_backlog.py",
                    "app/frontend/src/lib/maintenanceApi.ts",
                    "app/frontend/src/pages/MaintenanceEvidencePage.tsx",
                    "app/backend/services/legal_public_benchmark_sampler.py",
                    "app/backend/services/legal_fixture_quick_suite.py",
                    "app/backend/services/legal_fixture_model_matrix.py",
                    "app/backend/services/legal_fixture_prompt_pack.py",
                    "app/backend/services/legal_fixture_gateway_manifest.py",
                    "app/backend/services/legal_fixture_run_plan.py",
                    "app/backend/services/legal_fixture_local_run_package.py",
                    "app/backend/services/legal_fixture_response_normalizer.py",
                    "app/backend/services/legal_fixture_local_run_review.py",
                    "app/backend/services/legal_fixture_run_report.py",
                    "app/backend/services/legal_fixture_evidence_bundle.py",
                    "app/backend/services/legal_fixture_improvement.py",
                    "app/backend/tests/test_legal_review_benchmark.py",
                    "app/backend/tests/test_legal_research_backlog.py",
                    "app/backend/tests/test_legal_public_benchmark_sampler.py",
                    "app/backend/tests/test_legal_fixture_quick_suite.py",
                    "app/backend/tests/test_legal_fixture_model_matrix.py",
                    "app/backend/tests/test_legal_fixture_prompt_pack.py",
                    "app/backend/tests/test_legal_fixture_gateway_manifest.py",
                    "app/backend/tests/test_legal_fixture_run_plan.py",
                    "app/backend/tests/test_legal_fixture_local_run_package.py",
                    "app/backend/tests/test_legal_fixture_response_normalizer.py",
                    "app/backend/tests/test_legal_fixture_local_run_review.py",
                    "app/backend/tests/test_legal_fixture_run_report.py",
                    "app/backend/tests/test_legal_fixture_evidence_bundle.py",
                    "app/backend/tests/test_legal_fixture_improvement.py",
                    "docs/LEGAL_REVIEW_BENCHMARK.md",
                    "docs/LEGAL_RESEARCH_BACKLOG.md",
                    "docs/LEGAL_BENCHMARK_FIXTURES.md",
                    "docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md",
                    "docs/LEGAL_FIXTURE_QUICK_SUITE.md",
                    "docs/LEGAL_FIXTURE_MODEL_MATRIX.md",
                    "docs/LEGAL_FIXTURE_PROMPT_PACK.md",
                    "docs/LEGAL_FIXTURE_GATEWAY_MANIFEST.md",
                    "docs/LEGAL_FIXTURE_RUN_PLAN.md",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_PACKAGE.md",
                    "docs/LEGAL_FIXTURE_RESPONSE_NORMALIZER.md",
                    "docs/LEGAL_FIXTURE_LOCAL_RUN_REVIEW.md",
                    "docs/LEGAL_FIXTURE_RUN_REPORT.md",
                    "docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md",
                    "docs/LEGAL_FIXTURE_IMPROVEMENT.md",
                ),
                validation_command="python -m pytest tests/test_legal_research_backlog.py tests/test_legal_review_benchmark.py tests/test_legal_public_benchmark_sampler.py tests/test_legal_fixture_quick_suite.py tests/test_legal_fixture_model_matrix.py tests/test_legal_fixture_prompt_pack.py tests/test_legal_fixture_gateway_manifest.py tests/test_legal_fixture_run_plan.py tests/test_legal_fixture_local_run_package.py tests/test_legal_fixture_response_normalizer.py tests/test_legal_fixture_local_run_review.py tests/test_legal_fixture_run_report.py tests/test_legal_fixture_evidence_bundle.py tests/test_legal_fixture_improvement.py -q",
            ),
            ReleaseCheck(
                id="legal-knowledge-audit",
                title="Legal knowledge seed audit coverage",
                category="legal_quality",
                required=True,
                owner="legal_knowledge_owner",
                evidence_paths=(
                    "app/backend/services/legal_knowledge_audit.py",
                    "app/backend/tests/test_legal_knowledge_audit.py",
                    "docs/LEGAL_KNOWLEDGE_AUDIT.md",
                ),
                validation_command="python -m pytest tests/test_legal_knowledge_audit.py -q",
            ),
            ReleaseCheck(
                id="legal-rag-evaluation",
                title="Legal RAG evaluation coverage",
                category="legal_quality",
                required=True,
                owner="legal_review_owner",
                evidence_paths=(
                    "app/backend/services/legal_rag_evaluation.py",
                    "app/backend/services/legal_grounding_quick_audit.py",
                    "app/backend/tests/test_legal_rag_evaluation.py",
                    "app/backend/tests/test_legal_grounding_quick_audit.py",
                    "docs/LEGAL_RAG_EVALUATION.md",
                    "docs/LEGAL_GROUNDING_QUICK_AUDIT.md",
                ),
                validation_command="python -m pytest tests/test_legal_grounding_quick_audit.py tests/test_legal_rag_evaluation.py tests/test_citation_audit.py tests/test_evidence_audit.py -q",
            ),
            ReleaseCheck(
                id="continuous-update-ledger",
                title="Continuous update ledger evidence",
                category="maintenance",
                required=False,
                owner="project_maintainer",
                evidence_paths=(
                    "app/backend/services/continuous_update_ledger.py",
                    "app/backend/tests/test_continuous_update_ledger.py",
                    "docs/CONTINUOUS_UPDATE_LEDGER.md",
                ),
                validation_command="python -m pytest tests/test_continuous_update_ledger.py -q",
                manual_note="This is progress evidence only; it must not claim the 24-hour or 100-update goal is complete before both are reviewable.",
            ),
            ReleaseCheck(
                id="oss-maintenance-evidence",
                title="OSS maintenance evidence",
                category="maintenance",
                required=False,
                owner="project_maintainer",
                evidence_paths=(
                    "app/backend/services/maintenance_evidence.py",
                    "app/backend/tests/test_maintenance_evidence.py",
                    "docs/OSS_MAINTENANCE_EVIDENCE.md",
                ),
                validation_command="python -m pytest tests/test_maintenance_evidence.py -q",
            ),
        ]

    def _state(self, value: str | None) -> ValidationState:
        normalized = str(value or "not_run").strip().lower()
        if normalized in {"pass", "passed", "ok", "success"}:
            return "pass"
        if normalized in {"fail", "failed", "error"}:
            return "fail"
        if normalized in {"waive", "waived", "skip", "skipped"}:
            return "waived"
        return "not_run"

    def _summary(self, status: str, blocking: list[dict[str, Any]], failed: list[dict[str, Any]]) -> str:
        if status == "ready_for_release_candidate":
            return "All required release checks passed or were explicitly waived."
        if failed:
            return f"Release is blocked by failed checks: {', '.join(check['id'] for check in failed)}."
        return f"Release requires validation for: {', '.join(check['id'] for check in blocking)}."
