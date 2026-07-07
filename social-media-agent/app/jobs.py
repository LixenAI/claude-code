"""
APScheduler background jobs, started from the FastAPI lifespan:

  publish_due_posts     — every 60s: push scheduled posts whose time has come
  render_queued_videos  — every 30s: render one queued short video at a time
  auto_generate_batches — every 15min: fire each brand's weekly batch
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app import models
from app.db import SessionLocal

log = logging.getLogger("jobs")

MISSED_WINDOW_HOURS = 24
DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def publish_due_posts() -> None:
    from app.services.publishing import publish_post

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due = (
            db.query(models.Post)
            .filter(
                models.Post.status == models.SCHEDULED,
                models.Post.scheduled_at != None,  # noqa: E711
                models.Post.scheduled_at <= now,
            )
            .all()
        )
        for post in due:
            scheduled_at = post.scheduled_at
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            if scheduled_at < now - timedelta(hours=MISSED_WINDOW_HOURS):
                post.status = models.FAILED
                post.error_message = "Missed posting window (server was down >24h past the slot)"
                db.commit()
                continue
            # don't auto-publish a reel whose video hasn't rendered yet;
            # give the renderer a grace period, then send caption-only/manual
            if (
                post.video_status in (models.VIDEO_QUEUED, models.VIDEO_RENDERING)
                and scheduled_at > now - timedelta(minutes=30)
            ):
                continue
            post.status = models.PUBLISHING
            db.commit()
            log.info("Publishing post %s (%s/%s)", post.id, post.brand.slug, post.platform)
            publish_post(db, post)
    except Exception:
        log.exception("publish_due_posts crashed")
        db.rollback()
    finally:
        db.close()


def render_queued_videos() -> None:
    from app.services.video_generator import render_video

    db = SessionLocal()
    try:
        # one at a time — rendering is CPU-heavy
        if db.query(models.Post).filter(models.Post.video_status == models.VIDEO_RENDERING).count():
            return
        post = (
            db.query(models.Post)
            .filter(
                models.Post.video_status == models.VIDEO_QUEUED,
                models.Post.status.notin_([models.REJECTED]),
            )
            .order_by(models.Post.scheduled_at.isnot(None).desc(), models.Post.scheduled_at)
            .first()
        )
        if post is None:
            return
        post.video_status = models.VIDEO_RENDERING
        db.commit()
        log.info("Rendering video for post %s", post.id)
        try:
            rel_path = render_video(post, post.brand)
            post.video_path = rel_path
            post.video_status = models.VIDEO_READY
            post.video_error = ""
        except Exception as e:  # noqa: BLE001 — record render failure on the row
            post.video_status = models.VIDEO_FAILED
            post.video_error = str(e)[:2000]
            log.exception("Video render failed for post %s", post.id)
        db.commit()
    except Exception:
        log.exception("render_queued_videos crashed")
        db.rollback()
    finally:
        db.close()


def auto_generate_batches() -> None:
    from app.services.generation import execute_generation_run, start_generation_run

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        for brand in db.query(models.Brand).filter_by(auto_generate_enabled=True).all():
            try:
                from zoneinfo import ZoneInfo
                local_now = now.astimezone(ZoneInfo(brand.timezone or "UTC"))
            except Exception:
                local_now = now

            target_day = DAY_NAMES.index((brand.auto_generate_day or "monday").lower())
            if local_now.weekday() != target_day:
                continue
            hour, minute = (int(x) for x in (brand.auto_generate_time or "07:00").split(":"))
            fire_at = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if local_now < fire_at:
                continue

            last = brand.last_auto_generate_at
            if last is not None:
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                if now - last < timedelta(days=6):
                    continue

            brand.last_auto_generate_at = now
            run = start_generation_run(db, brand, {}, trigger="auto")
            db.commit()
            log.info("Auto-generating weekly batch for %s (run %s)", brand.slug, run.id)
            execute_generation_run(run.id)
    except Exception:
        log.exception("auto_generate_batches crashed")
        db.rollback()
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(publish_due_posts, "interval", seconds=60, max_instances=1, coalesce=True)
    scheduler.add_job(render_queued_videos, "interval", seconds=30, max_instances=1, coalesce=True)
    scheduler.add_job(auto_generate_batches, "interval", minutes=15, max_instances=1, coalesce=True)
    return scheduler
