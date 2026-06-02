# @File: backend/routers/payments.py
# @Desc: Stripe payment integration for report unlock and subscription plans
import logging
import os
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse
from services.entitlements import EntitlementService
from services.orders import OrdersService
from services.product_catalog import get_sku, plan_from_sku, public_product_catalog
from services.review_reports import Review_reportsService

logger = logging.getLogger(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

router = APIRouter(prefix="/api/v1/payment", tags=["payment"])


class CheckoutSessionRequest(BaseModel):
    sku: str
    related_review_id: Optional[int] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str
    order_id: int


class PaymentVerificationRequest(BaseModel):
    session_id: str


class PaymentStatusResponse(BaseModel):
    status: str
    order_id: Optional[int] = None
    payment_status: str
    related_review_id: Optional[int] = None


@router.get("/catalog")
async def get_payment_catalog(locale: str = "zh"):
    """Return the single public product catalog used by frontend pricing and payments."""
    return {"items": public_product_catalog(locale)}


@router.post("/create_payment_session", response_model=CheckoutSessionResponse)
async def create_payment_session(
    data: CheckoutSessionRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe checkout session for a SKU."""
    try:
        sku_info = get_sku(data.sku)
        if not sku_info:
            raise HTTPException(status_code=400, detail=f"Unknown sku: {data.sku}")

        frontend_host = request.headers.get("App-Host")
        if frontend_host and not frontend_host.startswith(("http://", "https://")):
            frontend_host = f"https://{frontend_host}"
        if not frontend_host:
            frontend_host = data.success_url or "http://localhost:5173"

        orders_service = OrdersService(db)
        order = await orders_service.create(
            {
                "sku": data.sku,
                "amount": sku_info["amount"],
                "currency": sku_info["currency"],
                "status": "pending",
                "related_review_id": data.related_review_id,
                "plan_type": sku_info.get("plan_type") or data.sku,
            },
            user_id=current_user.id,
        )

        line_items = [
            {
                "price_data": {
                    "currency": sku_info["currency"],
                    "product_data": {"name": sku_info["name"]},
                    "unit_amount": sku_info["amount"],
                },
                "quantity": 1,
            }
        ]

        success_url = (
            f"{frontend_host}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
            f"&order_id={order.id}&sku={data.sku}"
        )
        if data.related_review_id:
            success_url += f"&review_id={data.related_review_id}"
        cancel_url = f"{frontend_host}/pricing"

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "order_id": str(order.id),
                "user_id": current_user.id,
                "sku": data.sku,
                "review_id": str(data.related_review_id or ""),
            },
        )

        await orders_service.update(
            order.id,
            {"stripe_session_id": session.id},
            user_id=current_user.id,
        )

        return CheckoutSessionResponse(session_id=session.id, url=session.url, order_id=order.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment session creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")


@router.post("/verify_payment", response_model=PaymentStatusResponse)
async def verify_payment(
    data: PaymentVerificationRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify Stripe checkout session, mark the order paid, and unlock the related review."""
    try:
        session = stripe.checkout.Session.retrieve(data.session_id)
        order_id = session.metadata.get("order_id")
        review_id = session.metadata.get("review_id")
        sku = session.metadata.get("sku")

        status_mapping = {"complete": "paid", "open": "pending", "expired": "cancelled"}
        status = status_mapping.get(session.status, "pending")

        if order_id:
            orders_service = OrdersService(db)
            await orders_service.update(int(order_id), {"status": status}, user_id=current_user.id)

        if status == "paid" and review_id and sku == "report_unlock":
            try:
                reports_service = Review_reportsService(db)
                await reports_service.update(int(review_id), {"is_paid": True}, user_id=current_user.id)
            except Exception as exc:
                logger.warning(f"unlock report failed: {exc}")

        plan_type = plan_from_sku(sku)
        if status == "paid" and plan_type:
            await EntitlementService(db).upsert_subscription(
                user_id=str(current_user.id),
                plan_type=plan_type,
                status="active",
            )

        return PaymentStatusResponse(
            status=status,
            order_id=int(order_id) if order_id else None,
            payment_status=session.payment_status,
            related_review_id=int(review_id) if review_id else None,
        )
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify payment: {str(e)}")
