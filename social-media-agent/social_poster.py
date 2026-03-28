"""
Social media posting module.
Handles posting to Facebook, Instagram (Meta Graph API), and TikTok.
"""

import os
import requests


# --- Meta (Facebook + Instagram) ---

META_GRAPH_BASE = "https://graph.facebook.com/v19.0"


def post_to_facebook(message: str) -> dict:
    """
    Post a text update to a Facebook Page.
    Page: Lixen.AI (ID: 928531400351443)
    Requires: META_ACCESS_TOKEN, META_PAGE_ID
    """
    page_id = os.environ["META_PAGE_ID"]
    token = os.environ["META_ACCESS_TOKEN"]

    url = f"{META_GRAPH_BASE}/{page_id}/feed"
    payload = {"message": message, "access_token": token}

    response = requests.post(url, data=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    print(f"[Facebook] Posted successfully. Post ID: {result.get('id')}")
    return result


def post_to_instagram_caption(caption: str, image_url: str) -> dict:
    """
    Post a photo with caption to Instagram Business account.
    Account: lixen.ai (ID: 17841408430198402)
    Requires: META_ACCESS_TOKEN, META_IG_USER_ID
    Requires a publicly accessible image_url (hosted image).

    Two-step process:
    1. Create a media container
    2. Publish the container
    """
    ig_user_id = os.environ["META_IG_USER_ID"]
    token = os.environ["META_ACCESS_TOKEN"]

    # Step 1: Create media container
    container_url = f"{META_GRAPH_BASE}/{ig_user_id}/media"
    container_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    }
    container_resp = requests.post(container_url, data=container_payload, timeout=30)
    container_resp.raise_for_status()
    creation_id = container_resp.json()["id"]

    # Step 2: Publish the container
    publish_url = f"{META_GRAPH_BASE}/{ig_user_id}/media_publish"
    publish_payload = {"creation_id": creation_id, "access_token": token}
    publish_resp = requests.post(publish_url, data=publish_payload, timeout=30)
    publish_resp.raise_for_status()
    result = publish_resp.json()

    print(f"[Instagram] Posted successfully. Media ID: {result.get('id')}")
    return result


def post_to_instagram_text_only(caption: str) -> dict:
    """
    Post a text-only update to Instagram via a Facebook Page
    (uses the Page's linked Instagram for text posts / stories).
    For caption-only posts without an image, we post to Facebook
    which syncs to the linked Instagram account if cross-posting is enabled.
    """
    print("[Instagram] Note: Text-only IG posts require an image via the Graph API.")
    print("[Instagram] Posting caption to Facebook instead (cross-post to IG).")
    return post_to_facebook(caption)


# --- TikTok ---

TIKTOK_BASE = "https://open.tiktokapis.com/v2"


def post_to_tiktok_text(text: str) -> dict:
    """
    Create a TikTok text post (Direct Post API).
    Requires: TIKTOK_ACCESS_TOKEN, TIKTOK_OPEN_ID

    Account: LixenAI | AI Agent Service ✨
    Open ID: 000MKkVmyEEjs3pnDIk6WCPUbxmJe9sHp5

    TikTok Content Posting API — text posts (Business accounts).
    Docs: https://developers.tiktok.com/doc/content-posting-api-get-started
    """
    token = os.environ["TIKTOK_ACCESS_TOKEN"]
    open_id = os.environ.get("TIKTOK_OPEN_ID", "000MKkVmyEEjs3pnDIk6WCPUbxmJe9sHp5")

    url = f"{TIKTOK_BASE}/post/publish/text/init/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    payload = {
        "post_info": {
            "title": text[:150],  # TikTok caption max 150 chars for text posts
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
        },
        "open_id": open_id,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    result = response.json()
    print(f"[TikTok] Post initiated. Publish ID: {result.get('data', {}).get('publish_id')}")
    return result


# --- Dispatcher ---

PLATFORM_HANDLERS = {
    "facebook": post_to_facebook,
    "instagram": post_to_instagram_text_only,
    "tiktok": post_to_tiktok_text,
}


def post_content(platform: str, content: str, image_url: str = None) -> dict:
    """
    Route content to the correct platform poster.

    Args:
        platform: "facebook", "instagram", or "tiktok"
        content: The caption/body text to post
        image_url: Optional public image URL (required for IG photo posts)
    """
    platform = platform.lower().strip()

    if platform == "instagram" and image_url:
        return post_to_instagram_caption(content, image_url)

    handler = PLATFORM_HANDLERS.get(platform)
    if not handler:
        raise ValueError(f"Unknown platform: {platform}. Choose: facebook, instagram, tiktok")

    return handler(content)


def post_to_all_platforms(content: str, image_url: str = None) -> dict:
    """Post the same content to all three platforms."""
    results = {}
    for platform in ["facebook", "instagram", "tiktok"]:
        try:
            results[platform] = post_content(platform, content, image_url)
        except Exception as e:
            print(f"[{platform.capitalize()}] Error: {e}")
            results[platform] = {"error": str(e)}
    return results


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
    post_content("facebook", test_caption)
