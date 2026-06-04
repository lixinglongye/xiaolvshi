from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
from typing import Any


TARGET_CONTINUOUS_HOURS = 24
DEFAULT_MAX_GAP_HOURS = 5
DEFAULT_GIT_SINCE = "48 hours ago"

SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret)",
    re.IGNORECASE,
)


class GitHistoryEvidenceService:
    """Evaluate git commit cadence as metadata-only maintenance evidence."""

    def build_evidence(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        raw_events = payload if isinstance(payload, list) else data.get("events")
        events_source = "submitted_metadata" if isinstance(raw_events, list) else "local_git_log"
        max_gap_hours = self._bounded_int(data.get("max_allowed_gap_hours"), DEFAULT_MAX_GAP_HOURS, 1, 12)
        git_since = self._safe_since(data.get("git_since") or DEFAULT_GIT_SINCE)
        raw_events = raw_events if isinstance(raw_events, list) else self._load_git_events(git_since)
        commit_events = [
            self._commit_event(item, index)
            for index, item in enumerate(raw_events, start=1)
            if isinstance(item, dict)
        ]
        commit_events = sorted(commit_events, key=lambda item: item["timestamp"] or "")
        valid_events = [item for item in commit_events if item["status"] == "pass"]
        longest_window = self._longest_window(valid_events, max_gap_hours)
        exceeded_gaps = self._exceeded_gaps(valid_events, max_gap_hours)
        commit_cadence_ready = longest_window["verified_hours"] >= TARGET_CONTINUOUS_HOURS

        blockers = []
        if not commit_cadence_ready:
            blockers.append(
                {
                    "id": "git-history-window-short",
                    "severity": "review",
                    "detail": f"Need {TARGET_CONTINUOUS_HOURS - longest_window['verified_hours']} more commit-cadence hour(s).",
                }
            )
        if exceeded_gaps:
            blockers.append(
                {
                    "id": "git-history-gap-exceeded",
                    "severity": "review",
                    "detail": f"{len(exceeded_gaps)} gap(s) exceed the {max_gap_hours} hour limit.",
                }
            )
        if len(valid_events) != len(commit_events):
            blockers.append(
                {
                    "id": "invalid-git-history-records",
                    "severity": "hard",
                    "detail": f"{len(commit_events) - len(valid_events)} commit record(s) are missing required metadata.",
                }
            )
        blockers.append(
            {
                "id": "non-commit-validation-evidence-required",
                "severity": "review",
                "detail": "Git cadence does not prove test, credential-scan, push, low-resource fixture, or release-review events by itself.",
            }
        )

        return {
            "status": "cadence_reviewable" if commit_cadence_ready else "collecting",
            "summary": {
                "source": events_source,
                "git_since": git_since,
                "target_continuous_hours": TARGET_CONTINUOUS_HOURS,
                "max_allowed_gap_hours": max_gap_hours,
                "commit_count": len(commit_events),
                "valid_commit_count": len(valid_events),
                "invalid_commit_count": len(commit_events) - len(valid_events),
                "longest_window_hours": longest_window["verified_hours"],
                "max_observed_gap_hours": longest_window["max_observed_gap_hours"],
                "commit_cadence_ready": commit_cadence_ready,
                "ready_for_goal_claim": False,
                "raw_patch_included": False,
                "raw_payload_echoed": False,
            },
            "longest_window": longest_window,
            "commit_events": commit_events,
            "gap_analysis": exceeded_gaps,
            "blockers": blockers,
            "privacy_boundary": {
                "raw_patch_included": False,
                "raw_diff_included": False,
                "author_email_included": False,
                "credentials_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "output_scope": "commit hashes, timestamps, sanitized titles, and cadence gaps only",
            },
            "validation_commands": [
                "python -m pytest tests/test_git_history_evidence.py -q",
                "git log --since=\"48 hours ago\" --pretty=format:\"%h %cI %s\" --reverse",
            ],
        }

    def _load_git_events(self, git_since: str) -> list[dict[str, Any]]:
        repo_root = Path(__file__).resolve().parents[3]
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"--since={git_since}",
                    "--pretty=format:%H%x1f%cI%x1f%s",
                    "--reverse",
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        events = []
        for line in result.stdout.splitlines():
            parts = line.split("\x1f", 2)
            if len(parts) != 3:
                continue
            commit_hash, timestamp, title = parts
            events.append({"commit_hash": commit_hash, "timestamp": timestamp, "title": title})
        return events

    def _commit_event(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        timestamp = self._timestamp(item.get("timestamp") or item.get("committed_at") or item.get("time"))
        commit_hash = self._commit_hash(item.get("commit_hash") or item.get("commit") or item.get("hash"))
        missing_fields = []
        if not timestamp:
            missing_fields.append("timestamp")
        if not commit_hash:
            missing_fields.append("commit_hash")
        return {
            "id": self._safe_token(item.get("id") or f"git-commit-{index}"),
            "commit_hash": commit_hash[:12],
            "timestamp": timestamp,
            "title": self._safe_title(item.get("title") or item.get("subject") or item.get("message")),
            "status": "fail" if missing_fields else "pass",
            "missing_fields": missing_fields,
        }

    def _longest_window(self, events: list[dict[str, Any]], max_gap_hours: int) -> dict[str, Any]:
        dated_events = [
            (self._parse_timestamp(item["timestamp"]), item)
            for item in events
            if item.get("timestamp")
        ]
        dated_events = [(timestamp, item) for timestamp, item in dated_events if timestamp is not None]
        if not dated_events:
            return self._window_payload([])

        best_chain: list[tuple[datetime, dict[str, Any]]] = []
        current_chain: list[tuple[datetime, dict[str, Any]]] = []
        max_gap_seconds = max_gap_hours * 3600
        for timestamp, item in sorted(dated_events, key=lambda pair: pair[0]):
            if current_chain and (timestamp - current_chain[-1][0]).total_seconds() > max_gap_seconds:
                best_chain = self._larger_window(best_chain, current_chain)
                current_chain = []
            current_chain.append((timestamp, item))
        best_chain = self._larger_window(best_chain, current_chain)
        return self._window_payload(best_chain)

    def _window_payload(self, chain: list[tuple[datetime, dict[str, Any]]]) -> dict[str, Any]:
        if not chain:
            return {
                "start_timestamp": None,
                "end_timestamp": None,
                "verified_hours": 0,
                "commit_count": 0,
                "commit_hashes": [],
                "max_observed_gap_hours": 0,
            }
        gaps = [
            int((chain[index][0] - chain[index - 1][0]).total_seconds() // 3600)
            for index in range(1, len(chain))
        ]
        return {
            "start_timestamp": chain[0][0].isoformat().replace("+00:00", "Z"),
            "end_timestamp": chain[-1][0].isoformat().replace("+00:00", "Z"),
            "verified_hours": max(0, int((chain[-1][0] - chain[0][0]).total_seconds() // 3600)),
            "commit_count": len(chain),
            "commit_hashes": [item["commit_hash"] for _, item in chain],
            "max_observed_gap_hours": max(gaps) if gaps else 0,
        }

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

    def _exceeded_gaps(self, events: list[dict[str, Any]], max_gap_hours: int) -> list[dict[str, Any]]:
        dated_events = [
            (self._parse_timestamp(item["timestamp"]), item)
            for item in events
            if item.get("timestamp")
        ]
        dated_events = [(timestamp, item) for timestamp, item in dated_events if timestamp is not None]
        gaps = []
        for index in range(1, len(dated_events)):
            previous_timestamp, previous = dated_events[index - 1]
            timestamp, current = dated_events[index]
            gap_hours = int((timestamp - previous_timestamp).total_seconds() // 3600)
            if gap_hours > max_gap_hours:
                gaps.append(
                    {
                        "from_commit": previous["commit_hash"],
                        "to_commit": current["commit_hash"],
                        "gap_hours": gap_hours,
                    }
                )
        return gaps

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

    def _safe_title(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw or SENSITIVE_PATTERN.search(raw):
            return "redacted"
        return re.sub(r"\s+", " ", raw)[:120]

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace(" ", "-")[:90]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9_.:-]+", "-", raw).strip("-")

    def _safe_since(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw or SENSITIVE_PATTERN.search(raw):
            return DEFAULT_GIT_SINCE
        return raw[:40]

    def _bounded_int(self, value: Any, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))
