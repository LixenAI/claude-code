"""
Publishing orchestration: compose the final caption, route to the
brand's driver, and record the outcome on the post row.

Outcomes:
  posted  — driver confirmed the post went out (or landed in TikTok inbox)
  ready   — no credentials / manual mode: content + video are rendered,
            user posts by hand from the dashboard and hits "mark posted"
  failed  — driver had credentials but the attempt errored
"""

import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import models
from app.services.publishers import MissingCredentials, PublishError
from app.services.publishers.ghl import publish_ghl
from app.services.publishers.native import publish_instagram, publish_tiktok
from app.services.video_generator import media_root

PLATFORM_LIMITS = {"facebook": 63206, "instagram": 2200, "tiktok": 2200}


def compose_caption(post: models.Post) -> str:
    parts = [post.caption.strip()]
    if post.hashtags.strip():
        parts.append(post.hashtags.strip())
    text = "\n\n".join(p for p in parts if p)
    limit = PLATFORM_LIMITS.get(post.platform, 2200)
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def _video_abs_path(post: models.Post) -> str | None:
    if post.video_status == models.VIDEO_READY and post.video_path:
        abs_path = os.path.join(os.path.dirname(media_root()), post.video_path)
        if os.path.exists(abs_path):
            return abs_path
    return None


def _dry_run() -> bool:
    return os.environ.get("PUBLISH_DRY_RUN", os.environ.get("GHL_DRY_RUN", "")) == "1"


def publish_post(db: Session, post: models.Post) -> models.Post:
    """Publish (or hand off) a single post. Sets status and commits."""
    brand = post.brand
    caption = compose_caption(post)
    video_abs = _video_abs_path(post)

    if _dry_run():
        print(f"[publish DRY RUN] {brand.slug}/{post.platform} post {post.id}: {caption[:80]!r} video={bool(video_abs)}")
        post.status = models.POSTED
        post.posted_at = datetime.now(timezone.utc)
        post.ghl_post_id = "dry_run"
        db.commit()
        return post

    try:
        if brand.publisher == models.PUBLISHER_MANUAL:
            raise MissingCredentials("manual publishing mode")

        if brand.publisher == models.PUBLISHER_GHL:
            video_url = None
            if video_abs and os.environ.get("PUBLIC_BASE_URL"):
                video_url = f"{os.environ['PUBLIC_BASE_URL'].rstrip('/')}/{post.video_path}"
            result = publish_ghl(caption, post.platform, brand.ghl_account_ids or {}, video_url, post.media_urls or [])
        elif post.platform == "instagram":
            result = publish_instagram(caption, post.video_path if video_abs else None, post.media_urls or [])
        elif post.platform == "tiktok":
            result = publish_tiktok(caption, video_abs)
        else:
            raise MissingCredentials(f"No native driver for platform '{post.platform}'")

        post.status = models.POSTED
        post.posted_at = datetime.now(timezone.utc)
        post.ghl_post_id = str(result.get("platform_post_id", ""))
        note = result.get("note", "")
        post.error_message = note  # informational (e.g. TikTok inbox draft)
    except MissingCredentials as e:
        # Not an error: content is ready, user posts manually from dashboard
        post.status = models.READY
        post.error_message = f"Manual posting: {e}"
    except (PublishError, Exception) as e:  # noqa: BLE001 — record any failure on the row
        post.status = models.FAILED
        post.error_message = str(e)[:2000]

    db.commit()
    return post
