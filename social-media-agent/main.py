"""
Entry point for the Lixen.AI Social Media Agent.

Usage:
    python main.py --mode dry-run       # Generate content, no posting (safe to test)
    python main.py --mode run-now       # Generate + post immediately
    python main.py --mode schedule      # Start weekly scheduler (Mon 7am)
    python main.py --mode schedule --day friday --time 09:00
"""

from scheduler import run_weekly_workflow, start_weekly_schedule
import argparse
import os
from dotenv import load_dotenv

load_dotenv()


def check_env() -> list[str]:
    """Return list of missing required environment variables."""
    required = ["ANTHROPIC_API_KEY"]
    posting_vars = [
        "META_ACCESS_TOKEN",
        "META_PAGE_ID",
        "META_IG_USER_ID",
        "TIKTOK_ACCESS_TOKEN",
    ]
    missing = [v for v in required if not os.environ.get(v)]
    missing_posting = [v for v in posting_vars if not os.environ.get(v)]
    return missing, missing_posting


def main():
    parser = argparse.ArgumentParser(
        description="Lixen.AI Social Media Content Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --mode dry-run              Generate + preview content (no posting)
  python main.py --mode run-now              Generate + post to all platforms now
  python main.py --mode schedule             Start weekly scheduler (Monday 07:00)
  python main.py --mode schedule --day wednesday --time 09:30
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "run-now", "schedule"],
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
    args = parser.parse_args()

    missing_required, missing_posting = check_env()

    if missing_required:
        print(f"ERROR: Missing required env vars: {', '.join(missing_required)}")
        print("Copy .env.example to .env and fill in your API keys.")
        return

    if args.mode == "run-now" and missing_posting:
        print(f"WARNING: Missing posting credentials: {', '.join(missing_posting)}")
        print("Set these in your .env file before running --mode run-now.\n")

    if args.mode == "dry-run":
        print("Mode: DRY RUN — content will be generated but NOT posted.\n")
        run_weekly_workflow(dry_run=True)

    elif args.mode == "run-now":
        print("Mode: RUN NOW — generating and posting to all platforms.\n")
        run_weekly_workflow(dry_run=False)

    elif args.mode == "schedule":
        print(f"Mode: SCHEDULE — every {args.day.capitalize()} at {args.time}\n")
        start_weekly_schedule(day=args.day, time_str=args.time, dry_run=False)


if __name__ == "__main__":
    main()
