#!/usr/bin/env python3
"""
GHL Lead Generator — Med Spa / Wellness / Spa

Steps:
  1. Search Google Places for businesses in your target city
  2. Find emails — tries Hunter.io first, falls back to scraping the website
  3. Push contacts directly into GHL

Requirements in .env:
  GHL_API_KEY, GHL_LOCATION_ID,
  GOOGLE_PLACES_API_KEY, HUNTER_API_KEY (optional — used if quota remains),
  TARGET_CITY (e.g. "Miami, FL")
"""

import os
import re
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GHL_API_KEY     = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
GOOGLE_API_KEY  = os.getenv("GOOGLE_PLACES_API_KEY")
HUNTER_API_KEY  = os.getenv("HUNTER_API_KEY")
TARGET_CITY     = os.getenv("TARGET_CITY", "Miami, FL")

GHL_HEADERS = {
    "Authorization": f"Bearer {GHL_API_KEY}",
    "Content-Type":  "application/json",
    "Version":       "2021-07-28",
}

SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

SEARCH_TERMS = [
    "med spa", "wellness center", "day spa", "medical spa",
    "dermatologist aesthetics", "beauty clinic", "aesthetic clinic",
]
MAX_LEADS        = 100
hunter_exhausted = False  # flips to True when Hunter.io quota runs out


# ── Validation ──────────────────────────────────────────────────────────────

def validate_env():
    required = {
        "GHL_API_KEY":           GHL_API_KEY,
        "GHL_LOCATION_ID":       GHL_LOCATION_ID,
        "GOOGLE_PLACES_API_KEY": GOOGLE_API_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"ERROR: Missing credentials: {', '.join(missing)}")
        print("Re-run setup.sh to enter them.")
        sys.exit(1)
    if not HUNTER_API_KEY:
        print("Note: HUNTER_API_KEY not set — will scrape websites for emails.")


# ── Step 1: Google Places ────────────────────────────────────────────────────

def search_places(query: str) -> list:
    url    = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": f"{query} in {TARGET_CITY}", "key": GOOGLE_API_KEY}
    places = []

    while True:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"  Google Places error {resp.status_code}: {resp.text[:200]}")
            break

        data    = resp.json()
        results = data.get("results", [])
        places.extend(results)

        next_token = data.get("next_page_token")
        if not next_token or len(places) >= MAX_LEADS:
            break

        time.sleep(2)
        params = {"pagetoken": next_token, "key": GOOGLE_API_KEY}

    return places


def get_place_details(place_id: str) -> dict:
    url    = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"place_id": place_id, "fields": "website,name,formatted_phone_number", "key": GOOGLE_API_KEY}
    resp   = requests.get(url, params=params, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("result", {})
    return {}


def extract_domain(url: str) -> str | None:
    if not url:
        return None
    url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return url.split("/")[0].split("?")[0]


# ── Step 2a: Hunter.io ───────────────────────────────────────────────────────

def find_email_hunter(domain: str) -> dict | None:
    global hunter_exhausted
    if hunter_exhausted or not HUNTER_API_KEY:
        return None

    params = {"domain": domain, "api_key": HUNTER_API_KEY, "limit": 3}
    resp   = requests.get("https://api.hunter.io/v2/domain-search", params=params, timeout=10)

    if resp.status_code == 429 or (resp.status_code == 200 and
            resp.json().get("errors", [{}])[0].get("code") == 429):
        print("\n  [Hunter.io quota exhausted — switching to website scraping]")
        hunter_exhausted = True
        return None

    if resp.status_code != 200:
        return None

    emails = resp.json().get("data", {}).get("emails", [])
    if not emails:
        return None

    generic = {"info", "hello", "contact", "support", "admin", "office", "team"}
    named   = [e for e in emails if e.get("first_name") and e["value"].split("@")[0].lower() not in generic]
    best    = named[0] if named else emails[0]

    return {"email": best.get("value"), "first_name": best.get("first_name", ""), "last_name": best.get("last_name", "")}


# ── Step 2b: Website scraper fallback ────────────────────────────────────────

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

SKIP_DOMAINS = {
    "sentry.io", "sentry-next.wixpress.com", "wixpress.com",
    "wix.com", "squarespace.com", "example.com", "domain.com",
    "schema.org", "google.com", "facebook.com", "instagram.com",
    "yoursite.com", "yourdomain.com", "email.com",
}

# File extensions that appear in image/asset paths mismatched as emails
SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
                   ".pdf", ".css", ".js", ".woff", ".ttf"}

# TLDs that are never real email TLDs
FAKE_TLDS = {"jpg", "jpeg", "png", "gif", "svg", "webp", "ico", "pdf",
             "css", "js", "woff", "ttf", "xml", "json"}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", ""]


