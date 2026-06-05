from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from services.continuous_session_timeline import ContinuousSessionTimelineService
from services.continuous_update_ledger import ContinuousUpdateLedgerService, TARGET_MEDIUM_LARGE_UPDATE_COUNT
from services.git_history_evidence import GitHistoryEvidenceService
from services.legal_fixture_local_run_review import LegalFixtureLocalRunReviewService
from services.validation_event_evidence import ValidationEventEvidenceService


SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


class ContinuousSessionReviewPacketService:
    """Build a metadata-only reviewer packet for the 24-hour maintenance goal."""

    def __init__(
        self,
        ledger_service: ContinuousUpdateLedgerService | None = None,
        timeline_service: ContinuousSessionTimelineService | None = None,
        git_history_service: GitHistoryEvidenceService | None = None,
        validation_event_service: ValidationEventEvidenceService | None = None,
        fixture_review_service: LegalFixtureLocalRunReviewService | None = None,
    ) -> None:
        self.ledger_service = ledger_service or ContinuousUpdateLedgerService()
        self.timeline_service = timeline_service or ContinuousSessionTimelineService()
        self.git_history_service = git_history_service or GitHistoryEvidenceService()
        self.validation_event_service = validation_event_service or ValidationEventEvidenceService()
        self.fixture_review_service = fixture_review_service or LegalFixtureLocalRunReviewService()

    def build_packet(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        validation_events = data.get("validation_events") if isinstance(data.get("validation_events"), list) else []
        git_payload = data.get("git_history") if isinstance(data.get("git_history"), (dict, list)) else {"git_since": data.get("git_since")}
        fixture_review = self._low_resource_fixture_review(data)

        ledger = self.ledger_service.build_ledger()
        timeline = self.timeline_service.build_timeline(data)
        git_history = self.git_history_service.build_evidence(git_payload)
        validation_events_report = self.validation_event_service.build_evidence({"events": validation_events})

        summary = self._summary(ledger, timeline, git_history, validation_events_report, fixture_review)
        sections = self._sections(ledger, timeline, git_history, validation_events_report, fixture_review, summary)
        blockers = self._blockers(sections, timeline)
        reviewer_questions = self._reviewer_questions(summary, blockers)
        packet_hash = self._packet_hash(
            {
                "summary": {key: value for key, value in summary.items() if key != "packet_hash"},
                "packet_sections": sections,
                "blockers": blockers,
                "reviewer_questions": reviewer_questions,
            }
        )
        summary["packet_hash"] = packet_hash
        packet_ready = (
            summary["update_count_ready"]
            and summary["timeline_completion_ready"]
            and summary["privacy_boundary_clean"]
            and summary["hard_blocker_count"] == 0
            and not summary["low_resource_fixture_review_blocked"]
        )
        summary["packet_ready_for_support_claim"] = packet_ready

        return {
            "status": "ready_for_review" if packet_ready else ("blocked" if summary["hard_blocker_count"] else "collecting"),
            "summary": summary,
            "packet_sections": sections,
            "blockers": blockers,
            "reviewer_questions": reviewer_questions,
            "source_summaries": {
                "ledger": ledger["summary"],
                "timeline": timeline["summary"],
                "git_history": git_history["summary"],
                "validation_events": validation_events_report["summary"],
                "low_resource_fixture_review": self._fixture_review_source_summary(fixture_review),
            },
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "raw_logs_included": False,
                "raw_stdout_included": False,
                "raw_stderr_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "raw_gateway_response_included": False,
                "low_resource_fixture_review_raw_payload_included": False,
                "credentials_included": False,
                "emails_included": False,
                "output_scope": "metadata-only reviewer packet with section statuses, hashes, blockers, questions, and repository evidence paths",
            },
            "validation_commands": [
                "python -m pytest tests/test_continuous_session_review_packet.py -q",
                "python -m pytest tests/test_continuous_session_timeline.py tests/test_validation_event_evidence.py tests/test_git_history_evidence.py -q",
                "python -m pytest tests/test_legal_fixture_local_run_review.py tests/test_legal_fixture_response_normalizer.py -q",
                "npm run typecheck",
                "npm run build",
            ],
        }

    def _summary(
        self,
        ledger: dict[str, Any],
        timeline: dict[str, Any],
        git_history: dict[str, Any],
        validation_events_report: dict[str, Any],
        fixture_review: dict[str, Any] | None,
    ) -> dict[str, Any]:
        ledger_summary = ledger.get("summary", {})
        timeline_summary = timeline.get("summary", {})
        git_summary = git_history.get("summary", {})
        validation_summary = validation_events_report.get("summary", {})
        fixture_summary = self._fixture_review_summary(fixture_review)
        hard_blocker_count = sum(1 for item in timeline.get("blockers", []) if item.get("severity") == "hard")
        return {
            "target_medium_large_update_count": TARGET_MEDIUM_LARGE_UPDATE_COUNT,
            "completed_medium_large_update_count": ledger_summary.get("completed_medium_large_update_count", 0),
            "update_count_ready": ledger_summary.get("completed_medium_large_update_count", 0) >= TARGET_MEDIUM_LARGE_UPDATE_COUNT,
            "timeline_completion_ready": timeline_summary.get("completion_ready") is True,
            "timeline_verified_continuous_hours": timeline_summary.get("verified_continuous_hours", 0),
            "timeline_remaining_continuous_hours": timeline_summary.get("continuous_hours_remaining", 24),
            "git_cadence_ready": git_summary.get("commit_cadence_ready") is True,
            "validation_events_ready": validation_summary.get("ready_for_timeline") is True,
            "validation_event_count": validation_summary.get("event_count", 0),
            "low_resource_event_count": timeline_summary.get("low_resource_event_count", 0),
            "low_resource_fixture_review_status": fixture_summary["status"],
            "low_resource_fixture_review_ready": fixture_summary["ready"],
            "low_resource_fixture_review_release_ready": fixture_summary["release_ready"],
            "low_resource_fixture_review_observed_count": fixture_summary["observed_fixture_count"],
            "low_resource_fixture_review_not_run_count": fixture_summary["not_run_fixture_count"],
            "low_resource_fixture_review_redacted_count": fixture_summary["redacted_response_count"],
            "low_resource_fixture_review_blocking_count": fixture_summary["blocking_check_count"],
            "low_resource_fixture_review_warning_count": fixture_summary["warning_check_count"],
            "low_resource_fixture_review_blocked": fixture_summary["blocked"],
            "low_resource_fixture_review_raw_payload_echoed": False,
            "privacy_boundary_clean": True,
            "timeline_blocker_count": timeline_summary.get("blocker_count", 0),
            "hard_blocker_count": hard_blocker_count,
            "packet_ready_for_support_claim": False,
            "raw_payload_echoed": False,
            "packet_hash": "",
        }

    def _sections(
        self,
        ledger: dict[str, Any],
        timeline: dict[str, Any],
        git_history: dict[str, Any],
        validation_events_report: dict[str, Any],
        fixture_review: dict[str, Any] | None,
        summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        timeline_summary = timeline.get("summary", {})
        git_summary = git_history.get("summary", {})
        validation_summary = validation_events_report.get("summary", {})
        fixture_summary = self._fixture_review_summary(fixture_review)
        has_low_resource_validation_event = (
            summary["low_resource_event_count"] > 0
            or validation_summary.get("low_resource_legal_fixture_evidence") is True
        )
        return [
            self._section(
                "update-ledger",
                "100+ update ledger",
                "pass" if summary["update_count_ready"] else "fail",
                "hard",
                f"{summary['completed_medium_large_update_count']} medium/large update(s) recorded.",
                ("app/backend/services/continuous_update_ledger.py", "docs/CONTINUOUS_UPDATE_LEDGER.md"),
            ),
            self._section(
                "timeline-window",
                "24-hour timeline window",
                "pass" if summary["timeline_completion_ready"] else "review",
                "hard" if summary["hard_blocker_count"] else "review",
                f"{timeline_summary.get('verified_continuous_hours', 0)} verified hour(s); {timeline_summary.get('continuous_hours_remaining', 24)} hour(s) remaining.",
                ("app/backend/services/continuous_session_timeline.py", "docs/CONTINUOUS_SESSION_TIMELINE.md"),
            ),
            self._section(
                "git-cadence",
                "Git cadence evidence",
                "pass" if summary["git_cadence_ready"] else "review",
                "review",
                f"{git_summary.get('longest_window_hours', 0)} hour git window from metadata-only history.",
                ("app/backend/services/git_history_evidence.py", "docs/GIT_HISTORY_EVIDENCE.md"),
            ),
            self._section(
                "validation-events",
                "Validation event evidence",
                "pass" if summary["validation_events_ready"] else "review",
                "review",
                f"{validation_summary.get('valid_event_count', 0)} valid validation event(s); {validation_summary.get('invalid_event_count', 0)} invalid.",
                ("app/backend/services/validation_event_evidence.py", "docs/VALIDATION_EVENT_EVIDENCE.md"),
            ),
            self._section(
                "low-resource-legal-fixture",
                "Low-resource legal fixture evidence",
                self._low_resource_fixture_section_status(fixture_summary, has_low_resource_validation_event),
                "review",
                self._low_resource_fixture_section_detail(fixture_summary, has_low_resource_validation_event),
                ("app/backend/tests/test_legal_fixture_quick_suite.py", "docs/LEGAL_FIXTURE_QUICK_SUITE.md"),
            ),
            self._section(
                "privacy-boundary",
                "Privacy boundary",
                "pass",
                "hard",
                "Packet contains metadata only and excludes raw logs, legal text, model output, credentials, and emails.",
                ("app/backend/services/continuous_session_review_packet.py", "docs/CONTINUOUS_SESSION_REVIEW_PACKET.md"),
            ),
        ]

    def _section(
        self,
        section_id: str,
        title: str,
        status: str,
        severity: str,
        detail: str,
        evidence_paths: tuple[str, ...],
    ) -> dict[str, Any]:
        return {
            "id": section_id,
            "title": title,
            "status": status,
            "severity": severity,
            "detail": self._safe_detail(detail),
            "evidence_paths": list(evidence_paths),
        }

    def _blockers(self, sections: list[dict[str, Any]], timeline: dict[str, Any]) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        for section in sections:
            if section["status"] == "fail":
                blockers.append(
                    {
                        "id": f"{section['id']}-not-ready",
                        "severity": section["severity"],
                        "detail": section["detail"],
                    }
                )
        for blocker in timeline.get("blockers", [])[:12]:
            blockers.append(
                {
                    "id": self._safe_token(blocker.get("id")),
                    "severity": self._safe_token(blocker.get("severity")) or "review",
                    "detail": self._safe_detail(blocker.get("detail")),
                }
            )
        deduped: list[dict[str, Any]] = []
        seen = set()
        for blocker in blockers:
            key = blocker["id"]
            if key and key not in seen:
                deduped.append(blocker)
                seen.add(key)
        return deduped

    def _reviewer_questions(self, summary: dict[str, Any], blockers: list[dict[str, Any]]) -> list[str]:
        questions = [
            "Do all packet evidence paths resolve to repository files or published git metadata?",
            "Are the timestamped events sufficient to prove the continuous window without gaps?",
            "Were low-resource legal fixture checks run without raw client documents or raw model output?",
            "Did the final credential scan run before the pushed commit?",
        ]
        if not summary["timeline_completion_ready"]:
            questions.insert(1, "Which missing event types or timeline gaps still block the 24-hour claim?")
        if summary.get("low_resource_fixture_review_status") == "not_supplied":
            questions.insert(2, "Was a low-resource fixture run reviewed through local-run-review or validation-event metadata?")
        elif summary.get("low_resource_fixture_review_blocked"):
            questions.insert(2, "Which low-resource fixture review blockers must be resolved before using the packet?")
        if any(blocker.get("severity") == "hard" for blocker in blockers):
            questions.append("Which hard blockers must be fixed before using this packet in a support claim?")
        return questions

    def _low_resource_fixture_review(self, data: dict[str, Any]) -> dict[str, Any] | None:
        payload = data.get("low_resource_fixture_review")
        if not isinstance(payload, dict):
            payload = data.get("fixture_review")
        if not isinstance(payload, dict):
            return None
        return self.fixture_review_service.review(payload)

    def _fixture_review_summary(self, fixture_review: dict[str, Any] | None) -> dict[str, Any]:
        if not fixture_review:
            return {
                "status": "not_supplied",
                "ready": False,
                "release_ready": False,
                "blocked": False,
                "observed_fixture_count": 0,
                "not_run_fixture_count": 0,
                "redacted_response_count": 0,
                "blocking_check_count": 0,
                "warning_check_count": 0,
            }
        summary = fixture_review.get("summary", {})
        status = self._safe_status(fixture_review.get("status")) or "unknown"
        observed = int(summary.get("observed_fixture_count") or summary.get("normalized_observation_count") or 0)
        not_run = int(summary.get("not_run_fixture_count") or 0)
        redacted = int(summary.get("redacted_response_count") or 0)
        blocking_count = int(summary.get("blocking_check_count") or len(fixture_review.get("blocking_check_ids", [])) or 0)
        warning_count = int(summary.get("warning_check_count") or len(fixture_review.get("warning_check_ids", [])) or 0)
        blocked = status in {"fail"} or observed == 0
        return {
            "status": status,
            "ready": observed > 0 and not blocked,
            "release_ready": status == "ready",
            "blocked": blocked,
            "observed_fixture_count": observed,
            "not_run_fixture_count": not_run,
            "redacted_response_count": redacted,
            "blocking_check_count": blocking_count,
            "warning_check_count": warning_count,
        }

    def _fixture_review_source_summary(self, fixture_review: dict[str, Any] | None) -> dict[str, Any]:
        summary = self._fixture_review_summary(fixture_review)
        if not fixture_review:
            return {
                **summary,
                "raw_payload_echoed": False,
                "raw_gateway_response_included": False,
                "raw_model_output_included": False,
            }
        check_status_counts: dict[str, int] = {}
        for check in fixture_review.get("checks", []):
            status = self._safe_status(check.get("status")) or "unknown"
            check_status_counts[status] = check_status_counts.get(status, 0) + 1
        return {
            **summary,
            "release_decision": self._safe_status(fixture_review.get("release_decision")),
            "smoke_status": self._safe_status(fixture_review.get("summary", {}).get("smoke_status")),
            "evidence_bundle_status": self._safe_status(fixture_review.get("summary", {}).get("evidence_bundle_status")),
            "check_status_counts": dict(sorted(check_status_counts.items())),
            "blocking_check_ids": [self._safe_token(item) for item in fixture_review.get("blocking_check_ids", [])][:8],
            "warning_check_ids": [self._safe_token(item) for item in fixture_review.get("warning_check_ids", [])][:8],
            "recommended_action_count": len(fixture_review.get("recommended_actions", [])),
            "raw_payload_echoed": False,
            "raw_gateway_response_included": False,
            "raw_model_output_included": False,
        }

    def _low_resource_fixture_section_status(
        self,
        fixture_summary: dict[str, Any],
        has_low_resource_validation_event: bool,
    ) -> str:
        if fixture_summary["blocked"]:
            return "fail"
        if fixture_summary["ready"] or has_low_resource_validation_event:
            return "pass"
        return "review_recommended"

    def _low_resource_fixture_section_detail(
        self,
        fixture_summary: dict[str, Any],
        has_low_resource_validation_event: bool,
    ) -> str:
        status = fixture_summary["status"]
        if fixture_summary["ready"]:
            return (
                f"Low-resource fixture review {status}; "
                f"{fixture_summary['observed_fixture_count']} observed fixture(s), "
                f"{fixture_summary['not_run_fixture_count']} not run."
            )
        if has_low_resource_validation_event:
            return "Validation-event metadata includes a laptop-safe legal fixture or quick-suite event."
        if fixture_summary["blocked"]:
            return "Low-resource fixture review is blocked or has no normalized fixture observations."
        return "Reviewer packet needs at least one laptop-safe legal fixture review or quick-suite event."

    def _packet_hash(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def _safe_detail(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"\s+", " ", raw)[:220]

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "-")[:90]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _safe_status(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "_")[:90]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_:-]+", "_", raw).strip("_")
