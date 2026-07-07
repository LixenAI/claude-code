"""
Entry point for the Lixen.AI Social Media Agent.

Usage:
    python main.py --mode dry-run       # Generate content, no posting (safe to test)
    python main.py --mode run-now       # Generate + post immediately
    python main.py --mode schedule      # Start weekly scheduler (Mon 7am)
    python main.py --mode schedule --day friday --time 09:00
"""

from scheduler import run_weekly_workflow, start_weekly_schedule
from ghl_webhook import run_server as run_webhook_server
from ghl_setup import run_setup
import argparse
import os
from dotenv import load_dotenv

load_dotenv()


def check_env() -> tuple[list[str], list[str]]:
    """Return (missing_required, missing_posting) env var lists."""
    required = ["ANTHROPIC_API_KEY"]
    posting_vars = ["GHL_API_KEY", "GHL_LOCATION_ID"]
    missing = [v for v in required if not os.environ.get(v)]
    missing_posting = [v for v in posting_vars if not os.environ.get(v)]
    return missing, missing_posting


def main():
    parser = argparse.ArgumentParser(
        description="Lixen.AI Social Media Content Agent + GHL Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode setup                Verify GHL connection + create workflows
  python main.py --mode dry-run              Generate + preview content (no posting)
  python main.py --mode run-now              Generate + post via GHL Social Planner
  python main.py --mode schedule             Weekly scheduler (Monday 07:00)
  python main.py --mode schedule --day wednesday --time 09:30
  python main.py --mode webhook              Start Anthropic→GHL webhook server
  python main.py --mode webhook --port 8080
  python main.py --mode serve                Unified platform: dashboard + API + scheduler
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["setup", "dry-run", "run-now", "schedule", "webhook", "serve"],
        default="dry-run",
        help="Execution mode (default: dry-run)",
    )
    parser.add_argument(
        "--day",
        default="monday",
        help="Day for weekly schedule: monday-sunday (default: monday)",
    )
    parser.add_argument(
        "--time",
        default="07:00",
        help="Time for weekly schedule HH:MM 24h (default: 07:00)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port for webhook server (default: 8000 or WEBHOOK_PORT env var)",
    )
    args = parser.parse_args()

    missing_required, missing_posting = check_env()

    if missing_required:
        print(f"ERROR: Missing required env vars: {', '.join(missing_required)}")
        print("Copy .env.example to .env and fill in your API keys.")
        return

    if args.mode in ("run-now", "schedule") and missing_posting:
        print(f"WARNING: Missing GHL credentials: {', '.join(missing_posting)}")
        print("Set GHL_API_KEY and GHL_LOCATION_ID in your .env file.\n")

    if args.mode == "setup":
        print("Mode: SETUP — verifying GHL connection and creating workflows.\n")
        run_setup()

    elif args.mode == "dry-run":
        print("Mode: DRY RUN — content will be generated but NOT posted.\n")
        run_weekly_workflow(dry_run=True)

    elif args.mode == "run-now":
        print("Mode: RUN NOW — generating and posting via GHL Social Planner.\n")
        run_weekly_workflow(dry_run=False)

    elif args.mode == "schedule":
        print(f"Mode: SCHEDULE — every {args.day.capitalize()} at {args.time}\n")
        start_weekly_schedule(day=args.day, time_str=args.time, dry_run=False)

    elif args.mode == "webhook":
        print("Mode: WEBHOOK — starting Anthropic → GHL webhook server.\n")
        run_webhook_server(port=args.port)

    elif args.mode == "serve":
        print("Mode: SERVE — unified platform: API + dashboard + scheduler.\n")
        import uvicorn
        port = args.port or int(os.environ.get("WEBHOOK_PORT", 8000))
        uvicorn.run("app.server:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
