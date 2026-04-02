"""
run_agent.py — Lixen.AI Social Media Agent: combined process.

Runs BOTH the FastAPI webhook server AND the weekly content scheduler
in a single Python process using threads. Deploy this one file on any
server (VPS, Railway, Render, Fly.io) with:

    python run_agent.py

Environment variables required:
    ANTHROPIC_API_KEY   — from console.anthropic.com
    GHL_API_KEY         — your GHL Private Integration Token
    GHL_LOCATION_ID     — C7e7ReTQ4FXMZp9TjxzU
    WEBHOOK_PORT        — default 8000
    WEBHOOK_SECRET      — lixen-ai-webhook-2026
"""

import os
import threading
import logging
import schedule
import time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("lixen-ai")


# ── Weekly content scheduler thread ──────────────────────────────────────────

def _run_weekly():
    from scheduler import run_weekly_workflow
    log.info("Weekly content run starting…")
    try:
        run_weekly_workflow(dry_run=False)
        log.info("Weekly content run complete.")
    except Exception as e:
        log.error(f"Weekly content run failed: {e}", exc_info=True)


def _scheduler_thread():
    day = os.environ.get("SCHEDULE_DAY", "monday").lower()
    time_str = os.environ.get("SCHEDULE_TIME", "07:00")

    log.info(f"Scheduler: every {day.capitalize()} at {time_str}")
    getattr(schedule.every(), day).at(time_str).do(_run_weekly)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ── FastAPI webhook server thread ─────────────────────────────────────────────

def _webhook_thread():
    import uvicorn
    from ghl_webhook import app

    port = int(os.environ.get("WEBHOOK_PORT", 8000))
    log.info(f"Webhook server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    missing = [k for k in ("ANTHROPIC_API_KEY", "GHL_API_KEY", "GHL_LOCATION_ID")
               if not os.environ.get(k)]
    if missing:
        log.error(f"Missing required env vars: {', '.join(missing)}")
        log.error("Copy .env.example to .env, fill in your keys, then re-run.")
        raise SystemExit(1)

    log.info("Lixen.AI Social Media Agent starting…")

    # Start webhook server in background thread
    wt = threading.Thread(target=_webhook_thread, daemon=True, name="webhook")
    wt.start()

    # Run scheduler in main thread (keeps process alive)
    _scheduler_thread()
