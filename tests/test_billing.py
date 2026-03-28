"""Tests for Stripe billing endpoints — checkout, portal, webhook, and usage."""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from api.db.models import User
from api.dependencies import get_current_user
from api.main import app
from api.v1.auth import _hash_password


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_user() -> User:
    """User on the free plan with no Stripe customer."""
    return User(
        id=uuid.uuid4(),
        email="billing@example.com",
        hashed_password=_hash_password("pw"),
        plan="free",
        episodes_this_month=2,
        stripe_customer_id=None,
    )


@pytest.fixture
def paid_user() -> User:
    """User on the creator plan with an existing Stripe customer ID."""
    return User(
        id=uuid.uuid4(),
        email="paid@example.com",
        hashed_password=_hash_password("pw"),
        plan="creator",
        episodes_this_month=3,
        stripe_customer_id="cus_existing123",
    )


@pytest.fixture
def authed_client(client: AsyncClient, fake_user: User):
    """AsyncClient authenticated as fake_user (free plan)."""
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def paid_client(client: AsyncClient, paid_user: User):
    """AsyncClient authenticated as paid_user (creator plan with customer ID)."""
    app.dependency_overrides[get_current_user] = lambda: paid_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# GET /v1/billing/usage
# ---------------------------------------------------------------------------


async def test_usage_returns_correct_plan_and_count(
    authed_client: AsyncClient, fake_user: User
) -> None:
    """GET /v1/billing/usage returns the user's current plan and episode count."""
    response = await authed_client.get("/v1/billing/usage")
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "free"
    assert data["episodes_this_month"] == 2
    assert data["limit"] == 1  # free plan limit


async def test_usage_creator_plan_has_correct_limit(
    paid_client: AsyncClient, paid_user: User
) -> None:
    """GET /v1/billing/usage returns limit=15 for creator plan."""
    response = await paid_client.get("/v1/billing/usage")
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "creator"
    assert data["limit"] == 15


async def test_usage_studio_plan_has_no_limit(
    client: AsyncClient, db_session
) -> None:
    """GET /v1/billing/usage returns limit=null for studio plan (unlimited)."""
    studio_user = User(
        id=uuid.uuid4(),
        email="studio@example.com",
        hashed_password=_hash_password("pw"),
        plan="studio",
        episodes_this_month=50,
    )
    app.dependency_overrides[get_current_user] = lambda: studio_user
    response = await client.get("/v1/billing/usage")
    app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 200
    assert response.json()["limit"] is None


# ---------------------------------------------------------------------------
# POST /v1/billing/checkout
# ---------------------------------------------------------------------------


