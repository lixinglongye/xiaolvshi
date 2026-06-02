from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SEED_PATH = BACKEND_DIR / "data" / "legal_knowledge" / "contract_law_seed.json"

REQUIRED_FIELDS = (
    "source_id",
    "source_name",
    "article_number",
    "article_title",
    "source_type",
    "authority_level",
    "jurisdiction",
    "legal_domain",
    "topics",
    "keywords",
    "text",
    "summary",
    "source_url",
    "official_source_url",
    "effective_status",
    "verification_status",
)

CRITICAL_CONTRACT_TOPICS = (
    "合同效力",
    "主体资格",
    "格式条款",
    "违约责任",
    "解除",
    "损害赔偿",
    "担保",
    "租赁",
)


class LegalKnowledgeAuditService:
    """Audits local legal knowledge seed files before they are used for review."""

    def audit_seed_file(
        self,
        seed_path: str | Path | None = None,
        *,
        today: date | None = None,
        max_age_days: int = 180,
    ) -> dict[str, Any]:
        path = Path(seed_path) if seed_path else DEFAULT_SEED_PATH
        payload = self._load(path)
        records = payload.get("records") if isinstance(payload.get("records"), list) else []
        today = today or date.today()

        duplicate_ids = self._duplicate_source_ids(records)
        missing_fields = self._missing_required_fields(records)
        generated_at = _parse_date(payload.get("generated_at"))
        age_days = (today - generated_at).days if generated_at else None
        stale = age_days is None or age_days > max_age_days
        verified_count = sum(1 for item in records if _text(item.get("verification_status")) in {"已校验", "verified"})
        reviewable_ratio = round(verified_count / len(records), 3) if records else 0
        topic_counter = self._topic_counter(records)
        missing_topics = [topic for topic in CRITICAL_CONTRACT_TOPICS if topic not in topic_counter]

        status = self._status(
            record_count=len(records),
            duplicate_ids=duplicate_ids,
            missing_fields=missing_fields,
            stale=stale,
            reviewable_ratio=reviewable_ratio,
            missing_topics=missing_topics,
        )

        return {
            "status": status,
            "score": self._score(status, duplicate_ids, missing_fields, stale, reviewable_ratio, missing_topics),
            "seed_path": str(path),
            "schema_version": payload.get("schema_version"),
            "generated_at": payload.get("generated_at"),
            "age_days": age_days,
            "max_age_days": max_age_days,
            "record_count": len(records),
            "duplicate_source_ids": duplicate_ids,
            "missing_required_fields": missing_fields,
            "reviewable_ratio": reviewable_ratio,
            "verified_count": verified_count,
            "source_type_counts": dict(Counter(_text(item.get("source_type")) or "unknown" for item in records)),
            "authority_level_counts": dict(Counter(_text(item.get("authority_level")) or "unknown" for item in records)),
            "topic_counts": dict(topic_counter),
            "missing_critical_topics": missing_topics,
            "recommended_actions": self._recommended_actions(status, stale, missing_fields, duplicate_ids, missing_topics),
        }

    def _load(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            raise ValueError("Legal knowledge seed must be a JSON object.")
        return payload

    def _duplicate_source_ids(self, records: list[dict[str, Any]]) -> list[str]:
        counts = Counter(_text(item.get("source_id")) for item in records)
        return sorted(source_id for source_id, count in counts.items() if source_id and count > 1)

    def _missing_required_fields(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        missing: list[dict[str, Any]] = []
        for index, item in enumerate(records):
            fields = [field for field in REQUIRED_FIELDS if _is_empty(item.get(field))]
            if fields:
                missing.append(
                    {
                        "index": index,
                        "source_id": _text(item.get("source_id")) or f"record-{index}",
                        "fields": fields,
                    }
                )
        return missing

    def _topic_counter(self, records: list[dict[str, Any]]) -> Counter:
        counter: Counter = Counter()
        for item in records:
            topics = item.get("topics")
            if isinstance(topics, list):
                counter.update(_text(topic) for topic in topics if _text(topic))
        return counter

    def _status(
        self,
        *,
        record_count: int,
        duplicate_ids: list[str],
        missing_fields: list[dict[str, Any]],
        stale: bool,
        reviewable_ratio: float,
        missing_topics: list[str],
    ) -> str:
        if record_count == 0 or duplicate_ids or missing_fields:
            return "fail"
        if stale or reviewable_ratio < 0.85 or missing_topics:
            return "warn"
        return "pass"

    def _score(
        self,
        status: str,
        duplicate_ids: list[str],
        missing_fields: list[dict[str, Any]],
        stale: bool,
        reviewable_ratio: float,
        missing_topics: list[str],
    ) -> int:
        score = 100
        score -= min(30, len(duplicate_ids) * 10)
        score -= min(30, len(missing_fields) * 6)
        if stale:
            score -= 15
        score -= int(max(0, 0.95 - reviewable_ratio) * 40)
        score -= min(20, len(missing_topics) * 3)
        if status == "fail":
            score = min(score, 60)
        return max(0, min(100, score))

    def _recommended_actions(
        self,
        status: str,
        stale: bool,
        missing_fields: list[dict[str, Any]],
        duplicate_ids: list[str],
        missing_topics: list[str],
    ) -> list[str]:
        actions: list[str] = []
        if duplicate_ids:
            actions.append(f"Deduplicate source IDs: {', '.join(duplicate_ids)}.")
        if missing_fields:
            actions.append("Fill required metadata fields before seeding the legal knowledge database.")
        if stale:
            actions.append("Refresh the legal knowledge seed and verify official source links.")
        if missing_topics:
            actions.append(f"Add coverage for critical contract topics: {', '.join(missing_topics)}.")
        if not actions and status == "pass":
            actions.append("Seed file is ready for routine database refresh.")
        return actions


def _text(value: Any) -> str:
    return str(value or "").strip()


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value
    return False


def _parse_date(value: Any) -> date | None:
    text = _text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None
