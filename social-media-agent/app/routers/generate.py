"""Trigger + poll content generation runs."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.services.generation import execute_generation_run, start_generation_run

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/brands/{brand_id}/generate", response_model=schemas.GenerationRunOut, status_code=202)
def generate(brand_id: int, body: schemas.GenerateRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    brand = db.get(models.Brand, brand_id)
    if brand is None:
        raise HTTPException(404, "Brand not found")
    run = start_generation_run(db, brand, body.model_dump(), trigger="manual")
    background.add_task(execute_generation_run, run.id)
    return run


@router.get("/generation-runs/{run_id}", response_model=schemas.GenerationRunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.GenerationRun, run_id)
    if run is None:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/brands/{brand_id}/generation-runs", response_model=list[schemas.GenerationRunOut])
def list_runs(brand_id: int, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(models.GenerationRun)
        .filter_by(brand_id=brand_id)
        .order_by(models.GenerationRun.id.desc())
        .limit(limit)
        .all()
    )
