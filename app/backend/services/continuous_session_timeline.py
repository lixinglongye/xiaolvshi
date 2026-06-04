from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from services.continuous_session_evidence import ContinuousSessionEvidenceService
from services.continuous_update_ledger import ContinuousUpdateLedgerService
from services.git_history_evidence import GitHistoryEvidenceService
from services.maintenance_heartbeat_evidence import MaintenanceHeartbeatEvidenceService
from services.validation_event_evidence import ValidationEventEvidenceService


TARGET_CONTINUOUS_HOURS = 24
TARGET_MEDIUM_LARGE_UPDATE_COUNT = 100
LOW_RESOURCE_ROUTE_REFS = (
    "/api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2",
    "/api/v1/maintenance/legal-review-benchmark/local-run-review",
    "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
)

SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


class ContinuousSessionTimelineService:
    """Build a reviewer-facing maintenance timeline without claiming proof early."""

    def __init__(
        self,
        ledger_service: ContinuousUpdateLedgerService | None = None,
        session_service: ContinuousSessionEvidenceService | None = None,
        heartbeat_service: MaintenanceHeartbeatEvidenceService | None = None,
        git_history_service: GitHistoryEvidenceService | None = None,
        validation_event_service: ValidationEventEvidenceService | None = None,
    ) -> None:
        self.ledger_service = ledger_service or ContinuousUpdateLedgerService()
        self.session_service = session_service or ContinuousSessionEvidenceService()
        self.heartbeat_service = heartbeat_service or MaintenanceHeartbeatEvidenceService()
        self.git_history_service = git_history_service or GitHistoryEvidenceService()
        self.validation_event_service = validation_event_service or ValidationEventEvidenceService()

    def build_timeline(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        ledger = self.ledger_service.build_ledger()
        ledger_summary = ledger["summary"]
        raw_events = payload if isinstance(payload, list) else data.get("events")
        events = raw_events if isinstance(raw_events, list) else []
        validation_events = data.get("validation_events") if isinstance(data.get("validation_events"), list) else []
        validation_report = self.validation_event_service.build_evidence({"events": validation_events})
        normalized_validation_events = validation_report.get("normalized_session_events") or []
        combined_events = events + normalized_validation_events
        heartbeat_events = data.get("heartbeat_events") if isinstance(data.get("heartbeat_events"), list) else combined_events
        completed_updates = self._bounded_int(
            data.get("completed_medium_large_update_count"),
            ledger_summary["completed_medium_large_update_count"],
            0,
            10000,
        )

        session_report = self.session_service.build_report(
            {
                "events": combined_events,
                "completed_medium_large_update_count": completed_updates,
                "target_medium_large_update_count": TARGET_MEDIUM_LARGE_UPDATE_COUNT,
                "max_allowed_gap_hours": data.get("max_allowed_gap_hours"),
            }
        )
        heartbeat_report = self.heartbeat_service.build_evidence(heartbeat_events)
        git_history_report = self.git_history_service.build_evidence(
            data.get("git_history") if isinstance(data.get("git_history"), (dict, list)) else {"git_since": data.get("git_since")}
        )
        timeline_events = self._timeline_events(
            session_report,
            ledger_summary,
            git_history_report,
            {item.get("id") for item in normalized_validation_events if item.get("id")},
        )
        blockers = self._blockers(
            session_report,
            heartbeat_report,
            git_history_report,
            validation_report,
            completed_updates,
            timeline_events,
        )
        completion_ready = not blockers and session_report["summary"]["ready_for_goal_claim"] is True
        status = "ready_for_review" if completion_ready else ("blocked" if self._has_hard_blocker(blockers) else "collecting")

        return {
            "status": status,
            "summary": {
                "target_continuous_hours": TARGET_CONTINUOUS_HOURS,
                "target_medium_large_update_count": TARGET_MEDIUM_LARGE_UPDATE_COUNT,
                "completed_medium_large_update_count": completed_updates,
                "remaining_medium_large_update_count": max(0, TARGET_MEDIUM_LARGE_UPDATE_COUNT - completed_updates),
                "verified_continuous_hours": session_report["summary"]["verified_continuous_hours"],
                "continuous_hours_remaining": session_report["summary"]["continuous_hours_remaining"],
                "event_count": len(timeline_events),
                "submitted_event_count": session_report["summary"]["event_count"],
                "valid_event_count": session_report["summary"]["valid_event_count"],
                "invalid_event_count": session_report["summary"]["invalid_event_count"],
                "submitted_validation_event_count": validation_report["summary"]["event_count"],
                "valid_validation_event_count": validation_report["summary"]["valid_event_count"],
                "invalid_validation_event_count": validation_report["summary"]["invalid_event_count"],
                "low_resource_event_count": sum(1 for item in timeline_events if item["low_resource"] is True),
                "blocker_count": len(blockers),
                "completion_ready": completion_ready,
                "raw_payload_echoed": False,
            },
            "timeline_events": timeline_events,
            "best_window": session_report["best_window"],
            "blockers": blockers,
            "source_summaries": {
                "ledger": {
                    "completed_medium_large_update_count": ledger_summary["completed_medium_large_update_count"],
                    "continuous_hours_verified": ledger_summary["continuous_hours_verified"],
                    "completion_ready": ledger_summary["completion_ready"],
                },
                "session_validator": session_report["summary"],
                "heartbeat": heartbeat_report["summary"],
                "git_history": git_history_report["summary"],
                "validation_events": validation_report["summary"],
            },
            "low_resource_evidence_routes": list(LOW_RESOURCE_ROUTE_REFS),
            "reviewer_notes": self._reviewer_notes(blockers, completion_ready),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "credentials_included": False,
                "emails_included": False,
                "output_scope": "metadata-only maintenance timeline",
            },
            "validation_commands": [
                "python -m pytest tests/test_continuous_session_timeline.py -q",
                "python -m pytest tests/test_validation_event_evidence.py -q",
                "python -m pytest tests/test_git_history_evidence.py -q",
                "python -m pytest tests/test_continuous_session_evidence.py tests/test_maintenance_heartbeat_evidence.py tests/test_continuous_update_ledger.py -q",
                "python -m pytest tests/test_legal_fixture_quick_suite.py tests/test_legal_document_benchmark_suite.py -q",
            ],
        }

    def _timeline_events(
        self,
        session_report: dict[str, Any],
        ledger_summary: dict[str, Any],
        git_history_report: dict[str, Any],
        validation_event_ids: set[str],
    ) -> list[dict[str, Any]]:
        best_window_ids = set(session_report["best_window"].get("record_ids") or [])
        events = [
            {
                "id": "ledger-100-plus-checkpoint",
                "source": "continuous_update_ledger",
                "event_type": "ledger_checkpoint",
                "timestamp": None,
                "status": "pass" if ledger_summary["completed_medium_large_update_count"] >= TARGET_MEDIUM_LARGE_UPDATE_COUNT else "fail",
                "labels": ["100-plus-updates", "repository-backed"],
                "evidence_paths": ["app/backend/services/continuous_update_ledger.py", "docs/CONTINUOUS_UPDATE_LEDGER.md"],
                "commit_hash": "",
                "validation_id": "continuous-update-ledger",
                "low_resource": False,
                "in_best_window": False,
            }
        ]
        git_window = git_history_report.get("longest_window") or {}
        if git_window.get("commit_count", 0) > 0:
            events.append(
                {
                    "id": "git-history-cadence-window",
                    "source": "git_history_evidence",
                    "event_type": "commit_cadence",
                    "timestamp": git_window.get("start_timestamp"),
                    "status": "pass" if git_history_report["summary"].get("commit_cadence_ready") else "review",
                    "labels": ["commit-cadence", "metadata-only"],
                    "evidence_paths": ["app/backend/services/git_history_evidence.py", "docs/GIT_HISTORY_EVIDENCE.md"],
                    "commit_hash": "",
                    "validation_id": "git-history-evidence",
                    "low_resource": False,
                    "in_best_window": False,
                    "cadence_summary": {
                        "verified_hours": git_window.get("verified_hours"),
                        "commit_count": git_window.get("commit_count"),
                        "max_observed_gap_hours": git_window.get("max_observed_gap_hours"),
                    },
                }
            )

        for record in session_report.get("session_records", []):
            labels = list(record.get("labels") or [])
            event_type = str(record.get("event_type") or "unknown")
            events.append(
                {
                    "id": record.get("id") or "",
                    "source": "validation_event_evidence"
                    if (record.get("id") or "") in validation_event_ids
                    else "continuous_session_evidence",
                    "event_type": event_type,
                    "timestamp": record.get("timestamp"),
                    "status": record.get("status") or "fail",
                    "labels": labels,
                    "evidence_paths": list(record.get("evidence_paths") or []),
                    "commit_hash": record.get("commit_hash") or "",
                    "validation_id": record.get("validation_id") or record.get("evidence_ref") or "",
                    "low_resource": event_type in {"test", "benchmark", "legal_fixture"} and (
                        "low-resource" in labels or "quick-suite" in labels
                    ),
                    "in_best_window": (record.get("id") or "") in best_window_ids,
                }
            )
        return sorted(events, key=lambda item: item["timestamp"] or "9999-12-31T23:59:59Z")

    def _blockers(
        self,
        session_report: dict[str, Any],
        heartbeat_report: dict[str, Any],
        git_history_report: dict[str, Any],
        validation_report: dict[str, Any],
        completed_updates: int,
        timeline_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        if completed_updates < TARGET_MEDIUM_LARGE_UPDATE_COUNT:
            blockers.append(
                {
                    "id": "ledger-update-count-short",
                    "severity": "hard",
                    "detail": "100+ medium/large update evidence is not satisfied.",
                }
            )
        for gap in session_report.get("gap_analysis", []):
            if gap.get("status") == "open":
                blockers.append(
                    {
                        "id": self._safe_token(gap.get("id")),
                        "severity": "hard" if gap.get("id") in {"invalid-session-records"} else "review",
                        "detail": self._safe_detail(gap.get("detail")),
                    }
                )
        heartbeat_missing = heartbeat_report.get("summary", {}).get("missing_event_types") or []
        if heartbeat_missing:
            blockers.append(
                {
                    "id": "heartbeat-event-types-missing",
                    "severity": "review",
                    "detail": ",".join(self._safe_token(item) for item in heartbeat_missing if self._safe_token(item)),
                }
            )
        if session_report["summary"].get("event_count", 0) == 0:
            blockers.append(
                {
                    "id": "timeline-events-missing",
                    "severity": "review",
                    "detail": "No non-git timestamped maintenance events were submitted for the 24-hour timeline.",
                }
            )
        validation_summary = validation_report.get("summary", {})
        if validation_summary.get("invalid_event_count", 0) > 0:
            blockers.append(
                {
                    "id": "invalid-validation-events",
                    "severity": "hard",
                    "detail": f"{validation_summary['invalid_event_count']} validation event(s) are invalid.",
                }
            )
        elif validation_summary.get("event_count", 0) > 0 and validation_summary.get("missing_event_types"):
            blockers.append(
                {
                    "id": "validation-event-types-missing",
                    "severity": "review",
                    "detail": ",".join(
                        self._safe_token(item)
                        for item in validation_summary["missing_event_types"]
                        if self._safe_token(item)
                    ),
                }
            )
        if git_history_report["summary"].get("invalid_commit_count", 0) > 0:
            blockers.append(
                {
                    "id": "invalid-git-history-records",
                    "severity": "hard",
                    "detail": f"{git_history_report['summary']['invalid_commit_count']} git history record(s) are invalid.",
                }
            )
        return blockers

    def _reviewer_notes(self, blockers: list[dict[str, Any]], completion_ready: bool) -> list[str]:
        if completion_ready:
            return [
                "The 100+ update count and the submitted 24-hour timeline are both reviewable.",
                "Confirm every evidence path resolves in the repository or published Git history before making a public claim.",
            ]
        notes = [
            "Keep the support or reviewer claim blocked until both the 100+ update count and 24-hour timeline are reviewable.",
            "Use low-resource legal fixture tests for laptop-safe quality evidence; do not attach raw model responses or client documents.",
        ]
        if any(blocker["id"] == "timeline-events-missing" for blocker in blockers):
            notes.append("Submit timestamped commit, test, credential-scan, review, and push metadata to begin timeline verification.")
        return notes

    def _has_hard_blocker(self, blockers: list[dict[str, Any]]) -> bool:
        return any(blocker.get("severity") == "hard" for blocker in blockers)

    def _safe_detail(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return raw[:180]

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "-")[:90]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))
