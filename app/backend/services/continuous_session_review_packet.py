from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from services.continuous_session_timeline import ContinuousSessionTimelineService
from services.continuous_update_ledger import ContinuousUpdateLedgerService, TARGET_MEDIUM_LARGE_UPDATE_COUNT
from services.git_history_evidence import GitHistoryEvidenceService
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
    ) -> None:
        self.ledger_service = ledger_service or ContinuousUpdateLedgerService()
        self.timeline_service = timeline_service or ContinuousSessionTimelineService()
        self.git_history_service = git_history_service or GitHistoryEvidenceService()
        self.validation_event_service = validation_event_service or ValidationEventEvidenceService()

    def build_packet(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        validation_events = data.get("validation_events") if isinstance(data.get("validation_events"), list) else []
        git_payload = data.get("git_history") if isinstance(data.get("git_history"), (dict, list)) else {"git_since": data.get("git_since")}

        ledger = self.ledger_service.build_ledger()
        timeline = self.timeline_service.build_timeline(data)
        git_history = self.git_history_service.build_evidence(git_payload)
        validation_events_report = self.validation_event_service.build_evidence({"events": validation_events})

        summary = self._summary(ledger, timeline, git_history, validation_events_report)
        sections = self._sections(ledger, timeline, git_history, validation_events_report, summary)
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
            },
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "raw_logs_included": False,
                "raw_stdout_included": False,
                "raw_stderr_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "credentials_included": False,
                "emails_included": False,
                "output_scope": "metadata-only reviewer packet with section statuses, hashes, blockers, questions, and repository evidence paths",
            },
            "validation_commands": [
                "python -m pytest tests/test_continuous_session_review_packet.py -q",
                "python -m pytest tests/test_continuous_session_timeline.py tests/test_validation_event_evidence.py tests/test_git_history_evidence.py -q",
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
    ) -> dict[str, Any]:
        ledger_summary = ledger.get("summary", {})
        timeline_summary = timeline.get("summary", {})
        git_summary = git_history.get("summary", {})
        validation_summary = validation_events_report.get("summary", {})
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
        summary: dict[str, Any],
    ) -> list[dict[str, Any]]:
        timeline_summary = timeline.get("summary", {})
        git_summary = git_history.get("summary", {})
        validation_summary = validation_events_report.get("summary", {})
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
                "pass" if summary["low_resource_event_count"] > 0 or validation_summary.get("low_resource_legal_fixture_evidence") else "review",
                "review",
                "Reviewer packet needs at least one laptop-safe legal fixture or quick-suite event.",
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
        if any(blocker.get("severity") == "hard" for blocker in blockers):
            questions.append("Which hard blockers must be fixed before using this packet in a support claim?")
        return questions

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
