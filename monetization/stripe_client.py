"""
Lixen.AI — Stripe API Client

Wraps stripe-python to handle:
  • Customer creation / lookup
  • Subscription creation, cancellation, upgrade/downgrade
  • Customer Portal session (self-serve billing)
  • Checkout Session (hosted payment page)
  • Webhook signature verification

Environment variables required:
  STRIPE_SECRET_KEY          — sk_live_... or sk_test_...
  STRIPE_WEBHOOK_SECRET      — whsec_...
  STRIPE_SMART_MONTHLY       — price_... for Smart monthly
  STRIPE_SMART_ANNUAL        — price_... for Smart annual
  STRIPE_PRO_MONTHLY         — price_... for Pro monthly
  STRIPE_PRO_ANNUAL          — price_... for Pro annual
  APP_BASE_URL               — e.g. https://app.lixen.ai (for redirect URLs)
"""

import os
import stripe
from dotenv import load_dotenv

from plans import PLANS, Plan, get_plan

load_dotenv()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

# ── Price ID resolution ───────────────────────────────────────────────────

def _price_id(plan_id: str, billing: str) -> str:
    """Return the Stripe Price ID for a plan + billing interval."""
    env_map = {
        ("smart", "monthly"): "STRIPE_SMART_MONTHLY",
        ("smart", "annual"):  "STRIPE_SMART_ANNUAL",
        ("pro",   "monthly"): "STRIPE_PRO_MONTHLY",
        ("pro",   "annual"):  "STRIPE_PRO_ANNUAL",
    }
    key = env_map.get((plan_id, billing))
    if not key:
        raise ValueError(f"Unknown plan/billing combo: {plan_id}/{billing}")
    price = os.environ.get(key, "")
    if not price:
        raise EnvironmentError(f"Missing env var: {key}")
    return price


# ── Customer ──────────────────────────────────────────────────────────────

def get_or_create_customer(email: str, name: str = "", metadata: dict = None) -> stripe.Customer:
    """
    Look up an existing Stripe customer by email, or create one.
    Returns the stripe.Customer object.
    """
    existing = stripe.Customer.list(email=email, limit=1)
    if existing.data:
        return existing.data[0]

    params: dict = {"email": email}
    if name:
        params["name"] = name
    if metadata:
        params["metadata"] = metadata

    return stripe.Customer.create(**params)


def update_customer_metadata(customer_id: str, metadata: dict) -> stripe.Customer:
    """Merge new metadata onto an existing customer."""
    return stripe.Customer.modify(customer_id, metadata=metadata)


# ── Checkout Session (hosted payment page) ────────────────────────────────

def create_checkout_session(
    customer_id: str,
    plan_id: str,
    billing: str = "monthly",
    success_path: str = "/billing/success",
    cancel_path: str = "/billing/cancel",
) -> str:
    """
    Create a Stripe Checkout Session and return its URL.

    The customer completes payment on Stripe's hosted page, then is
    redirected back to APP_BASE_URL + success_path / cancel_path.
    """
    base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    price = _price_id(plan_id, billing)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price, "quantity": 1}],
        success_url=f"{base_url}{success_path}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}{cancel_path}",
        subscription_data={
            "metadata": {"plan_id": plan_id, "billing": billing},
        },
        allow_promotion_codes=True,
    )
    return session.url


# ── Customer Portal (self-serve billing) ──────────────────────────────────

def create_portal_session(customer_id: str, return_path: str = "/dashboard") -> str:
    """
    Create a Stripe Customer Portal session and return its URL.
    Lets the customer update payment method, cancel, or view invoices.
    """
    base_url = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{base_url}{return_path}",
    )
    return session.url


# ── Subscription management ───────────────────────────────────────────────

def get_active_subscription(customer_id: str) -> stripe.Subscription | None:
    """Return the customer's first active/trialing subscription, or None."""
    subs = stripe.Subscription.list(
        customer=customer_id,
        status="active",
        limit=1,
    )
    if subs.data:
        return subs.data[0]

    trialing = stripe.Subscription.list(
        customer=customer_id,
        status="trialing",
        limit=1,
    )
    return trialing.data[0] if trialing.data else None


def change_plan(
    subscription_id: str,
    new_plan_id: str,
    new_billing: str = "monthly",
    prorate: bool = True,
) -> stripe.Subscription:
    """
    Upgrade or downgrade an existing subscription to a new plan/billing.

    Uses Stripe's immediate proration so the customer is charged/credited
    the prorated difference right away.
    """
    sub = stripe.Subscription.retrieve(subscription_id)
    item_id = sub["items"]["data"][0]["id"]
    new_price = _price_id(new_plan_id, new_billing)

    return stripe.Subscription.modify(
        subscription_id,
        items=[{"id": item_id, "price": new_price}],
        proration_behavior="always_invoice" if prorate else "none",
        metadata={"plan_id": new_plan_id, "billing": new_billing},
    )


def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
    """
    Cancel a subscription.

    at_period_end=True  — cancel at end of current billing period (default)
    at_period_end=False — cancel immediately
    """
    if at_period_end:
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
    return stripe.Subscription.cancel(subscription_id)


# ── Webhook signature verification ───────────────────────────────────────

def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """
    Verify a Stripe webhook signature and return the parsed Event.
    Raises stripe.error.SignatureVerificationError on failure.
    """
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise EnvironmentError("STRIPE_WEBHOOK_SECRET is not set")
    return stripe.Webhook.construct_event(payload, sig_header, secret)


# ── Quick-look helpers ────────────────────────────────────────────────────

def get_plan_id_from_subscription(sub: stripe.Subscription) -> str | None:
    """Extract the Lixen plan ID stored in subscription metadata."""
    return sub.get("metadata", {}).get("plan_id")


def get_upcoming_invoice(customer_id: str) -> stripe.Invoice | None:
    """Return the next invoice for a customer, or None."""
    try:
        return stripe.Invoice.upcoming(customer=customer_id)
    except stripe.error.InvalidRequestError:
        return None
