"""
Native platform publishing — no GoHighLevel involved.

Instagram: Meta Graph API (requires an IG Professional account linked
to a Facebook Page, IG_ACCESS_TOKEN + IG_USER_ID, and PUBLIC_BASE_URL
so Meta can fetch the media file this server hosts under /media).

TikTok: Content Posting API (requires TIKTOK_ACCESS_TOKEN from your
TikTok developer app). Default flow uploads to the account's inbox —
the video appears in the TikTok app as a draft to confirm, which works
for unaudited apps. Set TIKTOK_DIRECT_POST=1 once your app is audited
to publish directly.
"""

import os
import time

import requests

from app.services.publishers import MissingCredentials, PublishError

GRAPH_BASE = "https://graph.facebook.com/v21.0"
TIKTOK_BASE = "https://open.tiktokapis.com/v2"


def _public_url(rel_path: str) -> str:
    base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    if not base:
        raise MissingCredentials("PUBLIC_BASE_URL not set — Meta must be able to fetch media over HTTPS")
    return f"{base}/{rel_path.lstrip('/')}"


# ── Instagram (Meta Graph API) ────────────────────────────────────────────

def publish_instagram(caption: str, video_rel_path: str | None, image_urls: list[str]) -> dict:
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    ig_user = os.environ.get("IG_USER_ID", "")
    if not token or not ig_user:
        raise MissingCredentials("IG_ACCESS_TOKEN / IG_USER_ID not set")

    params: dict = {"caption": caption, "access_token": token}
    if video_rel_path:
        params["media_type"] = "REELS"
        params["video_url"] = _public_url(video_rel_path)
    elif image_urls:
        params["image_url"] = image_urls[0]
    else:
        raise PublishError("Instagram requires media — render a video or attach an image URL")

    resp = requests.post(f"{GRAPH_BASE}/{ig_user}/media", data=params, timeout=60)
    if resp.status_code >= 400:
        raise PublishError(f"IG container create failed: {resp.status_code} {resp.text[:300]}")
    container_id = resp.json()["id"]

    # Reels containers transcode asynchronously — poll until FINISHED
    for _ in range(60):
        status = requests.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        ).json()
        code = status.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise PublishError(f"IG media container errored: {status}")
        time.sleep(5)
    else:
        raise PublishError("IG media container never finished processing")

    publish = requests.post(
        f"{GRAPH_BASE}/{ig_user}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=60,
    )
    if publish.status_code >= 400:
        raise PublishError(f"IG publish failed: {publish.status_code} {publish.text[:300]}")
    return {"platform_post_id": publish.json().get("id", ""), "driver": "instagram_graph"}


# ── TikTok (Content Posting API) ──────────────────────────────────────────

def publish_tiktok(caption: str, video_abs_path: str | None) -> dict:
    token = os.environ.get("TIKTOK_ACCESS_TOKEN", "")
    if not token:
        raise MissingCredentials("TIKTOK_ACCESS_TOKEN not set")
    if not video_abs_path or not os.path.exists(video_abs_path):
        raise PublishError("TikTok requires a rendered video")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    size = os.path.getsize(video_abs_path)
    direct = os.environ.get("TIKTOK_DIRECT_POST", "") == "1"

    if direct:
        init_url = f"{TIKTOK_BASE}/post/publish/video/init/"
        payload = {
            "post_info": {
                "title": caption[:2200],
                "privacy_level": "PUBLIC_TO_EVERYONE",
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": size,
                "total_chunk_count": 1,
            },
        }
    else:
        init_url = f"{TIKTOK_BASE}/post/publish/inbox/video/init/"
        payload = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": size,
                "total_chunk_count": 1,
            }
        }

    resp = requests.post(init_url, json=payload, headers=headers, timeout=60)
    data = resp.json()
    if resp.status_code >= 400 or data.get("error", {}).get("code") not in ("ok", None):
        raise PublishError(f"TikTok init failed: {resp.status_code} {str(data)[:300]}")

    upload_url = data["data"]["upload_url"]
    publish_id = data["data"]["publish_id"]

    with open(video_abs_path, "rb") as f:
        upload = requests.put(
            upload_url,
            data=f,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{size - 1}/{size}",
            },
            timeout=600,
        )
    if upload.status_code >= 400:
        raise PublishError(f"TikTok upload failed: {upload.status_code} {upload.text[:300]}")

    return {
        "platform_post_id": publish_id,
        "driver": "tiktok_direct" if direct else "tiktok_inbox",
        "note": "" if direct else "Uploaded to TikTok inbox — open the TikTok app to confirm the draft.",
    }
