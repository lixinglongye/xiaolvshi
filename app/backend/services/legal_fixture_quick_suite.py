from __future__ import annotations

from typing import Any

from services.legal_fixture_run_plan import LegalFixtureRunPlanService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.legal_review_benchmark import LegalReviewBenchmarkService


DEFAULT_FIXTURE_PRIORITY = (
    "fixture-service-agreement-small",
    "fixture-lease-dispute-notice-small",
    "fixture-low-text-pdf-page-small",
    "fixture-adversarial-upload-small",
)


class LegalFixtureQuickSuiteService:
    """Build a tiny legal benchmark run plan for low-resource local machines."""

    def __init__(
        self,
        benchmark_service: LegalReviewBenchmarkService | None = None,
        run_plan_service: LegalFixtureRunPlanService | None = None,
        sampler_service: LegalPublicBenchmarkSamplerService | None = None,
    ) -> None:
        self.benchmark_service = benchmark_service or LegalReviewBenchmarkService()
        self.run_plan_service = run_plan_service or LegalFixtureRunPlanService()
        self.sampler_service = sampler_service or LegalPublicBenchmarkSamplerService()

    def build_suite(self, fixture_limit: int = 3) -> dict[str, Any]:
        suite = self.benchmark_service.build_suite()
        smoke_template = suite["fixture_smoke_template"]
        run_plan = self.run_plan_service.build_plan()
        public_sampler = self.sampler_service.build_plan()
        selected_ids = self._selected_fixture_ids(smoke_template["fixtures"], fixture_limit)
        cheap_steps = [
            step
            for step in run_plan["steps"]
            if step["phase"] == "cheap_first" and step["fixture_id"] in selected_ids
        ]
        fixtures_by_id = {fixture["id"]: fixture for fixture in smoke_template["fixtures"]}
        selected_fixtures = [
            self._fixture_row(fixtures_by_id[step["fixture_id"]], step, public_sampler)
            for step in sorted(cheap_steps, key=lambda item: selected_ids.index(item["fixture_id"]))
            if step["fixture_id"] in fixtures_by_id
        ]
        mapped_sources = self._public_source_mapping(public_sampler, selected_ids)
        estimated_cost = sum(step["estimated_request_cost_usd"] or 0.0 for step in cheap_steps)
        status = "ready" if selected_fixtures and run_plan["status"] in {"ready", "pass"} else "warn"
        return {
            "status": status,
            "method": {
                "type": "low-resource-legal-fixture-quick-suite",
                "notes": [
                    "Uses existing synthetic legal fixtures only; no public benchmark download is performed.",
                    "Runs cheap_first fixture batches serially with max_parallel_requests fixed at 1.",
                    "Public benchmark sources remain metadata mappings until license and attribution review is complete.",
                    "Submit normalized observations to fixture-smoke, then fixture-run-report and fixture-evidence-bundle.",
                ],
            },
            "summary": {
                "selected_fixture_count": len(selected_fixtures),
                "available_fixture_count": smoke_template["fixture_count"],
                "benchmark_case_count": suite["case_count"],
                "public_source_count": public_sampler["summary"]["source_count"],
                "mapped_public_source_count": len(mapped_sources),
                "license_review_required_source_count": sum(
                    1 for row in mapped_sources if row["sampling_state"] == "license_review_required"
                ),
                "catalog_only_source_count": sum(1 for row in mapped_sources if row["sampling_state"] == "catalog_only"),
                "estimated_cheap_first_cost_usd": round(estimated_cost, 8),
                "max_parallel_requests": 1,
                "network_access": "disabled_by_default",
                "model_call_policy": "manual_serial_only",
            },
            "selected_fixtures": selected_fixtures,
            "quick_steps": self._quick_steps(selected_fixtures),
            "public_source_mapping": mapped_sources,
            "observation_template": {
                fixture_id: smoke_template["default_observations"][fixture_id]
                for fixture_id in selected_ids
                if fixture_id in smoke_template["default_observations"]
            },
            "validation_commands": [
                "python -m pytest tests/test_legal_fixture_quick_suite.py tests/test_legal_review_benchmark.py -q",
                "python -m pytest tests/test_legal_fixture_run_plan.py tests/test_legal_public_benchmark_sampler.py -q",
            ],
            "release_evidence_targets": [
                "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
                "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
                "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
            ],
            "recommended_actions": self._recommended_actions(mapped_sources),
            "privacy_note": (
                "The quick suite contains synthetic fixture excerpts, model IDs, cost estimates, and public source metadata only. "
                "Do not paste real client documents, public benchmark raw text, emails, API keys, or raw model outputs into source control."
            ),
        }

    def _selected_fixture_ids(self, fixtures: list[dict[str, Any]], fixture_limit: int) -> list[str]:
        known_ids = {str(fixture["id"]) for fixture in fixtures}
        try:
            requested_limit = int(fixture_limit)
        except (TypeError, ValueError):
            requested_limit = 3
        limit = max(1, min(requested_limit, len(known_ids)))
        prioritized = [fixture_id for fixture_id in DEFAULT_FIXTURE_PRIORITY if fixture_id in known_ids]
        remainder = sorted(known_ids - set(prioritized))
        return (prioritized + remainder)[:limit]

    def _fixture_row(
        self,
        fixture: dict[str, Any],
        step: dict[str, Any],
        public_sampler: dict[str, Any],
    ) -> dict[str, Any]:
        mapped_sources = [
            source["source_id"]
            for source in public_sampler["source_plans"]
            if fixture["id"] in source["local_fixture_ids"]
        ]
        return {
            "fixture_id": fixture["id"],
            "title": fixture["title"],
            "matter_type": fixture["matter_type"],
            "task": step["task"],
            "model": step["model"],
            "model_cost_tier": step["model_cost_tier"],
            "estimated_request_cost_usd": step["estimated_request_cost_usd"],
            "prompt_tokens_estimate": step["prompt_tokens_estimate"],
            "completion_tokens_budget": step["completion_tokens_budget"],
            "expected_routes": fixture["expected_routes"],
            "expected_tasks": fixture["expected_tasks"],
            "expected_signals": fixture["expected_signals"],
            "linked_case_ids": fixture["linked_case_ids"],
            "public_source_ids": mapped_sources,
            "input_char_count": len(str(fixture["input_excerpt"])),
            "input_excerpt": fixture["input_excerpt"],
            "observation_target": step["observation_target"],
            "improvement_target": step["improvement_target"],
            "run_condition": "always in quick-suite cheap_first phase",
        }

    def _public_source_mapping(self, public_sampler: dict[str, Any], selected_ids: list[str]) -> list[dict[str, Any]]:
        rows = []
        selected = set(selected_ids)
        for source in public_sampler["source_plans"]:
            fixture_ids = [fixture_id for fixture_id in source["local_fixture_ids"] if fixture_id in selected]
            if not fixture_ids:
                continue
            rows.append(
                {
                    "source_id": source["source_id"],
                    "title": source["title"],
                    "sampling_state": source["sampling_state"],
                    "resource_profile": source["resource_profile"],
                    "local_fixture_ids": fixture_ids,
                    "benchmark_case_ids": source["benchmark_case_ids"],
                    "validation_targets": source["validation_targets"],
                    "license_gate": source["license_gate"],
                    "download_policy": source["download_policy"],
                    "run_policy": "metadata_only_until_license_review_passes",
                }
            )
        return rows

    def _quick_steps(self, selected_fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
        fixture_ids = [fixture["fixture_id"] for fixture in selected_fixtures]
        return [
            {
                "order": 1,
                "id": "fetch-quick-suite",
                "action": "Fetch this endpoint and keep fixture_limit small.",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/quick-suite",
            },
            {
                "order": 2,
                "id": "run-cheap-first-serial",
                "action": "Run selected fixture prompts one at a time using cheap_first models.",
                "fixture_ids": fixture_ids,
                "max_parallel_requests": 1,
            },
            {
                "order": 3,
                "id": "score-fixture-smoke",
                "action": "Submit normalized observations to fixture-smoke.",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
            },
            {
                "order": 4,
                "id": "bundle-evidence",
                "action": "Submit the same observations to run-report and evidence-bundle before changing defaults.",
                "endpoints": [
                    "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
                    "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
                ],
            },
        ]

    def _recommended_actions(self, mapped_sources: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Use this quick suite for laptop checks before running the full legal fixture run plan.",
            "Keep public benchmark rows as source metadata until license, attribution, and privacy review are complete.",
            "Escalate only selected fixtures that fail fixture-smoke coverage.",
        ]
        if any(row["sampling_state"] == "catalog_only" for row in mapped_sources):
            actions.append("Treat corpus-scale sources as design references, not default local tests.")
        return actions
