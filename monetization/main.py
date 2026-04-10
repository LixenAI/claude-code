"""
Lixen.AI Monetization — CLI Entry Point

Usage:
  python main.py status <email>
  python main.py subscribe <email> <name> --plan smart|pro [--billing monthly|annual] [--ghl-id <id>]
  python main.py upgrade <email> --plan pro [--billing monthly|annual]
  python main.py downgrade <email> --plan smart [--billing monthly|annual]
  python main.py cancel <email> [--immediate]
  python main.py portal <email>
  python main.py webhook [--port 8001]
  python main.py plans
"""

import argparse
import sys
from dotenv import load_dotenv

load_dotenv()


# ── Helpers ───────────────────────────────────────────────────────────────

def _print_status(s):
    from datetime import datetime, timezone

    print(f"\nCustomer:  {s.email}")
    print(f"Plan:      {s.plan_name or 'None'}")
    print(f"Status:    {s.status}")
    print(f"Billing:   {s.billing_interval or '—'}")
    if s.current_period_end:
        dt = datetime.fromtimestamp(s.current_period_end, tz=timezone.utc)
        print(f"Period end: {dt.strftime('%Y-%m-%d')}")
    if s.cancel_at_period_end:
        print("NOTE: Subscription will cancel at period end.")
    print(f"Stripe customer: {s.stripe_customer_id or '—'}")
    print(f"Stripe sub:      {s.stripe_subscription_id or '—'}")
    print()


# ── Commands ──────────────────────────────────────────────────────────────

def cmd_plans(args):
    from plans import PLANS, format_plan_summary
    for plan in PLANS.values():
        print(format_plan_summary(plan, "monthly"))
        print()


def cmd_status(args):
    from subscriptions import get_status
    s = get_status(args.email)
    _print_status(s)


def cmd_subscribe(args):
    from subscriptions import subscribe
    url = subscribe(
        email=args.email,
        name=args.name,
        plan_id=args.plan,
        billing=args.billing,
        ghl_contact_id=args.ghl_id or "",
    )
    print(f"\nCheckout URL for {args.email}:\n{url}\n")
    print("Share this link with the customer to complete payment.")


def cmd_upgrade(args):
    from subscriptions import upgrade
    msg = upgrade(args.email, args.plan, args.billing)
    print(f"\n{msg}\n")


def cmd_downgrade(args):
    from subscriptions import downgrade
    msg = downgrade(args.email, args.plan, args.billing)
    print(f"\n{msg}\n")


def cmd_cancel(args):
    from subscriptions import cancel
    msg = cancel(args.email, immediate=args.immediate)
    print(f"\n{msg}\n")


def cmd_portal(args):
    from subscriptions import billing_portal_url
    url = billing_portal_url(args.email)
    print(f"\nBilling portal for {args.email}:\n{url}\n")


def cmd_webhook(args):
    from webhooks import run_server
    run_server(port=args.port)


# ── Argument parser ───────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Lixen.AI Monetization CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py plans
  python main.py status owner@medspa.com
  python main.py subscribe owner@medspa.com "Jane Smith" --plan pro --billing annual
  python main.py upgrade owner@medspa.com --plan pro
  python main.py downgrade owner@medspa.com --plan smart
  python main.py cancel owner@medspa.com
  python main.py portal owner@medspa.com
  python main.py webhook --port 8001
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # plans
    sub.add_parser("plans", help="Show available plans and pricing")

    # status
    p_status = sub.add_parser("status", help="Show subscription status for a customer")
    p_status.add_argument("email")

    # subscribe
    p_sub = sub.add_parser("subscribe", help="Create a checkout URL for a new customer")
    p_sub.add_argument("email")
    p_sub.add_argument("name", help="Customer full name")
    p_sub.add_argument("--plan", choices=["smart", "pro"], required=True)
    p_sub.add_argument("--billing", choices=["monthly", "annual"], default="monthly")
    p_sub.add_argument("--ghl-id", default="", dest="ghl_id", help="GHL contact ID to link")

    # upgrade
    p_up = sub.add_parser("upgrade", help="Upgrade a customer to a higher plan")
    p_up.add_argument("email")
    p_up.add_argument("--plan", choices=["smart", "pro"], required=True)
    p_up.add_argument("--billing", choices=["monthly", "annual"], default="monthly")

    # downgrade
    p_down = sub.add_parser("downgrade", help="Downgrade a customer to a lower plan")
    p_down.add_argument("email")
    p_down.add_argument("--plan", choices=["smart", "pro"], required=True)
    p_down.add_argument("--billing", choices=["monthly", "annual"], default="monthly")

    # cancel
    p_cancel = sub.add_parser("cancel", help="Cancel a customer subscription")
    p_cancel.add_argument("email")
    p_cancel.add_argument("--immediate", action="store_true",
                          help="Cancel now instead of at period end")

    # portal
    p_portal = sub.add_parser("portal", help="Generate a Stripe billing portal URL")
    p_portal.add_argument("email")

    # webhook
    p_wh = sub.add_parser("webhook", help="Start the Stripe webhook server")
    p_wh.add_argument("--port", type=int, default=None)

    return parser


# ── Entry ─────────────────────────────────────────────────────────────────

COMMAND_MAP = {
    "plans":     cmd_plans,
    "status":    cmd_status,
    "subscribe": cmd_subscribe,
    "upgrade":   cmd_upgrade,
    "downgrade": cmd_downgrade,
    "cancel":    cmd_cancel,
    "portal":    cmd_portal,
    "webhook":   cmd_webhook,
}


def main():
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMAND_MAP.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)
    try:
        handler(args)
    except (ValueError, PermissionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
