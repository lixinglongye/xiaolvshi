from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any


TARGET_CONTINUOUS_HOURS = 24
TARGET_MEDIUM_LARGE_UPDATE_COUNT = 100
DEFAULT_MAX_GAP_HOURS = 4
REQUIRED_EVENT_TYPES = ("commit", "test", "push", "review", "credential_scan")
OPTIONAL_EVENT_TYPES = ("benchmark", "legal_fixture", "doc_update", "heartbeat")
ALLOWED_EVENT_TYPES = REQUIRED_EVENT_TYPES + OPTIONAL_EVENT_TYPES

SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SessionEventType:
    event_type: str
    purpose: str
    required_evidence: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_evidence"] = list(self.required_evidence)
        return data


class ContinuousSessionEvidenceService:
    """Validate explicit 24-hour maintenance-session evidence without inventing proof."""

    def build_report(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        events = payload if isinstance(payload, list) else data.get("events")
        raw_events = events if isinstance(events, list) else []
        max_gap_hours = self._bounded_int(data.get("max_allowed_gap_hours"), DEFAULT_MAX_GAP_HOURS, 1, 12)
        completed_updates = self._bounded_int(data.get("completed_medium_large_update_count"), 0, 0, 10000)
        target_updates = self._bounded_int(
            data.get("target_medium_large_update_count"),
            TARGET_MEDIUM_LARGE_UPDATE_COUNT,
            1,
            10000,
        )

        records = [
            self._record(item, index)
            for index, item in enumerate(raw_events, start=1)
            if isinstance(item, dict)
        ]
        records = sorted(records, key=lambda item: item["timestamp"] or "")
        valid_records = [item for item in records if item["status"] == "pass"]
        window = self._best_window(valid_records, max_gap_hours)
        required_missing = [
            event_type
            for event_type in REQUIRED_EVENT_TYPES
            if event_type not in set(window["event_types"])
        ]
        low_resource_test_evidence = any(
            item["event_type"] in {"test", "benchmark", "legal_fixture"}
            and ("low-resource" in item["labels"] or "quick-suite" in item["labels"])
            for item in valid_records
        )
        update_count_ready = completed_updates >= target_updates
        invalid_count = len(records) - len(valid_records)
        ready = (
            window["verified_continuous_hours"] >= TARGET_CONTINUOUS_HOURS
            and not required_missing
            and update_count_ready
            and invalid_count == 0
            and low_resource_test_evidence
        )

        return {
            "status": "ready_for_review" if ready else ("needs_attention" if invalid_count else "collecting"),
            "summary": {
                "target_continuous_hours": TARGET_CONTINUOUS_HOURS,
                "target_medium_large_update_count": target_updates,
                "completed_medium_large_update_count": completed_updates,
                "remaining_medium_large_update_count": max(0, target_updates - completed_updates),
                "event_count": len(records),
                "valid_event_count": len(valid_records),
                "invalid_event_count": invalid_count,
                "max_allowed_gap_hours": max_gap_hours,
                "verified_continuous_hours": window["verified_continuous_hours"],
                "continuous_hours_remaining": max(0, TARGET_CONTINUOUS_HOURS - window["verified_continuous_hours"]),
                "required_event_types": list(REQUIRED_EVENT_TYPES),
                "missing_event_types": required_missing,
                "low_resource_test_evidence": low_resource_test_evidence,
                "ready_for_goal_claim": ready,
                "raw_payload_echoed": False,
            },
            "session_policy": {
                "continuity_rule": (
                    "Use the longest chain of valid timestamped events where adjacent records are no more than "
                    f"{max_gap_hours} hour(s) apart."
                ),
                "completion_rule": (
                    "Both the 24-hour continuous evidence window and 100+ medium/large shipped updates must be "
                    "reviewable before completion can be claimed."
                ),
                "required_event_types": [item.to_api() for item in self._event_types()],
            },
            "best_window": window,
            "session_records": records,
            "gap_analysis": self._gap_analysis(
                records,
                valid_records,
                window,
                required_missing,
                low_resource_test_evidence,
                update_count_ready,
                max_gap_hours,
            ),
            "recommended_actions": self._recommended_actions(
                window,
                required_missing,
                low_resource_test_evidence,
                update_count_ready,
            ),
            "privacy_note": (
                "Session evidence stores only sanitized ids, event types, timestamps, commit hashes, validation labels, "
                "short evidence refs, and repository paths. It must not store API keys, account credentials, emails, "
                "raw client documents, prompts, raw model responses, or private legal matter text."
            ),
            "validation_commands": [
                "python -m pytest tests/test_continuous_session_evidence.py -q",
            ],
        }

    def _event_types(self) -> tuple[SessionEventType, ...]:
        return (
            SessionEventType("commit", "Repository-backed implementation or documentation work.", ("timestamp", "commit_hash")),
            SessionEventType("test", "Focused local validation, typecheck, build, or fixture run.", ("timestamp", "validation_id")),
            SessionEventType("push", "Remote GitHub evidence was published for review.", ("timestamp", "commit_hash")),
            SessionEventType("review", "Maintainer reviewed release, evidence, or product-risk claims.", ("timestamp", "validation_id")),
            SessionEventType("credential_scan", "Credential material scan ran before commit or push.", ("timestamp", "validation_id")),
        )

    def _record(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        event_type = self._safe_token(item.get("event_type") or item.get("type") or "")
        timestamp = self._timestamp(item.get("timestamp") or item.get("created_at") or item.get("time"))
        commit_hash = self._commit_hash(item.get("commit_hash") or item.get("commit") or "")
        validation_id = self._safe_token(item.get("validation_id") or item.get("check_id") or "")
        evidence_ref = self._safe_token(item.get("evidence_ref") or item.get("run_id") or item.get("id") or "")
        labels = self._safe_list(item.get("labels"), max_items=12)
        evidence_paths = self._safe_paths(item.get("evidence_paths"))
        missing_fields = []

        if not timestamp:
            missing_fields.append("timestamp")
        if event_type not in ALLOWED_EVENT_TYPES:
            missing_fields.append("event_type")
        if event_type in {"commit", "push"} and not commit_hash:
            missing_fields.append("commit_hash")
        if event_type in {"test", "review", "credential_scan", "benchmark", "legal_fixture"} and not (validation_id or evidence_ref):
            missing_fields.append("validation_id")

        return {
            "id": self._safe_token(item.get("id") or f"session-{index}"),
            "event_type": event_type or "unknown",
            "timestamp": timestamp,
            "commit_hash": commit_hash,
            "validation_id": validation_id,
            "evidence_ref": evidence_ref,
            "labels": labels,
            "evidence_paths": evidence_paths,
            "status": "fail" if missing_fields else "pass",
            "missing_fields": missing_fields,
        }

    def _best_window(self, records: list[dict[str, Any]], max_gap_hours: int) -> dict[str, Any]:
        dated_records = [
            (self._parse_timestamp(item["timestamp"]), item)
            for item in records
            if item.get("timestamp")
        ]
        dated_records = [(timestamp, item) for timestamp, item in dated_records if timestamp is not None]
        if not dated_records:
            return self._window_payload([])

        best_chain: list[tuple[datetime, dict[str, Any]]] = []
        current_chain: list[tuple[datetime, dict[str, Any]]] = []
        max_gap_seconds = max_gap_hours * 3600
        for timestamp, item in sorted(dated_records, key=lambda pair: pair[0]):
            if current_chain and (timestamp - current_chain[-1][0]).total_seconds() > max_gap_seconds:
                best_chain = self._larger_window(best_chain, current_chain)
                current_chain = []
            current_chain.append((timestamp, item))
        best_chain = self._larger_window(best_chain, current_chain)
        return self._window_payload(best_chain)

    def _larger_window(
        self,
        left: list[tuple[datetime, dict[str, Any]]],
        right: list[tuple[datetime, dict[str, Any]]],
    ) -> list[tuple[datetime, dict[str, Any]]]:
        if not left:
            return right
        if not right:
            return left
        left_span = (left[-1][0] - left[0][0]).total_seconds()
        right_span = (right[-1][0] - right[0][0]).total_seconds()
        if right_span > left_span:
            return right
        if right_span == left_span and len(right) > len(left):
            return right
        return left

    def _window_payload(self, chain: list[tuple[datetime, dict[str, Any]]]) -> dict[str, Any]:
        if not chain:
            return {
                "start_timestamp": None,
                "end_timestamp": None,
                "record_count": 0,
                "event_types": [],
                "record_ids": [],
                "verified_continuous_hours": 0,
                "max_observed_gap_hours": 0,
            }
        gaps = [
            int((chain[index][0] - chain[index - 1][0]).total_seconds() // 3600)
            for index in range(1, len(chain))
        ]
        span_hours = int((chain[-1][0] - chain[0][0]).total_seconds() // 3600)
        return {
            "start_timestamp": chain[0][0].isoformat().replace("+00:00", "Z"),
            "end_timestamp": chain[-1][0].isoformat().replace("+00:00", "Z"),
            "record_count": len(chain),
            "event_types": sorted({item["event_type"] for _, item in chain}),
            "record_ids": [item["id"] for _, item in chain],
            "verified_continuous_hours": max(0, span_hours),
            "max_observed_gap_hours": max(gaps) if gaps else 0,
        }

    def _gap_analysis(
        self,
        records: list[dict[str, Any]],
        valid_records: list[dict[str, Any]],
        window: dict[str, Any],
        required_missing: list[str],
        low_resource_test_evidence: bool,
        update_count_ready: bool,
        max_gap_hours: int,
    ) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        broken_gaps = self._broken_gaps(valid_records, max_gap_hours)
        if window["verified_continuous_hours"] < TARGET_CONTINUOUS_HOURS:
            gaps.append(
                {
                    "id": "continuous-session-window-short",
                    "status": "open",
                    "detail": f"Need {TARGET_CONTINUOUS_HOURS - window['verified_continuous_hours']} more verified hour(s).",
                }
            )
        if broken_gaps:
            gaps.append(
                {
                    "id": "continuous-session-window-broken",
                    "status": "open",
                    "detail": f"{len(broken_gaps)} gap(s) exceed the {max_gap_hours} hour limit.",
                    "gaps": broken_gaps[:10],
                }
            )
        if required_missing:
            gaps.append(
                {
                    "id": "required-session-event-types-missing",
                    "status": "open",
                    "detail": ", ".join(required_missing),
                }
            )
        invalid_count = len(records) - len(valid_records)
        if invalid_count:
            gaps.append(
                {
                    "id": "invalid-session-records",
                    "status": "open",
                    "detail": f"{invalid_count} record(s) are missing required metadata.",
                }
            )
        if not low_resource_test_evidence:
            gaps.append(
                {
                    "id": "low-resource-test-evidence-missing",
                    "status": "open",
                    "detail": "Add a quick-suite or low-resource test, benchmark, or legal fixture event.",
                }
            )
        if not update_count_ready:
            gaps.append(
                {
                    "id": "medium-large-update-count-short",
                    "status": "open",
                    "detail": "The 100+ medium/large shipped update count was not provided or is below target.",
                }
            )
        if not gaps:
            gaps.append({"id": "continuous-session-reviewable", "status": "closed", "detail": "Session evidence is reviewable."})
        return gaps

    def _broken_gaps(self, records: list[dict[str, Any]], max_gap_hours: int) -> list[dict[str, Any]]:
        dated_records = [
            (self._parse_timestamp(item["timestamp"]), item)
            for item in records
            if item.get("timestamp")
        ]
        dated_records = [(timestamp, item) for timestamp, item in dated_records if timestamp is not None]
        gaps = []
        for index in range(1, len(dated_records)):
            previous_timestamp, previous = dated_records[index - 1]
            timestamp, current = dated_records[index]
            gap_hours = int((timestamp - previous_timestamp).total_seconds() // 3600)
            if gap_hours > max_gap_hours:
                gaps.append(
                    {
                        "from_event_id": previous["id"],
                        "to_event_id": current["id"],
                        "gap_hours": gap_hours,
                    }
                )
        return gaps

    def _recommended_actions(
        self,
        window: dict[str, Any],
        required_missing: list[str],
        low_resource_test_evidence: bool,
        update_count_ready: bool,
    ) -> list[str]:
        actions = []
        if window["verified_continuous_hours"] < TARGET_CONTINUOUS_HOURS:
            actions.append("Keep collecting timestamped work, validation, push, review, and credential-scan events across the full 24 hours.")
        if required_missing:
            actions.append(f"Add missing required session event types: {', '.join(required_missing)}.")
        if not low_resource_test_evidence:
            actions.append("Record at least one low-resource quick suite, benchmark, or legal fixture validation event.")
        if not update_count_ready:
            actions.append("Attach the continuous update ledger summary showing 100+ medium/large shipped updates.")
        if not actions:
            actions.append("Export the session report with release readiness, OSS maintenance evidence, and the continuous update ledger.")
        return actions

    def _timestamp(self, value: Any) -> str | None:
        parsed = self._parse_timestamp(value)
        return parsed.isoformat().replace("+00:00", "Z") if parsed else None

    def _parse_timestamp(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str) and value.strip() and not SENSITIVE_PATTERN.search(value):
            raw = value.strip().replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(raw)
            except ValueError:
                return None
        else:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _commit_hash(self, value: Any) -> str:
        raw = str(value or "").strip().lower()
        if SENSITIVE_PATTERN.search(raw):
            return ""
        return raw if re.fullmatch(r"[0-9a-f]{7,40}", raw) else ""

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "-")[:90]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _safe_list(self, value: Any, max_items: int) -> list[str]:
        if not isinstance(value, list):
            return []
        safe = []
        for item in value[:max_items]:
            token = self._safe_token(item)
            if token:
                safe.append(token)
        return safe

    def _safe_paths(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        paths = []
        for item in value[:20]:
            path = str(item or "").strip().replace("\\", "/")
            if not path or SENSITIVE_PATTERN.search(path):
                continue
            if path.startswith(("app/backend/", "app/frontend/", "docs/")):
                paths.append(path[:180])
        return paths

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))
