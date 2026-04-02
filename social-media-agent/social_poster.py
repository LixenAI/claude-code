"""
Social media posting via GoHighLevel Social Planner API.
GHL already has Facebook, Instagram, and TikTok connected —
no separate platform credentials needed.

Verified payload format (tested live 2026-04-01):
  POST /social-media-posting/{locationId}/posts
  Body: { accountIds, type, media, userId, summary, status, scheduleDate }
"""

import os
import requests

GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"

# Verified GHL Social Account IDs for Lixen.AI
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
    "facebook": "Facebook — Lixen.AI",
    "instagram": "Instagram — lixen.ai",
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
    post_type: str = "post",
    schedule_date: str = None,
    media: list[dict] = None,
) -> dict:
    """
    Create a social media post via GHL Social Planner.

    Args:
        body: Post caption / text content (maps to GHL 'summary' field)
        platforms: Any of: "facebook", "instagram", "tiktok"
        post_type: "post" | "story" | "reel"  (default: "post")
        schedule_date: ISO 8601 string for scheduling, e.g. "2026-05-01T09:00:00.000Z"
                       None = publish immediately (status: "published")
        media: List of GHL media objects, e.g. [{"url": "...", "type": "image"}]
               Empty list = text-only post

    Returns:
        GHL API response dict with post ID inside results.post._id
    """
    location_id = os.environ["GHL_LOCATION_ID"]
    user_id = os.environ.get("GHL_USER_ID", "n0VuVK7uRZWSsQRZDLa8")
    url = f"{GHL_API_BASE}/social-media-posting/{location_id}/posts"

    account_ids = []
    for platform in platforms:
        account_id = ACCOUNT_IDS.get(platform.lower().strip())
        if account_id:
            account_ids.append(account_id)
        else:
            print(f"  [GHL] Warning: unknown platform '{platform}', skipping")

    if not account_ids:
        raise ValueError(f"No valid platform account IDs resolved from: {platforms}")

    has_media = bool(media)
    # GHL rejects external image URLs for published/scheduled in a single call.
    # Workaround: create as draft first, then PATCH to published/scheduled.
    status = "draft" if has_media else ("scheduled" if schedule_date else "published")

    payload = {
        "accountIds": account_ids,
        "type": post_type,
        "media": media or [],
        "userId": user_id,
        "summary": body,
        "status": status,
    }

    if schedule_date and not has_media:
        payload["scheduleDate"] = schedule_date

    response = requests.post(url, json=payload, headers=_ghl_headers(), timeout=30)
    response.raise_for_status()
    result = response.json()

    # Step 2: promote draft to final status when media is attached
    if has_media:
        post_data = result.get("results", {}).get("post", result.get("results", {}))
        post_id = post_data.get("_id")
        if post_id:
            final_status = "scheduled" if schedule_date else "published"
            patch = {"status": final_status}
            if schedule_date:
                patch["scheduleDate"] = schedule_date
            patch_resp = requests.patch(
                f"{url}/{post_id}", json=patch, headers=_ghl_headers(), timeout=15
            )
            if patch_resp.status_code == 200:
                result["_promoted_to"] = final_status
            else:
                print(f"  [GHL] Warning: draft created but promote to {final_status} failed ({patch_resp.status_code})")

    post_data = result.get("results", {}).get("post", result.get("results", {}))
    post_id = post_data.get("_id", result.get("id", result.get("traceId", "OK")))
    platform_labels = [PLATFORM_LABELS.get(p.lower(), p) for p in platforms]
    final_status = result.get("_promoted_to", status)
    print(f"  [GHL ✓] {', '.join(platform_labels)}")
    print(f"          Status: {final_status} | Post ID: {post_id}")
    return result


def post_content(platform: str, content: str, image_url: str = None) -> dict:
    """Post to a single platform via GHL."""
    media = [{"url": image_url, "type": "Photo"}] if image_url else []
    return post_to_ghl(body=content, platforms=[platform], media=media)


def post_to_all_platforms(content: str, image_url: str = None) -> dict:
    """Post the same content to Facebook, Instagram, and TikTok via GHL."""
    media = [{"url": image_url, "type": "Photo"}] if image_url else []
    return post_to_ghl(
        body=content,
        platforms=["facebook", "instagram", "tiktok"],
        media=media,
    )


def schedule_post(
    content: str,
    platforms: list[str],
    schedule_date: str,
    post_type: str = "post",
    image_url: str = None,
) -> dict:
    """
    Schedule a post for a future date via GHL Social Planner.

    Args:
        content: Post caption/body
        platforms: ["facebook", "instagram", "tiktok"] or subset
        schedule_date: ISO 8601 e.g. "2026-05-01T09:00:00.000Z"
        post_type: "post" | "story" | "reel"
        image_url: Optional public media URL
    """
    media = [{"url": image_url, "type": "Photo"}] if image_url else []
    return post_to_ghl(
        body=content,
        platforms=platforms,
        post_type=post_type,
        schedule_date=schedule_date,
        media=media,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    test_caption = (
        "Your front desk just clocked out.\n\n"
        "Your AI one never will.\n\n"
        "Lixen.AI answers calls, replies to DMs, and books appointments — 24/7.\n\n"
        'DM us "AUDIT" to see what you\'re missing.\n\n'
        "#MedSpa #AIFrontDesk #BookingAutomation #MedSpaMarketing"
    )

    print("Posting test caption to Facebook via GHL Social Planner...\n")
    result = post_content("facebook", test_caption)
    print(result)
