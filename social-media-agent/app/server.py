"""
Unified platform server: REST API + web dashboard + background jobs
in one FastAPI process.

    python main.py --mode serve      (or: python run_agent.py)
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
MEDIA_DIR = os.path.join(BASE_DIR, "data", "media")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db import init_db
    from app.jobs import create_scheduler

    init_db()
    os.makedirs(MEDIA_DIR, exist_ok=True)
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Social Media Manager", version="2.0.0", lifespan=lifespan)

# API routers
from app.routers import brands, dashboard, generate, posts  # noqa: E402

app.include_router(brands.router)
app.include_router(posts.router)
app.include_router(generate.router)
app.include_router(dashboard.router)

# Legacy Lixen.AI GHL webhook endpoints (/health, /ghl/*)
try:
    from ghl_webhook import router as ghl_router
    app.include_router(ghl_router)
except Exception:  # pragma: no cover — legacy module optional
    pass

# Rendered videos + downloads
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# Frontend SPA (present after `npm run build`)
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
