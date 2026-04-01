"""
Lixen.AI Design Library — maps (category, platform) → list of image URLs.

Permanent URLs are hosted on GHL CDN (assets.cdn.filesafe.space) — no expiry.
Canva design IDs for re-export are in CANVA_DESIGN_IDS below.

To add more images after exporting from Canva:
  1. Run:  python media_uploader.py  (downloads Canva URLs, uploads to GHL CDN)
  2. Paste the printed permanent URLs into DESIGNS below.

To re-export all designs from Canva (requires CANVA_API_TOKEN in .env):
  python canva_generator.py --re-export pain_instagram
  python canva_generator.py --re-export education_facebook
  ... etc, then run media_uploader.py immediately after.

Designs generated: 2026-04-01 | Brand kit: kAG7Nh5iE2c (RennXAI Studio)
"""

import random

# Category name aliases → normalised key
CATEGORY_ALIASES: dict[str, str] = {
    "pain":             "pain",
    "pain agitation":   "pain",
    "education":        "education",
    "social proof":     "proof",
    "proof":            "proof",
    "offer":            "offer",
    "engagement":       "engagement",
}

# ── Design URL Library ────────────────────────────────────────────────────────
# Permanent GHL CDN URLs (assets.cdn.filesafe.space) never expire.
# Empty lists = no image yet — posts fall back to text-only gracefully.

DESIGNS: dict[tuple[str, str], list[str]] = {
    # ── Pain Agitation ────────────────────────────────────────────────────────
    ("pain", "instagram"): [
        # DAHFnLNKe04 — Every Missed Call
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/4237474b-419e-412a-9ad6-b5d1a7d885aa.jpg",
        # DAHFnMJ_rmc — Every Missed Call Is A Missed Booking
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/1790c099-28d8-4817-a18b-cb8b035899a9.jpg",
        # DAHFnA4DAgc — Every Missed Call (alt)
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/c6ebf7a2-9e1d-429b-b56b-f07dcbd3290c.jpg",
    ],
    ("pain", "facebook"): [],  # reuse instagram — handled by fallback
    ("pain", "tiktok"):   [],  # reuse instagram — handled by fallback

    # ── Education ─────────────────────────────────────────────────────────────
    ("education", "facebook"): [
        # DAHFnERvR58 — AI Front Desk Solutions
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/95840971-427c-4d64-af25-a34ec146608f.jpg",
        # DAHFnPT5_uE — How AI Enhances Your Front Desk
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/1cbb11e4-f1d4-4436-b7f0-5eee99f7e360.jpg",
        # DAHFnNU52sQ — How AI Handles Your Front Desk
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/e253d0d1-b5a2-49a4-9f78-80c670cd5966.jpg",
    ],
    ("education", "instagram"): [],  # reuse facebook — handled by fallback
    ("education", "tiktok"):    [],

    # ── Social Proof ──────────────────────────────────────────────────────────
    ("proof", "instagram"): [
        # DAHFnNXejyM — Zero Missed Calls
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/fc360560-57e2-4562-a11c-9315473ce587.jpg",
        # DAHFnD1qsKU — Transforming Communication
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/fd2c76d4-cbc2-41aa-b9b9-5d4a87bbdca1.jpg",
    ],
    ("proof", "facebook"): [],  # reuse instagram — handled by fallback
    ("proof", "tiktok"):   [],

    # ── Offer ─────────────────────────────────────────────────────────────────
    ("offer", "instagram"): [
        # DAHFnNQ5qCo — Unlock Your Potential (story)
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/9a5e149e-7e6f-4c5e-b372-6078f5331ee0.jpg",
        # DAHFnK_uyXY — Book Your Free Audit (story)
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/76b65fca-0be6-49f2-a42c-14e78fb9b71e.jpg",
    ],
    ("offer", "facebook"): [],  # reuse instagram — handled by fallback
    ("offer", "tiktok"):   [],

    # ── Engagement ────────────────────────────────────────────────────────────
    ("engagement", "instagram"): [
        # DAHFnASCh7I — Missed Calls?
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/a85ceb48-1289-4be4-916a-41538c2069f2.jpg",
        # DAHFnAI16O4 — Missed Calls Poll
        "https://assets.cdn.filesafe.space/C7e7ReTQ4FXMZp9TjxzU/media/2084e702-f878-4d54-8eb5-c591e80f4778.jpg",
    ],
    ("engagement", "facebook"): [],  # reuse instagram — handled by fallback
    ("engagement", "tiktok"):   [],
}

