from __future__ import annotations

from typing import Any

from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.model_route_legal_benchmark_risk_queue import ModelRouteLegalBenchmarkRiskQueueService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService


APPROVED_REVIEW_STATES = {"approved", "pass", "ok"}


class LegalPublicBenchmarkLicenseGateService:
    """Review public legal benchmark source readiness without importing samples."""

    def __init__(
        self,
        sampler_service: LegalPublicBenchmarkSamplerService | None = None,
        user_need_coverage_service: UserNeedBenchmarkCoverageService | None = None,
        route_risk_service: ModelRouteLegalBenchmarkRiskQueueService | None = None,
    ) -> None:
        self.sampler_service = sampler_service or LegalPublicBenchmarkSamplerService()
        self.user_need_coverage_service = user_need_coverage_service or UserNeedBenchmarkCoverageService()
        self.route_risk_service = route_risk_service or ModelRouteLegalBenchmarkRiskQueueService()

    def build_gate(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        data = config if isinstance(config, dict) else {}
        sampler = self.sampler_service.build_plan(data)
        user_need_coverage = self.user_need_coverage_service.build_coverage()
        route_risk_queue = self.route_risk_service.build_queue()
        source_rows = [
            self._source_row(source, data, user_need_coverage, route_risk_queue)
            for source in sampler["source_plans"]
        ]
        user_need_rows = self._user_need_rows(source_rows, user_need_coverage)
        ready_rows = [row for row in source_rows if row["review_state"] == "approved"]
        review_rows = [row for row in source_rows if row["review_state"] == "license_review_required"]
        catalog_rows = [row for row in source_rows if row["review_state"] == "catalog_only"]
        claim_block_rows = [row for row in source_rows if row["release_claim_blocked"]]
        status = "ready" if not review_rows and not claim_block_rows else "review_required"

        return {
            "id": "legal-public-benchmark-license-gate",
            "title": "Legal public benchmark license gate",
            "status": status,
            "method": {
                "type": "metadata-only-public-benchmark-license-gate",
                "notes": [
                    "Joins public benchmark sampler source states with user-need coverage and model-route risk metadata.",
                    "Blocks public benchmark sample import until license, attribution, privacy, and storage review are explicit.",
                    "Keeps corpus-scale sources catalog-only unless a separate resource-controlled job is approved.",
                    "Does not download datasets, call models, call gateways, or return public benchmark text.",
                ],
            },
            "summary": {
                "source_count": len(source_rows),
                "approved_source_count": len(ready_rows),
                "license_review_required_source_count": len(review_rows),
                "catalog_only_source_count": len(catalog_rows),
                "release_claim_blocked_source_count": len(claim_block_rows),
                "linked_user_need_count": len(user_need_rows),
                "linked_route_task_count": len(
                    {
                        task_id
                        for row in source_rows
                        for task_id in row["linked_route_task_ids"]
                    }
                ),
                "sampling_ready_source_count": sampler["summary"]["sampling_ready_source_count"],
                "network_called": False,
                "dataset_downloaded": False,
                "model_called": False,
                "gateway_called": False,
                "raw_public_text_returned": False,
                "configuration_written": False,
            },
            "source_rows": source_rows,
            "user_need_rows": user_need_rows,
            "review_policy": {
                "default_decision": "block_public_sample_import",
                "approved_sampling_scope": "capped metadata-driven sampling only",
                "requires_license_review": True,
                "requires_attribution_review": True,
                "requires_privacy_review": True,
                "requires_storage_policy_review": True,
                "requires_local_fixture_mapping": True,
                "allows_raw_public_text_by_default": False,
                "allows_public_score_claim_by_default": False,
                "allows_gateway_calls": False,
                "allows_dataset_downloads": False,
            },
            "blocking_check_ids": [f"source:{row['source_id']}" for row in claim_block_rows],
            "warning_check_ids": [f"source:{row['source_id']}" for row in review_rows],
            "recommended_actions": self._recommended_actions(source_rows),
            "privacy_boundary": {
                "returns_public_benchmark_text": False,
                "returns_dataset_samples": False,
                "returns_raw_legal_text": False,
                "returns_fixture_snippets": False,
                "returns_prompts": False,
                "returns_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "network_called": False,
                "dataset_downloaded": False,
                "model_called": False,
                "gateway_called": False,
                "output_scope": "source ids, task labels, user-need ids, route task ids, checklist states, and actions only",
            },
            "claim_boundary": {
                "public_benchmark_scores_claimed": False,
                "leaderboard_rank_claimed": False,
                "external_dataset_execution_claimed": False,
                "production_accuracy_claimed": False,
                "real_client_document_validation_claimed": False,
                "automatic_license_clearance_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_legal_public_benchmark_license_gate.py tests/test_legal_public_benchmark_sampler.py -q",
                "python -m pytest tests/test_user_need_benchmark_coverage.py tests/test_model_route_legal_benchmark_risk_queue.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _source_row(
        self,
        source: dict[str, Any],
        config: dict[str, Any],
        user_need_coverage: dict[str, Any],
        route_risk_queue: dict[str, Any],
    ) -> dict[str, Any]:
        source_id = str(source.get("source_id") or "")
        review_state = self._review_state(source, config)
        decision = self._decision(source, review_state)
        linked_user_need_ids = sorted(
            {
                str(row["need_id"])
                for row in user_need_coverage.get("coverage_rows", [])
                if source_id in {str(item) for item in row.get("linked_public_source_ids", [])}
            }
        )
        linked_route_task_ids = sorted(
            {
                str(row["task_id"])
                for row in route_risk_queue.get("queue_rows", [])
                if source_id in {str(item) for item in row.get("research_source_ids", [])}
            }
        )
        return {
            "id": f"{source_id}-license-gate",
            "source_id": source_id,
            "title": str(source.get("title") or source_id),
            "url": str(source.get("url") or ""),
            "priority": str(source.get("priority") or "medium"),
            "resource_profile": str(source.get("resource_profile") or "unknown"),
            "sampling_state": str(source.get("sampling_state") or "unknown"),
            "review_state": review_state,
            "decision": decision,
            "release_claim_blocked": decision != "allow_capped_metadata_sampling",
            "max_samples": _safe_int(source.get("max_samples")),
            "license_gate": str(source.get("license_gate") or "license_review_required"),
            "source_license_note": str(source.get("source_license_note") or ""),
            "linked_user_need_ids": linked_user_need_ids,
            "linked_route_task_ids": linked_route_task_ids,
            "validation_targets": [str(item) for item in source.get("validation_targets", [])],
            "required_checks": self._required_checks(source, review_state),
            "next_action": self._next_action(source, decision),
            "raw_text_import_allowed": False,
            "public_score_claim_allowed": False,
            "dataset_download_allowed": False,
            "network_call_allowed": False,
        }

    def _review_state(self, source: dict[str, Any], config: dict[str, Any]) -> str:
        if str(source.get("sampling_state") or "") == "catalog_only":
            return "catalog_only"
        reviews = config.get("license_reviews") if isinstance(config.get("license_reviews"), dict) else {}
        state = str(reviews.get(str(source.get("source_id") or "")) or "").strip().lower()
        if state in APPROVED_REVIEW_STATES and str(source.get("sampling_state") or "") == "sampling_ready":
            return "approved"
        return "license_review_required"

    def _decision(self, source: dict[str, Any], review_state: str) -> str:
        if review_state == "approved" and _safe_int(source.get("max_samples")) > 0:
            return "allow_capped_metadata_sampling"
        if review_state == "catalog_only":
            return "keep_catalog_only"
        return "block_public_sample_import"

    def _required_checks(self, source: dict[str, Any], review_state: str) -> list[dict[str, Any]]:
        approved = review_state == "approved"
        catalog_only = review_state == "catalog_only"
        checks = [
            ("license_terms_review", "Confirm source terms allow the intended capped sample use.", approved),
            ("attribution_plan", "Record source title, URL, subset or task family, and attribution note.", approved),
            ("privacy_review", "Confirm no personal data or sensitive legal text will enter local defaults.", approved),
            ("sample_cap_review", "Keep source sample count within the sampler max_samples cap.", approved or catalog_only),
            ("storage_policy_review", "Store only source ids, labels, observations, and attribution notes by default.", approved or catalog_only),
            ("local_fixture_mapping", "Map observations to synthetic local fixture ids before release claims.", True),
            ("route_risk_review", "Check cheap-first route-risk rows before model default promotion.", True),
        ]
        return [
            {
                "id": check_id,
                "status": "pass" if passed else "review_required",
                "required": True,
                "detail": detail,
            }
            for check_id, detail, passed in checks
        ]

    def _next_action(self, source: dict[str, Any], decision: str) -> str:
        source_id = str(source.get("source_id") or "source")
        if decision == "allow_capped_metadata_sampling":
            return f"Run capped metadata sampling for {source_id}; keep raw text and public score claims out of default evidence."
        if decision == "keep_catalog_only":
            return f"Keep {source_id} catalog-only until a separate resource-controlled and license-reviewed job exists."
        return f"Complete license, attribution, privacy, and storage review before importing any {source_id} sample."

    def _user_need_rows(
        self,
        source_rows: list[dict[str, Any]],
        user_need_coverage: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows = []
        for coverage in user_need_coverage.get("coverage_rows", []):
            need_id = str(coverage.get("need_id") or "")
            linked_sources = [
                row
                for row in source_rows
                if need_id in row["linked_user_need_ids"]
            ]
            if not linked_sources:
                continue
            blocked_sources = [row["source_id"] for row in linked_sources if row["release_claim_blocked"]]
            approved_sources = [row["source_id"] for row in linked_sources if row["review_state"] == "approved"]
            rows.append(
                {
                    "need_id": need_id,
                    "title": str(coverage.get("title") or need_id),
                    "priority_band": str(coverage.get("priority_band") or "unknown"),
                    "coverage_status": str(coverage.get("coverage_status") or "unknown"),
                    "linked_source_ids": [row["source_id"] for row in linked_sources],
                    "approved_source_ids": approved_sources,
                    "blocked_source_ids": blocked_sources,
                    "release_claim_blocked": bool(blocked_sources),
                    "next_action": (
                        "Keep public benchmark claims blocked until mapped sources pass license review."
                        if blocked_sources
                        else "Use approved source metadata only with synthetic fixture comparison."
                    ),
                }
            )
        rows.sort(key=lambda item: (item["release_claim_blocked"], len(item["blocked_source_ids"])), reverse=True)
        return rows

    def _recommended_actions(self, source_rows: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Keep public benchmark evidence metadata-only until source-level license, attribution, privacy, and storage review passes.",
            "Use synthetic local legal fixtures for default laptop tests; public sources may only add capped reviewed metadata.",
        ]
        blocked = [row["source_id"] for row in source_rows if row["decision"] == "block_public_sample_import"]
        catalog_only = [row["source_id"] for row in source_rows if row["decision"] == "keep_catalog_only"]
        if blocked:
            actions.append(f"Complete review before sampling: {', '.join(blocked[:6])}.")
        if catalog_only:
            actions.append(f"Keep corpus-scale sources catalog-only by default: {', '.join(catalog_only[:6])}.")
        return actions


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