def is_valid_email(email: str) -> bool:
    """Return False for obviously fake/junk emails caught by the scraper."""
    email = email.strip().lstrip("%20").lstrip()  # strip URL-encoded spaces

    parts = email.lower().split("@")
    if len(parts) != 2:
        return False
    local, edomain = parts

    # Reject image/asset filenames in local part
    if any(local.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False

    # Reject hex hashes (Sentry IDs etc — 20+ hex chars)
    if re.fullmatch(r"[0-9a-f]{20,}", local):
        return False

    # Reject fake TLDs
    tld = edomain.rsplit(".", 1)[-1] if "." in edomain else ""
    if tld in FAKE_TLDS:
        return False

    # Reject malformed domains (e.g. "wellnessintegrative.commailing")
    # A valid TLD is 2–6 alpha chars
    if not re.fullmatch(r"[a-z]{2,6}", tld):
        return False

    # Reject known junk domains
    if any(skip in edomain for skip in SKIP_DOMAINS):
        return False

    return True


def clean_email(email: str) -> str:
    """Strip URL encoding and whitespace from a raw scraped email."""
    return email.strip().lstrip("%20").strip()


def scrape_email(website: str, domain: str) -> dict | None:
    """Try to find a real contact email on the business website."""
    if not website:
        return None

    base = website.rstrip("/")
    found_email = None

    for path in CONTACT_PATHS:
        url = base + path
        try:
            r = requests.get(url, headers=SCRAPE_HEADERS, timeout=8, allow_redirects=True)
            if r.status_code != 200:
                continue

            emails = EMAIL_RE.findall(r.text)
            for raw in emails:
                email = clean_email(raw)
                if not is_valid_email(email):
                    continue
                edomain = email.lower().split("@")[1]
                # Prefer email hosted on the same domain
                if domain.split(".")[0] in edomain or edomain == domain:
                    found_email = email
                    break
                if not found_email:
                    found_email = email

            if found_email:
                break

        except requests.RequestException:
            continue

        time.sleep(0.3)

    if not found_email:
        return None

    return {"email": found_email, "first_name": "", "last_name": ""}


# ── Step 2: Find email (Hunter → scrape fallback) ────────────────────────────

def find_email(domain: str, website: str) -> dict | None:
    result = find_email_hunter(domain)
    if result:
        return result
    return scrape_email(website, domain)


# ── Step 3: Push to GHL ──────────────────────────────────────────────────────

def push_to_ghl(contact: dict) -> str:
    payload = {
        "locationId":  GHL_LOCATION_ID,
        "email":       contact["email"],
        "firstName":   contact.get("first_name", ""),
        "lastName":    contact.get("last_name", ""),
        "phone":       contact.get("phone", ""),
        "companyName": contact.get("company", ""),
        "source":      "lead-gen-script",
        "tags":        contact.get("tags", []),
    }

    resp = requests.post(
        "https://services.leadconnectorhq.com/contacts/",
        headers=GHL_HEADERS, json=payload, timeout=15,
    )

    if resp.status_code in (200, 201):
        return "new"
    if resp.status_code == 400 and "duplicated" in resp.text.lower():
        return "exists"
    if resp.status_code == 422:
        resp2 = requests.post(
            "https://services.leadconnectorhq.com/contacts/upsert",
            headers=GHL_HEADERS, json=payload, timeout=15,
        )
        return "new" if resp2.status_code in (200, 201) else "failed"
    return "failed"


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    validate_env()

    print(f"\nSearching for med spa / wellness leads in: {TARGET_CITY}")
    print("=" * 60)

    seen_domains = set()
    leads        = []

    for term in SEARCH_TERMS:
        if len(leads) >= MAX_LEADS:
            break

        print(f"\nSearching: '{term}'...")
        places = search_places(term)
        print(f"  Found {len(places)} places")

        for place in places:
            if len(leads) >= MAX_LEADS:
                break

            place_id = place.get("place_id")
            name     = place.get("name", "Unknown")

            details = get_place_details(place_id)
            website = details.get("website", "")
            phone   = details.get("formatted_phone_number", "")
            domain  = extract_domain(website)

            if not domain or domain in seen_domains:
                continue
            seen_domains.add(domain)

            print(f"  [{len(leads)+1}] {name} — {domain}", end=" ", flush=True)

            email_info = find_email(domain, website)
            if not email_info:
                print("(no email found)")
                continue

            name_lower = name.lower()
            if "med spa" in name_lower or "medical spa" in name_lower or "dermatolog" in name_lower:
                tag = "med spa"
            elif "wellness" in name_lower:
                tag = "wellness"
            else:
                tag = "spa"

            lead = {
                "company":    name,
                "email":      email_info["email"],
                "first_name": email_info["first_name"],
                "last_name":  email_info["last_name"],
                "phone":      phone,
                "tags":       [tag, "email-warmup"],
                "source":     "lead-gen-script",
            }

            result = push_to_ghl(lead)
            if result == "new":
                status = "pushed to GHL"
                leads.append(lead)
            elif result == "exists":
                status = "already in GHL"
            else:
                status = "push failed"
            print(f"→ {email_info['email']} ({status})")
            time.sleep(0.4)

    print(f"""
======================================
  Done — {len(leads)} new leads added to GHL
======================================
Contacts tagged: niche + 'email-warmup'
(Existing contacts were skipped)

Next steps:
  GHL → Contacts → Smart Lists → + New Smart List
  Filter: Tags → Contains → email-warmup
  Name it: TEST - Email Warmup Segment 01
  Save → use in your email campaign
""")


if __name__ == "__main__":
    main()
