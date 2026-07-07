"""
Slot math: turn a brand's recurring schedule_slots into concrete UTC
datetimes, and auto-assign approved posts to the next free slot.
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import models


def _local_now(brand: models.Brand) -> datetime:
    try:
        tz = ZoneInfo(brand.timezone or "UTC")
    except Exception:
        tz = timezone.utc
    return datetime.now(tz)


def _slot_occurrence(slot: models.ScheduleSlot, base_local: datetime) -> datetime:
    """Next occurrence of `slot` at or after base_local (same tz). Returns UTC."""
    hour, minute = (int(x) for x in slot.time_local.split(":"))
    days_ahead = (slot.day_of_week - base_local.weekday()) % 7
    candidate = (base_local + timedelta(days=days_ahead)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate <= base_local:
        candidate += timedelta(days=7)
    return candidate.astimezone(timezone.utc)


def _is_taken(db: Session, brand_id: int, when_utc: datetime) -> bool:
    return (
        db.query(models.Post)
        .filter(
            models.Post.brand_id == brand_id,
            models.Post.scheduled_at == when_utc,
            models.Post.status.in_([models.SCHEDULED, models.PUBLISHING, models.POSTED, models.READY]),
        )
        .count()
        > 0
    )


def next_slot_for(
    db: Session,
    brand: models.Brand,
    platform: str,
    pillar: str = "",
    max_weeks: int = 8,
) -> datetime | None:
    """
    Next free slot (UTC) for this brand+platform. Prefers slots whose
    pillar_hint matches the post's pillar; falls back to any platform slot.
    """
    slots = [s for s in brand.slots if s.active and s.platform == platform]
    if not slots:
        return None

    preferred = [s for s in slots if pillar and s.pillar_hint == pillar] or slots
    base_local = _local_now(brand)

    for week in range(max_weeks):
        occurrences = sorted(
            _slot_occurrence(s, base_local + timedelta(weeks=week)) for s in preferred
        )
        for when in occurrences:
            if not _is_taken(db, brand.id, when):
                return when
        # widen to all slots after the first pass on preferred ones
        preferred = slots
    return None


def auto_assign(db: Session, post: models.Post) -> datetime:
    """
    Assign scheduled_at from the brand's slot calendar. Falls back to
    tomorrow 18:00 brand-local when no slots exist.
    """
    brand = post.brand
    when = next_slot_for(db, brand, post.platform, pillar=post.pillar)
    if when is None:
        local = _local_now(brand)
        when = (local + timedelta(days=1)).replace(
            hour=18, minute=0, second=0, microsecond=0
        ).astimezone(timezone.utc)
    post.scheduled_at = when
    return when
