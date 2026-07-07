"""
Anthropic ↔ GoHighLevel Webhook Server (FastAPI)

Receives calls from GHL Workflows and responds using Claude Opus 4.6.

── Endpoints ──────────────────────────────────────────────────────────────
  GET  /health                  → health check
  POST /ghl/generate-and-post   → generate content + post to social media
  POST /ghl/reply               → generate reply to a contact message
  POST /ghl/qualify-lead        → score + summarise a lead
  POST /ghl/content             → generate content only (no posting)
───────────────────────────────────────────────────────────────────────────

── GHL Workflow Setup ──────────────────────────────────────────────────────
1. Deploy this server (or use `ngrok http 8000` to expose locally)
2. Automation → Workflows → + New Workflow
3. Add action: Custom Webhook / HTTP Request
4. URL: https://your-server.com/ghl/generate-and-post
5. Method: POST
6. Body example — weekly content run:
   {
     "secret": "your_webhook_secret",
     "platforms": ["facebook", "instagram", "tiktok"]
   }
7. Body example — reply to inbound DM:
   {
     "secret": "your_webhook_secret",
     "contact_name": "{{contact.name}}",
     "message": "{{last_message_body}}",
     "platform": "instagram",
     "contact_id": "{{contact.id}}"
   }
8. Use {{webhook.reply}} in a following Send Message action
───────────────────────────────────────────────────────────────────────────
"""

import os
import hmac
import json
import asyncio
from datetime import datetime, timezone

import anthropic
import uvicorn
from fastapi import APIRouter, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from design_library import get_design_url
from social_poster import post_to_ghl

load_dotenv()

# Endpoints live on a router so the unified app (app/server.py) can mount
# them alongside the new /api routes; the standalone `app` below keeps
# `python main.py webhook` working unchanged.
router = APIRouter()

# ── Prompts ──────────────────────────────────────────────────────────────

REPLY_SYSTEM = """You are the AI assistant for Lixen.AI — a done-for-you AI operating
system for med spas. You reply to inbound messages from med spa owners on behalf of
the Lixen.AI team.

Tone: warm, professional, direct. Never salesy. Sound like a knowledgeable team member.
Goal: book a discovery call or keep the conversation moving toward one.
CTA options: "Book a free 15-min call at lixen.ai" or "Reply with any questions."
Keep replies under 150 words unless asked something detailed.
Never mention you are an AI unless directly asked."""

CONTENT_SYSTEM = """You are the Lixen.AI Social Media Content Creator — a senior
direct-response copywriter for med spas. Create a single platform-ready post.
Return ONLY the post text, ready to copy-paste. No markdown headers. No explanations."""

QUALIFY_SYSTEM = """You are a lead qualification assistant for Lixen.AI.
Given contact information, score the lead 1-10 and summarise in 2-3 sentences.
Return only valid JSON: {"score": 8, "tier": "hot", "summary": "...", "recommended_action": "..."}
Tiers: hot (8-10), warm (5-7), cold (1-4)."""


# ── Helpers ──────────────────────────────────────────────────────────────

def _verify_secret(body: dict) -> bool:
    expected = os.environ.get("WEBHOOK_SECRET", "")
    if not expected:
        return True
    incoming = body.get("secret", "")
    return hmac.compare_digest(str(incoming), expected)


async def call_claude(system: str, user_message: str, max_tokens: int = 1024) -> str:
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    for block in response.content:
        if block.type == "text":
            return block.text.strip()
    return ""


def _post_via_ghl(body: str, platforms: list[str], media_urls: list[str] = None) -> dict:
    """Synchronous GHL Social Planner post (called from async context via run_in_executor)."""
    media = [{"url": u, "type": "Photo"} for u in media_urls] if media_urls else []
    return post_to_ghl(body=body, platforms=platforms, media=media)


def _send_ghl_message(contact_id: str, message: str, channel: str = "sms") -> dict:
    """Send a message to a GHL contact via the Conversations API."""
    import requests as req

    GHL_API_BASE = "https://services.leadconnectorhq.com"
    url = f"{GHL_API_BASE}/conversations/messages"
    headers = {
        "Authorization": f"Bearer {os.environ['GHL_API_KEY']}",
        "Version": "2021-04-15",
        "Content-Type": "application/json",
    }

    channel_map = {
        "sms": "SMS",
        "email": "Email",
        "instagram": "IG",
        "facebook": "FB",
        "whatsapp": "WhatsApp",
    }

    payload = {
        "type": channel_map.get(channel.lower(), "SMS"),
        "contactId": contact_id,
        "message": message,
    }

    response = req.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


