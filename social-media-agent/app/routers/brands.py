"""Brands CRUD + slots + connected-account discovery."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db

router = APIRouter(prefix="/api", tags=["brands"])


def _get_brand(db: Session, brand_id: int) -> models.Brand:
    brand = db.get(models.Brand, brand_id)
    if brand is None:
        raise HTTPException(404, "Brand not found")
    return brand


@router.get("/brands", response_model=list[schemas.BrandOut])
def list_brands(db: Session = Depends(get_db)):
    return db.query(models.Brand).order_by(models.Brand.id).all()


@router.post("/brands", response_model=schemas.BrandOut, status_code=201)
def create_brand(body: schemas.BrandCreate, db: Session = Depends(get_db)):
    if db.query(models.Brand).filter_by(slug=body.slug).first():
        raise HTTPException(409, "Slug already exists")
    brand = models.Brand(**body.model_dump())
    brand.pillars = [p.model_dump() for p in body.pillars]
    db.add(brand)
    db.commit()
    return brand


@router.get("/brands/{brand_id}", response_model=schemas.BrandOut)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    return _get_brand(db, brand_id)


@router.patch("/brands/{brand_id}", response_model=schemas.BrandOut)
def update_brand(brand_id: int, body: schemas.BrandUpdate, db: Session = Depends(get_db)):
    brand = _get_brand(db, brand_id)
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "pillars" and value is not None:
            value = [p if isinstance(p, dict) else p.model_dump() for p in value]
        setattr(brand, key, value)
    db.commit()
    return brand


@router.get("/brands/{brand_id}/ghl-accounts")
def list_ghl_accounts(brand_id: int, db: Session = Depends(get_db)):
    """Live list of social accounts connected in GHL (legacy publisher only)."""
    _get_brand(db, brand_id)
    try:
        import os
        import requests as req

        resp = req.get(
            f"https://services.leadconnectorhq.com/social-media-posting/{os.environ['GHL_LOCATION_ID']}/accounts",
            headers={
                "Authorization": f"Bearer {os.environ['GHL_API_KEY']}",
                "Version": "2021-07-28",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except KeyError as e:
        raise HTTPException(400, f"GHL not configured: missing {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"GHL account listing failed: {e}")


# ── Slots ────────────────────────────────────────────────────────────────

@router.get("/brands/{brand_id}/slots", response_model=list[schemas.SlotOut])
def list_slots(brand_id: int, db: Session = Depends(get_db)):
    _get_brand(db, brand_id)
    return (
        db.query(models.ScheduleSlot)
        .filter_by(brand_id=brand_id)
        .order_by(models.ScheduleSlot.day_of_week, models.ScheduleSlot.time_local)
        .all()
    )


@router.post("/brands/{brand_id}/slots", response_model=schemas.SlotOut, status_code=201)
def create_slot(brand_id: int, body: schemas.SlotIn, db: Session = Depends(get_db)):
    _get_brand(db, brand_id)
    slot = models.ScheduleSlot(brand_id=brand_id, **body.model_dump())
    db.add(slot)
    db.commit()
    return slot


@router.patch("/slots/{slot_id}", response_model=schemas.SlotOut)
def update_slot(slot_id: int, body: schemas.SlotUpdate, db: Session = Depends(get_db)):
    slot = db.get(models.ScheduleSlot, slot_id)
    if slot is None:
        raise HTTPException(404, "Slot not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(slot, key, value)
    db.commit()
    return slot


@router.delete("/slots/{slot_id}", status_code=204)
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.get(models.ScheduleSlot, slot_id)
    if slot is None:
        raise HTTPException(404, "Slot not found")
    db.delete(slot)
    db.commit()
