"""
Scheduler: runs the content generation + posting workflow on a weekly schedule.
Can also be triggered manually or run as a one-shot batch.
"""

import os
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

from content_generator import generate_weekly_batch, parse_posts_from_batch
from social_poster import post_content


load_dotenv()

# Platform caption character limits
PLATFORM_LIMITS = {
    "facebook": 63206,
    "instagram": 2200,
    "tiktok": 2200,
}

# Map platform names from generator output to poster keys
PLATFORM_MAP = {
    "instagram": "instagram",
    "tiktok": "tiktok",
    "facebook": "facebook",
    "all platforms": None,  # handled specially
}


def extract_caption(post_content_str: str) -> str:
    """
    Pull the body caption text from a generated post.
    Returns the BODY section + CTA, stripped of markdown headers.
    """
    lines = post_content_str.split("\n")
    capture = False
    caption_lines = []

    for line in lines:
        if "---BODY---" in line or "---HOOK" in line:
            capture = True
            continue
        if "---HASHTAGS---" in line:
            # Include hashtags in caption
            caption_lines.append("")
            continue
        if "---PLATFORM VARIANTS---" in line:
            break
        if capture:
            caption_lines.append(line)

    return "\n".join(caption_lines).strip()


def truncate_for_platform(text: str, platform: str) -> str:
    """Truncate content to platform character limit if needed."""
    limit = PLATFORM_LIMITS.get(platform.lower(), 2200)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text


def run_weekly_workflow(dry_run: bool = False) -> None:
    """
    Full workflow:
    1. Generate 5 posts via Claude
    2. Parse them
    3. Post each to its target platform
    4. Log results
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}")
    print(f"Lixen.AI Weekly Content Workflow — {timestamp}")
    print(f"{'='*60}\n")

    # Step 1: Generate content
    batch_output = generate_weekly_batch()

    # Step 2: Parse into individual posts
    posts = parse_posts_from_batch(batch_output)
    print(f"\nGenerated {len(posts)} posts.\n")

    if not posts:
        print("No posts parsed. Check generator output format.")
        return

    # Step 3: Post each
    results = []
    for i, post in enumerate(posts, 1):
        platform_raw = post.get("platform", "").lower().strip()
        content_str = post.get("content", "")
        caption = extract_caption(content_str)

        # Handle "all platforms" posts
        if "all" in platform_raw:
            targets = ["facebook", "instagram", "tiktok"]
        else:
            target = PLATFORM_MAP.get(platform_raw, platform_raw)
            targets = [target] if target else []

        for platform in targets:
            caption_trimmed = truncate_for_platform(caption, platform)
            print(f"\n[Post {i}] → {platform.upper()} ({post.get('category', 'Unknown')})")

            if dry_run:
                print(f"[DRY RUN] Would post {len(caption_trimmed)} chars to {platform}")
                print(caption_trimmed[:200] + ("..." if len(caption_trimmed) > 200 else ""))
                results.append({"platform": platform, "status": "dry_run"})
            else:
                try:
                    result = post_content(platform, caption_trimmed)
                    results.append({"platform": platform, "status": "success", "result": result})
                except Exception as e:
                    print(f"  ERROR: {e}")
                    results.append({"platform": platform, "status": "error", "error": str(e)})

    # Step 4: Summary
    print(f"\n{'='*60}")
    print("WORKFLOW COMPLETE")
    success = sum(1 for r in results if r.get("status") == "success")
    errors = sum(1 for r in results if r.get("status") == "error")
    dry = sum(1 for r in results if r.get("status") == "dry_run")
    print(f"  Posts sent:  {success}")
    print(f"  Dry runs:    {dry}")
    print(f"  Errors:      {errors}")
    print(f"{'='*60}\n")


def start_weekly_schedule(
    day: str = "monday",
    time_str: str = "07:00",
    dry_run: bool = False,
) -> None:
    """
    Start the scheduler. Runs the workflow every week on `day` at `time_str`.

    Args:
        day: Day of week (monday–sunday)
        time_str: Time in HH:MM 24h format
        dry_run: If True, generates content but does not post
    """
    print(f"Scheduler started — runs every {day.capitalize()} at {time_str}")
    print("Press Ctrl+C to stop.\n")

    getattr(schedule.every(), day).at(time_str).do(
        run_weekly_workflow, dry_run=dry_run
    )

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Lixen.AI Social Media Scheduler")
    parser.add_argument(
        "--mode",
        choices=["run-now", "schedule", "dry-run"],
        default="dry-run",
        help="run-now: post immediately | schedule: start weekly scheduler | dry-run: generate without posting",
    )
    parser.add_argument("--day", default="monday", help="Scheduler day (default: monday)")
    parser.add_argument("--time", default="07:00", help="Scheduler time HH:MM (default: 07:00)")

    args = parser.parse_args()

    if args.mode == "run-now":
        run_weekly_workflow(dry_run=False)
    elif args.mode == "dry-run":
        run_weekly_workflow(dry_run=True)
    elif args.mode == "schedule":
        start_weekly_schedule(day=args.day, time_str=args.time, dry_run=False)
