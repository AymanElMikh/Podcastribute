"""Stripe billing routes — checkout, customer portal, webhook, and usage."""

from datetime import datetime, timedelta, timezone

import stripe
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.db.models import User
from api.db.session import get_db
from api.dependencies import PLAN_LIMITS, get_current_user

log = structlog.get_logger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])



def _get_plan_price_id(plan: str) -> str:
    """Return the Stripe price ID for a given plan name.

    Args:
        plan: Plan name (starter|creator|studio).

    Returns:
        Stripe price ID string.

    Raises:
        HTTPException: 400 if the plan is unknown or unconfigured.
    """
    price_map: dict[str, str] = {
        "starter": settings.STRIPE_PRICE_STARTER,
        "creator": settings.STRIPE_PRICE_CREATOR,
        "studio": settings.STRIPE_PRICE_STUDIO,
    }
    price_id = price_map.get(plan, "")
    if not price_id:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown or unconfigured plan: {plan!r}. Valid plans: starter, creator, studio.",
        )
    return price_id


def _plan_from_price_id(price_id: str) -> str | None:
    """Return the plan name for a Stripe price ID, or None if unrecognised.

    Args:
        price_id: Stripe price ID to look up.

    Returns:
        Plan name string, or None.
    """
    mapping = {
        settings.STRIPE_PRICE_STARTER: "starter",
        settings.STRIPE_PRICE_CREATOR: "creator",
        settings.STRIPE_PRICE_STUDIO: "studio",
    }
    return mapping.get(price_id)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CheckoutRequest(BaseModel):
    """Request body for creating a Stripe Checkout session."""

    plan: str
    success_url: str = "/settings?upgraded=true"
    cancel_url: str = "/settings"


class CheckoutResponse(BaseModel):
    """Response with the Stripe Checkout redirect URL."""

    checkout_url: str


class PortalResponse(BaseModel):
    """Response with the Stripe Customer Portal redirect URL."""

    portal_url: str


class UsageResponse(BaseModel):
    """Current user's episode usage statistics."""

    episodes_this_month: int
    limit: int | None
    plan: str
    reset_at: datetime | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_or_create_stripe_customer(user: User, db: AsyncSession) -> str:
    """Return the user's Stripe customer ID, creating one if necessary.

    Args:
        user: Authenticated User ORM object.
        db: Async database session.

    Returns:
        Stripe customer ID string.
    """
    if user.stripe_customer_id:
        return user.stripe_customer_id

    stripe.api_key = settings.STRIPE_SECRET_KEY
    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    await db.flush()
    log.info("stripe_customer_created", user_id=str(user.id), customer_id=customer.id)
    return customer.id


