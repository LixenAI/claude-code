"""
Lixen.AI — High-level Subscription Management

Orchestrates Stripe + GHL:
  • subscribe()      — onboard a new paying customer
  • upgrade()        — move to a higher plan
  • downgrade()      — move to a lower plan
  • cancel()         — cancel subscription
  • get_status()     — current plan + status for a customer email
"""

import os
from dataclasses import dataclass
from typing import Optional

import stripe as stripe_module
from dotenv import load_dotenv

import stripe_client as sc
from plans import get_plan, Plan
from ghl_sync import sync_subscription_to_ghl

load_dotenv()


@dataclass
class SubscriptionStatus:
    email: str
    plan_id: Optional[str]          # "smart" | "pro" | None
    plan_name: Optional[str]
    status: str                     # "active" | "trialing" | "canceled" | "none"
    billing_interval: Optional[str] # "monthly" | "annual"
    current_period_end: Optional[int]  # Unix timestamp
    cancel_at_period_end: bool
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]


# ── Public API ────────────────────────────────────────────────────────────

def subscribe(
    email: str,
    name: str,
    plan_id: str,
    billing: str = "monthly",
    ghl_contact_id: str = "",
) -> str:
    """
    Create a Stripe customer (or retrieve existing) and return a
    hosted Checkout Session URL for the customer to complete payment.

    Calls ghl_sync after successful checkout happen via the webhook.
    Returns: checkout URL string
    """
    if not get_plan(plan_id):
        raise ValueError(f"Unknown plan: {plan_id}")

    metadata = {}
    if ghl_contact_id:
        metadata["ghl_contact_id"] = ghl_contact_id

    customer = sc.get_or_create_customer(email=email, name=name, metadata=metadata)
    return sc.create_checkout_session(
        customer_id=customer["id"],
        plan_id=plan_id,
        billing=billing,
    )


def upgrade(customer_email: str, new_plan_id: str, new_billing: str = "monthly") -> str:
    """
    Immediately upgrade a customer to a higher plan with proration.
    Returns a human-readable confirmation string.
    Raises ValueError if no active subscription found.
    """
    customer = sc.get_or_create_customer(email=customer_email)
    sub = sc.get_active_subscription(customer["id"])
    if not sub:
        raise ValueError(f"No active subscription for {customer_email}")

    new_plan = get_plan(new_plan_id)
    if not new_plan:
        raise ValueError(f"Unknown plan: {new_plan_id}")

    updated_sub = sc.change_plan(sub["id"], new_plan_id, new_billing, prorate=True)
    sync_subscription_to_ghl(customer, updated_sub)

    return (
        f"Upgraded {customer_email} to {new_plan.name} ({new_billing}). "
        f"Prorated invoice created."
    )


def downgrade(customer_email: str, new_plan_id: str, new_billing: str = "monthly") -> str:
    """
    Downgrade a customer to a lower plan, effective at period end.
    Returns a human-readable confirmation string.
    """
    customer = sc.get_or_create_customer(email=customer_email)
    sub = sc.get_active_subscription(customer["id"])
    if not sub:
        raise ValueError(f"No active subscription for {customer_email}")

    new_plan = get_plan(new_plan_id)
    if not new_plan:
        raise ValueError(f"Unknown plan: {new_plan_id}")

    # Schedule the change at period end (no immediate proration)
    updated_sub = sc.change_plan(sub["id"], new_plan_id, new_billing, prorate=False)
    sync_subscription_to_ghl(customer, updated_sub)

    return (
        f"Scheduled downgrade of {customer_email} to {new_plan.name} ({new_billing}). "
        f"Takes effect at end of current billing period."
    )


def cancel(customer_email: str, immediate: bool = False) -> str:
    """
    Cancel a customer's subscription.
    immediate=False cancels at period end (default — allows access until expiry).
    immediate=True cancels right now.
    """
    customer = sc.get_or_create_customer(email=customer_email)
    sub = sc.get_active_subscription(customer["id"])
    if not sub:
        raise ValueError(f"No active subscription for {customer_email}")

    updated_sub = sc.cancel_subscription(sub["id"], at_period_end=not immediate)
    sync_subscription_to_ghl(customer, updated_sub)

    if immediate:
        return f"Subscription for {customer_email} canceled immediately."
    return (
        f"Subscription for {customer_email} will cancel at period end "
        f"(Unix ts: {updated_sub.get('current_period_end')})."
    )


def get_status(customer_email: str) -> SubscriptionStatus:
    """Return the current subscription status for a customer email."""
    existing = stripe_module.Customer.list(email=customer_email, limit=1)
    if not existing.data:
        return SubscriptionStatus(
            email=customer_email,
            plan_id=None,
            plan_name=None,
            status="none",
            billing_interval=None,
            current_period_end=None,
            cancel_at_period_end=False,
            stripe_customer_id=None,
            stripe_subscription_id=None,
        )

    customer = existing.data[0]
    sub = sc.get_active_subscription(customer["id"])

    if not sub:
        return SubscriptionStatus(
            email=customer_email,
            plan_id=None,
            plan_name=None,
            status="none",
            billing_interval=None,
            current_period_end=None,
            cancel_at_period_end=False,
            stripe_customer_id=customer["id"],
            stripe_subscription_id=None,
        )

    plan_id = sc.get_plan_id_from_subscription(sub)
    plan = get_plan(plan_id) if plan_id else None
    billing = sub.get("metadata", {}).get("billing", "monthly")

    return SubscriptionStatus(
        email=customer_email,
        plan_id=plan_id,
        plan_name=plan.name if plan else None,
        status=sub["status"],
        billing_interval=billing,
        current_period_end=sub.get("current_period_end"),
        cancel_at_period_end=sub.get("cancel_at_period_end", False),
        stripe_customer_id=customer["id"],
        stripe_subscription_id=sub["id"],
    )


def billing_portal_url(customer_email: str) -> str:
    """Return a Stripe Customer Portal URL for the customer to manage billing."""
    existing = stripe_module.Customer.list(email=customer_email, limit=1)
    if not existing.data:
        raise ValueError(f"No Stripe customer found for {customer_email}")
    return sc.create_portal_session(existing.data[0]["id"])
