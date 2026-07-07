"""
Idempotent brand seeding. Upserts by slug; existing rows are only
back-filled where empty so UI edits are never clobbered.
"""

import os

from sqlalchemy.orm import Session

from app import models
from app.prompts.rennewme import (
    RENNEWME_BATCH_TEMPLATE,
    RENNEWME_PILLARS,
    RENNEWME_SLOTS,
    RENNEWME_SYSTEM_PROMPT,
)


def _lixen_brand_data() -> dict:
    from content_generator import SYSTEM_PROMPT, WEEKLY_BATCH_PROMPT
    from social_poster import ACCOUNT_IDS

    return {
        "slug": "lixen-ai",
        "name": "Lixen.AI",
        "description": "AI front desk for med spas — direct-response B2B content.",
        "system_prompt": SYSTEM_PROMPT,
        "batch_prompt_template": WEEKLY_BATCH_PROMPT,
        "pillars": [
            {"key": "pain", "name": "Pain Agitation", "description": "Make them feel the cost of missed calls", "example_hooks": []},
            {"key": "education", "name": "Education", "description": "Explain AI front desk simply, no jargon", "example_hooks": []},
            {"key": "proof", "name": "Social Proof", "description": "Results, demos, case studies, before/after", "example_hooks": []},
            {"key": "offer", "name": "Offer", "description": "Smart/Pro plans, discovery call CTA, urgency", "example_hooks": []},
            {"key": "engagement", "name": "Engagement", "description": "Polls, questions, relatable scenarios", "example_hooks": []},
        ],
        "platforms": ["facebook", "instagram", "tiktok"],
        "ghl_account_ids": dict(ACCOUNT_IDS),
        "publisher": models.PUBLISHER_GHL,
        "autonomy": models.AUTONOMY_AUTO,
        # Off by default: existing CLI/webhook flows keep handling Lixen
        # until the user enables the new pipeline in Brand Settings.
        "auto_generate_enabled": False,
        "posts_per_batch": 5,
    }


def _rennewme_brand_data() -> dict:
    return {
        "slug": "rennewme",
        "name": "@rennewme",
        "description": "Personal brand: getting unstuck + AI leverage for self-renewal. Growth phase — no selling.",
        "system_prompt": RENNEWME_SYSTEM_PROMPT,
        "batch_prompt_template": RENNEWME_BATCH_TEMPLATE,
        "pillars": RENNEWME_PILLARS,
        "platforms": ["instagram", "tiktok"],
        "ghl_account_ids": {},
        "publisher": models.PUBLISHER_NATIVE,
        "tts_voice": os.environ.get("RENNEWME_TTS_VOICE", "en-US-AndrewNeural"),
        "autonomy": models.AUTONOMY_APPROVAL,
        "auto_generate_enabled": True,
        "auto_generate_day": "monday",
        "auto_generate_time": "07:00",
        "posts_per_batch": 9,
    }


def _upsert_brand(db: Session, data: dict, slots: list[dict] | None = None) -> models.Brand:
    brand = db.query(models.Brand).filter_by(slug=data["slug"]).first()
    if brand is None:
        brand = models.Brand(**data)
        db.add(brand)
        db.flush()
    else:
        # Back-fill only fields that are still empty
        for key, value in data.items():
            if key == "slug":
                continue
            current = getattr(brand, key, None)
            if current in (None, "", [], {}):
                setattr(brand, key, value)

    if slots and not db.query(models.ScheduleSlot).filter_by(brand_id=brand.id).count():
        for slot in slots:
            db.add(models.ScheduleSlot(brand_id=brand.id, **slot))
    return brand


def seed_brands(db: Session) -> None:
    _upsert_brand(db, _lixen_brand_data())
    _upsert_brand(db, _rennewme_brand_data(), slots=RENNEWME_SLOTS)
    db.commit()
