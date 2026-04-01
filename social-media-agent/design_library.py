"""
Lixen.AI Design Library — maps (category, platform) → list of Canva export URLs.

⚠️  URL EXPIRY: Canva signed export URLs expire ~18-24 hours after generation.
    To refresh expired URLs, run: python canva_generator.py --re-export
    Or export manually from Canva using the design IDs in CANVA_DESIGN_IDS below.

    For permanent URLs: download the JPGs and re-upload to Cloudflare R2 / S3,
    then replace the entries here with your CDN URLs.

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
# Each entry is a list of URLs so get_design_url() can rotate through variants.
# Canva design IDs are stored in CANVA_DESIGN_IDS below for re-export.

DESIGNS: dict[tuple[str, str], list[str]] = {
    # ── Pain Agitation ────────────────────────────────────────────────────────
    ("pain", "instagram"): [
        # DAHFnLNKe04 — "Instagram Post - Every Missed Call"
        "https://export-download.canva.com/NKe04/DAHFnLNKe04/-1/0/0001-4734907859747627840.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260331%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260331T194206Z&X-Amz-Expires=64438&X-Amz-Signature=f991cbacb72b661fdbb4459f4db857b19a7a1b2105bb69e8990db4388cd51eef&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A36%3A04%20GMT",
        # DAHFnMJ_rmc — "Instagram Post - Every Missed Call Is A Missed Booking"
        "https://export-download.canva.com/J_rmc/DAHFnMJ_rmc/-1/0/0001-4572778270711675598.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260401%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260401T080916Z&X-Amz-Expires=19814&X-Amz-Signature=3c0d0e2f3a9c0229f98a033d92a6b3a8f5e217f1dba1c4f14c517fc230a6ce9d&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A39%3A30%20GMT",
        # DAHFnA4DAgc — "Instagram Post - Every Missed Call Is A Missed Booking" (v4)
        "https://export-download.canva.com/4DAgc/DAHFnA4DAgc/-1/0/0001-5454357898741564586.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260401%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260401T015937Z&X-Amz-Expires=42210&X-Amz-Signature=7252d8f50d257b4da72196f3560c3c3027088140ef84940a1329c93aecf1899c&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A43%3A07%20GMT",
    ],
    ("pain", "facebook"):  [],  # reuse instagram — handled by fallback in get_design_url
    ("pain", "tiktok"):    [],  # reuse instagram — handled by fallback

    # ── Education ─────────────────────────────────────────────────────────────
    ("education", "facebook"): [
        # DAHFnERvR58 — "Facebook Post - AI Front Desk Solutions"
        "https://export-download.canva.com/RvR58/DAHFnERvR58/-1/0/0001-2278194260842326663.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260401%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260401T074513Z&X-Amz-Expires=20731&X-Amz-Signature=242537183b44b661160c953de9db7d86150bc5fe29bc6a0cc8431a43bde255b1&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A30%3A44%20GMT",
        # DAHFnPT5_uE — "Facebook Post - How AI Enhances Your Front Desk"
        "https://export-download.canva.com/T5_uE/DAHFnPT5_uE/-1/0/0001-3323029375991390667.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260401%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260401T093626Z&X-Amz-Expires=15171&X-Amz-Signature=8d8d0fb709fd7866510accb174b3548f76f282d9fedf746c9a7090c9a2cd0d88&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A49%3A17%20GMT",
        # DAHFnNU52sQ — "Facebook Post - How AI Handles Your Front Desk"
        "https://export-download.canva.com/U52sQ/DAHFnNU52sQ/-1/0/0001-676038693658310113.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260401%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260401T114424Z&X-Amz-Expires=6933&X-Amz-Signature=611dfb85470a07516290c1795ff4806e2942662094c228ce40f7948a3999bd47&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A39%3A57%20GMT",
    ],
    ("education", "instagram"): [],  # reuse facebook variant — handled by fallback
    ("education", "tiktok"):    [],

    # ── Social Proof ──────────────────────────────────────────────────────────
    ("proof", "instagram"):  [],  # TODO: generate via canva_generator.py prompts
    ("proof", "facebook"):   [],
    ("proof", "tiktok"):     [],

    # ── Offer ─────────────────────────────────────────────────────────────────
    ("offer", "instagram"): [
        # DAHFnNQ5qCo — "Your Story - Unlock Your Potential"
        "https://export-download.canva.com/Q5qCo/DAHFnNQ5qCo/-1/0/0001-5127846928036691178.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260331%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260331T232246Z&X-Amz-Expires=51516&X-Amz-Signature=df17c42936b7a43a1abc19b5e2b853c15146187bca061229aaf8e2acb6aadf02&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A41%3A22%20GMT",
        # DAHFnK_uyXY — "Your Story - Book Your Free Audit"
        "https://export-download.canva.com/_uyXY/DAHFnK_uyXY/-1/0/0001-8693571931490947491.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAQYCGKMUH5AO7UJ26%2F20260401%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260401T054423Z&X-Amz-Expires=27333&X-Amz-Signature=dd41f615d180cb4f37b3fd01941339d475fde2b973edec7287a5b00f66e511bd&X-Amz-SignedHeaders=host%3Bx-amz-expected-bucket-owner&response-expires=Wed%2C%2001%20Apr%202026%2013%3A19%3A56%20GMT",
    ],
    ("offer", "facebook"): [],  # reuse instagram story — handled by fallback
    ("offer", "tiktok"):   [],

    # ── Engagement ────────────────────────────────────────────────────────────
    ("engagement", "instagram"): [],  # TODO: generate via canva_generator.py prompts
    ("engagement", "facebook"):  [],
    ("engagement", "tiktok"):    [],
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
