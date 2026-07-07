"""
Minimal smoke tests: seed, generate→parse→queue, approve→slot,
publish transitions, legacy /health. Run with: pytest tests/
"""

import os
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["PUBLISH_DRY_RUN"] = "1"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

SAMPLE_OUTPUT = """**PLATFORM:** TikTok
**CATEGORY:** Getting Unstuck
**FORMAT:** Reel Script

---HOOK (0-3 seconds)---
"You already know what to do."

---BODY---
[talking head]
Stop collecting advice. Start acting on the advice you already have.

---CTA---
Follow for more.

---HASHTAGS---
#gettingunstuck #growth
"""


@pytest.fixture(scope="session")
def client():
    from app.db import init_db
    init_db()

    # Build app WITHOUT the background scheduler (lifespan not run by design)
    from app.server import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_seed_creates_both_brands(client):
    brands = client.get("/api/brands").json()
    slugs = {b["slug"] for b in brands}
    assert {"lixen-ai", "rennewme"} <= slugs
    renn = next(b for b in brands if b["slug"] == "rennewme")
    assert renn["autonomy"] == "approval"
    assert renn["publisher"] == "native"
    assert len(renn["pillars"]) == 5


def test_rennewme_has_slots(client):
    renn = next(b for b in client.get("/api/brands").json() if b["slug"] == "rennewme")
    slots = client.get(f"/api/brands/{renn['id']}/slots").json()
    assert len(slots) == 9


def _make_post(client):
    """Simulate a generation run via the parser (no API call)."""
    from app import models
    from app.db import SessionLocal
    from app.services.generation import parse_generated_posts

    db = SessionLocal()
    brand = db.query(models.Brand).filter_by(slug="rennewme").first()
    parsed = parse_generated_posts(brand, SAMPLE_OUTPUT)
    assert len(parsed) == 1
    item = parsed[0]
    assert item["platform"] == "tiktok"
    assert item["format"] == "reel_script"
    assert item["hook"] == "You already know what to do."
    assert "#gettingunstuck" in item["hashtags"]
    post = models.Post(brand_id=brand.id, status=models.PENDING_APPROVAL, **item)
    db.add(post)
    db.commit()
    post_id = post.id
    db.close()
    return post_id


def test_parse_approve_and_slot_assignment(client):
    post_id = _make_post(client)
    res = client.post(f"/api/posts/{post_id}/approve", json={})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "scheduled"
    assert body["scheduled_at"] is not None  # auto-assigned from slot calendar
    assert body["video_status"] == "queued"  # reel scripts queue a render


def test_publish_now_dry_run(client):
    post_id = _make_post(client)
    client.post(f"/api/posts/{post_id}/approve", json={})
    res = client.post(f"/api/posts/{post_id}/publish-now")
    assert res.status_code == 200
    assert res.json()["status"] == "posted"
    assert res.json()["ghl_post_id"] == "dry_run"


def test_publish_falls_back_to_ready_without_creds(client, monkeypatch):
    monkeypatch.delenv("PUBLISH_DRY_RUN", raising=False)
    monkeypatch.delenv("TIKTOK_ACCESS_TOKEN", raising=False)
    post_id = _make_post(client)
    client.post(f"/api/posts/{post_id}/approve", json={})
    res = client.post(f"/api/posts/{post_id}/publish-now")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"  # manual-posting fallback, not failed
    monkeypatch.setenv("PUBLISH_DRY_RUN", "1")

    # manual flow completes with mark-posted
    res = client.post(f"/api/posts/{post_id}/mark-posted")
    assert res.json()["status"] == "posted"


def test_reject(client):
    post_id = _make_post(client)
    res = client.post(f"/api/posts/{post_id}/reject")
    assert res.json()["status"] == "rejected"


def test_dashboard_counts(client):
    renn = next(b for b in client.get("/api/brands").json() if b["slug"] == "rennewme")
    data = client.get(f"/api/dashboard?brand_id={renn['id']}").json()
    assert data["counts"].get("posted", 0) >= 1


def test_legacy_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_video_script_extraction():
    from app import models
    from app.services.video_generator import extract_script_segments

    post = models.Post(
        hook="You already know what to do.",
        raw_generated=SAMPLE_OUTPUT,
        caption="x",
    )
    segments = extract_script_segments(post)
    assert segments[0] == "You already know what to do."
    assert any("Stop collecting advice" in s for s in segments)
    # bracketed cues stripped
    assert not any("[" in s for s in segments)
