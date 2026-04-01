"""
Lixen.AI Design Library — maps (category, platform) → Canva export URL.

To populate image URLs:
  1. Open Canva and export each design as PNG (Share → Download → PNG)
  2. Upload to a public CDN (Cloudflare R2, S3, or paste the Canva share link)
  3. Replace the None values below with the public image URL strings

Canva designs were generated with brand kit kAG7Nh5iE2c (RennXAI Studio).
Design edit links are stored in canva_generator.py.

Category keys (lowercase):
  pain, education, proof, offer, engagement

Platform keys (lowercase):
  instagram, facebook, tiktok
"""

# fmt: off
DESIGNS: dict[tuple[str, str], str | None] = {
    # ── Pain Agitation ────────────────────────────────────────────────────
    ("pain", "instagram"):      None,  # export dg-09578935 → paste URL here
    ("pain", "facebook"):       None,  # export dg-0ad72fd6 → paste URL here
    ("pain", "tiktok"):         None,  # reuse instagram pain design

    # ── Education ─────────────────────────────────────────────────────────
    ("education", "instagram"): None,  # export dg-68c99ece → paste URL here
    ("education", "facebook"):  None,  # export dg-68c99ece or dg-8c052972
    ("education", "tiktok"):    None,  # reuse instagram education design

    # ── Social Proof ──────────────────────────────────────────────────────
    ("proof", "instagram"):     None,  # generate + export via canva_generator.py
    ("proof", "facebook"):      None,
    ("proof", "tiktok"):        None,

    # ── Offer ─────────────────────────────────────────────────────────────
    ("offer", "instagram"):     None,  # export dg-4ab30ccd (story) → paste URL
    ("offer", "facebook"):      None,  # export dg-4ded80d7 → paste URL here
    ("offer", "tiktok"):        None,

    # ── Engagement ────────────────────────────────────────────────────────
    ("engagement", "instagram"): None,  # generate + export via canva_generator.py
    ("engagement", "facebook"):  None,
    ("engagement", "tiktok"):    None,
}
# fmt: on

# Canva design IDs for reference (from generation session 2026-04-01)
CANVA_DESIGN_IDS = {
    "instagram_pain_1": "dg-09578935",
    "instagram_pain_2": "dg-7c3a92b0",
    "instagram_pain_3": "dg-89f3b024",
    "instagram_pain_4": "dg-bce3254c",
    "facebook_education_1": "dg-0ad72fd6",
    "facebook_education_2": "dg-68c99ece",
    "facebook_education_3": "dg-8c052972",
    "facebook_education_4": "dg-cee92b87",
    "instagram_story_offer_1": "dg-4ab30ccd",
    "instagram_story_offer_2": "dg-4ded80d7",
    "instagram_story_offer_3": "dg-66259ea4",
    "instagram_story_offer_4": "dg-9790a262",
}


def get_design_url(category: str, platform: str) -> str | None:
    """
    Return the image URL for a given content category and platform.

    Falls back: (category, platform) → (category, instagram) → None

    Args:
        category: "pain" | "education" | "proof" | "offer" | "engagement"
        platform: "instagram" | "facebook" | "tiktok"

    Returns:
        Public image URL string, or None if not yet populated.
    """
    cat = category.lower().strip()
    plat = platform.lower().strip()

    # Direct match
    url = DESIGNS.get((cat, plat))
    if url:
        return url

    # Fallback: try instagram variant (works for tiktok reuse)
    url = DESIGNS.get((cat, "instagram"))
    if url:
        return url

    return None


def list_missing() -> list[tuple[str, str]]:
    """Return all (category, platform) pairs that still need an image URL."""
    return [(cat, plat) for (cat, plat), url in DESIGNS.items() if url is None]


if __name__ == "__main__":
    missing = list_missing()
    if missing:
        print(f"Missing image URLs ({len(missing)}):")
        for cat, plat in missing:
            print(f"  ({cat!r}, {plat!r})")
    else:
        print("All design URLs populated.")
