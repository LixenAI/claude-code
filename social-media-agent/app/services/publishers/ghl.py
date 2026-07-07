"""
Legacy GoHighLevel Social Planner driver — kept for the Lixen.AI brand.
The new personal-brand pipeline defaults to the native driver instead.
"""

import os

from app.services.publishers import MissingCredentials, PublishError


def publish_ghl(caption: str, platform: str, account_ids: dict, video_public_url: str | None, image_urls: list[str]) -> dict:
    if not os.environ.get("GHL_API_KEY") or not os.environ.get("GHL_LOCATION_ID"):
        raise MissingCredentials("GHL_API_KEY / GHL_LOCATION_ID not set")
    if not account_ids.get(platform):
        raise MissingCredentials(f"No GHL account id configured for {platform}")

    from social_poster import post_to_ghl

    media = []
    post_type = "post"
    if video_public_url:
        media = [{"url": video_public_url, "type": "Video"}]
        post_type = "reel" if platform in ("instagram", "tiktok") else "post"
    elif image_urls:
        media = [{"url": image_urls[0], "type": "Photo"}]

    try:
        result = post_to_ghl(
            body=caption,
            platforms=[platform],
            post_type=post_type,
            media=media,
            account_ids=account_ids,
        )
    except Exception as e:
        raise PublishError(f"GHL post failed: {e}") from e

    post_data = result.get("results", {}).get("post", result.get("results", {}))
    return {"platform_post_id": str(post_data.get("_id", "")), "driver": "ghl"}
