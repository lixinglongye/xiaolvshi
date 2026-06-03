from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from models.subscriptions import Subscriptions
from services.billing_quota_repository import BillingQuotaRepository
from services.product_catalog import PLAN_LIMITS
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from services.entitlements import EntitlementService
except ModuleNotFoundError as exc:
    if exc.name != "fastapi":
        raise
    EntitlementService = None


ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
DEFAULT_ACTION = "review"
DEFAULT_USAGE_METRIC = "review_credits"
COUNTER_BUCKET = "subject_metric_monthly"
POLICY_VERSION = "billing-entitlement-quota-binding-v1"
SOURCE_COMPONENT = "billing_entitlement_quota_binding"
UNLIMITED_QUOTA_THRESHOLD = 999999
QUOTA_SUBJECT_HASH_PATTERN = re.compile(r"^qsh_[A-Za-z0-9_-]{16,128}$")

PLAN_ALIASES = {
    "pro": "personal",
    "professional": "personal",
    "personal_plan": "personal",
    "lawyer_plan": "lawyer",
    "enterprise_plan": "enterprise",
}


class BillingEntitlementQuotaBindingService:
    """Facade that binds entitlement plan limits to persisted quota counters."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        quota_repository: BillingQuotaRepository | None = None,
    ) -> None:
        self.db = db
        self.entitlements = EntitlementService(db) if EntitlementService is not None else _LocalEntitlementService(db)
        self.quota_repository = quota_repository or BillingQuotaRepository()

    async def build_entitlement_summary(
        self,
        *,
        user_id: str,
        quota_subject_hash: str,
        user_role: str = "user",
        quota_window: str | None = None,
        requested_units: int = 1,
        last_usage_event: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        decision = await self._load_decision(
            user_id=user_id,
            quota_subject_hash=quota_subject_hash,
            user_role=user_role,
            quota_window=quota_window,
            requested_units=requested_units,
        )
        return self._summary_payload(decision, last_usage_event=last_usage_event)

    async def consume_report_usage(
        self,
        *,
        user_id: str,
        quota_subject_hash: str,
        source: str,
        event_id: str,
        units: int = 1,
        user_role: str = "user",
        quota_window: str | None = None,
        occurred_at: datetime | str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(units, int) or isinstance(units, bool) or units <= 0:
            raise ValueError("billing_entitlement_quota_units_must_be_positive")

        decision = await self._load_decision(
            user_id=user_id,
            quota_subject_hash=quota_subject_hash,
            user_role=user_role,
            quota_window=quota_window,
            requested_units=units,
        )
        event_token = self._event_token(source, event_id)
        existing_event = await self.quota_repository._get_usage_by_idempotency_key(
            self.db,
            self._idempotency_key(decision, event_token),
        )
        if existing_event is not None and existing_event.units == units:
            decision = self._decision_from_existing_event(decision, existing_event)
        event = self._usage_event(
            decision=decision,
            source=source,
            source_event_id=event_id,
            units=units,
            occurred_at=occurred_at,
        )
        recorded = await self.quota_repository.record_usage_event(self.db, event)

        return await self.build_entitlement_summary(
            user_id=user_id,
            quota_subject_hash=quota_subject_hash,
            user_role=user_role,
            quota_window=decision["quota_window"],
            requested_units=units,
            last_usage_event=self._event_result(recorded),
        )

    async def record_report_usage(self, **kwargs: Any) -> dict[str, Any]:
        return await self.consume_report_usage(**kwargs)

    async def _load_decision(
        self,
        *,
        user_id: str,
        quota_subject_hash: str,
        user_role: str,
        quota_window: str | None,
        requested_units: int,
    ) -> dict[str, Any]:
        self._assert_quota_subject_hash(quota_subject_hash)
        resolved_window = quota_window or current_quota_window()
        subscription = await self.entitlements.get_or_create_subscription(user_id=user_id, user_role=user_role)
        raw_plan = str(subscription.plan_type or "free").strip().lower()
        effective_plan = "admin" if user_role == "admin" else PLAN_ALIASES.get(raw_plan, raw_plan)
        limits = PLAN_LIMITS.get(effective_plan)
        status = str(subscription.status or "active").strip().lower()
        snapshot = await self.quota_repository.get_usage_snapshot(
            self.db,
            quota_subject_hash,
            DEFAULT_USAGE_METRIC,
            resolved_window,
        )
        persisted_usage = self._number_or_zero(snapshot.get("used"))
        limit = self._resolve_report_limit(subscription.report_quota_monthly, limits)
        remaining = self._remaining(limit=limit, used=persisted_usage)
        reason_codes = self._reason_codes(
            plan_known=limits is not None,
            status=status,
            limit=limit,
            remaining=remaining,
            requested_units=requested_units,
        )
        can_create_report = not reason_codes

        return {
            "quota_subject_hash": quota_subject_hash,
            "quota_window": resolved_window,
            "plan_type": raw_plan,
            "effective_plan_type": effective_plan,
            "plan_known": limits is not None,
            "subscription_status": status,
            "limit": limit,
            "persisted_usage": persisted_usage,
            "remaining": remaining,
            "requested_units": requested_units,
            "can_create_report": can_create_report,
            "decision_status": "ready" if can_create_report else "blocked",
            "reason_codes": reason_codes,
            "usage_snapshot": snapshot,
        }

    def _summary_payload(
        self,
        decision: dict[str, Any],
        *,
        last_usage_event: dict[str, Any] | None,
    ) -> dict[str, Any]:
        persisted_usage = self._api_number(decision["persisted_usage"])
        limit = self._api_number(decision["limit"])
        remaining = self._api_number(decision["remaining"])
        snapshot = decision["usage_snapshot"]

        return {
            "scope": "billing-entitlement-quota-binding",
            "quota_subject_hash": decision["quota_subject_hash"],
            "quota_window": decision["quota_window"],
            "action": DEFAULT_ACTION,
            "usage_metric": DEFAULT_USAGE_METRIC,
            "plan_type": decision["plan_type"],
            "effective_plan_type": decision["effective_plan_type"],
            "subscription_status": decision["subscription_status"],
            "limit": limit,
            "report_quota_monthly": limit,
            "persisted_usage": persisted_usage,
            "reports_used_month": persisted_usage,
            "remaining": remaining,
            "reports_remaining": remaining,
            "can_create_report": decision["can_create_report"],
            "decision_status": decision["decision_status"],
            "reason_codes": list(decision["reason_codes"]),
            "usage_snapshot": {
                "event_count": int(snapshot.get("event_count") or 0),
                "units": self._api_number(snapshot.get("units") or 0),
                "used": persisted_usage,
                "remaining": remaining,
            },
            "last_usage_event": last_usage_event,
        }

    def _usage_event(
        self,
        *,
        decision: dict[str, Any],
        source: str,
        source_event_id: str,
        units: int,
        occurred_at: datetime | str | None,
    ) -> dict[str, Any]:
        allowed = bool(decision["can_create_report"])
        event_token = self._event_token(source, source_event_id)
        timestamp = self._timestamp(occurred_at, decision["quota_window"])
        event: dict[str, Any] = {
            "event_id": f"bqb_{event_token}",
            "event_type": "billing_quota_usage_counter",
            "timestamp": timestamp,
            "idempotency_key": self._idempotency_key(decision, event_token),
            "quota_subject_hash": decision["quota_subject_hash"],
            "subject_type": "account",
            "plan_type": decision["effective_plan_type"],
            "subscription_status": decision["subscription_status"],
            "action": DEFAULT_ACTION,
            "usage_metric": DEFAULT_USAGE_METRIC,
            "units": units,
            "request_units": units,
            "quota_window": decision["quota_window"],
            "counter_bucket": COUNTER_BUCKET,
            "allowed": allowed,
            "decision_status": "ready" if allowed else "blocked",
            "used_before": self._api_number(decision["persisted_usage"]),
            "over_limit_reason_codes": list(decision["reason_codes"]),
            "policy_version": POLICY_VERSION,
            "entitlement_snapshot_id": self._entitlement_snapshot_id(decision),
            "source_component": SOURCE_COMPONENT,
        }

        if decision["limit"] is not None and decision["limit"] < UNLIMITED_QUOTA_THRESHOLD:
            event["limit"] = self._api_number(decision["limit"])
        if decision["remaining"] is not None and decision["limit"] is not None and decision["limit"] < UNLIMITED_QUOTA_THRESHOLD:
            remaining_before = float(decision["remaining"])
            event["remaining_before"] = self._api_number(remaining_before)
            event["remaining_after"] = self._api_number(max(remaining_before - units, 0) if allowed else remaining_before)
        if not allowed:
            event["over_limit_reasons"] = self._over_limit_reasons(decision, units, timestamp)
            event["blocked_at"] = timestamp
        return event

    def _over_limit_reasons(self, decision: dict[str, Any], units: int, timestamp: str) -> list[dict[str, Any]]:
        reasons = []
        for code in decision["reason_codes"]:
            reason: dict[str, Any] = {
                "code": code,
                "metric": DEFAULT_USAGE_METRIC,
                "requested": units,
                "quota_window": decision["quota_window"],
                "policy_version": POLICY_VERSION,
                "blocked_at": timestamp,
                "source_component": SOURCE_COMPONENT,
            }
            if decision["limit"] is not None:
                reason["limit"] = self._api_number(decision["limit"])
            if decision["persisted_usage"] is not None:
                reason["used"] = self._api_number(decision["persisted_usage"])
            if decision["remaining"] is not None:
                reason["remaining"] = self._api_number(decision["remaining"])
            reasons.append(reason)
        return reasons

    def _event_result(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "recorded": bool(event["recorded"]),
            "idempotent_replay": bool(event["idempotent_replay"]),
            "decision_status": event["decision_status"],
            "units": self._api_number(event["units"]),
            "used": self._api_number(event["used"]),
            "remaining": self._api_number(event["remaining"]),
            "reason_codes": list(event["reason_codes"]),
        }

    def _decision_from_existing_event(self, decision: dict[str, Any], row: Any) -> dict[str, Any]:
        restored = dict(decision)
        used_after = self._number_or_zero(row.used_value)
        remaining_after = float(row.remaining_value) if self._is_number(row.remaining_value) else None
        limit = float(row.limit_value) if self._is_number(row.limit_value) else None
        allowed = row.decision_status == "ready"

        if allowed:
            used_before = max(used_after - int(row.units), 0)
            remaining_before = remaining_after + int(row.units) if remaining_after is not None else None
        else:
            used_before = used_after
            remaining_before = remaining_after

        restored["limit"] = limit
        restored["persisted_usage"] = used_before
        restored["remaining"] = remaining_before
        restored["requested_units"] = int(row.units)
        restored["can_create_report"] = allowed
        restored["decision_status"] = row.decision_status
        restored["reason_codes"] = self.quota_repository._loads_reason_codes(row.reason_codes_json)
        return restored

    def _reason_codes(
        self,
        *,
        plan_known: bool,
        status: str,
        limit: float | None,
        remaining: float | None,
        requested_units: int,
    ) -> list[str]:
        codes: list[str] = []
        if not plan_known:
            codes.append("unknown_plan")
        if status not in ACTIVE_SUBSCRIPTION_STATUSES:
            codes.append("inactive_subscription")
        if plan_known and limit is None:
            codes.append("plan_limit_unavailable")
        if remaining is not None and limit is not None and limit < UNLIMITED_QUOTA_THRESHOLD and remaining < requested_units:
            codes.append("report_quota_exhausted")
        return codes

    def _resolve_report_limit(self, subscription_limit: Any, limits: dict[str, Any] | None) -> float | None:
        if self._is_number(subscription_limit):
            return float(subscription_limit)
        if not limits:
            return None
        catalog_limit = limits.get("report_quota_monthly")
        return float(catalog_limit) if self._is_number(catalog_limit) else None

    def _remaining(self, *, limit: float | None, used: float) -> float | None:
        if limit is None:
            return None
        if limit >= UNLIMITED_QUOTA_THRESHOLD:
            return float(UNLIMITED_QUOTA_THRESHOLD)
        return max(limit - used, 0)

    def _idempotency_key(self, decision: dict[str, Any], event_token: str) -> str:
        return (
            "bqp:v1:"
            f"{decision['quota_subject_hash']}:"
            f"{decision['quota_window']}:"
            f"{DEFAULT_ACTION}:"
            f"{DEFAULT_USAGE_METRIC}:"
            f"{event_token}"
        )

    def _entitlement_snapshot_id(self, decision: dict[str, Any]) -> str:
        payload = "|".join(
            [
                decision["quota_subject_hash"],
                decision["quota_window"],
                decision["effective_plan_type"],
                str(decision["limit"]),
                str(decision["persisted_usage"]),
                decision["decision_status"],
            ]
        )
        return f"ent_snap_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"

    def _event_token(self, source: str, source_event_id: str) -> str:
        if not str(source).strip() or not str(source_event_id).strip():
            raise ValueError("billing_entitlement_quota_source_event_required")
        digest = hashlib.sha256(f"{source}|{source_event_id}".encode("utf-8")).hexdigest()
        return f"src_{digest[:24]}"

    def _timestamp(self, occurred_at: datetime | str | None, quota_window: str) -> str:
        if isinstance(occurred_at, datetime):
            value = occurred_at
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if isinstance(occurred_at, str) and occurred_at.strip():
            return occurred_at.strip()
        return f"{quota_window}-01T00:00:00Z"

    def _assert_quota_subject_hash(self, quota_subject_hash: str) -> None:
        if not isinstance(quota_subject_hash, str) or not QUOTA_SUBJECT_HASH_PATTERN.match(quota_subject_hash):
            raise ValueError("billing_entitlement_quota_subject_hash_required")

    def _number_or_zero(self, value: Any) -> float:
        if self._is_number(value):
            return max(float(value), 0)
        return 0.0

    def _api_number(self, value: Any) -> int | float | None:
        if value is None:
            return None
        if self._is_number(value):
            number = float(value)
            return int(number) if number.is_integer() else number
        return None

    def _is_number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)


def current_quota_window(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return f"{value.year:04d}-{value.month:02d}"


def build_quota_subject_hash(raw_subject: str, *, namespace: str = "billing-entitlement") -> str:
    if not str(raw_subject).strip():
        raise ValueError("billing_entitlement_quota_raw_subject_required")
    digest = hashlib.sha256(f"{namespace}|{raw_subject}".encode("utf-8")).hexdigest()
    return f"qsh_{digest[:32]}"


class _LocalEntitlementService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_latest_subscription(self, user_id: str) -> Subscriptions | None:
        result = await self.db.execute(
            select(Subscriptions)
            .where(Subscriptions.user_id == user_id)
            .order_by(Subscriptions.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_or_create_subscription(self, user_id: str, user_role: str = "user") -> Subscriptions:
        subscription = await self.get_latest_subscription(user_id)
        if subscription:
            await self._reset_period_if_needed(subscription)
            return subscription

        plan_type = "admin" if user_role == "admin" else "free"
        limits = PLAN_LIMITS.get(plan_type, PLAN_LIMITS["free"])
        now = datetime.now()
        subscription = Subscriptions(
            user_id=user_id,
            plan_type=plan_type,
            status="active",
            report_quota_monthly=limits["report_quota_monthly"],
            reports_used_month=0,
            team_seats=limits["team_seats"],
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def _reset_period_if_needed(self, subscription: Subscriptions) -> None:
        now = datetime.now()
        if subscription.current_period_end and subscription.current_period_end > now:
            return
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=30)
        subscription.reports_used_month = 0
        await self.db.commit()
        await self.db.refresh(subscription)


async def build_entitlement_summary(
    db: AsyncSession,
    *,
    user_id: str,
    quota_subject_hash: str,
    user_role: str = "user",
    quota_window: str | None = None,
) -> dict[str, Any]:
    return await BillingEntitlementQuotaBindingService(db).build_entitlement_summary(
        user_id=user_id,
        quota_subject_hash=quota_subject_hash,
        user_role=user_role,
        quota_window=quota_window,
    )


async def consume_report_usage(
    db: AsyncSession,
    *,
    user_id: str,
    quota_subject_hash: str,
    source: str,
    event_id: str,
    units: int = 1,
    user_role: str = "user",
    quota_window: str | None = None,
    occurred_at: datetime | str | None = None,
) -> dict[str, Any]:
    return await BillingEntitlementQuotaBindingService(db).consume_report_usage(
        user_id=user_id,
        quota_subject_hash=quota_subject_hash,
        source=source,
        event_id=event_id,
        units=units,
        user_role=user_role,
        quota_window=quota_window,
        occurred_at=occurred_at,
    )
