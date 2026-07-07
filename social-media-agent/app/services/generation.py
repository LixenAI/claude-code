"""
Brand-aware content generation: builds the prompt from the brand row,
calls Claude, parses the structured output into Post rows, and queues
reel scripts for video rendering.
"""

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import models
from app.db import SessionLocal
from app.services.scheduling import auto_assign

MODEL = "claude-opus-4-6"


# ── Parsing helpers ───────────────────────────────────────────────────────

def _section(content: str, name: str) -> str:
    """Extract text between ---NAME--- markers (tolerates suffixes like 'HOOK (0-3 seconds)')."""
    pattern = rf"---\s*{name}[^\n]*?---\s*\n(.*?)(?=\n---[A-Z]|\Z)"
    m = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _header_field(content: str, name: str) -> str:
    m = re.search(rf"\*\*{name}:\*\*\s*(.+)", content)
    return m.group(1).strip() if m else ""


def _match_pillar(brand: models.Brand, category: str) -> str:
    cat = category.lower().strip()
    for pillar in brand.pillars or []:
        if pillar["name"].lower() in cat or cat in pillar["name"].lower() or pillar["key"] in cat.replace(" ", "_"):
            return pillar["key"]
    return cat.replace(" ", "_")[:64]


def _detect_format(format_line: str) -> tuple[str, str]:
    """Returns (format, post_type)."""
    f = format_line.lower()
    if "reel" in f or "script" in f or "video" in f:
        return "reel_script", "reel"
    if "carousel" in f:
        return "carousel", "post"
    if "quote" in f:
        return "quote_image", "post"
    if "story" in f:
        return "story", "story"
    return "caption", "post"


def parse_generated_posts(brand: models.Brand, raw_output: str) -> list[dict]:
    """Split a batch on **PLATFORM:** markers and structure each post."""
    posts = []
    for section in raw_output.split("**PLATFORM:**")[1:]:
        content = "**PLATFORM:**" + section
        platform = section.strip().split("\n")[0].split("/")[0].strip().lower()
        if platform not in ("instagram", "tiktok", "facebook"):
            continue

        category = _header_field(content, "CATEGORY")
        fmt, post_type = _detect_format(_header_field(content, "FORMAT"))
        hook = _section(content, "HOOK").split("\n")[0].strip().strip('"')
        body = _section(content, "BODY")
        cta = _section(content, "CTA")
        hashtags = _section(content, "HASHTAGS").replace("\n", " ").strip()

        caption_parts = [p for p in (hook, body, cta) if p]
        caption = "\n\n".join(caption_parts)
        # strip video-only cues from the caption text
        caption = re.sub(r"\[[^\]]*\]", "", caption)
        caption = re.sub(r"\n{3,}", "\n\n", caption).strip()

        posts.append({
            "platform": platform,
            "post_type": post_type,
            "format": fmt,
            "pillar": _match_pillar(brand, category),
            "hook": hook,
            "caption": caption,
            "hashtags": hashtags,
            "raw_generated": content.strip(),
        })
    return posts


# ── Prompt building ───────────────────────────────────────────────────────

def build_prompt(brand: models.Brand, params: dict) -> str:
    pillar = params.get("pillar")
    platform = params.get("platform")
    fmt = params.get("format")
    topic = params.get("topic")
    count = params.get("count") or brand.posts_per_batch

    if not any([pillar, platform, fmt, topic]):
        template = brand.batch_prompt_template or "Create {count} posts."
        try:
            return template.format(count=count)
        except (KeyError, IndexError):
            return template

    pillar_names = {p["key"]: p["name"] for p in (brand.pillars or [])}
    lines = [f"Create {count} post{'s' if count != 1 else ''} now."]
    if pillar:
        lines.append(f"Content pillar: {pillar_names.get(pillar, pillar)}.")
    if platform:
        lines.append(f"Platform: {platform}.")
    else:
        lines.append(f"Platforms: rotate across {', '.join(brand.platforms)}.")
    if fmt:
        lines.append(f"Format: {fmt.replace('_', ' ')}.")
    if topic:
        lines.append(f"Topic/angle: {topic}.")
    lines.append("Every post must follow the OUTPUT FORMAT exactly (starting with **PLATFORM:**). Vary the hooks.")
    return "\n".join(lines)


# ── Run execution (called from BackgroundTasks / scheduler jobs) ──────────

def execute_generation_run(run_id: int) -> None:
    """Runs with its own DB session — safe for background execution."""
    db: Session = SessionLocal()
    try:
        run = db.get(models.GenerationRun, run_id)
        if run is None:
            return
        brand = db.get(models.Brand, run.brand_id)

        prompt = build_prompt(brand, run.params or {})
        run.prompt_used = prompt
        run.model = MODEL
        db.commit()

        from content_generator import generate_post
        raw = generate_post(prompt, streaming=False, system_prompt=brand.system_prompt, model=MODEL)
        run.raw_output = raw

        parsed = parse_generated_posts(brand, raw)
        if not parsed:
            run.status = "failed"
            run.error = "No posts parsed from model output — check the brand's OUTPUT FORMAT markers."
            db.commit()
            return

        for item in parsed:
            post = models.Post(
                brand_id=brand.id,
                generation_run_id=run.id,
                status=models.PENDING_APPROVAL,
                video_status=models.VIDEO_QUEUED if item["format"] == "reel_script" else models.VIDEO_NONE,
                **item,
            )
            db.add(post)
            db.flush()
            if brand.autonomy == models.AUTONOMY_AUTO:
                auto_assign(db, post)
                post.status = models.SCHEDULED

        run.status = "done"
        run.post_count = len(parsed)
        db.commit()
    except Exception as e:  # noqa: BLE001 — record failure on the run row
        db.rollback()
        run = db.get(models.GenerationRun, run_id)
        if run is not None:
            run.status = "failed"
            run.error = str(e)[:2000]
            db.commit()
    finally:
        db.close()


def start_generation_run(db: Session, brand: models.Brand, params: dict, trigger: str = "manual") -> models.GenerationRun:
    run = models.GenerationRun(
        brand_id=brand.id,
        trigger=trigger,
        params={k: v for k, v in params.items() if v is not None},
        status="running",
        created_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    return run
