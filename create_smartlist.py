#!/usr/bin/env python3
"""
Create GHL Smart List: TEST - Email Warmup Segment 01

Filters applied:
  1. Email is not empty
  2. Tags contain: med spa | wellness | spa
  3. Source is not: cold, unverified
  4. Last activity within last 180 days

Usage:
  1. Copy .env.example to .env and fill in GHL_API_KEY and GHL_LOCATION_ID
  2. pip install -r requirements.txt
  3. python create_smartlist.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GHL_API_KEY")
LOCATION_ID = os.getenv("GHL_LOCATION_ID")

BASE_URL = "https://services.leadconnectorhq.com"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Version": "2021-07-28",
}

SMART_LIST_NAME = "TEST - Email Warmup Segment 01"

# Last activity cutoff: 180 days ago
cutoff_date = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def build_smart_list_payload() -> dict:
    """
    Build the GHL v2 smart list filter payload.

    GHL smart list filters use a nested group structure:
      - filterGroups: list of groups (joined by AND)
      - Each group has filters joined by OR (within the group)

    Filter reference:
      field keys: https://highlevel.stoplight.io/docs/integrations/
    """
    return {
        "name": SMART_LIST_NAME,
        "filterGroups": [
            # Filter 1 — Email is not empty
            {
                "filters": [
                    {
                        "field": "email",
                        "operator": "is_not_empty",
                        "value": None,
                    }
                ]
            },
            # Filter 2 — Tags contain med spa OR wellness OR spa
            {
                "filters": [
                    {
                        "field": "tags",
                        "operator": "contains",
                        "value": "med spa",
                    },
                    {
                        "field": "tags",
                        "operator": "contains",
                        "value": "wellness",
                    },
                    {
                        "field": "tags",
                        "operator": "contains",
                        "value": "spa",
                    },
                ]
            },
            # Filter 3 — Source is not cold or unverified
            {
                "filters": [
                    {
                        "field": "source",
                        "operator": "is_not",
                        "value": "cold",
                    },
                    {
                        "field": "source",
                        "operator": "is_not",
                        "value": "unverified",
                    },
                ]
            },
            # Filter 4 — Last activity within last 180 days
            {
                "filters": [
                    {
                        "field": "lastActivityDate",
                        "operator": "greater_than",
                        "value": cutoff_date,
                    }
                ]
            },
        ],
    }


def create_smart_list() -> dict:
    url = f"{BASE_URL}/contacts/smartlists"
    payload = build_smart_list_payload()

    print(f"Creating smart list: {SMART_LIST_NAME!r}")
    print(f"Endpoint: POST {url}")
    print(f"Payload:\n{json.dumps(payload, indent=2)}\n")

    response = requests.post(url, headers=HEADERS, json=payload, timeout=30)

    if response.status_code in (200, 201):
        data = response.json()
        print(f"Smart list created successfully!")
        print(f"  ID   : {data.get('smartList', {}).get('id') or data.get('id')}")
        print(f"  Name : {SMART_LIST_NAME}")
        print(f"\nNext step: In GHL → Marketing → Emails, select this list as your audience.")
        return data
    else:
        print(f"Error {response.status_code}: {response.text}")
        sys.exit(1)


def validate_env():
    missing = []
    if not API_KEY:
        missing.append("GHL_API_KEY")
    if not LOCATION_ID:
        missing.append("GHL_LOCATION_ID")
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


if __name__ == "__main__":
    validate_env()
    HEADERS["locationId"] = LOCATION_ID
    create_smart_list()
