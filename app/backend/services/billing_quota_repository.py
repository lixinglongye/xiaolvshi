from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Iterable

from models.billing_quota_idempotency_keys import BillingQuotaIdempotencyKey
from models.billing_quota_usage_counters import BillingQuotaUsageCounter
from services.billing_quota_persistence_plan import BillingQuotaPersistencePlanService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


SOURCE_HASH_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "quota_subject_hash",
    "plan_type",
    "action",
    "usage_metric",
    "units",
    "request_units",
    "quota_window",
    "counter_bucket",
    "allowed",
    "decision_status",
    "limit",
    "used_before",
    "remaining_before",
    "remaining_after",
    "over_limit_reason_codes",
    "over_limit_reasons",
    "policy_version",
    "entitlement_snapshot_id",
)


class BillingQuotaRepository:
    def __init__(self, validator: BillingQuotaPersistencePlanService | None = None) -> None:
        self.validator = validator or BillingQuotaPersistencePlanService()

    async def record_usage_event(self, db: AsyncSession, event: dict[str, Any]) -> dict[str, Any]:
        sanitized = self._validated_event(event)
        source_event_hash = self._source_event_hash(sanitized)

        existing_key = await self._get_idempotency_key(db, sanitized["idempotency_key"])
        if existing_key is not None:
            if existing_key.source_event_hash != source_event_hash:
                await db.rollback()
                raise ValueError("billing_quota_idempotency_conflict")
            existing_key.seen_count += 1
            existing_key.last_seen_at = self._utcnow()
            await db.commit()
            existing_row = await self._get_usage_by_idempotency_key(db, sanitized["idempotency_key"])
            if existing_row is None:
                raise ValueError("billing_quota_idempotency_ledger_missing_counter")
            return self._event_to_api(existing_row, recorded=False, idempotent_replay=True)

        existing_source_event = await self._get_usage_by_source_event_hash(db, source_event_hash)
        if existing_source_event is not None:
            raise ValueError("billing_quota_source_event_duplicate")

        row = BillingQuotaUsageCounter(
            idempotency_key=sanitized["idempotency_key"],
            source_event_hash=source_event_hash,
            quota_subject_hash=sanitized["quota_subject_hash"],
            quota_window=sanitized["quota_window"],
            usage_metric=sanitized["usage_metric"],
            units=sanitized["units"],
            limit_value=self._number_or_none(sanitized.get("limit")),
            used_value=self._used_value(sanitized),
            remaining_value=self._remaining_value(sanitized),
            decision_status=str(sanitized["decision_status"]),
            reason_codes_json=json.dumps(self._reason_codes(sanitized), separators=(",", ":")),
        )
        ledger = BillingQuotaIdempotencyKey(
            idempotency_key=sanitized["idempotency_key"],
            source_event_hash=source_event_hash,
            quota_subject_hash=sanitized["quota_subject_hash"],
            quota_window=sanitized["quota_window"],
            usage_metric=sanitized["usage_metric"],
        )

        db.add(row)
        db.add(ledger)
        await db.commit()
        await db.refresh(row)
        return self._event_to_api(row, recorded=True, idempotent_replay=False)

    async def get_usage_snapshot(
        self,
        db: AsyncSession,
        quota_subject_hash: str,
        usage_metric: str,
        quota_window: str,
    ) -> dict[str, Any]:
        rows = await self._list_usage_rows(
            db,
            quota_subject_hash=quota_subject_hash,
            usage_metric=usage_metric,
            quota_window=quota_window,
        )
        if not rows:
            return {
                "quota_subject_hash": quota_subject_hash,
                "usage_metric": usage_metric,
                "quota_window": quota_window,
                "units": 0,
                "event_count": 0,
                "limit": None,
                "used": 0,
                "remaining": None,
                "decision_status": None,
                "reason_codes": [],
            }

        latest = rows[-1]
        limit_value = self._latest_number(rows, "limit_value")
        used_value = self._latest_number(rows, "used_value")
        remaining_value = self._latest_number(rows, "remaining_value")
        if used_value is None:
            used_value = sum(row.units for row in rows)
        if remaining_value is None and limit_value is not None:
            remaining_value = max(limit_value - used_value, 0)

        return {
            "quota_subject_hash": quota_subject_hash,
            "usage_metric": usage_metric,
            "quota_window": quota_window,
            "units": sum(row.units for row in rows),
            "event_count": len(rows),
            "limit": limit_value,
            "used": used_value,
            "remaining": remaining_value,
            "decision_status": latest.decision_status,
            "reason_codes": self._merged_reason_codes(rows),
        }

    async def list_events(self, db: AsyncSession, quota_subject_hash: str) -> list[dict[str, Any]]:
        result = await db.execute(
            select(BillingQuotaUsageCounter)
            .where(BillingQuotaUsageCounter.quota_subject_hash == quota_subject_hash)
            .order_by(BillingQuotaUsageCounter.id.asc())
        )
        return [self._event_to_api(row, recorded=True, idempotent_replay=False) for row in result.scalars().all()]

    async def _get_idempotency_key(
        self,
        db: AsyncSession,
        idempotency_key: str,
    ) -> BillingQuotaIdempotencyKey | None:
        result = await db.execute(
            select(BillingQuotaIdempotencyKey).where(BillingQuotaIdempotencyKey.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def _get_usage_by_idempotency_key(
        self,
        db: AsyncSession,
        idempotency_key: str,
    ) -> BillingQuotaUsageCounter | None:
        result = await db.execute(
            select(BillingQuotaUsageCounter).where(BillingQuotaUsageCounter.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()

    async def _get_usage_by_source_event_hash(
        self,
        db: AsyncSession,
        source_event_hash: str,
    ) -> BillingQuotaUsageCounter | None:
        result = await db.execute(
            select(BillingQuotaUsageCounter).where(BillingQuotaUsageCounter.source_event_hash == source_event_hash)
        )
        return result.scalar_one_or_none()

    async def _list_usage_rows(
        self,
        db: AsyncSession,
        *,
        quota_subject_hash: str,
        usage_metric: str,
        quota_window: str,
    ) -> list[BillingQuotaUsageCounter]:
        result = await db.execute(
            select(BillingQuotaUsageCounter)
            .where(
                BillingQuotaUsageCounter.quota_subject_hash == quota_subject_hash,
                BillingQuotaUsageCounter.usage_metric == usage_metric,
                BillingQuotaUsageCounter.quota_window == quota_window,
            )
            .order_by(BillingQuotaUsageCounter.id.asc())
        )
        return list(result.scalars().all())

    def _validated_event(self, event: dict[str, Any]) -> dict[str, Any]:
        checks = self.validator.validate_sample_events([event])
        check = checks[0] if checks else {"allowed_to_persist": False, "failures": ["validation_unavailable"]}
        if not check.get("allowed_to_persist"):
            failures = ",".join(check.get("failures") or ["validation_failed"])
            raise ValueError(f"billing_quota_event_validation_failed:{failures}")
        return dict(event)

    def _source_event_hash(self, event: dict[str, Any]) -> str:
        payload = {
            field: self._json_safe(event[field])
            for field in SOURCE_HASH_FIELDS
            if field in event
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _event_to_api(
        self,
        row: BillingQuotaUsageCounter,
        *,
        recorded: bool,
        idempotent_replay: bool,
    ) -> dict[str, Any]:
        return {
            "id": row.id,
            "idempotency_key": row.idempotency_key,
            "quota_subject_hash": row.quota_subject_hash,
            "quota_window": row.quota_window,
            "usage_metric": row.usage_metric,
            "units": row.units,
            "limit": row.limit_value,
            "used": row.used_value,
            "remaining": row.remaining_value,
            "decision_status": row.decision_status,
            "reason_codes": self._loads_reason_codes(row.reason_codes_json),
            "recorded": recorded,
            "idempotent_replay": idempotent_replay,
        }

    def _used_value(self, event: dict[str, Any]) -> float | None:
        limit_value = self._number_or_none(event.get("limit"))
        remaining_value = self._remaining_value(event)
        if limit_value is not None and remaining_value is not None:
            return max(limit_value - remaining_value, 0)

        used_before = self._number_or_none(event.get("used_before"))
        if used_before is None:
            return None
        if event.get("allowed") is False:
            return used_before
        return used_before + int(event["units"])

    def _remaining_value(self, event: dict[str, Any]) -> float | None:
        remaining_after = self._number_or_none(event.get("remaining_after"))
        if remaining_after is not None:
            return remaining_after
        return self._number_or_none(event.get("remaining_before"))

    def _number_or_none(self, value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _reason_codes(self, event: dict[str, Any]) -> list[str]:
        codes = set(self._iter_codes(event.get("over_limit_reason_codes")))
        for item in event.get("over_limit_reasons") or []:
            if isinstance(item, dict):
                codes.update(self._iter_codes(item.get("code")))
        return sorted(codes)

    def _iter_codes(self, value: Any) -> Iterable[str]:
        if value is None:
            return ()
        if isinstance(value, str):
            raw_values: Iterable[Any] = (value,)
        else:
            try:
                raw_values = tuple(value)
            except TypeError:
                raw_values = (value,)
        return tuple(str(code).strip().lower() for code in raw_values if str(code).strip())

    def _loads_reason_codes(self, value: str | None) -> list[str]:
        if not value:
            return []
        loaded = json.loads(value)
        if not isinstance(loaded, list):
            return []
        return [str(code) for code in loaded]

    def _merged_reason_codes(self, rows: list[BillingQuotaUsageCounter]) -> list[str]:
        codes: set[str] = set()
        for row in rows:
            codes.update(self._loads_reason_codes(row.reason_codes_json))
        return sorted(codes)

    def _latest_number(self, rows: list[BillingQuotaUsageCounter], field: str) -> float | None:
        for row in reversed(rows):
            value = getattr(row, field)
            if value is not None:
                return float(value)
        return None

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(key): self._json_safe(value[key]) for key in sorted(value)}
        if isinstance(value, (list, tuple)):
            return [self._json_safe(item) for item in value]
        if isinstance(value, set):
            return [self._json_safe(item) for item in sorted(value)]
        return value

    def _utcnow(self) -> datetime:
        return datetime.now(timezone.utc)


repository = BillingQuotaRepository()


async def record_usage_event(db: AsyncSession, event: dict[str, Any]) -> dict[str, Any]:
    return await repository.record_usage_event(db, event)


async def get_usage_snapshot(
    db: AsyncSession,
    quota_subject_hash: str,
    usage_metric: str,
    quota_window: str,
) -> dict[str, Any]:
    return await repository.get_usage_snapshot(db, quota_subject_hash, usage_metric, quota_window)


async def list_events(db: AsyncSession, quota_subject_hash: str) -> list[dict[str, Any]]:
    return await repository.list_events(db, quota_subject_hash)