# ── Canva Design IDs for re-export ────────────────────────────────────────────
# Use these with `python canva_generator.py --re-export <design_id>` or
# via the Canva MCP export-design tool when URLs expire.

CANVA_DESIGN_IDS: dict[str, dict] = {
    "pain_instagram": {
        "v1": "DAHFnLNKe04",   # Every Missed Call
        "v2": "DAHFnMJ_rmc",   # Every Missed Call Is A Missed Booking
        "v3": "DAHFnLndafM",   # Missed Calls?
        "v4": "DAHFnA4DAgc",   # Every Missed Call Is A Missed Booking (alt)
    },
    "education_facebook": {
        "v1": "DAHFnERvR58",   # AI Front Desk Solutions
        "v2": "DAHFnCv6O4M",   # How AI Manages Your Front Desk
        "v3": "DAHFnPT5_uE",   # How AI Enhances Your Front Desk
        "v4": "DAHFnNU52sQ",   # How AI Handles Your Front Desk
    },
    "offer_story": {
        "v1": "DAHFnNQ5qCo",   # Unlock Your Potential
        "v2": "DAHFnKpPHmU",   # Book Your Free
        "v3": "DAHFnHsp2dg",   # Unlock Your Spa's Potential
        "v4": "DAHFnK_uyXY",   # Book Your Free Audit
    },
    "proof_instagram": {
        "v1": "DAHFnNXejyM",   # Zero Missed Calls
        "v2": "DAHFnD1qsKU",   # Transforming Communication
        "v3": "DAHFnMS7Jjw",   # Elevate Your Med Spa Experience
        "v4": "DAHFnLZ3j6Q",   # 40% of calls to zero
    },
    "engagement_instagram": {
        "v1": "DAHFnASCh7I",   # Missed Calls?
        "v2": "DAHFnAI16O4",   # Missed Calls Poll
        "v3": "DAHFnDXTe6g",   # Count them wisely
        "v4": "DAHFnDfe438",   # Missed Calls Inquiry
    },
}


def get_design_url(
    category: str,
    platform: str,
    strategy: str = "random",
) -> str | None:
    """
    Return a public image URL for a given content category and platform.

    Fallback chain:
      (category, platform) → (category, any available platform) → None

    Args:
        category:  raw category string from content_generator (case-insensitive)
                   e.g. "Pain Agitation", "pain", "Education", "Offer"
        platform:  "instagram" | "facebook" | "tiktok"
        strategy:  "random" rotates variants; "first" always returns first URL

    Returns:
        Public image URL string, or None if no images available.
    """
    cat = CATEGORY_ALIASES.get(category.lower().strip())
    if not cat:
        return None

    plat = platform.lower().strip()

    # Direct match
    urls = DESIGNS.get((cat, plat), [])

    # Fallback: try other platforms in this category
    if not urls:
        for fallback in ("instagram", "facebook", "tiktok"):
            if fallback != plat:
                urls = DESIGNS.get((cat, fallback), [])
                if urls:
                    break

    if not urls:
        return None

    return random.choice(urls) if strategy == "random" else urls[0]


def list_missing() -> list[tuple[str, str]]:
    """Return all (category, platform) pairs that have no image URLs."""
    return [(cat, plat) for (cat, plat), urls in DESIGNS.items() if not urls]


def list_available() -> list[tuple[str, str, int]]:
    """Return all (category, platform, count) tuples that have URLs."""
    return [(cat, plat, len(urls)) for (cat, plat), urls in DESIGNS.items() if urls]


if __name__ == "__main__":
    print("Available designs:")
    for cat, plat, count in list_available():
        print(f"  ({cat!r}, {plat!r}) — {count} variant(s)")

    missing = list_missing()
    if missing:
        print(f"\nMissing ({len(missing)} slots) — run canva_generator.py to fill:")
        for cat, plat in missing:
            if not any(
                get_design_url(cat, plat2, "first")
                for plat2 in ("instagram", "facebook", "tiktok")
                if plat2 != plat
            ):
                print(f"  ({cat!r}, {plat!r})  ← no fallback available")
