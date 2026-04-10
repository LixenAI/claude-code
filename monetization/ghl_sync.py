"""
Lixen.AI — GoHighLevel Subscription Sync

Keeps GHL contact records up to date whenever a Stripe subscription changes.

What it writes to GHL:
  Custom Fields:
    lixen_plan          — "smart" | "pro" | "none"
    lixen_plan_status   — "active" | "trialing" | "canceled" | "past_due"
    lixen_billing       — "monthly" | "annual"
    lixen_period_end    — ISO date of current period end

  Tags (added, never removed automatically):
    lixen-subscribed    — added on first successful payment
    lixen-plan-smart    — while on Smart plan
    lixen-plan-pro      — while on Pro plan
    lixen-canceling     — when cancel_at_period_end = true
    lixen-canceled      — after subscription fully ends
    lixen-payment-failed — when a payment attempt fails

Environment variables required:
  GHL_API_KEY       — Bearer token for GHL API v2
  GHL_LOCATION_ID   — Your GHL location/sub-account ID
"""

import os
import logging
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

GHL_API_KEY     = os.environ.get("GHL_API_KEY", "")
GHL_LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "")

GHL_HEADERS = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type":  "application/json",
    "Version":       "2021-07-28",
}

GHL_BASE = "https://services.leadconnectorhq.com"


# ── Internal helpers ──────────────────────────────────────────────────────

def _ghl_available() -> bool:
    """Return True if GHL credentials are configured."""
    return bool(GHL_API_KEY and GHL_LOCATION_ID)


def _find_contact_by_email(email: str) -> str | None:
    """Return GHL contact ID for the given email, or None."""
    if not _ghl_available():
        return None
    try:
        resp = requests.get(
            f"{GHL_BASE}/contacts/search",
            headers=GHL_HEADERS,
            params={"locationId": GHL_LOCATION_ID, "query": email},
            timeout=10,
        )
        resp.raise_for_status()
        contacts = resp.json().get("contacts", [])
        return contacts[0]["id"] if contacts else None
    except Exception as exc:
        log.warning("GHL contact lookup failed for %s: %s", email, exc)
        return None


def _update_contact_fields(contact_id: str, custom_fields: list[dict]) -> bool:
    """
    Update custom fields on a GHL contact.

    custom_fields format:
        [{"id": "field_key", "value": "field_value"}, ...]
    """
    try:
        resp = requests.put(
            f"{GHL_BASE}/contacts/{contact_id}",
            headers=GHL_HEADERS,
            json={"customFields": custom_fields},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        log.warning("GHL field update failed for contact %s: %s", contact_id, exc)
        return False


def _add_tags(contact_id: str, *tags: str) -> bool:
    """Add one or more tags to a GHL contact."""
    if not tags:
        return True
    try:
        resp = requests.post(
            f"{GHL_BASE}/contacts/{contact_id}/tags",
            headers=GHL_HEADERS,
            json={"tags": list(tags)},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        log.warning("GHL tag update failed for contact %s: %s", contact_id, exc)
        return False


# ── Public API ────────────────────────────────────────────────────────────

def sync_subscription_to_ghl(customer: dict, sub: dict) -> bool:
    """
    Sync a Stripe customer + subscription to the matching GHL contact.

    Resolves the GHL contact ID from:
      1. customer.metadata.ghl_contact_id (set at checkout time)
      2. Email lookup via GHL search API

    Writes plan/status fields to the contact. Returns True on success.
    """
    if not _ghl_available():
        log.debug("GHL not configured — skipping sync")
        return False

    email = customer.get("email", "")
    ghl_contact_id = customer.get("metadata", {}).get("ghl_contact_id") or _find_contact_by_email(email)

    if not ghl_contact_id:
        log.info("No GHL contact found for %s — skipping sync", email)
        return False

    # Extract values from Stripe objects
    plan_id     = sub.get("metadata", {}).get("plan_id", "none")
    billing     = sub.get("metadata", {}).get("billing", "monthly")
    status      = sub.get("status", "none")
    period_end  = sub.get("current_period_end")

    period_end_iso = ""
    if period_end:
        period_end_iso = datetime.fromtimestamp(period_end, tz=timezone.utc).strftime("%Y-%m-%d")

    fields = [
        {"id": "lixen_plan",        "value": plan_id},
        {"id": "lixen_plan_status", "value": status},
        {"id": "lixen_billing",     "value": billing},
        {"id": "lixen_period_end",  "value": period_end_iso},
    ]

    ok = _update_contact_fields(ghl_contact_id, fields)
    if ok:
        log.info(
            "GHL sync: contact=%s plan=%s status=%s billing=%s",
            ghl_contact_id, plan_id, status, billing,
        )
    return ok


def tag_ghl_contact(customer: dict, *tags: str) -> bool:
    """
    Add tags to the GHL contact matching this Stripe customer.
    Resolves contact the same way as sync_subscription_to_ghl.
    """
    if not _ghl_available():
        return False

    email = customer.get("email", "")
    ghl_contact_id = customer.get("metadata", {}).get("ghl_contact_id") or _find_contact_by_email(email)

    if not ghl_contact_id:
        log.info("No GHL contact found for %s — skipping tagging", email)
        return False

    ok = _add_tags(ghl_contact_id, *tags)
    if ok:
        log.info("GHL tags added: contact=%s tags=%s", ghl_contact_id, tags)
    return ok
