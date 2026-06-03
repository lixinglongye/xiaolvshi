from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.billing_entitlement_quota_binding import (
    BillingEntitlementQuotaBindingService,
    build_quota_subject_hash,
)


router = APIRouter(prefix="/api/v1/billing-usage", tags=["billing-usage"])


class ConsumeReportUsageRequest(BaseModel):
    source: str
    event_id: str
    units: int = 1
    quota_window: Optional[str] = None
    quota_subject_hash: Optional[str] = None


def _quota_subject_hash(current_user: UserResponse, quota_subject_hash: str | None) -> str:
    if quota_subject_hash:
        return quota_subject_hash
    return build_quota_subject_hash(str(current_user.id))


@router.get("/me")
async def get_my_billing_usage(
    quota_subject_hash: str | None = None,
    quota_window: str | None = None,
    requested_units: int = 1,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        summary = await BillingEntitlementQuotaBindingService(db).build_entitlement_summary(
            user_id=str(current_user.id),
            user_role=current_user.role,
            quota_subject_hash=_quota_subject_hash(current_user, quota_subject_hash),
            quota_window=quota_window,
            requested_units=requested_units,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "data": summary}


@router.post("/consume-report")
async def consume_report_usage(
    data: ConsumeReportUsageRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        summary = await BillingEntitlementQuotaBindingService(db).consume_report_usage(
            user_id=str(current_user.id),
            user_role=current_user.role,
            quota_subject_hash=_quota_subject_hash(current_user, data.quota_subject_hash),
            source=data.source,
            event_id=data.event_id,
            units=data.units,
            quota_window=data.quota_window,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "data": summary}
