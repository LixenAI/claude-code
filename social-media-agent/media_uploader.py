"""
media_uploader.py — Upload Canva export images to GHL Media Library.

Canva signed export URLs expire ~24 hours after generation. This script
downloads each image from design_library.py and uploads it to GHL's Media
Library, which gives back a permanent CDN URL (no expiry).

USAGE:
    python media_uploader.py                    # upload all expired/missing
    python media_uploader.py --dry-run          # preview without uploading
    python media_uploader.py --force            # re-upload even if URL looks valid

After running, the script prints a ready-to-paste Python dict with the new
permanent URLs. Copy them into design_library.py DESIGNS.

REQUIREMENTS:
    GHL_API_KEY and GHL_LOCATION_ID must be set in .env or environment.
"""

import os
import io
import sys
import argparse
import requests
from dotenv import load_dotenv

from design_library import DESIGNS, CANVA_DESIGN_IDS

load_dotenv()

GHL_API_BASE = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"


def _ghl_headers(content_type: str = "application/json") -> dict:
    return {
        "Authorization": f"Bearer {os.environ['GHL_API_KEY']}",
        "Version": GHL_API_VERSION,
        "Content-Type": content_type,
    }


def _is_expired_or_missing(url: str | None) -> bool:
    """Return True if URL is None, empty, or a Canva signed URL (expires)."""
    if not url:
        return True
    return "export-download.canva.com" in url or "X-Amz-Expires" in url


def download_image(url: str) -> tuple[bytes, str]:
    """
    Download image bytes from a URL.
    Returns (image_bytes, content_type).
    """
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "image/jpeg")
    return resp.content, content_type


def upload_to_ghl_media(
    image_bytes: bytes,
    filename: str,
    content_type: str = "image/jpeg",
    location_id: str = None,
) -> str | None:
    """
    Upload an image to the GHL Media Library.

    Args:
        image_bytes:  Raw image bytes
        filename:     Filename including extension (e.g. "pain_instagram_v1.jpg")
        content_type: MIME type
        location_id:  GHL location ID (defaults to GHL_LOCATION_ID env var)

    Returns:
        Permanent public URL string, or None on failure.
    """
    location_id = location_id or os.environ["GHL_LOCATION_ID"]

    upload_url = f"{GHL_API_BASE}/medias/upload-file"
    headers = {
        "Authorization": f"Bearer {os.environ['GHL_API_KEY']}",
        "Version": GHL_API_VERSION,
    }

    files = {
        "file": (filename, io.BytesIO(image_bytes), content_type),
    }
    data = {
        "locationId": location_id,
        "name": filename,
        "parentId": "",
        "altId": location_id,
        "altType": "location",
    }

    resp = requests.post(upload_url, files=files, data=data, headers=headers, timeout=60)

    if resp.status_code not in (200, 201):
        print(f"    [GHL Media] Upload failed ({resp.status_code}): {resp.text[:200]}")
        return None

    result = resp.json()
    # GHL media response has 'mediaUrl' or nested in 'data'
    media_url = (
        result.get("mediaUrl")
        or result.get("data", {}).get("mediaUrl")
        or result.get("url")
        or result.get("data", {}).get("url")
    )
    return media_url


def build_filename(category: str, platform: str, idx: int) -> str:
    return f"lixen_ai_{category}_{platform}_v{idx + 1}.jpg"


def run(dry_run: bool = False, force: bool = False) -> None:
    """Main upload loop."""
    print("Lixen.AI Media Uploader — GHL Media Library")
    print("=" * 50)

    location_id = os.environ.get("GHL_LOCATION_ID")
    if not location_id:
        print("ERROR: GHL_LOCATION_ID not set. Add it to .env and retry.")
        sys.exit(1)
    if not os.environ.get("GHL_API_KEY"):
        print("ERROR: GHL_API_KEY not set. Add it to .env and retry.")
        sys.exit(1)

    new_urls: dict[tuple[str, str], list[str]] = {}
    total_uploaded = 0
    total_skipped = 0
    total_failed = 0

    for (cat, plat), url_list in DESIGNS.items():
        if not url_list:
            print(f"\n  [{cat}/{plat}] No URLs — skipping (no images to upload)")
            new_urls[(cat, plat)] = []
            continue

        new_url_list = []
        for idx, url in enumerate(url_list):
            filename = build_filename(cat, plat, idx)

            if not force and not _is_expired_or_missing(url):
                print(f"\n  [{cat}/{plat}][v{idx + 1}] Already permanent — skipping")
                new_url_list.append(url)
                total_skipped += 1
                continue

            print(f"\n  [{cat}/{plat}][v{idx + 1}] Uploading {filename}...")
            print(f"    Source: {url[:70]}...")

            if dry_run:
                print("    [DRY RUN] Would download + upload to GHL Media Library")
                new_url_list.append(url)
                total_skipped += 1
                continue

            try:
                image_bytes, content_type = download_image(url)
                print(f"    Downloaded: {len(image_bytes):,} bytes ({content_type})")

                ghl_url = upload_to_ghl_media(
                    image_bytes,
                    filename,
                    content_type=content_type,
                    location_id=location_id,
                )

                if ghl_url:
                    print(f"    Uploaded: {ghl_url}")
                    new_url_list.append(ghl_url)
                    total_uploaded += 1
                else:
                    print("    Upload returned no URL — keeping original")
                    new_url_list.append(url)
                    total_failed += 1

            except requests.HTTPError as e:
                print(f"    Download failed ({e.response.status_code}): URL likely expired")
                print("    → Re-export from Canva: python canva_generator.py --re-export " + cat)
                new_url_list.append(url)
                total_failed += 1
            except Exception as e:
                print(f"    ERROR: {e}")
                new_url_list.append(url)
                total_failed += 1

        new_urls[(cat, plat)] = new_url_list

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"DONE  Uploaded: {total_uploaded}  Skipped: {total_skipped}  Failed: {total_failed}")

    if not dry_run and total_uploaded > 0:
        print("\n── Paste these permanent URLs into design_library.py DESIGNS ──\n")
        for (cat, plat), urls in new_urls.items():
            if not urls:
                continue
            ghl_urls = [u for u in urls if u and "leadconnectorhq" in u or (u and "msgsndr" in u)]
            if ghl_urls:
                print(f'    ("{cat}", "{plat}"): [')
                for u in urls:
                    print(f'        "{u}",')
                print("    ],")

    if total_failed > 0:
        print("\nFor failed uploads, re-export designs with:")
        print("  python canva_generator.py --re-export <category>")
        print("  Then run this script again.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Canva images to GHL Media Library")
    parser.add_argument("--dry-run", action="store_true", help="Preview without uploading")
    parser.add_argument("--force", action="store_true", help="Re-upload even non-expiring URLs")
    args = parser.parse_args()

    run(dry_run=args.dry_run, force=args.force)