async def test_checkout_creates_stripe_session(
    authed_client: AsyncClient, fake_user: User
) -> None:
    """POST /v1/billing/checkout returns a checkout_url from Stripe."""
    mock_customer = MagicMock()
    mock_customer.id = "cus_new123"

    mock_session = MagicMock()
    mock_session.id = "cs_test_abc"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc"

    with (
        patch("api.v1.billing.stripe.Customer.create", return_value=mock_customer),
        patch(
            "api.v1.billing.stripe.checkout.Session.create",
            return_value=mock_session,
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await authed_client.post(
            "/v1/billing/checkout",
            json={"plan": "starter"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "checkout_url" in data
    assert "checkout.stripe.com" in data["checkout_url"]


async def test_checkout_reuses_existing_customer(
    paid_client: AsyncClient, paid_user: User
) -> None:
    """POST /v1/billing/checkout skips Customer.create when customer already exists."""
    mock_session = MagicMock()
    mock_session.id = "cs_test_reuse"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_reuse"

    with (
        patch("api.v1.billing.stripe.Customer.create") as mock_create,
        patch(
            "api.v1.billing.stripe.checkout.Session.create",
            return_value=mock_session,
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await paid_client.post(
            "/v1/billing/checkout",
            json={"plan": "creator"},
        )

    assert response.status_code == 200
    mock_create.assert_not_called()


async def test_checkout_returns_400_for_unknown_plan(
    authed_client: AsyncClient,
) -> None:
    """POST /v1/billing/checkout returns 400 for an unrecognised plan name."""
    with patch("api.v1.billing.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await authed_client.post(
            "/v1/billing/checkout",
            json={"plan": "enterprise"},
        )

    assert response.status_code == 400


async def test_checkout_returns_400_for_unconfigured_price(
    authed_client: AsyncClient,
) -> None:
    """POST /v1/billing/checkout returns 400 when price ID is empty string."""
    with patch("api.v1.billing.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_PRICE_STARTER = ""  # not configured
        mock_settings.STRIPE_PRICE_CREATOR = ""
        mock_settings.STRIPE_PRICE_STUDIO = ""

        response = await authed_client.post(
            "/v1/billing/checkout",
            json={"plan": "starter"},
        )

    assert response.status_code == 400


async def test_checkout_returns_502_on_stripe_error(
    authed_client: AsyncClient, fake_user: User
) -> None:
    """POST /v1/billing/checkout returns 502 when Stripe raises an error."""
    import stripe as _stripe

    mock_customer = MagicMock()
    mock_customer.id = "cus_err"

    with (
        patch("api.v1.billing.stripe.Customer.create", return_value=mock_customer),
        patch(
            "api.v1.billing.stripe.checkout.Session.create",
            side_effect=_stripe.StripeError("Network error"),
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await authed_client.post(
            "/v1/billing/checkout",
            json={"plan": "starter"},
        )

    assert response.status_code == 502


# ---------------------------------------------------------------------------
# POST /v1/billing/portal
# ---------------------------------------------------------------------------


async def test_portal_returns_portal_url(
    paid_client: AsyncClient, paid_user: User
) -> None:
    """POST /v1/billing/portal returns a portal_url for users with a customer ID."""
    mock_session = MagicMock()
    mock_session.url = "https://billing.stripe.com/p/session_xyz"

    with (
        patch(
            "api.v1.billing.stripe.billing_portal.Session.create",
            return_value=mock_session,
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"

        response = await paid_client.post("/v1/billing/portal")

    assert response.status_code == 200
    data = response.json()
    assert "portal_url" in data
    assert "billing.stripe.com" in data["portal_url"]


async def test_portal_returns_400_without_stripe_customer(
    authed_client: AsyncClient, fake_user: User
) -> None:
    """POST /v1/billing/portal returns 400 when user has no Stripe customer ID."""
    response = await authed_client.post("/v1/billing/portal")
    assert response.status_code == 400


async def test_portal_returns_502_on_stripe_error(
    paid_client: AsyncClient,
) -> None:
    """POST /v1/billing/portal returns 502 when Stripe raises an error."""
    import stripe as _stripe

    with (
        patch(
            "api.v1.billing.stripe.billing_portal.Session.create",
            side_effect=_stripe.StripeError("Connection error"),
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"

        response = await paid_client.post("/v1/billing/portal")

    assert response.status_code == 502


# ---------------------------------------------------------------------------
# POST /v1/billing/webhook
# ---------------------------------------------------------------------------


def _make_webhook_payload(event_type: str, data: dict) -> bytes:
    """Build a minimal Stripe webhook payload."""
    return json.dumps(
        {
            "id": "evt_test_123",
            "type": event_type,
            "data": {"object": data},
        }
    ).encode()


async def test_webhook_rejects_invalid_signature(client: AsyncClient) -> None:
    """POST /v1/billing/webhook returns 400 on signature verification failure."""
    import stripe as _stripe

    with patch(
        "api.v1.billing.stripe.Webhook.construct_event",
        side_effect=_stripe.SignatureVerificationError("bad sig", "sig_header"),
    ):
        response = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "bad"},
        )

    assert response.status_code == 400


async def test_webhook_checkout_completed_updates_user_plan(
    client: AsyncClient, db_session
) -> None:
    """Webhook checkout.session.completed updates user.plan and stripe_customer_id."""
    user = User(
        id=uuid.uuid4(),
        email="webhook@example.com",
        hashed_password=_hash_password("pw"),
        plan="free",
        episodes_this_month=0,
        stripe_customer_id=None,
    )
    db_session.add(user)
    await db_session.commit()

    mock_sub = MagicMock()
    mock_sub.get = lambda key, default=None: {
        "items": {"data": [{"price": {"id": "price_creator123"}}]},
    }.get(key, default)

    event_data = {
        "id": "evt_test_checkout",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_webhook123",
                "subscription": "sub_abc",
                "metadata": {"user_id": str(user.id)},
            }
        },
    }

    with (
        patch(
            "api.v1.billing.stripe.Webhook.construct_event",
            return_value=event_data,
        ),
        patch(
            "api.v1.billing.stripe.Subscription.retrieve",
            return_value=mock_sub,
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=sig"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}

    await db_session.refresh(user)
    assert user.stripe_customer_id == "cus_webhook123"
    assert user.plan == "creator"


async def test_webhook_subscription_deleted_downgrades_to_free(
    client: AsyncClient, db_session
) -> None:
    """Webhook customer.subscription.deleted sets user.plan to free."""
    user = User(
        id=uuid.uuid4(),
        email="cancel@example.com",
        hashed_password=_hash_password("pw"),
        plan="creator",
        episodes_this_month=0,
        stripe_customer_id="cus_cancel456",
    )
    db_session.add(user)
    await db_session.commit()

    event_data = {
        "id": "evt_test_cancel",
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_cancel456"}},
    }

    with (
        patch(
            "api.v1.billing.stripe.Webhook.construct_event",
            return_value=event_data,
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=sig"},
        )

    assert response.status_code == 200
    await db_session.refresh(user)
    assert user.plan == "free"


async def test_webhook_subscription_updated_changes_plan(
    client: AsyncClient, db_session
) -> None:
    """Webhook customer.subscription.updated updates plan from price ID."""
    user = User(
        id=uuid.uuid4(),
        email="upgrade@example.com",
        hashed_password=_hash_password("pw"),
        plan="starter",
        episodes_this_month=0,
        stripe_customer_id="cus_upgrade789",
    )
    db_session.add(user)
    await db_session.commit()

    event_data = {
        "id": "evt_test_update",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "customer": "cus_upgrade789",
                "items": {
                    "data": [{"price": {"id": "price_studio123"}}]
                },
            }
        },
    }

    with (
        patch(
            "api.v1.billing.stripe.Webhook.construct_event",
            return_value=event_data,
        ),
        patch("api.v1.billing.settings") as mock_settings,
    ):
        mock_settings.STRIPE_SECRET_KEY = "sk_test_key"
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_STARTER = "price_starter123"
        mock_settings.STRIPE_PRICE_CREATOR = "price_creator123"
        mock_settings.STRIPE_PRICE_STUDIO = "price_studio123"

        response = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=sig"},
        )

    assert response.status_code == 200
    await db_session.refresh(user)
    assert user.plan == "studio"


async def test_webhook_payment_failed_returns_200(client: AsyncClient) -> None:
    """Webhook invoice.payment_failed is handled gracefully (logs only)."""
    event_data = {
        "id": "evt_test_payment_fail",
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_broke", "amount_due": 4900}},
    }

    with patch(
        "api.v1.billing.stripe.Webhook.construct_event",
        return_value=event_data,
    ):
        response = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=sig"},
        )

    assert response.status_code == 200
    assert response.json() == {"received": True}


async def test_webhook_unknown_event_type_returns_200(client: AsyncClient) -> None:
    """Unknown webhook event types are silently ignored."""
    event_data = {
        "id": "evt_test_unknown",
        "type": "some.unknown.event",
        "data": {"object": {}},
    }

    with patch(
        "api.v1.billing.stripe.Webhook.construct_event",
        return_value=event_data,
    ):
        response = await client.post(
            "/v1/billing/webhook",
            content=b"{}",
            headers={"stripe-signature": "t=1,v1=sig"},
        )

    assert response.status_code == 200
