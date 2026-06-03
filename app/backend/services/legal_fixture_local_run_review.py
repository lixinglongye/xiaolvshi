from __future__ import annotations

from typing import Any

from services.legal_fixture_evidence_bundle import LegalFixtureEvidenceBundleService
from services.legal_fixture_response_normalizer import LegalFixtureResponseNormalizerService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.legal_review_benchmark import LegalReviewBenchmarkService


class LegalFixtureLocalRunReviewService:
    """Review a small local fixture gateway run without calling any model."""

    def __init__(
        self,
        normalizer_service: LegalFixtureResponseNormalizerService | None = None,
        benchmark_service: LegalReviewBenchmarkService | None = None,
        run_report_service: LegalFixtureRunReportService | None = None,
        evidence_bundle_service: LegalFixtureEvidenceBundleService | None = None,
    ) -> None:
        self.normalizer_service = normalizer_service or LegalFixtureResponseNormalizerService()
        self.benchmark_service = benchmark_service or LegalReviewBenchmarkService()
        self.run_report_service = run_report_service or LegalFixtureRunReportService(self.benchmark_service)
        self.evidence_bundle_service = evidence_bundle_service or LegalFixtureEvidenceBundleService()

    def template(self) -> dict[str, Any]:
        normalizer_template = self.normalizer_service.template()
        return {
            "status": "ready",
            "method": {
                "type": "local-fixture-run-review-template",
                "notes": [
                    "Use this when a low-resource machine can only run one or two local fixture gateway requests.",
                    "POST accepts the same response payload as local-response-normalizer and returns smoke, run-report, and evidence-bundle results.",
                    "The review is deterministic and never calls NewAPI, Gemini, or the app AI gateway.",
                ],
            },
            "payload_shape": normalizer_template["payload_shape"],
            "follow_up_endpoints": [
                "/api/v1/maintenance/legal-review-benchmark/local-run-package",
                "/api/v1/maintenance/legal-review-benchmark/local-response-normalizer",
                "/api/v1/maintenance/legal-review-benchmark/local-run-review",
                "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
                "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
                "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
            ],
            "validation_command": (
                "python -m pytest tests/test_legal_fixture_local_run_review.py "
                "tests/test_legal_fixture_response_normalizer.py -q"
            ),
            "privacy_note": (
                "Paste only local gateway JSON responses. Do not include Authorization headers, real client documents, "
                "emails, public benchmark raw examples, or committed raw outputs."
            ),
        }

    def review(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        normalizer = self.normalizer_service.normalize(payload)
        run_report_payload = normalizer["run_report_payload"]
        observations = run_report_payload["observations"]
        smoke = self.benchmark_service.evaluate_fixture_smoke(observations)
        run_report = self.run_report_service.build_report(run_report_payload)
        evidence_bundle = self.evidence_bundle_service.build_bundle(run_report_payload)
        checks = self._checks(normalizer, smoke, run_report, evidence_bundle)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": self._status(normalizer, smoke, run_report, evidence_bundle, blocking, warnings),
            "release_decision": run_report["release_decision"],
            "method": {
                "type": "local-fixture-run-review",
                "notes": [
                    "Composes response normalization, fixture smoke scoring, cheap-first run reporting, and release evidence bundling.",
                    "Scores only supplied local fixture responses; missing fixtures remain not_run in the smoke and report outputs.",
                    "Does not return gateway headers, request prompts, or full response envelopes.",
                ],
            },
            "summary": {
                "response_count": normalizer["summary"]["response_count"],
                "normalized_observation_count": normalizer["summary"]["normalized_observation_count"],
                "redacted_response_count": normalizer["summary"]["redacted_response_count"],
                "smoke_status": smoke["status"],
                "smoke_score": smoke["score"],
                "observed_fixture_count": run_report["summary"]["observed_fixture_count"],
                "not_run_fixture_count": run_report["summary"]["not_run_fixture_count"],
                "escalation_required_count": run_report["summary"]["escalation_required_count"],
                "observed_request_count": run_report["summary"]["observed_request_count"],
                "observed_cost_usd": run_report["summary"]["observed_cost_usd"],
                "evidence_bundle_status": evidence_bundle["status"],
                "evidence_component_count": evidence_bundle["summary"]["component_count"],
                "blocking_check_count": len(blocking),
                "warning_check_count": len(warnings),
            },
            "normalizer_summary": normalizer["summary"],
            "response_summaries": normalizer["response_summaries"],
            "smoke_result": smoke,
            "run_report": run_report,
            "evidence_bundle": evidence_bundle,
            "run_report_payload": run_report_payload,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(normalizer, run_report, evidence_bundle, blocking, warnings),
            "privacy_note": (
                "The review keeps raw gateway envelopes out of the response. Normalized output text is included only "
                "inside run_report_payload for local scoring and should not be committed."
            ),
        }

    def _checks(
        self,
        normalizer: dict[str, Any],
        smoke: dict[str, Any],
        run_report: dict[str, Any],
        evidence_bundle: dict[str, Any],
    ) -> list[dict[str, Any]]:
        checks = [
            self._check(
                "normalizer-ready",
                "fail" if normalizer["status"] == "fail" else ("warn" if normalizer["status"] == "warn" else "pass"),
                f"Response normalizer status is {normalizer['status']}.",
            ),
            self._check(
                "observations-present",
                "pass" if normalizer["summary"]["normalized_observation_count"] > 0 else "fail",
                f"Normalized {normalizer['summary']['normalized_observation_count']} fixture observations.",
            ),
            self._check(
                "fixture-smoke-reviewed",
                "pass" if smoke["status"] == "pass" else ("warn" if smoke["status"] in {"warn", "not_run"} else "fail"),
                f"Fixture smoke status is {smoke['status']} with score {smoke['score']}.",
            ),
            self._check(
                "run-report-reviewed",
                "pass" if run_report["status"] == "ready" else (
                    "warn" if run_report["status"] in {"review_recommended", "not_run"} else "fail"
                ),
                f"Run report status is {run_report['status']}.",
            ),
            self._check(
                "evidence-bundle-reviewed",
                "pass" if evidence_bundle["status"] == "ready" else (
                    "warn" if evidence_bundle["status"] in {"review_recommended", "not_run"} else "fail"
                ),
                f"Evidence bundle status is {evidence_bundle['status']}.",
            ),
        ]
        redaction_status = "warn" if normalizer["summary"]["redacted_response_count"] else "pass"
        checks.append(
            self._check(
                "secret-redaction-reviewed",
                redaction_status,
                f"Redacted {normalizer['summary']['redacted_response_count']} response contents.",
            )
        )
        return checks

    def _check(self, check_id: str, status: str, reason: str) -> dict[str, str]:
        return {
            "id": check_id,
            "status": status,
            "reason": reason,
        }

    def _status(
        self,
        normalizer: dict[str, Any],
        smoke: dict[str, Any],
        run_report: dict[str, Any],
        evidence_bundle: dict[str, Any],
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> str:
        if normalizer["status"] == "fail" or any(check["id"] == "observations-present" for check in blocking):
            return "fail"
        if run_report["status"] == "needs_escalation" or evidence_bundle["status"] == "blocked":
            return "needs_escalation"
        if smoke["status"] == "not_run" or run_report["status"] == "not_run":
            return "not_run"
        if run_report["status"] == "ready" and evidence_bundle["status"] == "ready" and not warnings:
            return "ready"
        return "review_recommended"

    def _recommended_actions(
        self,
        normalizer: dict[str, Any],
        run_report: dict[str, Any],
        evidence_bundle: dict[str, Any],
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            actions = [f"Resolve local run review blocker: {check['id']}." for check in blocking]
        elif warnings:
            actions = [f"Review local run warning: {check['id']}." for check in warnings]
        else:
            actions = ["Archive run_report and evidence_bundle with release readiness notes."]
        for source in (normalizer, run_report, evidence_bundle):
            for action in source.get("recommended_actions", []):
                if action not in actions:
                    actions.append(action)
        return actions
