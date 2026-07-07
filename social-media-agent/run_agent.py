"""
run_agent.py — deploy entrypoint.

Now a thin wrapper around the unified platform server (app/server.py),
which runs the API, the web dashboard, and the APScheduler background
jobs (publisher poller + weekly auto-generation) in one process.

    python run_agent.py

Required env: ANTHROPIC_API_KEY. Everything else is optional — see
.env.example for publishing credentials.
"""

import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Missing ANTHROPIC_API_KEY. Copy .env.example to .env and fill it in.")

    port = int(os.environ.get("WEBHOOK_PORT", 8000))
    print(f"Social Media Manager starting on port {port} …")
    uvicorn.run("app.server:app", host="0.0.0.0", port=port, log_level="info")
