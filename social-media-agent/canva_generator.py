"""
Canva Design Generator — Lixen.AI Social Media Designs

Use this module as a reference for regenerating branded designs in a
Claude Code session that has the Canva MCP server connected.

Brand Kit: kAG7Nh5iE2c  (RennXAI Studio)
  - Primary: #0A0A0A (near-black), #FFFFFF
  - Accent:  #C8A96E (gold), #1A1A2E (deep navy)
  - Font: Playfair Display (headings), Inter (body)

── How to regenerate designs in a new Claude Code session ──────────────────
1. Ask Claude to use mcp__canva__generate-design with the prompts below
2. Export each via mcp__canva__export-design (format: "png")
3. Copy the export URL into design_library.py

── Generation prompts per category ─────────────────────────────────────────
"""

BRAND_KIT_ID = "kAG7Nh5iE2c"

GENERATION_PROMPTS: dict[str, dict] = {
    "pain_instagram": {
        "title": "Pain Agitation — Instagram Post",
        "prompt": (
            "Lixen.AI luxury med spa AI brand. Dark background #0A0A0A. "
            "Large bold hook text: 'Every Missed Call Is A Missed Booking.' "
            "Gold accent (#C8A96E) underline. Subtext: 'Your AI front desk never sleeps.' "
            "Bottom CTA: 'DM AUDIT' in gold pill button. "
            "Instagram square 1080×1080. Minimal luxury aesthetic."
        ),
        "format": "Instagram Post (Square)",
        "design_ids": ["dg-09578935", "dg-7c3a92b0", "dg-89f3b024", "dg-bce3254c"],
    },
    "education_facebook": {
        "title": "Education — Facebook Post",
        "prompt": (
            "Lixen.AI AI front desk explainer. Dark luxury #1A1A2E background. "
            "Headline: 'How AI Answers Your Calls, Books Appointments & Replies to DMs — 24/7.' "
            "3-step visual: 1. AI Answers → 2. Books Appointment → 3. You Get Paid. "
            "Gold step numbers. Clean sans-serif. Facebook 1200×628 landscape."
        ),
        "format": "Facebook Post (Landscape)",
        "design_ids": ["dg-0ad72fd6", "dg-68c99ece", "dg-8c052972", "dg-cee92b87"],
    },
    "offer_instagram_story": {
        "title": "Offer — Instagram Story",
        "prompt": (
            "Lixen.AI free AI audit offer. Full bleed dark background. "
            "Large centered text: 'Book Your Free AI Audit.' "
            "Gold subtext: 'See exactly what your med spa is missing.' "
            "Urgency line: 'Limited spots this month.' "
            "CTA button: 'DM AUDIT' gold pill. Instagram Story 1080×1920."
        ),
        "format": "Instagram Story",
        "design_ids": ["dg-4ab30ccd", "dg-4ded80d7", "dg-66259ea4", "dg-9790a262"],
    },
    "proof_instagram": {
        "title": "Social Proof — Instagram Post",
        "prompt": (
            "Lixen.AI client result. Dark luxury card design. "
            "Pull quote: '\"We went from missing 40% of calls to zero missed calls in week one.\"' "
            "— Med Spa Owner, Miami. Gold quotation marks. "
            "Bottom: Lixen.AI logo + 'AI Operating System for Med Spas'. "
            "Instagram square 1080×1080."
        ),
        "format": "Instagram Post (Square)",
        "design_ids": [],  # not yet generated — run generate-design to create
    },
    "engagement_instagram": {
        "title": "Engagement — Instagram Post",
        "prompt": (
            "Lixen.AI engagement poll visual. Dark background. "
            "Bold question: 'How many calls does your spa miss per week?' "
            "4 answer options in gold-bordered boxes: 0-5 / 5-15 / 15-30 / 30+. "
            "Subtext: 'Comment your number below 👇' "
            "Instagram square 1080×1080. Warm luxury feel."
        ),
        "format": "Instagram Post (Square)",
        "design_ids": [],  # not yet generated
    },
    "pain_tiktok": {
        "title": "Pain Agitation — TikTok / Reel",
        "prompt": (
            "Lixen.AI TikTok video thumbnail / cover. Vertical 1080×1920. "
            "Dark background. Bold white text at top: 'POV: Your med spa just missed another call.' "
            "Center: phone ringing animation placeholder or static missed call screen. "
            "Bottom gold text: 'There's a fix for that. → lixen.ai'"
        ),
        "format": "TikTok Video Cover",
        "design_ids": [],  # not yet generated
    },
}


def print_generation_guide():
    """Print a guide for regenerating all designs in a Canva MCP session."""
    print("Lixen.AI Canva Design Generation Guide")
    print(f"Brand Kit ID: {BRAND_KIT_ID}\n")
    for key, cfg in GENERATION_PROMPTS.items():
        print(f"[{key}]")
        print(f"  Title:  {cfg['title']}")
        print(f"  Format: {cfg['format']}")
        if cfg["design_ids"]:
            print(f"  Existing IDs: {', '.join(cfg['design_ids'])}")
        else:
            print("  Status: needs generation")
        print(f"  Prompt: {cfg['prompt'][:100]}...")
        print()


if __name__ == "__main__":
    print_generation_guide()
