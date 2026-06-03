from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any


TARGET_HOURS = 24
REQUIRED_EVENT_TYPES = ("commit", "test", "push", "review")

SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HeartbeatEventType:
    event_type: str
    purpose: str
    required_fields: tuple[str, ...]
    accepted_evidence: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_fields"] = list(self.required_fields)
        data["accepted_evidence"] = list(self.accepted_evidence)
        return data


class MaintenanceHeartbeatEvidenceService:
    """Build a privacy-safe heartbeat evidence report for long maintenance windows."""

    def build_evidence(self, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        raw_events = events if isinstance(events, list) else []
        records = [
            self._record(item, index)
            for index, item in enumerate(raw_events, start=1)
            if isinstance(item, dict)
        ]
        records = sorted(records, key=lambda item: item["timestamp"] or "")
        valid_records = [item for item in records if item["status"] == "pass"]
        verified_hours = self._verified_hours(valid_records)
        missing_types = [event_type for event_type in REQUIRED_EVENT_TYPES if event_type not in {item["event_type"] for item in valid_records}]
        ready = verified_hours >= TARGET_HOURS and not missing_types

        return {
            "status": "ready_for_review" if ready else "collecting",
            "summary": {
                "target_hours": TARGET_HOURS,
                "event_count": len(records),
                "valid_event_count": len(valid_records),
                "invalid_event_count": len(records) - len(valid_records),
                "verified_continuous_hours": verified_hours,
                "remaining_hours": max(0, TARGET_HOURS - verified_hours),
                "required_event_types": list(REQUIRED_EVENT_TYPES),
                "missing_event_types": missing_types,
                "ready_for_goal_claim": ready,
                "raw_payload_echoed": False,
            },
            "event_type_schema": [item.to_api() for item in self._event_types()],
            "heartbeat_records": records,
            "gap_analysis": self._gap_analysis(records, missing_types, verified_hours),
            "recommended_actions": self._recommended_actions(missing_types, verified_hours),
            "privacy_note": (
                "Heartbeat evidence stores only event ids, event types, timestamps, commit hashes, validation labels, "
                "and repository paths. It must not include API keys, account credentials, emails, raw client documents, "
                "prompts, raw model responses, or private legal matter text."
            ),
            "validation_commands": [
                "python -m pytest tests/test_maintenance_heartbeat_evidence.py -q",
            ],
        }

    def _event_types(self) -> tuple[HeartbeatEventType, ...]:
        return (
            HeartbeatEventType(
                event_type="commit",
                purpose="Show repository-backed work occurred during the window.",
                required_fields=("timestamp", "commit_hash"),
                accepted_evidence=("git commit hash", "changed file paths", "commit title"),
            ),
            HeartbeatEventType(
                event_type="test",
                purpose="Show validation continued alongside implementation.",
                required_fields=("timestamp", "validation_id"),
                accepted_evidence=("pytest command", "typecheck command", "build command"),
            ),
            HeartbeatEventType(
                event_type="push",
                purpose="Show remote GitHub evidence was published for review.",
                required_fields=("timestamp", "commit_hash"),
                accepted_evidence=("origin/main update", "remote commit hash"),
            ),
            HeartbeatEventType(
                event_type="review",
                purpose="Show the maintainer reviewed claims, risks, or release evidence.",
                required_fields=("timestamp", "validation_id"),
                accepted_evidence=("release readiness check", "maintenance evidence update", "credential scan"),
            ),
        )

    def _record(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        timestamp = self._timestamp(item.get("timestamp") or item.get("created_at") or item.get("time"))
        event_type = self._safe_token(item.get("event_type") or item.get("type") or "")
        commit_hash = self._commit_hash(item.get("commit_hash") or item.get("commit") or "")
        validation_id = self._safe_token(item.get("validation_id") or item.get("check_id") or "")
        evidence_paths = self._safe_paths(item.get("evidence_paths"))
        missing_fields = []

        if not timestamp:
            missing_fields.append("timestamp")
        if event_type not in REQUIRED_EVENT_TYPES:
            missing_fields.append("event_type")
        if event_type in {"commit", "push"} and not commit_hash:
            missing_fields.append("commit_hash")
        if event_type in {"test", "review"} and not validation_id:
            missing_fields.append("validation_id")

        return {
            "id": self._safe_token(item.get("id") or f"heartbeat-{index}"),
            "event_type": event_type or "unknown",
            "timestamp": timestamp,
            "commit_hash": commit_hash,
            "validation_id": validation_id,
            "evidence_paths": evidence_paths,
            "status": "fail" if missing_fields else "pass",
            "missing_fields": missing_fields,
        }

    def _verified_hours(self, records: list[dict[str, Any]]) -> int:
        timestamps = [self._parse_timestamp(item["timestamp"]) for item in records if item.get("timestamp")]
        timestamps = [item for item in timestamps if item is not None]
        if len(timestamps) < 2:
            return 0
        span_seconds = (max(timestamps) - min(timestamps)).total_seconds()
        return max(0, int(span_seconds // 3600))

    def _gap_analysis(self, records: list[dict[str, Any]], missing_types: list[str], verified_hours: int) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        if verified_hours < TARGET_HOURS:
            gaps.append(
                {
                    "id": "continuous-window-short",
                    "status": "open",
                    "detail": f"Need {TARGET_HOURS - verified_hours} more verified hour(s).",
                }
            )
        if missing_types:
            gaps.append(
                {
                    "id": "required-event-types-missing",
                    "status": "open",
                    "detail": ", ".join(missing_types),
                }
            )
        invalid_count = sum(1 for item in records if item["status"] == "fail")
        if invalid_count:
            gaps.append(
                {
                    "id": "invalid-heartbeat-records",
                    "status": "open",
                    "detail": f"{invalid_count} record(s) are missing required metadata.",
                }
            )
        if not gaps:
            gaps.append({"id": "heartbeat-window-reviewable", "status": "closed", "detail": "Heartbeat evidence is reviewable."})
        return gaps

    def _recommended_actions(self, missing_types: list[str], verified_hours: int) -> list[str]:
        actions = []
        if verified_hours < TARGET_HOURS:
            actions.append("Keep collecting timestamped commits, tests, pushes, and review events across the full window.")
        if missing_types:
            actions.append(f"Add missing heartbeat event types: {', '.join(missing_types)}.")
        if not actions:
            actions.append("Export the heartbeat evidence with release readiness and continuous update ledger records.")
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
        raw = str(value or "").strip().lower().replace(" ", "-")[:80]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _safe_paths(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        paths = []
        for item in value[:20]:
            path = str(item or "").strip().replace("\\", "/")
            if not path or SENSITIVE_PATTERN.search(path):
                continue
            if path.startswith(("app/backend/", "app/frontend/", "docs/")):
                paths.append(path[:160])
        return paths
