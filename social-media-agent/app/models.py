"""
ORM models: brands, posts, generation_runs, schedule_slots.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# Post status lifecycle
DRAFT = "draft"
PENDING_APPROVAL = "pending_approval"
APPROVED = "approved"
SCHEDULED = "scheduled"
PUBLISHING = "publishing"
POSTED = "posted"
FAILED = "failed"
REJECTED = "rejected"
READY = "ready"  # rendered + due, awaiting manual publish (no API creds / manual mode)

POST_STATUSES = [DRAFT, PENDING_APPROVAL, APPROVED, SCHEDULED, PUBLISHING, POSTED, FAILED, REJECTED, READY]

# Brand autonomy modes
AUTONOMY_APPROVAL = "approval"
AUTONOMY_AUTO = "auto"

# Publisher drivers
PUBLISHER_NATIVE = "native"  # Instagram Graph API + TikTok Content Posting API
PUBLISHER_MANUAL = "manual"  # render everything, user posts by hand from dashboard
PUBLISHER_GHL = "ghl"        # legacy GoHighLevel Social Planner

# Video render states
VIDEO_NONE = "none"
VIDEO_QUEUED = "queued"
VIDEO_RENDERING = "rendering"
VIDEO_READY = "ready"
VIDEO_FAILED = "failed"


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    batch_prompt_template: Mapped[str] = mapped_column(Text, default="")
    pillars: Mapped[list] = mapped_column(JSON, default=list)
    platforms: Mapped[list] = mapped_column(JSON, default=list)
    ghl_account_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    publisher: Mapped[str] = mapped_column(String(16), default=PUBLISHER_NATIVE)
    tts_voice: Mapped[str] = mapped_column(String(64), default="en-US-AndrewNeural")
    autonomy: Mapped[str] = mapped_column(String(16), default=AUTONOMY_APPROVAL)
    auto_generate_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_generate_day: Mapped[str] = mapped_column(String(16), default="monday")
    auto_generate_time: Mapped[str] = mapped_column(String(8), default="07:00")
    posts_per_batch: Mapped[int] = mapped_column(Integer, default=5)
    timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    last_auto_generate_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    slots: Mapped[list["ScheduleSlot"]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    generation_run_id: Mapped[int | None] = mapped_column(ForeignKey("generation_runs.id"), nullable=True)
    platform: Mapped[str] = mapped_column(String(32))
    post_type: Mapped[str] = mapped_column(String(16), default="post")  # post | reel | story
    format: Mapped[str] = mapped_column(String(32), default="caption")  # reel_script | carousel | caption | quote_image | story
    pillar: Mapped[str] = mapped_column(String(64), default="")
    hook: Mapped[str] = mapped_column(Text, default="")
    caption: Mapped[str] = mapped_column(Text, default="")
    raw_generated: Mapped[str] = mapped_column(Text, default="")
    hashtags: Mapped[str] = mapped_column(Text, default="")
    media_urls: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default=PENDING_APPROVAL, index=True)
    video_status: Mapped[str] = mapped_column(String(16), default=VIDEO_NONE, index=True)
    video_path: Mapped[str] = mapped_column(String(512), default="")
    video_error: Mapped[str] = mapped_column(Text, default="")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ghl_post_id: Mapped[str] = mapped_column(String(128), default="")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    brand: Mapped["Brand"] = relationship(back_populates="posts")
    generation_run: Mapped["GenerationRun | None"] = relationship(back_populates="posts")


class GenerationRun(Base):
    __tablename__ = "generation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(16), default="manual")  # manual | auto | webhook
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    prompt_used: Mapped[str] = mapped_column(Text, default="")
    raw_output: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16), default="running")  # running | done | failed
    error: Mapped[str] = mapped_column(Text, default="")
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    posts: Mapped[list["Post"]] = relationship(back_populates="generation_run")


class ScheduleSlot(Base):
    __tablename__ = "schedule_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), index=True)
    platform: Mapped[str] = mapped_column(String(32))
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Monday .. 6=Sunday
    time_local: Mapped[str] = mapped_column(String(8))  # "18:00"
    post_type: Mapped[str] = mapped_column(String(16), default="post")
    pillar_hint: Mapped[str] = mapped_column(String(64), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    brand: Mapped["Brand"] = relationship(back_populates="slots")
