"""
Anthropic ↔ GoHighLevel Webhook Integration.

This HTTP server receives webhook calls from GHL Workflows and
responds using Claude (claude-opus-4-6). Use this to power:

  - AI-generated replies to contacts (DMs, SMS, email)
  - Content generation triggered by GHL workflow actions
  - Lead qualification / conversation AI
  - Custom AI actions inside GHL automations

── GHL Setup ──────────────────────────────────────────────────────────────
1. Deploy this server (or run locally + expose via ngrok)
2. In GHL: Automation → Workflows → + New Workflow
3. Add action: "Webhook" (Custom Webhook / HTTP Request)
4. URL: https://your-server.com/ghl/ai
5. Method: POST
6. Body (JSON):
   {
     "secret":       "{{your_webhook_secret}}",
     "action":       "generate_reply",         ← or "generate_content"
     "contact_name": "{{contact.name}}",
     "message":      "{{last_message_body}}",
     "platform":     "sms",                    ← sms | email | instagram | facebook
     "context":      "optional extra info"
   }
7. Use the response field "reply" in the next workflow step
   (e.g. Send Message action)
───────────────────────────────────────────────────────────────────────────

Supported actions:
  generate_reply    → craft a reply to a contact message
  generate_content  → create a social media post (returns formatted post)
  qualify_lead      → score and summarise a lead from contact fields
"""

import os
import hmac
import hashlib
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import anthropic
from dotenv import load_dotenv

load_dotenv()

REPLY_SYSTEM = """You are the AI assistant for Lixen.AI — a done-for-you AI operating
system for med spas. You reply to inbound messages from med spa owners and beauty clinic
owners on behalf of the Lixen.AI team.

Tone: warm, professional, direct. Never salesy. Sound like a knowledgeable team member.
Goal: book a discovery call or keep the conversation moving toward a call.
CTA options: "Book a free 15-min call at lixen.ai" or "Reply with any questions".
Keep replies under 150 words unless asked something detailed."""

CONTENT_SYSTEM = """You are the Lixen.AI Social Media Content Creator.
Create a single platform-ready post based on the input. Return ONLY the post text,
ready to copy-paste. No markdown headers, no explanations."""

QUALIFY_SYSTEM = """You are a lead qualification assistant for Lixen.AI.
Given contact information, score the lead 1-10 and summarise in 2-3 sentences.
Return JSON: {"score": 8, "summary": "...", "recommended_action": "..."}"""


def _check_secret(body: dict) -> bool:
    expected = os.environ.get("WEBHOOK_SECRET", "")
    if not expected:
        return True  # Secret not configured — allow all (set one in production)
    return hmac.compare_digest(body.get("secret", ""), expected)


def call_claude(system: str, user_message: str, max_tokens: int = 1024) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
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


def handle_generate_reply(data: dict) -> dict:
    contact_name = data.get("contact_name", "there")
    message = data.get("message", "")
    platform = data.get("platform", "general")
    context = data.get("context", "")

    user_prompt = (
        f"Contact name: {contact_name}\n"
        f"Platform: {platform}\n"
        f"Their message: {message}\n"
    )
    if context:
        user_prompt += f"Additional context: {context}\n"
    user_prompt += "\nWrite a reply."

    reply = call_claude(REPLY_SYSTEM, user_prompt, max_tokens=512)
    return {"success": True, "action": "generate_reply", "reply": reply}


def handle_generate_content(data: dict) -> dict:
    topic = data.get("topic", "Lixen.AI AI front desk for med spas")
    platform = data.get("platform", "Instagram")
    category = data.get("category", "Pain Agitation")
    cta = data.get("cta", 'DM "AUDIT"')

    user_prompt = (
        f"Platform: {platform}\n"
        f"Category: {category}\n"
        f"Topic: {topic}\n"
        f"CTA: {cta}\n\n"
        "Write the post now."
    )

    content = call_claude(CONTENT_SYSTEM, user_prompt, max_tokens=2048)
    return {"success": True, "action": "generate_content", "content": content}


def handle_qualify_lead(data: dict) -> dict:
    contact_info = {
        k: v for k, v in data.items()
        if k not in ("secret", "action")
    }
    user_prompt = f"Lead data:\n{json.dumps(contact_info, indent=2)}\n\nQualify this lead."
    result_text = call_claude(QUALIFY_SYSTEM, user_prompt, max_tokens=512)

    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        result = {"raw": result_text}

    return {"success": True, "action": "qualify_lead", **result}


ACTION_HANDLERS = {
    "generate_reply": handle_generate_reply,
    "generate_content": handle_generate_content,
    "qualify_lead": handle_qualify_lead,
}


class GHLWebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[Webhook] {self.address_string()} {format % args}")

    def send_json(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/ghl/ai":
            self.send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON"})
            return

        if not _check_secret(data):
            self.send_json(401, {"error": "Unauthorized"})
            return

        action = data.get("action")
        handler = ACTION_HANDLERS.get(action)

        if not handler:
            self.send_json(400, {
                "error": f"Unknown action '{action}'",
                "supported": list(ACTION_HANDLERS.keys()),
            })
            return

        try:
            result = handler(data)
            self.send_json(200, result)
        except Exception as e:
            print(f"[Webhook] Error in {action}: {e}")
            self.send_json(500, {"error": str(e)})

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "ok", "service": "lixen-ai-webhook"})
        else:
            self.send_json(404, {"error": "Not found"})


def run_server(port: int = None):
    port = port or int(os.environ.get("WEBHOOK_PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), GHLWebhookHandler)
    print(f"Lixen.AI GHL Webhook Server running on port {port}")
    print(f"Endpoint: POST http://0.0.0.0:{port}/ghl/ai")
    print(f"Health:   GET  http://0.0.0.0:{port}/health")
    print("\nSupported actions: generate_reply | generate_content | qualify_lead")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    run_server()
