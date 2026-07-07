"""Content queue: list/edit posts, approve/reject/regenerate, publish, render video."""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.services.publishing import publish_post
from app.services.scheduling import auto_assign

router = APIRouter(prefix="/api", tags=["posts"])

EDITABLE_STATUSES = [models.DRAFT, models.PENDING_APPROVAL, models.APPROVED, models.SCHEDULED, models.READY, models.FAILED]


def _get_post(db: Session, post_id: int) -> models.Post:
    post = db.get(models.Post, post_id)
    if post is None:
        raise HTTPException(404, "Post not found")
    return post


@router.get("/posts", response_model=list[schemas.PostOut])
def list_posts(
    brand_id: int | None = None,
    status: str | None = None,
    platform: str | None = None,
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    q = db.query(models.Post)
    if brand_id:
        q = q.filter(models.Post.brand_id == brand_id)
    if status:
        q = q.filter(models.Post.status.in_(status.split(",")))
    if platform:
        q = q.filter(models.Post.platform == platform)
    if from_:
        q = q.filter(models.Post.scheduled_at >= from_)
    if to:
        q = q.filter(models.Post.scheduled_at <= to)
    return q.order_by(models.Post.created_at.desc()).limit(limit).all()


@router.get("/posts/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    return _get_post(db, post_id)


@router.patch("/posts/{post_id}", response_model=schemas.PostOut)
def update_post(post_id: int, body: schemas.PostUpdate, db: Session = Depends(get_db)):
    post = _get_post(db, post_id)
    if post.status not in EDITABLE_STATUSES:
        raise HTTPException(409, f"Post in status '{post.status}' cannot be edited")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(post, key, value)
    db.commit()
    return post


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = _get_post(db, post_id)
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/approve", response_model=schemas.PostOut)
def approve_post(post_id: int, body: schemas.ApproveRequest, db: Session = Depends(get_db)):
    post = _get_post(db, post_id)
    if post.status not in (models.DRAFT, models.PENDING_APPROVAL, models.APPROVED, models.FAILED):
        raise HTTPException(409, f"Post in status '{post.status}' cannot be approved")
    if body.scheduled_at:
        post.scheduled_at = body.scheduled_at
    elif not post.scheduled_at:
        auto_assign(db, post)
    post.status = models.SCHEDULED
    post.error_message = ""
    # queue the video render if the script exists but hasn't rendered yet
    if post.format == "reel_script" and post.video_status in (models.VIDEO_NONE, models.VIDEO_FAILED):
        post.video_status = models.VIDEO_QUEUED
    db.commit()
    return post


@router.post("/posts/{post_id}/reject", response_model=schemas.PostOut)
def reject_post(post_id: int, db: Session = Depends(get_db)):
    post = _get_post(db, post_id)
    post.status = models.REJECTED
    db.commit()
    return post


@router.post("/posts/{post_id}/regenerate", response_model=schemas.GenerationRunOut, status_code=202)
def regenerate_post(post_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    """Reject this post and start a fresh single-post run with the same parameters."""
    from app.services.generation import execute_generation_run, start_generation_run

    post = _get_post(db, post_id)
    post.status = models.REJECTED
    params = {
        "count": 1,
        "pillar": post.pillar,
        "platform": post.platform,
        "format": post.format,
    }
    run = start_generation_run(db, post.brand, params, trigger="manual")
    background.add_task(execute_generation_run, run.id)
    return run


@router.post("/posts/{post_id}/publish-now", response_model=schemas.PostOut)
def publish_now(post_id: int, db: Session = Depends(get_db)):
    post = _get_post(db, post_id)
    if post.status == models.POSTED:
        raise HTTPException(409, "Post already published")
    post.status = models.PUBLISHING
    db.commit()
    return publish_post(db, post)


@router.post("/posts/{post_id}/retry", response_model=schemas.PostOut)
def retry_post(post_id: int, db: Session = Depends(get_db)):
    post = _get_post(db, post_id)
    if post.status != models.FAILED:
        raise HTTPException(409, "Only failed posts can be retried")
    post.status = models.SCHEDULED
    post.error_message = ""
    if not post.scheduled_at:
        auto_assign(db, post)
    db.commit()
    return post


@router.post("/posts/{post_id}/mark-posted", response_model=schemas.PostOut)
def mark_posted(post_id: int, db: Session = Depends(get_db)):
    """Manual flow: user posted it by hand, record it as done."""
    from datetime import timezone

    post = _get_post(db, post_id)
    post.status = models.POSTED
    post.posted_at = datetime.now(timezone.utc)
    post.error_message = ""
    db.commit()
    return post


@router.post("/posts/{post_id}/render-video", response_model=schemas.PostOut, status_code=202)
def render_video(post_id: int, db: Session = Depends(get_db)):
    """Queue (or re-queue) the short-video render for this post."""
    post = _get_post(db, post_id)
    if post.video_status == models.VIDEO_RENDERING:
        raise HTTPException(409, "Video already rendering")
    post.video_status = models.VIDEO_QUEUED
    post.video_error = ""
    db.commit()
    return post