# ── Routes ───────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "lixen-ai-webhook", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/ghl/generate-and-post")
async def generate_and_post(request: Request):
    """
    Generate social media content with Claude and immediately post it
    via GHL Social Planner.

    Body:
      secret      — webhook secret (required if WEBHOOK_SECRET is set)
      platforms   — ["facebook","instagram","tiktok"] (default: all three)
      topic       — optional topic override
      category    — optional category override (Pain/Education/Proof/Offer/Engagement)
      media_url   — optional public image/video URL
    """
    data = await request.json()

    if not _verify_secret(data):
        raise HTTPException(status_code=401, detail="Unauthorized")

    platforms = data.get("platforms", ["facebook", "instagram", "tiktok"])
    topic = data.get("topic", "AI front desk for med spas")
    category = data.get("category", "Pain Agitation")
    cta = data.get("cta", 'DM "AUDIT"')
    media_url = data.get("media_url")

    # Step 1: Generate content
    user_prompt = (
        f"Platform: {', '.join(platforms)}\n"
        f"Category: {category}\n"
        f"Topic: {topic}\n"
        f"CTA: {cta}\n\n"
        "Write the post now. Return only the caption, ready to publish."
    )
    content = await call_claude(CONTENT_SYSTEM, user_prompt, max_tokens=2048)

    # Step 2: Resolve image — explicit override takes priority, then design library
    if not media_url:
        primary_platform = platforms[0] if platforms else "instagram"
        media_url = get_design_url(category, primary_platform)

    # Step 3: Post via GHL (run sync call in thread pool)
    loop = asyncio.get_running_loop()
    ghl_result = await loop.run_in_executor(
        None, _post_via_ghl, content, platforms, [media_url] if media_url else None
    )

    return {
        "success": True,
        "content": content,
        "platforms": platforms,
        "image_url": media_url,
        "ghl_post_id": ghl_result.get("id", ghl_result.get("_id")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/ghl/reply")
async def generate_reply(request: Request):
    """
    Generate a Claude reply to a contact's inbound message.
    Optionally auto-sends it back via GHL Conversations API.

    Body:
      secret        — webhook secret
      contact_name  — contact's name (from GHL custom value)
      message       — the inbound message text
      platform      — sms | email | instagram | facebook | whatsapp
      contact_id    — GHL contact ID (required for auto_send)
      context       — optional extra context about the contact
      auto_send     — true to send the reply automatically (default: false)

    Trigger: GHL Workflow → Customer Reply / Inbound Message trigger
    Keyword filter: message contains "AUDIT" → call this endpoint
    """
    data = await request.json()

    if not _verify_secret(data):
        raise HTTPException(status_code=401, detail="Unauthorized")

    contact_name = data.get("contact_name", "there")
    message = data.get("message", "")
    platform = data.get("platform", "sms")
    contact_id = data.get("contact_id")
    context = data.get("context", "")
    auto_send = data.get("auto_send", False)

    user_prompt = (
        f"Contact name: {contact_name}\n"
        f"Platform: {platform}\n"
        f"Their message: {message}\n"
    )
    if context:
        user_prompt += f"Context: {context}\n"
    user_prompt += "\nWrite a reply."

    reply = await call_claude(REPLY_SYSTEM, user_prompt, max_tokens=512)

    result = {
        "success": True,
        "reply": reply,
        "contact_name": contact_name,
        "platform": platform,
    }

    # Optionally auto-send through GHL
    if auto_send and contact_id:
        loop = asyncio.get_running_loop()
        try:
            send_result = await loop.run_in_executor(
                None, _send_ghl_message, contact_id, reply, platform
            )
            result["sent"] = True
            result["conversation_id"] = send_result.get("conversationId")
        except Exception as e:
            result["sent"] = False
            result["send_error"] = str(e)

    return result


@router.post("/ghl/qualify-lead")
async def qualify_lead(request: Request):
    """
    Score a lead 1–10 and return a summary + recommended action.

    Body:
      secret          — webhook secret
      contact_name    — full name
      business_name   — clinic/spa name
      revenue         — estimated revenue (if known)
      staff_count     — team size
      pain_points     — what they mentioned
      source          — where they came from
      (any extra fields are included automatically)

    Returns JSON: { score, tier, summary, recommended_action }
    """
    data = await request.json()

    if not _verify_secret(data):
        raise HTTPException(status_code=401, detail="Unauthorized")

    lead_data = {k: v for k, v in data.items() if k != "secret"}
    user_prompt = f"Lead data:\n{json.dumps(lead_data, indent=2)}\n\nQualify this lead."

    result_text = await call_claude(QUALIFY_SYSTEM, user_prompt, max_tokens=512)

    try:
        qualification = json.loads(result_text)
    except json.JSONDecodeError:
        qualification = {"raw": result_text}

    return {"success": True, **qualification}


@router.post("/ghl/content")
async def generate_content_only(request: Request):
    """
    Generate social media content without posting.
    Use when you want to review before posting.

    Body:
      secret    — webhook secret
      platform  — Instagram | TikTok | Facebook | all
      category  — Pain | Education | Proof | Offer | Engagement
      topic     — specific topic or leave blank for default rotation
      cta       — call to action text
      format    — Reel Script | Carousel | Caption | Story
    """
    data = await request.json()

    if not _verify_secret(data):
        raise HTTPException(status_code=401, detail="Unauthorized")

    platform = data.get("platform", "Instagram")
    category = data.get("category", "Pain Agitation")
    topic = data.get("topic", "med spa AI front desk")
    cta = data.get("cta", 'DM "AUDIT"')
    fmt = data.get("format", "Caption")

    user_prompt = (
        f"Platform: {platform}\n"
        f"Format: {fmt}\n"
        f"Category: {category}\n"
        f"Topic: {topic}\n"
        f"CTA: {cta}\n\n"
        "Write the full post now."
    )

    content = await call_claude(CONTENT_SYSTEM, user_prompt, max_tokens=2048)

    return {
        "success": True,
        "content": content,
        "platform": platform,
        "category": category,
        "format": fmt,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Server ───────────────────────────────────────────────────────────────

# Standalone app for `python main.py webhook` / `python ghl_webhook.py`
app = FastAPI(title="Lixen.AI GHL Webhook", version="1.0.0")
app.include_router(router)


def run_server(port: int = None):
    port = port or int(os.environ.get("WEBHOOK_PORT", 8000))
    print(f"\nLixen.AI GHL Webhook Server")
    print(f"  POST http://0.0.0.0:{port}/ghl/generate-and-post")
    print(f"  POST http://0.0.0.0:{port}/ghl/reply")
    print(f"  POST http://0.0.0.0:{port}/ghl/qualify-lead")
    print(f"  POST http://0.0.0.0:{port}/ghl/content")
    print(f"  GET  http://0.0.0.0:{port}/health\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    run_server()
