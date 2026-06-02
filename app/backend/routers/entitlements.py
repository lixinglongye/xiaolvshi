import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.entitlements import EntitlementService
from services.orders import OrdersService
from services.product_catalog import get_sku, plan_from_sku
from services.review_reports import Review_reportsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entitlements", tags=["entitlements"])


class DemoActivationRequest(BaseModel):
    sku: str
    related_review_id: Optional[int] = None


@router.get("/me")
async def get_my_entitlements(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await EntitlementService(db).get_entitlement_summary(
        user_id=str(current_user.id),
        user_role=current_user.role,
    )


@router.post("/demo-activate")
async def activate_demo_entitlement(
    data: DemoActivationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Local/demo fallback used only when Stripe is unavailable."""
    if os.environ.get("STRIPE_SECRET_KEY") and os.environ.get("ALLOW_DEMO_PAYMENT") != "true":
        raise HTTPException(status_code=403, detail="Demo activation is disabled when Stripe is configured.")

    sku_info = get_sku(data.sku)
    if not sku_info:
        raise HTTPException(status_code=400, detail=f"Unknown sku: {data.sku}")

    order = await OrdersService(db).create(
        {
            "sku": data.sku,
            "amount": sku_info["amount"],
            "currency": sku_info["currency"],
            "status": "paid",
            "related_review_id": data.related_review_id,
            "plan_type": sku_info.get("plan_type") or data.sku,
            "stripe_session_id": f"demo_{current_user.id}",
        },
        user_id=str(current_user.id),
    )

    if data.sku == "report_unlock" and data.related_review_id:
        await Review_reportsService(db).update(
            data.related_review_id,
            {"is_paid": True},
            user_id=str(current_user.id),
        )

    plan_type = plan_from_sku(data.sku)
    subscription = None
    if plan_type:
        subscription = await EntitlementService(db).upsert_subscription(
            user_id=str(current_user.id),
            plan_type=plan_type,
            status="active",
        )

    return {
        "status": "paid",
        "order_id": order.id,
        "plan_type": subscription.plan_type if subscription else None,
    }
