"""
Pydantic schemas for the /api endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Pillar(BaseModel):
    key: str
    name: str
    description: str = ""
    example_hooks: list[str] = []


class SlotIn(BaseModel):
    platform: str
    day_of_week: int
    time_local: str
    post_type: str = "post"
    pillar_hint: str = ""
    active: bool = True


class SlotUpdate(BaseModel):
    platform: str | None = None
    day_of_week: int | None = None
    time_local: str | None = None
    post_type: str | None = None
    pillar_hint: str | None = None
    active: bool | None = None


class SlotOut(SlotIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int


class BrandBase(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = ""
    batch_prompt_template: str = ""
    pillars: list[Pillar] = []
    platforms: list[str] = []
    ghl_account_ids: dict[str, str] = {}
    publisher: str = "native"
    tts_voice: str = "en-US-AndrewNeural"
    autonomy: str = "approval"
    auto_generate_enabled: bool = False
    auto_generate_day: str = "monday"
    auto_generate_time: str = "07:00"
    posts_per_batch: int = 5
    timezone: str = "America/New_York"


class BrandCreate(BrandBase):
    slug: str


class BrandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    batch_prompt_template: str | None = None
    pillars: list[Pillar] | None = None
    platforms: list[str] | None = None
    ghl_account_ids: dict[str, str] | None = None
    publisher: str | None = None
    tts_voice: str | None = None
    autonomy: str | None = None
    auto_generate_enabled: bool | None = None
    auto_generate_day: str | None = None
    auto_generate_time: str | None = None
    posts_per_batch: int | None = None
    timezone: str | None = None


class BrandOut(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    last_auto_generate_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    generation_run_id: int | None = None
    platform: str
    post_type: str
    format: str
    pillar: str
    hook: str
    caption: str
    raw_generated: str
    hashtags: str
    media_urls: list[str] = []
    status: str
    video_status: str = "none"
    video_path: str = ""
    video_error: str = ""
    scheduled_at: datetime | None = None
    posted_at: datetime | None = None
    ghl_post_id: str = ""
    error_message: str = ""
    created_at: datetime
    updated_at: datetime


class PostUpdate(BaseModel):
    platform: str | None = None
    post_type: str | None = None
    format: str | None = None
    pillar: str | None = None
    hook: str | None = None
    caption: str | None = None
    hashtags: str | None = None
    media_urls: list[str] | None = None
    scheduled_at: datetime | None = None


class ApproveRequest(BaseModel):
    scheduled_at: datetime | None = None


class GenerateRequest(BaseModel):
    count: int | None = None
    pillar: str | None = None
    platform: str | None = None
    format: str | None = None
    topic: str | None = None


class GenerationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    brand_id: int
    trigger: str
    params: dict
    model: str = ""
    status: str
    error: str = ""
    post_count: int
    created_at: datetime


class GHLAccount(BaseModel):
    id: str
    name: str = ""
    platform: str = ""


class DashboardOut(BaseModel):
    brand_id: int
    counts: dict[str, int]
    upcoming: list[PostOut]
    recent_failures: list[PostOut]
