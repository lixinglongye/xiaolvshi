from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import re
from typing import Any


REQUIRED_VALIDATION_EVENT_TYPES = ("test", "credential_scan", "push", "review", "legal_fixture")
ALLOWED_VALIDATION_EVENT_TYPES = REQUIRED_VALIDATION_EVENT_TYPES + ("release_review",)
SESSION_EVENT_TYPE_MAP = {"release_review": "review"}
PASS_STATUSES = {
    "clean",
    "complete",
    "completed",
    "ok",
    "pass",
    "passed",
    "published",
    "pushed",
    "ready",
    "reviewed",
    "success",
    "succeeded",
}
RAW_FIELD_PATTERN = re.compile(
    r"(stdout|stderr|raw|log|logs|output|trace|prompt|response|model|document|legal_text|text_body|secret|password|api_key|token|email)",
    re.IGNORECASE,
)
SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ValidationEventType:
    event_type: str
    session_event_type: str
    required_metadata: tuple[str, ...]
    purpose: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_metadata"] = list(self.required_metadata)
        return data


class ValidationEventEvidenceService:
    """Normalize metadata-only validation events into timeline-ready session events."""

    def build_evidence(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        raw_events = payload if isinstance(payload, list) else data.get("events")
        events = raw_events if isinstance(raw_events, list) else []
        records = [
            self._record(item, index)
            for index, item in enumerate(events, start=1)
            if isinstance(item, dict)
        ]
        records = sorted(records, key=lambda item: item["timestamp"] or "")
        valid_records = [item for item in records if item["status"] == "pass"]
        present_types = {item["event_type"] for item in valid_records}
        missing_types = [
            event_type
            for event_type in REQUIRED_VALIDATION_EVENT_TYPES
            if event_type not in present_types
        ]
        invalid_count = len(records) - len(valid_records)
        normalized_events = [self._session_event(item) for item in valid_records]
        low_resource_legal_fixture = any(
            item["event_type"] == "legal_fixture"
            and ("low-resource" in item["labels"] or "quick-suite" in item["labels"])
            for item in valid_records
        )
        ready_for_timeline = bool(records) and invalid_count == 0 and not missing_types

        return {
            "status": "ready_for_timeline" if ready_for_timeline else ("needs_attention" if invalid_count else "collecting"),
            "summary": {
                "event_count": len(records),
                "valid_event_count": len(valid_records),
                "invalid_event_count": invalid_count,
                "required_event_types": list(REQUIRED_VALIDATION_EVENT_TYPES),
                "missing_event_types": missing_types,
                "event_type_counts": self._event_type_counts(valid_records),
                "normalized_session_event_count": len(normalized_events),
                "low_resource_legal_fixture_evidence": low_resource_legal_fixture,
                "ready_for_timeline": ready_for_timeline,
                "ready_for_goal_claim": False,
                "raw_payload_echoed": False,
            },
            "event_schema": [item.to_api() for item in self._event_types()],
            "event_reviews": records,
            "normalized_session_events": normalized_events,
            "missing_event_types": missing_types,
            "gap_analysis": self._gap_analysis(records, missing_types, invalid_count, low_resource_legal_fixture),
            "recommended_actions": self._recommended_actions(missing_types, invalid_count, low_resource_legal_fixture),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "raw_stdout_included": False,
                "raw_stderr_included": False,
                "raw_logs_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "credentials_included": False,
                "emails_included": False,
                "output_scope": "timestamps, sanitized ids, commit hashes, labels, statuses, and repository evidence paths only",
            },
            "validation_commands": [
                "python -m pytest tests/test_validation_event_evidence.py -q",
                "rg -n \"(sk-[A-Za-z0-9]{20,}|pa[s]sword|se[c]ret|@[A-Za-z0-9.-]+)\" app/backend app/frontend docs --glob \"!app/frontend/node_modules/**\" --glob \"!app/frontend/dist/**\"",
                "git push origin main",
            ],
        }

    def _event_types(self) -> tuple[ValidationEventType, ...]:
        return (
            ValidationEventType("test", "test", ("timestamp", "validation_id", "status"), "Focused pytest, typecheck, build, or benchmark run."),
            ValidationEventType("credential_scan", "credential_scan", ("timestamp", "validation_id", "status"), "Credential or sensitive-material scan before commit or push."),
            ValidationEventType("push", "push", ("timestamp", "commit_hash", "status"), "Remote GitHub push or published commit metadata."),
            ValidationEventType("review", "review", ("timestamp", "validation_id", "status"), "Maintainer release, evidence, or claim review."),
            ValidationEventType("release_review", "review", ("timestamp", "validation_id", "status"), "Alias for release-review metadata normalized to review."),
            ValidationEventType("legal_fixture", "legal_fixture", ("timestamp", "validation_id", "status"), "Low-resource legal document fixture or benchmark validation."),
        )

    def _record(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        raw_event_type = self._safe_token(item.get("event_type") or item.get("type") or "")
        event_type = SESSION_EVENT_TYPE_MAP.get(raw_event_type, raw_event_type)
        timestamp = self._timestamp(item.get("timestamp") or item.get("created_at") or item.get("time"))
        commit_hash = self._commit_hash(item.get("commit_hash") or item.get("commit") or item.get("hash"))
        validation_id = self._safe_token(
            item.get("validation_id") or item.get("check_id") or item.get("run_id") or item.get("id") or ""
        )
        labels = self._safe_list(item.get("labels"), max_items=12)
        if item.get("low_resource") is True and "low-resource" not in labels:
            labels.append("low-resource")
        evidence_paths = self._safe_paths(item.get("evidence_paths"))
        status = self._status(item.get("status") or item.get("result") or item.get("outcome"))
        rejected_fields = self._rejected_fields(item)
        missing_fields = []

        if not timestamp:
            missing_fields.append("timestamp")
        if raw_event_type not in ALLOWED_VALIDATION_EVENT_TYPES:
            missing_fields.append("event_type")
        if event_type == "push" and not commit_hash:
            missing_fields.append("commit_hash")
        if event_type in {"test", "credential_scan", "review", "legal_fixture"} and not validation_id:
            missing_fields.append("validation_id")
        if status not in PASS_STATUSES:
            missing_fields.append("status")
        if rejected_fields:
            missing_fields.append("metadata_only")

        record_id = self._safe_token(item.get("id") or f"validation-event-{index}") or f"validation-event-{index}"
        return {
            "id": record_id,
            "event_type": event_type or "unknown",
            "timestamp": timestamp,
            "commit_hash": commit_hash,
            "validation_id": validation_id,
            "status_label": status,
            "labels": labels,
            "evidence_paths": evidence_paths,
            "status": "fail" if missing_fields else "pass",
            "missing_fields": sorted(set(missing_fields)),
            "rejected_fields": rejected_fields,
        }

    def _session_event(self, record: dict[str, Any]) -> dict[str, Any]:
        session_event = {
            "id": f"validation-{record['id']}",
            "event_type": record["event_type"],
            "timestamp": record["timestamp"],
            "labels": list(record.get("labels") or []) + ["validation-event"],
            "evidence_paths": list(record.get("evidence_paths") or []),
        }
        if record["event_type"] == "push":
            session_event["commit_hash"] = record["commit_hash"]
        else:
            session_event["validation_id"] = record["validation_id"]
        return session_event

    def _gap_analysis(
        self,
        records: list[dict[str, Any]],
        missing_types: list[str],
        invalid_count: int,
        low_resource_legal_fixture: bool,
    ) -> list[dict[str, Any]]:
        gaps: list[dict[str, Any]] = []
        if not records:
            gaps.append(
                {
                    "id": "validation-events-missing",
                    "status": "open",
                    "detail": "Submit metadata-only test, credential-scan, push, review, and legal fixture validation events.",
                }
            )
        if missing_types:
            gaps.append(
                {
                    "id": "validation-event-types-missing",
                    "status": "open",
                    "detail": ",".join(missing_types),
                }
            )
        if invalid_count:
            gaps.append(
                {
                    "id": "invalid-validation-events",
                    "status": "open",
                    "detail": f"{invalid_count} validation event(s) are missing required metadata or include raw payload fields.",
                }
            )
        if not low_resource_legal_fixture:
            gaps.append(
                {
                    "id": "low-resource-legal-fixture-missing",
                    "status": "open",
                    "detail": "Attach at least one legal_fixture event labeled low-resource or quick-suite.",
                }
            )
        if not gaps:
            gaps.append({"id": "validation-events-reviewable", "status": "closed", "detail": "Validation events are timeline-ready."})
        return gaps

    def _recommended_actions(
        self,
        missing_types: list[str],
        invalid_count: int,
        low_resource_legal_fixture: bool,
    ) -> list[str]:
        actions = []
        if missing_types:
            actions.append(f"Add missing validation event metadata: {', '.join(missing_types)}.")
        if invalid_count:
            actions.append("Remove raw logs, raw legal text, raw model output, credentials, and emails; keep only metadata ids and paths.")
        if not low_resource_legal_fixture:
            actions.append("Record a laptop-safe legal_fixture result with a low-resource or quick-suite label.")
        if not actions:
            actions.append("Submit normalized events to the continuous-session timeline alongside commit cadence evidence.")
        return actions

    def _event_type_counts(self, records: list[dict[str, Any]]) -> dict[str, int]:
        counts = {event_type: 0 for event_type in REQUIRED_VALIDATION_EVENT_TYPES}
        for record in records:
            event_type = record.get("event_type")
            if event_type in counts:
                counts[event_type] += 1
        return counts

    def _rejected_fields(self, item: dict[str, Any]) -> list[str]:
        rejected = []
        allowed = {
            "check_id",
            "commit",
            "commit_hash",
            "created_at",
            "event_type",
            "evidence_paths",
            "hash",
            "id",
            "labels",
            "low_resource",
            "outcome",
            "result",
            "run_id",
            "status",
            "time",
            "timestamp",
            "type",
            "validation_id",
        }
        for key, value in item.items():
            key_token = self._safe_token(key)
            if not key_token:
                continue
            if key not in allowed or RAW_FIELD_PATTERN.search(str(key)):
                rejected.append(key_token)
                continue
            if isinstance(value, str) and SENSITIVE_PATTERN.search(value):
                rejected.append(key_token)
        return sorted(set(rejected))[:12]

    def _timestamp(self, value: Any) -> str | None:
        parsed = self._parse_timestamp(value)
        return parsed.isoformat().replace("+00:00", "Z") if parsed else None

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

    def _commit_hash(self, value: Any) -> str:
        raw = str(value or "").strip().lower()
        if SENSITIVE_PATTERN.search(raw):
            return ""
        return raw if re.fullmatch(r"[0-9a-f]{7,40}", raw) else ""

    def _status(self, value: Any) -> str:
        return self._safe_token(value)

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
