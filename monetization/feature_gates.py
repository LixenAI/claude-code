"""
Lixen.AI — Feature Gates

Checks whether a customer's active plan grants access to a given feature
or is within usage limits.

Usage (direct):
    from feature_gates import require_plan, check_limit, FEATURES

    # Check a feature flag
    if not require_plan(customer_email, FEATURES.AI_CALL_ANSWERING):
        raise PermissionError("Upgrade to Pro to unlock AI call answering.")

    # Check a usage limit
    ok, limit = check_limit(customer_email, "posts_per_week", used=3)
    if not ok:
        raise PermissionError(f"Weekly post limit reached ({limit} posts/week on Smart plan).")

Usage (decorator):
    from feature_gates import requires_feature, FEATURES

    @requires_feature(FEATURES.AI_CALL_ANSWERING)
    def handle_inbound_call(customer_email: str, ...):
        ...
"""

import functools
import logging
from dataclasses import dataclass

import stripe as stripe_module
from dotenv import load_dotenv

import stripe_client as sc
from plans import get_plan, Plan

load_dotenv()
log = logging.getLogger(__name__)


# ── Feature constants ─────────────────────────────────────────────────────

class FEATURES:
    """Symbolic names for boolean feature flags on a Plan."""
    AI_CALL_ANSWERING  = "ai_call_answering"
    AI_DM_REPLIES      = "ai_dm_replies"
    CUSTOM_BRAND_VOICE = "custom_brand_voice"
    PRIORITY_SUPPORT   = "priority_support"
    ADVANCED_ANALYTICS = "advanced_analytics"


class LIMITS:
    """Symbolic names for numeric usage limits on a Plan."""
    POSTS_PER_WEEK            = "posts_per_week"
    EMAIL_WARMUP_SLOTS        = "email_warmup_slots"
    LEAD_SEARCHES_PER_MONTH   = "lead_searches_per_month"


# ── Core helpers ──────────────────────────────────────────────────────────

def _get_plan_for_email(customer_email: str) -> Plan | None:
    """
    Look up the active Stripe subscription for the email and return its Plan.
    Returns None if no active subscription found.
    """
    customers = stripe_module.Customer.list(email=customer_email, limit=1)
    if not customers.data:
        return None

    sub = sc.get_active_subscription(customers.data[0]["id"])
    if not sub:
        return None

    plan_id = sc.get_plan_id_from_subscription(sub)
    return get_plan(plan_id) if plan_id else None


def require_feature(customer_email: str, feature: str) -> bool:
    """
    Return True if the customer's plan has the given feature enabled.
    Returns False if no active plan or feature is disabled on their plan.
    """
    plan = _get_plan_for_email(customer_email)
    if not plan:
        log.debug("require_feature: no active plan for %s", customer_email)
        return False
    enabled = getattr(plan, feature, False)
    log.debug("require_feature: %s.%s = %s (plan=%s)", customer_email, feature, enabled, plan.id)
    return bool(enabled)


def check_limit(customer_email: str, limit_name: str, used: int) -> tuple[bool, int]:
    """
    Check whether `used` is within the customer's plan limit for `limit_name`.

    Returns (allowed: bool, plan_limit: int).
    A plan_limit of -1 means unlimited.

    Examples:
        ok, limit = check_limit(email, LIMITS.POSTS_PER_WEEK, used=4)
        # ok=True, limit=5  (Smart plan, 4 < 5)

        ok, limit = check_limit(email, LIMITS.POSTS_PER_WEEK, used=6)
        # ok=False, limit=5  (Smart plan, 6 >= 5)
    """
    plan = _get_plan_for_email(customer_email)
    if not plan:
        return False, 0

    plan_limit = getattr(plan, limit_name, 0)
    if plan_limit == -1:
        return True, -1   # unlimited

    return used < plan_limit, plan_limit


# ── Decorator ─────────────────────────────────────────────────────────────

def requires_feature(feature: str):
    """
    Decorator that gates a function behind a plan feature.

    The decorated function MUST accept `customer_email` as its first
    positional argument or as a keyword argument.

    Raises PermissionError if the customer's plan does not include the feature.

    Example:
        @requires_feature(FEATURES.AI_CALL_ANSWERING)
        def answer_call(customer_email: str, call_data: dict):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve customer_email from first arg or kwarg
            email = kwargs.get("customer_email") or (args[0] if args else None)
            if not email:
                raise ValueError(
                    f"@requires_feature: could not resolve customer_email in call to {func.__name__}"
                )
            if not require_feature(email, feature):
                plan = _get_plan_for_email(email)
                plan_name = plan.name if plan else "no active plan"
                raise PermissionError(
                    f"Feature '{feature}' is not available on {plan_name}. "
                    f"Please upgrade your Lixen.AI plan."
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ── Convenience checks used by other agents ───────────────────────────────

def can_post(customer_email: str, posts_used_this_week: int) -> tuple[bool, str]:
    """
    Check if the customer can generate another social post this week.
    Returns (allowed, reason_string).
    """
    ok, limit = check_limit(customer_email, LIMITS.POSTS_PER_WEEK, posts_used_this_week)
    if ok:
        return True, ""
    limit_str = "unlimited" if limit == -1 else str(limit)
    return False, f"Weekly post limit reached ({posts_used_this_week}/{limit_str} on your plan)."


def can_search_leads(customer_email: str, searches_used_this_month: int) -> tuple[bool, str]:
    """
    Check if the customer can run another lead search this month.
    Returns (allowed, reason_string).
    """
    ok, limit = check_limit(customer_email, LIMITS.LEAD_SEARCHES_PER_MONTH, searches_used_this_month)
    if ok:
        return True, ""
    limit_str = "unlimited" if limit == -1 else str(limit)
    return False, (
        f"Monthly lead search limit reached ({searches_used_this_month}/{limit_str}). "
        f"Upgrade to Pro for unlimited searches."
    )


def can_add_warmup_inbox(customer_email: str, inboxes_active: int) -> tuple[bool, str]:
    """
    Check if the customer can add another email warmup inbox.
    Returns (allowed, reason_string).
    """
    ok, limit = check_limit(customer_email, LIMITS.EMAIL_WARMUP_SLOTS, inboxes_active)
    if ok:
        return True, ""
    limit_str = "unlimited" if limit == -1 else str(limit)
    return False, (
        f"Email warmup inbox limit reached ({inboxes_active}/{limit_str}). "
        f"Upgrade to Pro for up to 5 inboxes."
    )
