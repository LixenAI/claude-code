"""Dashboard summary: counts, upcoming schedule, recent failures."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=schemas.DashboardOut)
def dashboard(brand_id: int, db: Session = Depends(get_db)):
    counts = dict(
        db.query(models.Post.status, func.count(models.Post.id))
        .filter(models.Post.brand_id == brand_id)
        .group_by(models.Post.status)
        .all()
    )

    now = datetime.now(timezone.utc)
    upcoming = (
        db.query(models.Post)
        .filter(
            models.Post.brand_id == brand_id,
            models.Post.status.in_([models.SCHEDULED, models.READY, models.PUBLISHING]),
            models.Post.scheduled_at != None,  # noqa: E711
            models.Post.scheduled_at <= now + timedelta(days=7),
        )
        .order_by(models.Post.scheduled_at)
        .limit(20)
        .all()
    )

    recent_failures = (
        db.query(models.Post)
        .filter(models.Post.brand_id == brand_id, models.Post.status == models.FAILED)
        .order_by(models.Post.updated_at.desc())
        .limit(10)
        .all()
    )

    return schemas.DashboardOut(
        brand_id=brand_id,
        counts=counts,
        upcoming=upcoming,
        recent_failures=recent_failures,
    )
