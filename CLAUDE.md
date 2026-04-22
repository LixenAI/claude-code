# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

The repo root is a thin wrapper — all source lives in `social-media-agent/`. Run every command from that directory.

## Project: Lixen.AI Social Media Agent (`social-media-agent/`)

A Python agent that generates weekly social media posts with the Claude API and publishes them through GoHighLevel (GHL) Social Planner. It also exposes a FastAPI webhook server that GHL Workflows call for on-demand content, AI replies to inbound DMs, and lead qualification.

### Setup

```bash
cd social-media-agent
pip install -r requirements.txt
cp .env.example .env       # fill in ANTHROPIC_API_KEY, GHL_API_KEY, GHL_LOCATION_ID, WEBHOOK_SECRET
python main.py --mode setup    # verifies GHL auth + attempts to create GHL workflows
```

### Commonly used commands

All invoked from `social-media-agent/`:

```bash
python main.py --mode dry-run                  # generate content, print only — no posting
python main.py --mode run-now                  # generate + post via GHL Social Planner
python main.py --mode schedule                 # weekly scheduler, default Mon 07:00
python main.py --mode schedule --day friday --time 09:00
python main.py --mode webhook                  # FastAPI server on :8000 (or WEBHOOK_PORT)
python main.py --mode setup                    # re-verify GHL + (re)create workflows

python run_agent.py                             # single-process: scheduler thread + webhook server
                                                # this is what the Dockerfile / Procfile run

python design_library.py                        # list which (category, platform) slots have images
python media_uploader.py --dry-run              # preview Canva→GHL CDN uploads
python media_uploader.py                        # refresh expiring Canva URLs to permanent GHL URLs
python canva_generator.py --re-export pain_instagram   # requires CANVA_API_TOKEN in .env

docker compose up --build                       # run the combined agent in a container
```

There is no test suite, linter config, or type checker wired into this repo — don't invent one.

### Architecture

Content flows through four layers. Understand them before editing:

1. **`content_generator.py`** — Claude API calls. Uses `claude-opus-4-6` with `thinking={"type": "adaptive"}` and streaming for long outputs. `SYSTEM_PROMPT` is the canonical brand voice / audience / CTA rules; `generate_weekly_batch()` produces 5 posts covering all five content categories (Pain / Education / Proof / Offer / Engagement). `parse_posts_from_batch()` splits the batch by the `**PLATFORM:**` header the model is instructed to emit.

2. **`design_library.py`** — static mapping of `(category, platform) → [image_url, ...]`. `get_design_url()` does category-alias normalisation (`"Pain Agitation"` → `"pain"`) and platform fallback (tries `instagram`, `facebook`, `tiktok` in order). URLs must be permanent GHL CDN links (`assets.cdn.filesafe.space`); Canva signed URLs expire in ~24h and must be piped through `media_uploader.py`. `CANVA_DESIGN_IDS` keeps the source-of-truth IDs for re-exporting designs.

3. **`social_poster.py`** — GHL Social Planner client. `post_to_ghl()` handles a two-step quirk: **GHL rejects external media URLs in a single published/scheduled create**, so posts with media are created as `draft` and then PATCHed to `published`/`scheduled`. Don't "simplify" this into one call — it will fail. Account IDs for FB/IG/TikTok default to Lixen.AI's live values but are overridable via `GHL_*_ACCOUNT_ID` env vars.

4. **`scheduler.py`** — orchestrator. `run_weekly_workflow()` calls generator → parser → per-platform `post_content()`, applies `PLATFORM_LIMITS` truncation, and attaches an image from `design_library`. `start_weekly_schedule()` uses the `schedule` library with `getattr(schedule.every(), day)` to run weekly. `extract_caption()` parses the markdown-delimited sections (`---BODY---`, `---HASHTAGS---`, `---PLATFORM VARIANTS---`) the content generator emits — keep the generator's section headers and the extractor in sync if you change either.

The **webhook server** (`ghl_webhook.py`) is an independent FastAPI surface for GHL Workflows:

- `POST /ghl/generate-and-post` — generate + publish in one call
- `POST /ghl/reply` — Claude replies to inbound contact messages; if `auto_send=true` and `contact_id` is present it sends via GHL Conversations API
- `POST /ghl/qualify-lead` — scores a lead 1–10, returns JSON (`score`, `tier`, `summary`, `recommended_action`)
- `POST /ghl/content` — generate content without posting
- `GET /health`

Every POST verifies `body["secret"]` against `WEBHOOK_SECRET` using `hmac.compare_digest`. Blocking `requests` calls inside async handlers are dispatched through `loop.run_in_executor(None, ...)` — keep this pattern when adding new GHL calls.

**Entry points:**
- `main.py` — CLI dispatcher; picks one mode (setup / dry-run / run-now / schedule / webhook).
- `run_agent.py` — production entry point. Spawns the FastAPI server on a background thread and runs the weekly scheduler on the main thread. This is what `Dockerfile`, `docker-compose.yml`, and `Procfile` invoke — keep it single-process.
- `ghl_setup.py` — idempotent verifier + workflow creator. The GHL Workflows API isn't available on every plan; on failure it prints manual setup instructions rather than raising.

### Conventions to preserve

- **Claude model & thinking mode:** all three Claude call sites (`content_generator.py`, `ghl_webhook.py`) use `claude-opus-4-6` with `thinking={"type": "adaptive"}`. Keep them consistent when upgrading.
- **Env-var-first configuration:** secrets and IDs come from `.env` via `python-dotenv`. Defaults for `GHL_*_ACCOUNT_ID` and `GHL_USER_ID` are baked into `social_poster.py` / `ghl_setup.py` for the Lixen.AI location; override via env rather than editing code.
- **Post-output format is a contract:** `content_generator.SYSTEM_PROMPT` instructs Claude to emit `**PLATFORM:**`, `**CATEGORY:**`, `---HOOK---`, `---BODY---`, `---CTA---`, `---HASHTAGS---`, `---PLATFORM VARIANTS---`. `parse_posts_from_batch` and `extract_caption` depend on those exact delimiters.
- **Image refresh workflow:** when a Canva URL 404s, re-export via `canva_generator.py --re-export <key>` (keys in `CANVA_DESIGN_IDS`), then run `media_uploader.py` to upload to GHL CDN, then paste the permanent URLs into `DESIGNS` in `design_library.py`.
- **No test framework.** Modules have `if __name__ == "__main__"` smoke blocks (e.g. `social_poster.py` posts a test caption to Facebook live — don't run it casually).
