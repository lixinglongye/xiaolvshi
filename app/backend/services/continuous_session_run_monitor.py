from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from typing import Any

from services.continuous_session_evidence import (
    DEFAULT_MAX_GAP_HOURS,
    REQUIRED_EVENT_TYPES,
    TARGET_CONTINUOUS_HOURS,
)
from services.continuous_session_review_packet import ContinuousSessionReviewPacketService
from services.continuous_session_timeline import ContinuousSessionTimelineService
from services.continuous_update_ledger import ContinuousUpdateLedgerService, TARGET_MEDIUM_LARGE_UPDATE_COUNT


DEFAULT_CHECKPOINT_INTERVAL_HOURS = 2
SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


class ContinuousSessionRunMonitorService:
    """Monitor an active 24-hour maintenance run without turning it into proof."""

    def __init__(
        self,
        ledger_service: ContinuousUpdateLedgerService | None = None,
        timeline_service: ContinuousSessionTimelineService | None = None,
        review_packet_service: ContinuousSessionReviewPacketService | None = None,
    ) -> None:
        self.ledger_service = ledger_service or ContinuousUpdateLedgerService()
        self.timeline_service = timeline_service or ContinuousSessionTimelineService()
        self.review_packet_service = review_packet_service or ContinuousSessionReviewPacketService()

    def build_monitor(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        ledger = self.ledger_service.build_ledger(data)
        ledger_summary = ledger["summary"]
        low_resource_fixture_evidence = ledger.get("low_resource_fixture_evidence") or {}
        timeline_payload = self._timeline_payload(data, ledger_summary)
        timeline = self.timeline_service.build_timeline(timeline_payload)
        review_packet = self.review_packet_service.build_packet(timeline_payload)
        max_gap_hours = self._bounded_int(
            data.get("max_allowed_gap_hours"),
            DEFAULT_MAX_GAP_HOURS,
            1,
            12,
        )
        checkpoint_interval_hours = self._bounded_int(
            data.get("checkpoint_interval_hours"),
            DEFAULT_CHECKPOINT_INTERVAL_HOURS,
            1,
            6,
        )
        now = self._parse_timestamp(data.get("current_timestamp")) or datetime.now(timezone.utc)
        event_timestamps = self._event_timestamps(timeline.get("timeline_events", []))
        start_timestamp = self._start_timestamp(data, event_timestamps)
        latest_timestamp = event_timestamps[-1] if event_timestamps else None
        elapsed_hours = self._hours_between(start_timestamp, now) if start_timestamp else 0
        current_gap_hours = self._hours_between(latest_timestamp, now) if latest_timestamp else None
        next_checkpoint_due_at = self._next_checkpoint_due_at(
            latest_timestamp or start_timestamp,
            checkpoint_interval_hours,
        )
        checkpoint_due_in_hours = (
            self._hours_between(now, next_checkpoint_due_at)
            if next_checkpoint_due_at and next_checkpoint_due_at >= now
            else 0
        )
        required_evidence = self._required_evidence(timeline, low_resource_fixture_evidence)
        blockers = self._blockers(
            timeline,
            review_packet,
            ledger_summary,
            low_resource_fixture_evidence,
            elapsed_hours,
            current_gap_hours,
            max_gap_hours,
            required_evidence,
        )
        actions = self._next_actions(
            timeline,
            blockers,
            current_gap_hours,
            checkpoint_due_in_hours,
            checkpoint_interval_hours,
        )
        status = self._status(timeline, review_packet, blockers, event_timestamps, current_gap_hours, max_gap_hours)

        return {
            "status": status,
            "summary": {
                "target_continuous_hours": TARGET_CONTINUOUS_HOURS,
                "target_medium_large_update_count": TARGET_MEDIUM_LARGE_UPDATE_COUNT,
                "completed_medium_large_update_count": ledger_summary["completed_medium_large_update_count"],
                "update_count_ready": ledger_summary["completed_medium_large_update_count"] >= TARGET_MEDIUM_LARGE_UPDATE_COUNT,
                "event_count": timeline["summary"]["event_count"],
                "submitted_event_count": timeline["summary"]["submitted_event_count"],
                "valid_event_count": timeline["summary"]["valid_event_count"],
                "invalid_event_count": timeline["summary"]["invalid_event_count"],
                "verified_continuous_hours": timeline["summary"]["verified_continuous_hours"],
                "continuous_hours_remaining": timeline["summary"]["continuous_hours_remaining"],
                "elapsed_hours_since_start": elapsed_hours,
                "max_allowed_gap_hours": max_gap_hours,
                "current_gap_hours": current_gap_hours,
                "checkpoint_interval_hours": checkpoint_interval_hours,
                "next_checkpoint_due_at": self._format_timestamp(next_checkpoint_due_at),
                "next_checkpoint_due_in_hours": checkpoint_due_in_hours,
                "required_evidence_ready_count": sum(1 for item in required_evidence if item["status"] == "ready"),
                "required_evidence_count": len(required_evidence),
                "blocker_count": len(blockers),
                "low_resource_fixture_evidence_status": self._fixture_evidence_status(low_resource_fixture_evidence),
                "low_resource_fixture_evidence_ready": self._fixture_evidence_status(low_resource_fixture_evidence) == "ready",
                "low_resource_fixture_evidence_release_ready": self._fixture_summary_bool(
                    low_resource_fixture_evidence,
                    "release_ready",
                ),
                "low_resource_fixture_evidence_observed_count": self._fixture_summary_int(
                    low_resource_fixture_evidence,
                    "observed_fixture_count",
                ),
                "low_resource_fixture_evidence_archived_count": self._fixture_summary_int(
                    low_resource_fixture_evidence,
                    "archived_fixture_count",
                ),
                "low_resource_fixture_evidence_blocking_count": self._fixture_summary_int(
                    low_resource_fixture_evidence,
                    "blocking_check_count",
                ),
                "low_resource_fixture_evidence_raw_payload_echoed": False,
                "raw_payload_echoed": False,
                "newapi_called": False,
                "completion_ready": timeline["summary"]["completion_ready"] is True
                and review_packet["summary"]["packet_ready_for_support_claim"] is True,
            },
            "run_window": {
                "start_timestamp": self._format_timestamp(start_timestamp),
                "latest_event_timestamp": self._format_timestamp(latest_timestamp),
                "current_timestamp": self._format_timestamp(now),
                "best_window": timeline["best_window"],
            },
            "low_resource_fixture_evidence": low_resource_fixture_evidence,
            "required_evidence": required_evidence,
            "blockers": blockers,
            "next_actions": actions,
            "checkpoint_policy": {
                "checkpoint_interval_hours": checkpoint_interval_hours,
                "max_allowed_gap_hours": max_gap_hours,
                "required_event_types": list(REQUIRED_EVENT_TYPES),
                "rule": "Record metadata-only maintenance events before the next checkpoint and keep adjacent valid events inside the max gap.",
            },
            "source_summaries": {
                "ledger": ledger_summary,
                "timeline": timeline["summary"],
                "review_packet": review_packet["summary"],
                "low_resource_fixture_evidence": self._fixture_evidence_source_summary(low_resource_fixture_evidence),
            },
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "raw_logs_included": False,
                "raw_stdout_included": False,
                "raw_stderr_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "raw_gateway_response_included": False,
                "low_resource_fixture_evidence_raw_payload_included": False,
                "credentials_included": False,
                "emails_included": False,
                "newapi_called": False,
                "returns_archive_summaries_only": True,
                "output_scope": "metadata-only active-session monitor with timestamps, event types, readiness, blockers, and next actions",
            },
            "validation_commands": [
                "python -m pytest tests/test_continuous_session_run_monitor.py -q",
                "python -m pytest tests/test_continuous_session_timeline.py tests/test_continuous_session_review_packet.py tests/test_validation_event_evidence.py -q",
                "python -m pytest tests/test_continuous_update_ledger.py -q",
                "npm run typecheck",
                "npm run build",
            ],
        }

    def _timeline_payload(self, data: dict[str, Any], ledger_summary: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "completed_medium_large_update_count": ledger_summary["completed_medium_large_update_count"],
        }
        for key in ("events", "validation_events", "heartbeat_events", "git_history", "git_since", "max_allowed_gap_hours"):
            if key in data:
                payload[key] = data[key]
        for key in ("low_resource_fixture_review", "fixture_review", "local_run_review"):
            if isinstance(data.get(key), dict):
                payload[key] = data[key]
        return payload

    def _required_evidence(
        self,
        timeline: dict[str, Any],
        low_resource_fixture_evidence: dict[str, Any],
    ) -> list[dict[str, Any]]:
        event_types = {
            item.get("event_type")
            for item in timeline.get("timeline_events", [])
            if item.get("status") == "pass"
        }
        evidence = []
        descriptions = {
            "commit": "Repository commit or code/doc update checkpoint.",
            "test": "Focused pytest, typecheck, build, benchmark, or fixture validation.",
            "push": "GitHub push evidence for the active work window.",
            "review": "Release, privacy, evidence, or product-risk review checkpoint.",
            "credential_scan": "Secret scan before commit or push.",
        }
        for event_type in REQUIRED_EVENT_TYPES:
            ready = event_type in event_types
            evidence.append(
                {
                    "event_type": event_type,
                    "status": "ready" if ready else "missing",
                    "description": descriptions[event_type],
                }
            )
        low_resource_ready = timeline["summary"].get("low_resource_event_count", 0) > 0
        fixture_status = self._fixture_evidence_status(low_resource_fixture_evidence)
        fixture_ready = fixture_status == "ready"
        fixture_blocked = fixture_status in {"blocked", "needs_escalation"}
        if fixture_blocked:
            low_resource_status = "blocked"
        elif fixture_ready or low_resource_ready:
            low_resource_status = "ready"
        elif fixture_status == "review_recommended":
            low_resource_status = "review_recommended"
        else:
            low_resource_status = "missing"
        evidence.append(
            {
                "event_type": "low_resource_legal_fixture",
                "status": low_resource_status,
                "description": "Laptop-safe legal fixture or quick-suite run for the active window.",
                "fixture_evidence_status": fixture_status,
                "observed_fixture_count": self._fixture_summary_int(
                    low_resource_fixture_evidence,
                    "observed_fixture_count",
                ),
                "archived_fixture_count": self._fixture_summary_int(
                    low_resource_fixture_evidence,
                    "archived_fixture_count",
                ),
                "release_ready": self._fixture_summary_bool(low_resource_fixture_evidence, "release_ready"),
                "source_endpoints": low_resource_fixture_evidence.get("source_endpoints", {}),
            }
        )
        return evidence

    def _blockers(
        self,
        timeline: dict[str, Any],
        review_packet: dict[str, Any],
        ledger_summary: dict[str, Any],
        low_resource_fixture_evidence: dict[str, Any],
        elapsed_hours: int,
        current_gap_hours: int | None,
        max_gap_hours: int,
        required_evidence: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []
        if ledger_summary["completed_medium_large_update_count"] < TARGET_MEDIUM_LARGE_UPDATE_COUNT:
            blockers.append(
                {
                    "id": "update-ledger-not-ready",
                    "severity": "hard",
                    "detail": "The 100+ medium/large update count is still below target.",
                }
            )
        if elapsed_hours < TARGET_CONTINUOUS_HOURS:
            blockers.append(
                {
                    "id": "active-window-under-24h",
                    "severity": "hard",
                    "detail": f"{TARGET_CONTINUOUS_HOURS - elapsed_hours} hour(s) still need timestamped continuity evidence.",
                }
            )
        if current_gap_hours is None:
            blockers.append(
                {
                    "id": "active-events-missing",
                    "severity": "review",
                    "detail": "No timestamped active-run events were submitted.",
                }
            )
        elif current_gap_hours > max_gap_hours:
            blockers.append(
                {
                    "id": "current-checkpoint-gap-exceeded",
                    "severity": "hard",
                    "detail": f"The current event gap is {current_gap_hours} hour(s), above the {max_gap_hours} hour limit.",
                }
            )
        missing = [item["event_type"] for item in required_evidence if item["status"] != "ready"]
        if missing:
            blockers.append(
                {
                    "id": "required-evidence-missing",
                    "severity": "review",
                    "detail": ",".join(missing),
                }
            )
        fixture_status = self._fixture_evidence_status(low_resource_fixture_evidence)
        if fixture_status in {"blocked", "needs_escalation"}:
            blockers.append(
                {
                    "id": "low-resource-fixture-evidence-blocked",
                    "severity": "review",
                    "detail": "The supplied low-resource fixture review did not produce archive-safe ready evidence.",
                }
            )
        elif fixture_status == "review_recommended":
            blockers.append(
                {
                    "id": "low-resource-fixture-evidence-review-recommended",
                    "severity": "review",
                    "detail": "The low-resource fixture review needs reviewer follow-up before it can support the active run.",
                }
            )
        for blocker in timeline.get("blockers", [])[:8]:
            blockers.append(
                {
                    "id": self._safe_token(blocker.get("id")),
                    "severity": self._safe_token(blocker.get("severity")) or "review",
                    "detail": self._safe_detail(blocker.get("detail")),
                }
            )
        for blocker in review_packet.get("blockers", [])[:8]:
            blockers.append(
                {
                    "id": f"packet-{self._safe_token(blocker.get('id'))}",
                    "severity": self._safe_token(blocker.get("severity")) or "review",
                    "detail": self._safe_detail(blocker.get("detail")),
                }
            )
        return self._dedupe(blockers)

    def _next_actions(
        self,
        timeline: dict[str, Any],
        blockers: list[dict[str, Any]],
        current_gap_hours: int | None,
        checkpoint_due_in_hours: int,
        checkpoint_interval_hours: int,
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        if current_gap_hours is None:
            actions.append(
                {
                    "id": "start-active-run-events",
                    "priority": "high",
                    "detail": "Submit the first commit/test/review/scan/push event metadata for the active run.",
                }
            )
        elif checkpoint_due_in_hours == 0:
            actions.append(
                {
                    "id": "record-next-checkpoint-now",
                    "priority": "high",
                    "detail": "Record a fresh maintenance event and validation checkpoint now.",
                }
            )
        elif checkpoint_due_in_hours <= 1:
            actions.append(
                {
                    "id": "checkpoint-due-soon",
                    "priority": "medium",
                    "detail": "Prepare the next metadata-only checkpoint before the continuity gap reaches the limit.",
                }
            )
        if any(blocker["id"] == "required-evidence-missing" for blocker in blockers):
            actions.append(
                {
                    "id": "fill-required-evidence-types",
                    "priority": "high",
                    "detail": "Add missing required event types: commit, test, push, review, credential_scan, and low_resource_legal_fixture.",
                }
            )
        if any(blocker["id"].startswith("low-resource-fixture-evidence-") for blocker in blockers):
            actions.append(
                {
                    "id": "review-low-resource-fixture-evidence",
                    "priority": "high",
                    "detail": "Re-run or review the cheap-first fixture evidence through local-run-review and result-archive before relying on it.",
                }
            )
        if timeline["summary"].get("continuous_hours_remaining", TARGET_CONTINUOUS_HOURS) > 0:
            actions.append(
                {
                    "id": "continue-window",
                    "priority": "medium",
                    "detail": f"Keep collecting events every {checkpoint_interval_hours} hour(s) until the full 24-hour window is reviewable.",
                }
            )
        actions.append(
            {
                "id": "run-validation-batch",
                "priority": "medium",
                "detail": "Run focused backend tests, frontend typecheck/build, low-resource legal fixtures, and credential scans before the next push.",
            }
        )
        return actions[:6]

    def _status(
        self,
        timeline: dict[str, Any],
        review_packet: dict[str, Any],
        blockers: list[dict[str, Any]],
        event_timestamps: list[datetime],
        current_gap_hours: int | None,
        max_gap_hours: int,
    ) -> str:
        if (
            timeline["summary"].get("completion_ready") is True
            and review_packet["summary"].get("packet_ready_for_support_claim") is True
        ):
            return "ready_for_review"
        if not event_timestamps:
            return "not_started"
        if any(blocker.get("severity") == "hard" for blocker in blockers):
            if current_gap_hours is not None and current_gap_hours > max_gap_hours:
                return "blocked"
            return "running"
        return "at_risk" if blockers else "running"

    def _event_timestamps(self, events: list[dict[str, Any]]) -> list[datetime]:
        timestamps = []
        for event in events:
            if event.get("source") not in {"continuous_session_evidence", "validation_event_evidence"}:
                continue
            parsed = self._parse_timestamp(event.get("timestamp"))
            if parsed:
                timestamps.append(parsed)
        return sorted(timestamps)

    def _start_timestamp(self, data: dict[str, Any], event_timestamps: list[datetime]) -> datetime | None:
        return self._parse_timestamp(data.get("session_start_timestamp") or data.get("start_timestamp")) or (
            event_timestamps[0] if event_timestamps else None
        )

    def _next_checkpoint_due_at(
        self,
        anchor: datetime | None,
        checkpoint_interval_hours: int,
    ) -> datetime | None:
        if anchor is None:
            return None
        return anchor + timedelta(hours=checkpoint_interval_hours)

    def _hours_between(self, start: datetime | None, end: datetime | None) -> int:
        if start is None or end is None or end < start:
            return 0
        return int((end - start).total_seconds() // 3600)

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str) and value.strip() and not SENSITIVE_PATTERN.search(value):
            try:
                parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _format_timestamp(self, value: datetime | None) -> str | None:
        return value.isoformat().replace("+00:00", "Z") if value else None

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "-")[:100]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _safe_detail(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"\s+", " ", raw)[:240]

    def _fixture_evidence_status(self, evidence: dict[str, Any]) -> str:
        return self._safe_token(evidence.get("status")) or "not_supplied"

    def _fixture_summary_int(self, evidence: dict[str, Any], key: str) -> int:
        summary = evidence.get("summary") if isinstance(evidence.get("summary"), dict) else {}
        value = summary.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0

    def _fixture_summary_bool(self, evidence: dict[str, Any], key: str) -> bool:
        summary = evidence.get("summary") if isinstance(evidence.get("summary"), dict) else {}
        return summary.get(key) is True

    def _fixture_evidence_source_summary(self, evidence: dict[str, Any]) -> dict[str, Any]:
        summary = evidence.get("summary") if isinstance(evidence.get("summary"), dict) else {}
        return {
            "status": self._fixture_evidence_status(evidence),
            "review_status": self._safe_token(summary.get("review_status")) or "not_supplied",
            "archive_status": self._safe_token(summary.get("archive_status")) or "not_supplied",
            "observed_fixture_count": self._fixture_summary_int(evidence, "observed_fixture_count"),
            "archived_fixture_count": self._fixture_summary_int(evidence, "archived_fixture_count"),
            "blocking_check_count": self._fixture_summary_int(evidence, "blocking_check_count"),
            "warning_check_count": self._fixture_summary_int(evidence, "warning_check_count"),
            "release_ready": self._fixture_summary_bool(evidence, "release_ready"),
            "raw_payload_echoed": False,
            "raw_gateway_response_included": False,
            "raw_model_output_included": False,
        }

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    def _dedupe(self, blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped = []
        seen = set()
        for blocker in blockers:
            key = blocker.get("id")
            if key and key not in seen:
                deduped.append(blocker)
                seen.add(key)
        return deduped