async def _apply_plan_from_subscription(
    subscription: dict, db: AsyncSession
) -> None:
    """Update the user's plan based on a Stripe subscription object.

    Args:
        subscription: Stripe Subscription object (as dict).
        db: Async database session.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    customer_id: str = subscription.get("customer", "")
    if not customer_id:
        return

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        log.warning("webhook_user_not_found", customer_id=customer_id)
        return

    # Get the price ID from the first subscription item
    items = subscription.get("items", {}).get("data", [])
    price_id = items[0]["price"]["id"] if items else ""
    plan = _plan_from_price_id(price_id) or "free"

    user.plan = plan
    if user.plan_reset_at is None:
        user.plan_reset_at = datetime.now(timezone.utc) + timedelta(days=30)

    await db.flush()
    log.info("plan_updated", user_id=str(user.id), plan=plan, customer_id=customer_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for a subscription plan upgrade.

    Creates (or reuses) a Stripe Customer record, then initiates a Checkout
    session for the requested plan. The user is redirected to Stripe-hosted
    payment page.

    Args:
        body: CheckoutRequest with plan name and redirect URLs.
        db: Async database session.
        current_user: Authenticated user from JWT.

    Returns:
        CheckoutResponse with the Stripe Checkout redirect URL.

    Raises:
        HTTPException: 400 if the plan name is unknown or unconfigured.
        HTTPException: 502 if the Stripe API returns an error.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    price_id = _get_plan_price_id(body.plan)

    try:
        customer_id = await _get_or_create_stripe_customer(current_user, db)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            metadata={"user_id": str(current_user.id)},
        )
    except stripe.StripeError as exc:
        log.error("stripe_checkout_error", error=str(exc), user_id=str(current_user.id))
        raise HTTPException(status_code=502, detail=f"Stripe error: {exc.user_message}")

    log.info(
        "checkout_session_created",
        user_id=str(current_user.id),
        plan=body.plan,
        session_id=session.id,
    )
    return CheckoutResponse(checkout_url=session.url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PortalResponse:
    """Create a Stripe Customer Portal session for subscription management.

    Allows users to update their payment method, view invoices, or cancel.

    Args:
        db: Async database session.
        current_user: Authenticated user from JWT.

    Returns:
        PortalResponse with the Stripe Customer Portal redirect URL.

    Raises:
        HTTPException: 400 if the user has no Stripe customer record.
        HTTPException: 502 if the Stripe API returns an error.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No billing account found. Subscribe to a plan first.",
        )

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url="/settings",
        )
    except stripe.StripeError as exc:
        log.error("stripe_portal_error", error=str(exc), user_id=str(current_user.id))
        raise HTTPException(status_code=502, detail=f"Stripe error: {exc.user_message}")

    log.info("portal_session_created", user_id=str(current_user.id))
    return PortalResponse(portal_url=session.url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle incoming Stripe webhook events.

    Always verifies the webhook signature with stripe.Webhook.construct_event()
    before processing. Handles:

    - ``checkout.session.completed``: links Stripe customer to user, upgrades plan.
    - ``customer.subscription.updated``: updates user plan from subscription.
    - ``customer.subscription.deleted``: downgrades user to free plan.
    - ``invoice.payment_failed``: logs a warning (email notification is future work).

    Args:
        request: Raw FastAPI request (signature is in headers).
        db: Async database session.

    Returns:
        Dict ``{"received": True}`` on success.

    Raises:
        HTTPException: 400 if the signature header is missing or invalid.
    """
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError:
        log.warning("webhook_signature_invalid")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as exc:
        log.error("webhook_parse_error", error=str(exc))
        raise HTTPException(status_code=400, detail="Webhook parse error")

    event_type: str = event["type"]
    data: dict = event["data"]["object"]

    log.info("stripe_webhook_received", event_type=event_type, event_id=event["id"])

    if event_type == "checkout.session.completed":
        customer_id: str = data.get("customer", "")
        user_id_str: str = (data.get("metadata") or {}).get("user_id", "")

        if customer_id and user_id_str:
            try:
                import uuid as _uuid
                uid = _uuid.UUID(user_id_str)
            except ValueError:
                log.warning("webhook_invalid_user_id", user_id=user_id_str)
            else:
                result = await db.execute(select(User).where(User.id == uid))
                user = result.scalar_one_or_none()
                if user is not None:
                    user.stripe_customer_id = customer_id
                    # Retrieve the subscription to get the plan
                    subscription_id = data.get("subscription", "")
                    if subscription_id:
                        sub = stripe.Subscription.retrieve(subscription_id)
                        items = sub.get("items", {}).get("data", [])
                        price_id = items[0]["price"]["id"] if items else ""
                        plan = _plan_from_price_id(price_id) or "free"
                        user.plan = plan
                        if user.plan_reset_at is None:
                            user.plan_reset_at = (
                                datetime.now(timezone.utc) + timedelta(days=30)
                            )
                    await db.flush()
                    log.info(
                        "checkout_completed",
                        user_id=user_id_str,
                        customer_id=customer_id,
                    )

    elif event_type == "customer.subscription.updated":
        await _apply_plan_from_subscription(data, db)

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer", "")
        if customer_id:
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            if user is not None:
                user.plan = "free"
                await db.flush()
                log.info(
                    "subscription_cancelled",
                    user_id=str(user.id),
                    customer_id=customer_id,
                )

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer", "")
        log.warning(
            "payment_failed",
            customer_id=customer_id,
            amount_due=data.get("amount_due"),
        )

    await db.commit()
    return {"received": True}


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UsageResponse:
    """Return the current user's episode usage and plan limits.

    Args:
        db: Async database session.
        current_user: Authenticated user from JWT.

    Returns:
        UsageResponse with episodes_this_month, limit, plan, and reset_at.
    """
    limit = PLAN_LIMITS.get(current_user.plan)
    return UsageResponse(
        episodes_this_month=current_user.episodes_this_month,
        limit=limit,
        plan=current_user.plan,
        reset_at=current_user.plan_reset_at,
    )
