#!/usr/bin/env python3
"""
GHL Email Warmup — Contact Search & CSV Export
"TEST - Email Warmup Segment 01"

GHL's public API does not support creating Smart Lists programmatically.
This script instead searches your contacts with the same filters and exports
the results to warmup_contacts.csv so you can use them in your campaign.

Filters applied:
  1. Email is not empty
  2. Tags contain: med spa | wellness | spa
  3. Last activity within the last 180 days
  (Source filter applied post-fetch — excludes 'cold' and 'unverified')

Usage:
  bash setup.sh   (handles everything)
"""

import os
import sys
import csv
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY     = os.getenv("GHL_API_KEY")
LOCATION_ID = os.getenv("GHL_LOCATION_ID")

BASE_URL = "https://services.leadconnectorhq.com"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":  "application/json",
    "Version":       "2021-07-28",
}

OUTPUT_FILE  = "warmup_contacts.csv"
MAX_CONTACTS = 100

cutoff_dt = datetime.now(timezone.utc) - timedelta(days=180)


def validate_env():
    missing = [k for k, v in {"GHL_API_KEY": API_KEY, "GHL_LOCATION_ID": LOCATION_ID}.items() if not v]
    if missing:
        print(f"ERROR: Missing env vars: {', '.join(missing)}")
        print("Re-run setup.sh and enter your credentials.")
        sys.exit(1)


def fetch_contacts() -> list:
    """
    Pull contacts from GHL using the /contacts endpoint with query params.
    Fetches in pages and stops once we have MAX_CONTACTS qualifying contacts.
    """
    qualifying = []
    page       = 1
    page_limit = 100

    print("Fetching contacts from GHL...")

    while len(qualifying) < MAX_CONTACTS:
        params = {
            "locationId": LOCATION_ID,
            "limit":      page_limit,
            "skip":       (page - 1) * page_limit,
        }

        resp = requests.get(f"{BASE_URL}/contacts/", headers=HEADERS, params=params, timeout=30)

        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            sys.exit(1)

        data     = resp.json()
        contacts = data.get("contacts", [])

        if not contacts:
            break  # no more pages

        for c in contacts:
            if passes_filters(c):
                qualifying.append(c)
                if len(qualifying) >= MAX_CONTACTS:
                    break

        # If GHL returned fewer than page_limit, we've hit the last page
        if len(contacts) < page_limit:
            break

        page += 1

    return qualifying


def passes_filters(c: dict) -> bool:
    """Return True if this contact matches all warmup criteria."""

    # Filter 1 — Must have an email
    if not c.get("email"):
        return False

    # Filter 2 — Tags must contain at least one warmup keyword
    tags = [t.lower() for t in (c.get("tags") or [])]
    warmup_keywords = {"med spa", "wellness", "spa"}
    if not any(kw in tag for kw in warmup_keywords for tag in tags):
        return False

    # Filter 3 — Source must not be cold or unverified
    source = (c.get("source") or "").lower()
    if source in {"cold", "unverified"}:
        return False

    # Filter 4 — Last activity within 180 days
    last_activity = c.get("lastActivity") or c.get("dateUpdated")
    if last_activity:
        try:
            dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
            if dt < cutoff_dt:
                return False
        except ValueError:
            pass  # if we can't parse, include the contact

    return True


def export_csv(contacts: list):
    fields = ["id", "firstName", "lastName", "email", "phone", "tags", "source", "lastActivity", "dateAdded"]

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for c in contacts:
            row = {k: c.get(k, "") for k in fields}
            # Flatten tags list to a comma-separated string
            if isinstance(row.get("tags"), list):
                row["tags"] = ", ".join(row["tags"])
            writer.writerow(row)

    print(f"Saved {len(contacts)} contacts → {OUTPUT_FILE}")


def main():
    validate_env()

    contacts = fetch_contacts()

    print(f"\nFound {len(contacts)} contacts matching warmup filters.\n")

    if not contacts:
        print("No contacts matched. Check your tags — contacts need at least one of:")
        print("  'med spa', 'wellness', or 'spa'")
        print("\nIf your contacts aren't tagged yet, the Smart List must be")
        print("created manually in GHL → Contacts → Smart Lists (no tag filter).")
        sys.exit(0)

    # Print preview
    print(f"{'Name':<25} {'Email':<35} {'Tags'}")
    print("-" * 80)
    for c in contacts[:10]:
        name  = f"{c.get('firstName','')} {c.get('lastName','')}".strip()
        email = c.get("email", "")
        tags  = ", ".join(c.get("tags") or [])
        print(f"{name:<25} {email:<35} {tags}")

    if len(contacts) > 10:
        print(f"  ... and {len(contacts) - 10} more (see {OUTPUT_FILE})")

    export_csv(contacts)

    print(f"""
======================================
  Next Steps
======================================
1. Open warmup_contacts.csv to review your {len(contacts)} contacts.
2. In GHL → Contacts → Import, upload the CSV to create a segment,
   OR go to Marketing → Emails → New Campaign and use this list.
3. Track results after sending:
     Open Rate      > 25%
     Bounce Rate    < 2%
     Spam Complaints< 0.1%
     Unsubscribes   < 0.5%
""")


if __name__ == "__main__":
    main()
