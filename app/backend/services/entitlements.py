import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.subscriptions import Subscriptions
from services.product_catalog import PLAN_LIMITS, plan_from_sku


class EntitlementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_subscription(self, user_id: str) -> Optional[Subscriptions]:
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
        subscription = self._build_subscription(user_id=user_id, plan_type=plan_type, status="active")
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def upsert_subscription(
        self,
        *,
        user_id: str,
        plan_type: str,
        status: str = "active",
    ) -> Subscriptions:
        if plan_type not in PLAN_LIMITS:
            raise HTTPException(status_code=400, detail=f"Unknown plan_type: {plan_type}")

        subscription = await self.get_latest_subscription(user_id)
        limits = PLAN_LIMITS[plan_type]
        now = datetime.now()
        if not subscription:
            subscription = self._build_subscription(user_id=user_id, plan_type=plan_type, status=status)
            self.db.add(subscription)
        else:
            subscription.plan_type = plan_type
            subscription.status = status
            subscription.report_quota_monthly = limits["report_quota_monthly"]
            subscription.team_seats = limits["team_seats"]
            subscription.features_json = json.dumps(limits["features"], ensure_ascii=False)
            subscription.current_period_start = subscription.current_period_start or now
            subscription.current_period_end = subscription.current_period_end or now + timedelta(days=30)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def get_entitlement_summary(self, user_id: str, user_role: str = "user") -> Dict[str, Any]:
        subscription = await self.get_or_create_subscription(user_id=user_id, user_role=user_role)
        if user_role == "admin" and subscription.plan_type != "admin":
            limits = PLAN_LIMITS["admin"]
        else:
            limits = PLAN_LIMITS.get(subscription.plan_type, PLAN_LIMITS["free"])

        quota = subscription.report_quota_monthly or limits["report_quota_monthly"]
        used = subscription.reports_used_month or 0
        remaining = max(0, quota - used) if quota < 999999 else 999999
        features = self._parse_features(subscription.features_json) or limits["features"]
        return {
            "subscription_id": subscription.id,
            "plan_type": "admin" if user_role == "admin" else subscription.plan_type,
            "status": subscription.status or "active",
            "report_quota_monthly": quota,
            "reports_used_month": used,
            "reports_remaining": remaining,
            "team_seats": subscription.team_seats or limits["team_seats"],
            "features": features,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "is_admin": user_role == "admin",
            "can_create_report": (subscription.status or "active") == "active" and remaining > 0,
        }

    async def assert_can_create_report(self, user_id: str, user_role: str = "user") -> None:
        summary = await self.get_entitlement_summary(user_id=user_id, user_role=user_role)
        if summary["is_admin"]:
            return
        if summary["status"] != "active":
            raise HTTPException(status_code=402, detail="当前订阅未激活，无法生成新的深度审查报告。")
        if summary["reports_remaining"] <= 0:
            raise HTTPException(status_code=402, detail="本月报告额度已用完，请升级订阅或联系管理员。")

    async def consume_report(self, user_id: str, user_role: str = "user") -> None:
        if user_role == "admin":
            return
        subscription = await self.get_or_create_subscription(user_id=user_id, user_role=user_role)
        await self._reset_period_if_needed(subscription)
        subscription.reports_used_month = (subscription.reports_used_month or 0) + 1
        await self.db.commit()

    def _build_subscription(self, *, user_id: str, plan_type: str, status: str) -> Subscriptions:
        limits = PLAN_LIMITS.get(plan_type, PLAN_LIMITS["free"])
        now = datetime.now()
        return Subscriptions(
            user_id=user_id,
            plan_type=plan_type,
            status=status,
            report_quota_monthly=limits["report_quota_monthly"],
            reports_used_month=0,
            team_seats=limits["team_seats"],
            features_json=json.dumps(limits["features"], ensure_ascii=False),
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )

    async def _reset_period_if_needed(self, subscription: Subscriptions) -> None:
        now = datetime.now()
        if subscription.current_period_end and subscription.current_period_end > now:
            return
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=30)
        subscription.reports_used_month = 0
        await self.db.commit()
        await self.db.refresh(subscription)

    @staticmethod
    def _parse_features(raw: Optional[str]) -> list[str]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
