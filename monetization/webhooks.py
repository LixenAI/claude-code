"""
Lixen.AI — Stripe Webhook Handler (FastAPI)

Listens for Stripe events and keeps Lixen.AI state in sync.

── Endpoints ──────────────────────────────────────────────────────────────
  GET  /health             → health check
  POST /stripe/webhook     → Stripe event receiver
───────────────────────────────────────────────────────────────────────────

── Stripe Setup ────────────────────────────────────────────────────────────
1. Deploy this server (or use `ngrok http 8001` to expose locally)
2. Go to Stripe Dashboard → Developers → Webhooks → + Add endpoint
3. URL: https://your-server.com/stripe/webhook
4. Events to listen for:
     checkout.session.completed
     customer.subscription.updated
     customer.subscription.deleted
     invoice.payment_succeeded
     invoice.payment_failed
5. Copy the signing secret → STRIPE_WEBHOOK_SECRET in .env
───────────────────────────────────────────────────────────────────────────

── Events handled ──────────────────────────────────────────────────────────
  checkout.session.completed      — new subscription activated
  customer.subscription.updated   — plan change or cancellation scheduled
  customer.subscription.deleted   — subscription ended
  invoice.payment_succeeded       — renewal processed
  invoice.payment_failed          — payment failure (grace period warning)
───────────────────────────────────────────────────────────────────────────
"""

import os
import logging

import stripe
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

import stripe_client as sc
from ghl_sync import sync_subscription_to_ghl, tag_ghl_contact

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Lixen.AI Stripe Webhook", version="1.0.0")


# ── Health check ─────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "lixen-billing-webhook"}


# ── Webhook receiver ──────────────────────────────────────────────────────

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = sc.construct_webhook_event(payload, sig)
    except stripe.error.SignatureVerificationError as e:
        log.warning("Webhook signature verification failed: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature")
    except EnvironmentError as e:
        log.error("Webhook config error: %s", e)
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    event_type = event["type"]
    log.info("Received Stripe event: %s (id=%s)", event_type, event["id"])

    handlers = {
        "checkout.session.completed":    _on_checkout_completed,
        "customer.subscription.updated": _on_subscription_updated,
        "customer.subscription.deleted": _on_subscription_deleted,
        "invoice.payment_succeeded":     _on_payment_succeeded,
        "invoice.payment_failed":        _on_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            handler(event["data"]["object"])
        except Exception as exc:
            log.exception("Error handling %s: %s", event_type, exc)
            # Return 200 so Stripe doesn't retry indefinitely for app-level errors
            return JSONResponse({"status": "error", "detail": str(exc)}, status_code=200)

    return JSONResponse({"status": "received"})


# ── Event handlers ────────────────────────────────────────────────────────

def _on_checkout_completed(session: dict):
    """New subscription created via hosted Checkout."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    if not (customer_id and subscription_id):
        log.warning("checkout.session.completed missing customer/subscription")
        return

    customer = stripe.Customer.retrieve(customer_id)
    sub = stripe.Subscription.retrieve(subscription_id)
    plan_id = sc.get_plan_id_from_subscription(sub) or _infer_plan_from_sub(sub)

    log.info(
        "New subscription: customer=%s email=%s plan=%s",
        customer_id, customer.get("email"), plan_id,
    )

    sync_subscription_to_ghl(customer, sub)
    tag_ghl_contact(customer, f"lixen-plan-{plan_id}", "lixen-subscribed")


def _on_subscription_updated(sub: dict):
    """Plan change, upgrade, downgrade, or cancel_at_period_end set."""
    customer_id = sub.get("customer")
    customer = stripe.Customer.retrieve(customer_id)
    plan_id = sc.get_plan_id_from_subscription(sub)

    if sub.get("cancel_at_period_end"):
        log.info("Subscription set to cancel at period end: customer=%s", customer_id)
        tag_ghl_contact(customer, "lixen-canceling")
    else:
        log.info("Subscription updated: customer=%s plan=%s", customer_id, plan_id)

    sync_subscription_to_ghl(customer, sub)


def _on_subscription_deleted(sub: dict):
    """Subscription fully canceled (immediately or after grace period)."""
    customer_id = sub.get("customer")
    customer = stripe.Customer.retrieve(customer_id)

    log.info("Subscription deleted: customer=%s", customer_id)
    sync_subscription_to_ghl(customer, sub)
    tag_ghl_contact(customer, "lixen-canceled")


def _on_payment_succeeded(invoice: dict):
    """Recurring payment collected successfully."""
    customer_id = invoice.get("customer")
    amount = invoice.get("amount_paid", 0) / 100
    log.info("Payment succeeded: customer=%s amount=$%.2f", customer_id, amount)
    # Could trigger a "thank you" email via GHL workflow here


def _on_payment_failed(invoice: dict):
    """Payment attempt failed — customer needs to update payment method."""
    customer_id = invoice.get("customer")
    attempt_count = invoice.get("attempt_count", 0)
    customer = stripe.Customer.retrieve(customer_id)

    log.warning(
        "Payment failed: customer=%s email=%s attempt=%d",
        customer_id, customer.get("email"), attempt_count,
    )
    tag_ghl_contact(customer, "lixen-payment-failed")
    # Could trigger a dunning workflow in GHL here


# ── Helpers ───────────────────────────────────────────────────────────────

def _infer_plan_from_sub(sub: dict) -> str:
    """
    Fallback: infer plan_id from the Stripe Price ID when metadata is absent.
    """
    from plans import plan_from_stripe_price
    try:
        price_id = sub["items"]["data"][0]["price"]["id"]
        plan = plan_from_stripe_price(price_id)
        return plan.id if plan else "unknown"
    except (KeyError, IndexError):
        return "unknown"


# ── Entry point ───────────────────────────────────────────────────────────

def run_server(port: int = None):
    port = port or int(os.environ.get("BILLING_WEBHOOK_PORT", 8001))
    log.info("Starting Stripe webhook server on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
