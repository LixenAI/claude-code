"""
Social media posting via GoHighLevel Social Planner API.
GHL already has Facebook, Instagram, and TikTok connected —
no separate platform credentials needed.
"""

import os
import requests
from datetime import datetime, timezone

GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"

# Pre-filled GHL social account IDs for Lixen.AI
ACCOUNT_IDS = {
    "facebook": os.environ.get(
        "GHL_FB_ACCOUNT_ID",
        "698afe7a73eafb1d3b1dee6a_C7e7ReTQ4FXMZp9TjxzU_928531400351443_page",
    ),
    "instagram": os.environ.get(
        "GHL_IG_ACCOUNT_ID",
        "698afe9ddf13cb8b403358b3_C7e7ReTQ4FXMZp9TjxzU_17841408430198402",
    ),
    "tiktok": os.environ.get(
        "GHL_TIKTOK_ACCOUNT_ID",
        "698bfa551ce275697c2e8aca_C7e7ReTQ4FXMZp9TjxzU_000MKkVmyEEjs3pnDIk6WCPUbxmJe9sHp5_business",
    ),
}

PLATFORM_LABELS = {
    "facebook": "Facebook — Lixen.AI (928531400351443)",
    "instagram": "Instagram — lixen.ai (17841408430198402)",
    "tiktok": "TikTok — LixenAI | AI Agent Service ✨",
}


def _ghl_headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['GHL_API_KEY']}",
        "Version": GHL_API_VERSION,
        "Content-Type": "application/json",
    }


def post_to_ghl(
    body: str,
    platforms: list[str],
    schedule_date: str = None,
    media_urls: list[str] = None,
) -> dict:
    """
    Create a social media post via GHL Social Planner.

    Args:
        body: Post text/caption
        platforms: List of platforms — any of: "facebook", "instagram", "tiktok"
        schedule_date: ISO 8601 string to schedule (e.g. "2024-12-01T09:00:00.000Z").
                       None = post immediately (status: "published")
        media_urls: Optional list of public media URLs to attach

    Returns:
        GHL API response dict
    """
    location_id = os.environ["GHL_LOCATION_ID"]
    url = f"{GHL_API_BASE}/social-media-posting/location/{location_id}/posts"

    account_ids = []
    for platform in platforms:
        platform = platform.lower().strip()
        account_id = ACCOUNT_IDS.get(platform)
        if account_id:
            account_ids.append(account_id)
        else:
            print(f"  [GHL] Warning: unknown platform '{platform}', skipping")

    if not account_ids:
        raise ValueError(f"No valid platform account IDs resolved from: {platforms}")

    status = "scheduled" if schedule_date else "published"

    payload = {
        "accountIds": account_ids,
        "post": {
            "body": body,
            "status": status,
        },
    }

    if schedule_date:
        payload["scheduleDate"] = schedule_date

    if media_urls:
        payload["post"]["mediaUrls"] = media_urls

    response = requests.post(url, json=payload, headers=_ghl_headers(), timeout=30)
    response.raise_for_status()
    result = response.json()

    platform_labels = [PLATFORM_LABELS.get(p.lower(), p) for p in platforms]
    print(f"  [GHL] Posted to: {', '.join(platform_labels)}")
    print(f"  [GHL] Status: {status} | Post ID: {result.get('id', result.get('_id', 'N/A'))}")
    return result


def post_content(platform: str, content: str, image_url: str = None) -> dict:
    """Post to a single platform via GHL."""
    media = [image_url] if image_url else None
    return post_to_ghl(body=content, platforms=[platform], media_urls=media)


def post_to_all_platforms(content: str, image_url: str = None) -> dict:
    """Post the same content to Facebook, Instagram, and TikTok via GHL."""
    return post_to_ghl(
        body=content,
        platforms=["facebook", "instagram", "tiktok"],
        media_urls=[image_url] if image_url else None,
    )


def schedule_post(
    content: str,
    platforms: list[str],
    schedule_date: str,
    image_url: str = None,
) -> dict:
    """
    Schedule a post for a future date via GHL Social Planner.

    Args:
        content: Post caption/body
        platforms: ["facebook", "instagram", "tiktok"] or subset
        schedule_date: ISO 8601 e.g. "2024-12-02T09:00:00.000Z"
        image_url: Optional media URL
    """
    return post_to_ghl(
        body=content,
        platforms=platforms,
        schedule_date=schedule_date,
        media_urls=[image_url] if image_url else None,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    test_caption = (
        "Your front desk just clocked out.\n\n"
        "Your AI one never will.\n\n"
        "Lixen.AI answers calls, replies to DMs, and books appointments — 24/7.\n\n"
        "DM us 'AUDIT' to see what you're missing.\n\n"
        "#MedSpa #AIFrontDesk #BookingAutomation #MedSpaMarketing"
    )

    print("Testing GHL Social Planner post (Facebook only)...\n")
    result = post_content("facebook", test_caption)
    print(result)
