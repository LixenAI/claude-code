"""
GHL Setup Script — verifies connection and creates automation workflows.

Run once after filling in your .env:
    python ghl_setup.py

What it does:
  1. Verifies your GHL API key and location
  2. Lists connected social accounts (confirms FB/IG/TikTok are there)
  3. Creates two GHL Workflows via API:
       A) Weekly Content Poster  — time trigger every Monday 7am
       B) AUDIT Auto-Reply       — triggers when a contact sends "AUDIT"
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GHL_API_BASE = "https://services.leadconnectorhq.com"
LOCATION_ID = os.environ.get("GHL_LOCATION_ID", "C7e7ReTQ4FXMZp9TjxzU")
WEBHOOK_BASE_URL = os.environ.get("WEBHOOK_BASE_URL", "http://localhost:8000")


def _headers(version: str = "2021-07-28") -> dict:
    api_key = os.environ.get("GHL_API_KEY", "")
    if not api_key:
        print("ERROR: GHL_API_KEY not set in .env")
        sys.exit(1)
    return {
        "Authorization": f"Bearer {api_key}",
        "Version": version,
        "Content-Type": "application/json",
    }


# ── Step 1: Verify GHL connection ────────────────────────────────────────

def verify_connection() -> dict:
    print("1. Verifying GHL connection...")
    url = f"{GHL_API_BASE}/locations/{LOCATION_ID}"
    resp = requests.get(url, headers=_headers(), timeout=15)

    if resp.status_code == 401:
        print("   ✗ Invalid API key. Get it from GHL → Settings → Integrations → API Keys")
        sys.exit(1)
    elif resp.status_code == 404:
        print(f"   ✗ Location {LOCATION_ID} not found. Check GHL_LOCATION_ID in .env")
        sys.exit(1)

    resp.raise_for_status()
    location = resp.json().get("location", resp.json())
    print(f"   ✓ Connected to: {location.get('name', LOCATION_ID)}")
    return location


# ── Step 2: List social accounts ─────────────────────────────────────────

def list_social_accounts() -> list:
    print("\n2. Checking connected social accounts...")
    url = f"{GHL_API_BASE}/social-media-posting/location/{LOCATION_ID}/accounts"
    resp = requests.get(url, headers=_headers(), timeout=15)

    if resp.status_code == 404:
        print("   ! Social Planner API not available for this account tier.")
        return []

    resp.raise_for_status()
    accounts = resp.json().get("accounts", resp.json() if isinstance(resp.json(), list) else [])

    expected = {
        "698afe7a73eafb1d3b1dee6a_C7e7ReTQ4FXMZp9TjxzU_928531400351443_page": "Facebook — Lixen.AI",
        "698afe9ddf13cb8b403358b3_C7e7ReTQ4FXMZp9TjxzU_17841408430198402": "Instagram — lixen.ai",
        "698bfa551ce275697c2e8aca_C7e7ReTQ4FXMZp9TjxzU_000MKkVmyEEjs3pnDIk6WCPUbxmJe9sHp5_business": "TikTok — LixenAI",
    }

    found_ids = {a.get("id", a.get("_id", "")) for a in accounts}

    for account_id, label in expected.items():
        if account_id in found_ids:
            print(f"   ✓ {label}")
        else:
            print(f"   ✗ {label} — not found (may need reconnecting in GHL Social Planner)")

    return accounts


# ── Step 3: Create workflows ──────────────────────────────────────────────

def create_weekly_content_workflow() -> dict | None:
    """
    Creates a GHL Workflow:
    Trigger: Time-Based (every Monday at 07:00)
    Action:  HTTP Webhook → /ghl/generate-and-post
    """
    print("\n3a. Creating Weekly Content Poster workflow...")

    url = f"{GHL_API_BASE}/workflows/"
    payload = {
        "locationId": LOCATION_ID,
        "name": "Lixen.AI — Weekly Content Poster",
        "status": "active",
        "trigger": {
            "type": "schedule",
            "schedule": {
                "frequency": "weekly",
                "dayOfWeek": 1,  # 1 = Monday
                "time": "07:00",
                "timezone": "America/New_York",
            },
        },
        "actions": [
            {
                "type": "webhook",
                "name": "Generate & Post Weekly Content",
                "config": {
                    "url": f"{WEBHOOK_BASE_URL}/ghl/generate-and-post",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "secret": os.environ.get("WEBHOOK_SECRET", ""),
                        "platforms": ["facebook", "instagram", "tiktok"],
                    }),
                },
            },
            {
                "type": "internal_notification",
                "name": "Notify — Content Posted",
                "config": {
                    "message": "Weekly content has been posted to Facebook, Instagram, and TikTok by Lixen.AI Content Agent.",
                },
            },
        ],
    }

    resp = requests.post(url, json=payload, headers=_headers("2021-07-28"), timeout=15)

    if resp.status_code in (200, 201):
        workflow = resp.json()
        wf_id = workflow.get("id", workflow.get("_id", "created"))
        print(f"   ✓ Created: Lixen.AI — Weekly Content Poster (ID: {wf_id})")
        return workflow
    else:
        # Workflow API may not support programmatic creation on all GHL plans
        print(f"   ! Could not create workflow via API (status {resp.status_code}).")
        print(f"   → Create it manually in GHL: Automation → Workflows → + New")
        print(f"     Trigger: Time-Based → Every Monday 07:00 AM")
        print(f"     Action:  Custom Webhook → POST {WEBHOOK_BASE_URL}/ghl/generate-and-post")
        print(f'     Body:    {{"secret":"{os.environ.get("WEBHOOK_SECRET","")}", "platforms":["facebook","instagram","tiktok"]}}')
        return None


def create_audit_reply_workflow() -> dict | None:
    """
    Creates a GHL Workflow:
    Trigger: Inbound Message containing 'AUDIT'
    Action:  HTTP Webhook → /ghl/reply  (auto_send: true)
    """
    print("\n3b. Creating AUDIT Auto-Reply workflow...")

    url = f"{GHL_API_BASE}/workflows/"
    payload = {
        "locationId": LOCATION_ID,
        "name": "Lixen.AI — AUDIT Auto-Reply (AI)",
        "status": "active",
        "trigger": {
            "type": "inbound_message",
            "filter": {
                "messageContains": "AUDIT",
                "caseSensitive": False,
            },
        },
        "actions": [
            {
                "type": "webhook",
                "name": "Generate AI Reply",
                "config": {
                    "url": f"{WEBHOOK_BASE_URL}/ghl/reply",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "secret": os.environ.get("WEBHOOK_SECRET", ""),
                        "contact_name": "{{contact.name}}",
                        "message": "{{last_message_body}}",
                        "platform": "{{message.channel}}",
                        "contact_id": "{{contact.id}}",
                        "auto_send": True,
                    }),
                },
            },
        ],
    }

    resp = requests.post(url, json=payload, headers=_headers("2021-07-28"), timeout=15)

    if resp.status_code in (200, 201):
        workflow = resp.json()
        wf_id = workflow.get("id", workflow.get("_id", "created"))
        print(f"   ✓ Created: Lixen.AI — AUDIT Auto-Reply (ID: {wf_id})")
        return workflow
    else:
        print(f"   ! Could not create workflow via API (status {resp.status_code}).")
        print(f"   → Create it manually in GHL: Automation → Workflows → + New")
        print(f"     Trigger: Customer Replied → Message Contains 'AUDIT'")
        print(f"     Action:  Custom Webhook → POST {WEBHOOK_BASE_URL}/ghl/reply")
        print(f'     Body:    {{"secret":"...","contact_name":"{{{{contact.name}}}}","message":"{{{{last_message_body}}}}","contact_id":"{{{{contact.id}}}}","auto_send":true}}')
        return None


# ── Step 4: Test a generate-and-post call ────────────────────────────────

def test_generate_and_post(dry: bool = True) -> None:
    print("\n4. Testing generate-and-post endpoint...")
    webhook_url = f"{WEBHOOK_BASE_URL}/ghl/generate-and-post"

    try:
        resp = requests.get(f"{WEBHOOK_BASE_URL}/health", timeout=5)
        if resp.status_code != 200:
            print(f"   ! Webhook server not running at {WEBHOOK_BASE_URL}")
            print(f"     Start it with: python main.py --mode webhook")
            return
    except requests.ConnectionError:
        print(f"   ! Webhook server not reachable at {WEBHOOK_BASE_URL}")
        print(f"     Start it with: python main.py --mode webhook")
        return

    if dry:
        print(f"   → Skipping live test (server is running at {WEBHOOK_BASE_URL} ✓)")
        print(f"     To test: curl -X POST {webhook_url} \\")
        print(f'       -H "Content-Type: application/json" \\')
        print(f'       -d \'{{"secret":"{os.environ.get("WEBHOOK_SECRET","")}", "platforms":["facebook"]}}\'')
    else:
        payload = {
            "secret": os.environ.get("WEBHOOK_SECRET", ""),
            "platforms": ["facebook"],
            "category": "Pain Agitation",
            "topic": "missed calls costing med spas revenue",
        }
        resp = requests.post(webhook_url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        print(f"   ✓ Post generated and sent to GHL!")
        print(f"     Post ID: {result.get('ghl_post_id')}")
        print(f"     Preview: {result.get('content', '')[:120]}...")


# ── Main ─────────────────────────────────────────────────────────────────

def run_setup(skip_workflow_creation: bool = False, run_live_test: bool = False):
    print("=" * 60)
    print(" Lixen.AI — GHL Setup")
    print("=" * 60)

    verify_connection()
    list_social_accounts()

    if not skip_workflow_creation:
        create_weekly_content_workflow()
        create_audit_reply_workflow()

    test_generate_and_post(dry=not run_live_test)

    print("\n" + "=" * 60)
    print(" Setup complete.")
    print(" Next steps:")
    print("   1. python main.py --mode dry-run       → preview content")
    print("   2. python main.py --mode webhook        → start webhook server")
    print("   3. python main.py --mode run-now        → post immediately")
    print("   4. python main.py --mode schedule       → weekly auto-post")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lixen.AI GHL Setup")
    parser.add_argument("--skip-workflows", action="store_true", help="Skip workflow creation")
    parser.add_argument("--live-test", action="store_true", help="Run a live generate-and-post test")
    args = parser.parse_args()

    run_setup(
        skip_workflow_creation=args.skip_workflows,
        run_live_test=args.live_test,
    )
