"""
Lixen.AI — Subscription Plan Definitions

Two plans:
  smart  — Core AI automation  ($297/month)
  pro    — Full AI OS           ($597/month)

Limits of -1 mean unlimited.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Plan:
    id: str                          # "smart" | "pro"
    name: str
    price_monthly: int               # USD cents
    price_annual: int                # USD cents (per year, ~2 months free)
    stripe_price_id_monthly: str     # set via env — see stripe_client.py
    stripe_price_id_annual: str
    # Feature limits (-1 = unlimited)
    posts_per_week: int
    email_warmup_slots: int          # concurrent email addresses in warmup
    lead_searches_per_month: int
    # Feature flags
    ai_call_answering: bool
    ai_dm_replies: bool
    custom_brand_voice: bool
    priority_support: bool
    advanced_analytics: bool
    # Human-readable feature list for marketing / receipts
    features: tuple = field(default_factory=tuple)


PLANS: dict[str, Plan] = {
    "smart": Plan(
        id="smart",
        name="Smart",
        price_monthly=29700,           # $297
        price_annual=297000,           # $2,970 (~$247.50/mo, save $594)
        stripe_price_id_monthly="",    # overridden by env STRIPE_SMART_MONTHLY
        stripe_price_id_annual="",     # overridden by env STRIPE_SMART_ANNUAL
        posts_per_week=5,
        email_warmup_slots=1,
        lead_searches_per_month=200,
        ai_call_answering=False,
        ai_dm_replies=True,
        custom_brand_voice=False,
        priority_support=False,
        advanced_analytics=False,
        features=(
            "5 AI-generated social posts per week",
            "AI DM replies via GHL",
            "Email warmup (1 inbox)",
            "200 lead searches/month",
            "GHL workflow automation",
            "Standard support",
        ),
    ),
    "pro": Plan(
        id="pro",
        name="Pro",
        price_monthly=59700,           # $597
        price_annual=597000,           # $5,970 (~$497.50/mo, save $1,194)
        stripe_price_id_monthly="",    # overridden by env STRIPE_PRO_MONTHLY
        stripe_price_id_annual="",     # overridden by env STRIPE_PRO_ANNUAL
        posts_per_week=-1,             # unlimited
        email_warmup_slots=5,
        lead_searches_per_month=-1,    # unlimited
        ai_call_answering=True,
        ai_dm_replies=True,
        custom_brand_voice=True,
        priority_support=True,
        advanced_analytics=True,
        features=(
            "Unlimited AI social posts",
            "AI call answering (24/7)",
            "AI DM replies via GHL",
            "Email warmup (5 inboxes)",
            "Unlimited lead searches",
            "Custom brand voice",
            "Advanced analytics dashboard",
            "Priority support + onboarding call",
            "GHL workflow automation",
        ),
    ),
}


def get_plan(plan_id: str) -> Optional[Plan]:
    """Return a Plan or None if not found."""
    return PLANS.get(plan_id)


def plan_from_stripe_price(price_id: str) -> Optional[Plan]:
    """Reverse-lookup a Plan by any of its Stripe price IDs."""
    for plan in PLANS.values():
        if price_id in (plan.stripe_price_id_monthly, plan.stripe_price_id_annual):
            return plan
    return None


def format_plan_summary(plan: Plan, billing: str = "monthly") -> str:
    """Return a human-readable plan summary string."""
    price = plan.price_monthly if billing == "monthly" else plan.price_annual
    dollars = price / 100
    period = "month" if billing == "monthly" else "year"
    lines = [
        f"Lixen.AI {plan.name} — ${dollars:,.0f}/{period}",
        "",
        "Includes:",
    ]
    for feature in plan.features:
        lines.append(f"  ✓ {feature}")
    return "\n".join(lines)
