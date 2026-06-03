from __future__ import annotations

from typing import Any

from services.legal_fixture_evidence_bundle import LegalFixtureEvidenceBundleService
from services.legal_fixture_run_report import LegalFixtureRunReportService


RAW_FIELD_NAMES = {
    "api_key",
    "authorization",
    "content",
    "gateway_response",
    "output_text",
    "raw_output",
    "raw_response",
    "secret",
}


class LegalFixtureResultArchiveService:
    """Build a release-safe archive summary for cheap-first fixture runs."""

    def __init__(
        self,
        run_report_service: LegalFixtureRunReportService | None = None,
        evidence_bundle_service: LegalFixtureEvidenceBundleService | None = None,
    ) -> None:
        self.run_report_service = run_report_service or LegalFixtureRunReportService()
        self.evidence_bundle_service = evidence_bundle_service or LegalFixtureEvidenceBundleService()

    def build_archive(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        run_report = self.run_report_service.build_report(payload)
        evidence_bundle = self.evidence_bundle_service.build_bundle(payload)
        observations, run_metadata = self._split_payload(payload)
        fixture_summaries = self._fixture_summaries(run_report)
        request_summaries = self._request_summaries(run_metadata)
        dropped_raw_field_count = self._raw_field_count(payload)
        status = self._status(run_report["status"], evidence_bundle["status"])

        return {
            "status": status,
            "method": {
                "type": "cheap-first-fixture-result-archive",
                "notes": [
                    "Builds an archive-safe summary from normalized fixture observations and run metadata.",
                    "Does not call a model, gateway, or public benchmark source.",
                    "Drops raw model output text, gateway response bodies, credentials, and client-document content.",
                ],
            },
            "summary": {
                "fixture_count": run_report["summary"]["fixture_count"],
                "observed_fixture_count": run_report["summary"]["observed_fixture_count"],
                "archived_fixture_count": len(fixture_summaries),
                "request_metadata_count": len(request_summaries),
                "dropped_raw_field_count": dropped_raw_field_count,
                "input_observation_count": len(observations),
                "release_decision": run_report["release_decision"],
                "evidence_bundle_status": evidence_bundle["status"],
                "observed_cost_usd": run_report["summary"]["observed_cost_usd"],
            },
            "archive_record": {
                "id": f"legal-fixture-result-archive-{status}",
                "source_endpoint": "/api/v1/maintenance/legal-review-benchmark/result-archive",
                "source_report_endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
                "source_bundle_endpoint": "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
                "archive_fields": [
                    "fixture_result_summaries",
                    "request_metadata_summaries",
                    "release_decision",
                    "evidence_bundle_status",
                    "validation_commands",
                    "release_claims",
                ],
                "excluded_fields": sorted(RAW_FIELD_NAMES),
            },
            "fixture_result_summaries": fixture_summaries,
            "request_metadata_summaries": request_summaries,
            "release_claims": evidence_bundle["release_claims"],
            "validation_commands": self._validation_commands(),
            "recommended_actions": self._recommended_actions(status, run_report, dropped_raw_field_count),
            "privacy_note": (
                "Archive summaries are safe for repository evidence because they contain fixture IDs, scores, "
                "routes, model names, costs, and release decisions only. Raw output text, gateway JSON, keys, "
                "emails, and real client documents must stay out of git."
            ),
        }

    def _split_payload(self, payload: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
        if not payload:
            return {}, {}
        observations = payload.get("observations")
        run_metadata = payload.get("run_metadata")
        if isinstance(observations, dict):
            return observations, run_metadata if isinstance(run_metadata, dict) else {}
        return payload, {}

    def _fixture_summaries(self, run_report: dict[str, Any]) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for row in run_report["fixture_reports"]:
            if row["smoke_status"] == "not_run":
                continue
            summaries.append(
                {
                    "fixture_id": row["fixture_id"],
                    "title": row["title"],
                    "smoke_status": row["smoke_status"],
                    "score": row["score"],
                    "observed_route": row["observed_route"],
                    "expected_routes": row["expected_routes"],
                    "matched_signal_count": row["matched_signal_count"],
                    "missing_signal_count": row["missing_signal_count"],
                    "missing_task_count": row["missing_task_count"],
                    "high_priority_action_count": row["high_priority_action_count"],
                    "observed_model": row["observed_model"],
                    "observed_phase": row["observed_phase"],
                    "observed_cost_usd": row["observed_cost_usd"],
                    "recommended_next_step": row["recommended_next_step"],
                }
            )
        return summaries

    def _request_summaries(self, run_metadata: dict[str, Any]) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for fixture_id, metadata in sorted(run_metadata.items()):
            if not isinstance(metadata, dict):
                continue
            summaries.append(
                {
                    "fixture_id": str(fixture_id),
                    "phase": self._string_or_none(metadata.get("phase")),
                    "model": self._string_or_none(metadata.get("model")),
                    "estimated_cost_usd": self._number_or_none(metadata.get("estimated_cost_usd")),
                    "http_status": self._integer_or_none(metadata.get("http_status")),
                    "archived_fields": [
                        key
                        for key in ("phase", "model", "estimated_cost_usd", "http_status")
                        if key in metadata
                    ],
                }
            )
        return summaries

    def _raw_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            count = sum(1 for key in value if str(key).lower() in RAW_FIELD_NAMES)
            return count + sum(self._raw_field_count(item) for item in value.values())
        if isinstance(value, list):
            return sum(self._raw_field_count(item) for item in value)
        return 0

    def _status(self, run_report_status: str, evidence_bundle_status: str) -> str:
        if run_report_status == "not_run" or evidence_bundle_status == "not_run":
            return "not_run"
        if run_report_status == "needs_escalation" or evidence_bundle_status == "blocked":
            return "blocked"
        if run_report_status == "review_recommended" or evidence_bundle_status == "review_recommended":
            return "review_recommended"
        return "ready"

    def _recommended_actions(
        self,
        status: str,
        run_report: dict[str, Any],
        dropped_raw_field_count: int,
    ) -> list[str]:
        actions: list[str] = []
        if status == "not_run":
            actions.append("Run one or two cheap-first local fixtures, normalize responses, then rebuild this archive.")
        elif status == "blocked":
            actions.append("Resolve fixture-run-report escalations before archiving the result as release evidence.")
        elif status == "review_recommended":
            actions.append("Review warning fixture summaries before attaching the archive to release readiness.")
        else:
            actions.append("Attach this archive summary to release readiness; keep raw outputs outside source control.")

        if dropped_raw_field_count:
            actions.append(f"Dropped {dropped_raw_field_count} raw or secret-like input fields from the archive summary.")
        if run_report["summary"]["observed_cost_usd"] is None and status != "not_run":
            actions.append("Add sanitized estimated_cost_usd metadata if cost evidence is needed for the release note.")
        return actions

    def _validation_commands(self) -> list[str]:
        return [
            "python -m pytest tests/test_legal_fixture_result_archive.py tests/test_legal_fixture_run_report.py -q",
            "python -m pytest tests/test_legal_fixture_evidence_bundle.py tests/test_legal_review_benchmark.py -q",
        ]

    def _string_or_none(self, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def _number_or_none(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return round(max(0.0, float(value)), 8)
        return None

    def _integer_or_none(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        return None
