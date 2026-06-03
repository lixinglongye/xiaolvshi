from __future__ import annotations

from typing import Any

from services.legal_fixture_gateway_manifest import LegalFixtureGatewayManifestService
from services.legal_fixture_improvement import LegalFixtureImprovementService
from services.legal_fixture_model_matrix import LegalFixtureModelMatrixService
from services.legal_fixture_prompt_pack import LegalFixturePromptPackService
from services.legal_fixture_run_plan import LegalFixtureRunPlanService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.legal_review_benchmark import LegalReviewBenchmarkService


class LegalFixtureEvidenceBundleService:
    """Bundle legal fixture evidence for release readiness and OSS support applications."""

    def __init__(self) -> None:
        self.benchmark_service = LegalReviewBenchmarkService()
        self.model_matrix_service = LegalFixtureModelMatrixService()
        self.prompt_pack_service = LegalFixturePromptPackService()
        self.gateway_manifest_service = LegalFixtureGatewayManifestService()
        self.run_plan_service = LegalFixtureRunPlanService()
        self.run_report_service = LegalFixtureRunReportService()
        self.improvement_service = LegalFixtureImprovementService()
        self.public_sampler_service = LegalPublicBenchmarkSamplerService()

    def build_bundle(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        observations = self._observations(payload)
        benchmark_suite = self.benchmark_service.build_suite()
        smoke = self.benchmark_service.evaluate_fixture_smoke(observations)
        model_matrix = self.model_matrix_service.build_matrix()
        prompt_pack = self.prompt_pack_service.build_pack()
        gateway_manifest = self.gateway_manifest_service.build_manifest()
        public_sampler = self.public_sampler_service.build_plan()
        run_plan = self.run_plan_service.build_plan()
        run_report = self.run_report_service.build_report(payload)
        improvement = self.improvement_service.build_plan(observations)
        components = [
            self._component("benchmark_suite", benchmark_suite["status"], "/api/v1/maintenance/legal-review-benchmark"),
            self._component("fixture_smoke", smoke["status"], "/api/v1/maintenance/legal-review-benchmark/fixture-smoke"),
            self._component("model_matrix", model_matrix["status"], "/api/v1/maintenance/legal-review-benchmark/fixture-model-matrix"),
            self._component("prompt_pack", prompt_pack["status"], "/api/v1/maintenance/legal-review-benchmark/prompt-pack"),
            self._component("gateway_manifest", gateway_manifest["status"], "/api/v1/maintenance/legal-review-benchmark/gateway-manifest"),
            self._component("public_sampler", public_sampler["status"], "/api/v1/maintenance/legal-review-benchmark/public-sampler"),
            self._component("run_plan", run_plan["status"], "/api/v1/maintenance/legal-review-benchmark/fixture-run-plan"),
            self._component("run_report", run_report["status"], "/api/v1/maintenance/legal-review-benchmark/fixture-run-report"),
            self._component("improvement_plan", improvement["status"], "/api/v1/maintenance/legal-review-benchmark/fixture-improvements"),
        ]
        blocking = [item for item in components if item["status"] in {"fail", "needs_escalation", "needs_improvement"}]
        warnings = [item for item in components if item["status"] in {"warn", "review_recommended"}]
        not_run = [item for item in components if item["status"] == "not_run"]
        return {
            "status": self._status(blocking, warnings, not_run),
            "method": {
                "type": "legal-fixture-release-evidence-bundle",
                "notes": [
                    "Bundles deterministic local fixture evidence only; it never calls a model or gateway.",
                    "POST accepts the same observations and run_metadata shape used by fixture-run-report.",
                    "The bundle is safe for release notes and support applications after maintainer review.",
                ],
            },
            "summary": {
                "component_count": len(components),
                "blocking_component_count": len(blocking),
                "warning_component_count": len(warnings),
                "not_run_component_count": len(not_run),
                "fixture_count": run_plan["summary"]["fixture_count"],
                "prompt_count": prompt_pack["summary"]["fixture_count"],
                "cheap_first_candidate_count": model_matrix["summary"]["cheap_first_candidate_count"],
                "observed_fixture_count": run_report["summary"]["observed_fixture_count"],
                "public_sampler_source_count": public_sampler["summary"]["source_count"],
                "release_decision": run_report["release_decision"],
                "estimated_cheap_first_cost_usd": run_plan["summary"]["estimated_min_cost_usd"],
                "estimated_worst_case_cost_usd": run_plan["summary"]["estimated_max_cost_usd"],
            },
            "components": components,
            "artifacts": self._artifacts(),
            "validation_commands": self._validation_commands(),
            "release_claims": self._release_claims(run_report),
            "recommended_actions": self._recommended_actions(blocking, warnings, not_run, run_report),
            "privacy_note": (
                "The bundle references synthetic fixture IDs, scores, model IDs, cost tiers, evidence paths, "
                "and validation commands only. It must not include real client documents, API keys, emails, "
                "or raw model outputs."
            ),
        }

    def _observations(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        if not payload:
            return {}
        observations = payload.get("observations")
        if isinstance(observations, dict):
            return observations
        return payload

    def _component(self, component_id: str, status: str, endpoint: str) -> dict[str, Any]:
        return {
            "id": component_id,
            "status": status,
            "endpoint": endpoint,
        }

    def _artifacts(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "fixture-documents",
                "title": "Lightweight synthetic legal benchmark fixtures",
                "evidence_paths": ["docs/LEGAL_BENCHMARK_FIXTURES.md", "app/backend/services/legal_review_benchmark.py"],
                "archive_fields": ["fixture_count", "expected_signals", "expected_tasks"],
            },
            {
                "id": "fixture-model-matrix",
                "title": "Fixture-level Gemini/NewAPI model matrix",
                "evidence_paths": ["docs/LEGAL_FIXTURE_MODEL_MATRIX.md", "app/backend/services/legal_fixture_model_matrix.py"],
                "archive_fields": ["candidate_ladder", "premium_review_boundary", "cheap_first_candidate_count"],
            },
            {
                "id": "fixture-run-report",
                "title": "Cheap-first fixture run report",
                "evidence_paths": ["docs/LEGAL_FIXTURE_RUN_REPORT.md", "app/backend/services/legal_fixture_run_report.py"],
                "archive_fields": ["release_decision", "fixture_reports", "recommended_actions"],
            },
            {
                "id": "public-benchmark-sampler",
                "title": "Resource-capped public benchmark sampler",
                "evidence_paths": ["docs/LEGAL_PUBLIC_BENCHMARK_SAMPLER.md", "app/backend/services/legal_public_benchmark_sampler.py"],
                "archive_fields": ["source_plans", "sampling_batches", "resource_policy"],
            },
            {
                "id": "fixture-evidence-bundle",
                "title": "Release evidence bundle",
                "evidence_paths": ["docs/LEGAL_FIXTURE_EVIDENCE_BUNDLE.md", "app/backend/services/legal_fixture_evidence_bundle.py"],
                "archive_fields": ["components", "release_claims", "validation_commands"],
            },
        ]

    def _validation_commands(self) -> list[str]:
        return [
            "python -m pytest tests/test_legal_fixture_evidence_bundle.py tests/test_legal_fixture_model_matrix.py tests/test_legal_fixture_run_report.py -q",
            "python -m pytest tests/test_legal_review_benchmark.py tests/test_legal_public_benchmark_sampler.py tests/test_legal_fixture_prompt_pack.py tests/test_legal_fixture_gateway_manifest.py tests/test_legal_fixture_run_plan.py tests/test_legal_fixture_improvement.py -q",
        ]

    def _release_claims(self, run_report: dict[str, Any]) -> dict[str, Any]:
        ready = run_report["release_decision"] == "keep_cheap_first_defaults"
        return {
            "can_claim": [
                "The repository contains synthetic legal fixtures and deterministic smoke evaluators.",
                "Fixture model routing starts from cheap Gemini/NewAPI-compatible candidates.",
                "Premium model use is fixture-scoped and bounded by review/escalation decisions.",
            ],
            "claim_after_run": [
                "Cheap-first fixture outputs passed local smoke coverage."
                if ready
                else "Run fixture observations before claiming cheap-first fixture outputs passed.",
                "No fixture required escalation after smoke scoring."
                if ready
                else "Escalation and prompt/schema gaps must be reviewed before claiming all fixture paths passed.",
            ],
            "must_not_claim": [
                "Do not claim external user adoption, third-party PR volume, or production legal accuracy from this bundle.",
                "Do not claim real client-document benchmark results unless separately reviewed and authorized.",
            ],
        }

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
        not_run: list[dict[str, Any]],
        run_report: dict[str, Any],
    ) -> list[str]:
        if blocking:
            return [f"Resolve blocking fixture evidence component: {item['id']} ({item['status']})." for item in blocking]
        if not_run:
            return ["Run cheap-first fixture batches and POST observations to /fixture-evidence-bundle before using it as release evidence."]
        if warnings:
            return [f"Review warning fixture evidence component: {item['id']} ({item['status']})." for item in warnings]
        if run_report["release_decision"] == "keep_cheap_first_defaults":
            return ["Archive this evidence bundle with release readiness; cheap-first fixture defaults can be preserved."]
        return ["Review fixture-run-report decision before changing model defaults."]

    def _status(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]], not_run: list[dict[str, Any]]) -> str:
        if blocking:
            return "blocked"
        if not_run:
            return "not_run"
        if warnings:
            return "review_recommended"
        return "ready"
