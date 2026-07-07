# Social Media Manager — multi-brand AI content platform

One place to **generate content with Claude, render short videos, schedule,
approve, and auto-post** — built for growing the **@rennewme** personal brand
(Instagram + TikTok), with the legacy Lixen.AI GHL pipeline still supported as
a second brand.

## What it does

- **Content engine** — Claude writes platform-ready posts in each brand's voice
  against its content pillars (see `docs/rennewme-strategy.md`).
- **Short-video generation** — reel scripts are rendered into vertical
  1080×1920 MP4s with an AI voiceover (edge-tts) and animated captions (ffmpeg).
  No paid video APIs.
- **Approval queue** — generated posts wait for your review; edit, approve,
  reject, or regenerate from the dashboard. Flip a brand to full-auto when ready.
- **Scheduling** — recurring posting slots per brand; approved posts auto-assign
  to the next free slot; a background poller publishes them on time.
- **Publishing (GHL-independent)** — pluggable drivers per brand:
  - `native`: Instagram Graph API + TikTok Content Posting API
  - `manual`: everything rendered + queued as *ready*; you post with one tap
    and hit "Mark posted" (no credentials needed — the default until APIs are set up)
  - `ghl`: legacy GoHighLevel Social Planner (Lixen.AI)
- **Web dashboard** — React app served by the same FastAPI process:
  Dashboard, Queue, Calendar, Generate, Brand Settings.

## Quick start

```bash
cp .env.example .env          # set ANTHROPIC_API_KEY at minimum
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
python main.py --mode serve   # dashboard on http://localhost:8000
```

Or with Docker (ffmpeg included):

```bash
docker compose up --build
```

Set `PUBLISH_DRY_RUN=1` while testing — publishes are logged, not sent.

## Going live with @rennewme

1. Deploy somewhere with a public HTTPS URL and set `PUBLIC_BASE_URL`.
2. **Instagram**: convert @rennewme to a Professional account, link it to a
   Facebook Page, create a Meta app with `instagram_content_publish`, set
   `IG_ACCESS_TOKEN` + `IG_USER_ID`.
3. **TikTok**: create an app at developers.tiktok.com with the Content Posting
   API, set `TIKTOK_ACCESS_TOKEN`. Unaudited apps upload to your TikTok inbox
   (video arrives as a draft you confirm in the app — still 90% automated).
   After audit approval, set `TIKTOK_DIRECT_POST=1`.
4. Until then, leave the brand publisher on `native` — posts without
   credentials land in **Ready to post**: download the rendered video, post it,
   tap *Mark posted*. Or set the publisher to `manual` explicitly.
5. Approve your first batch from the Queue. When you trust the output, flip
   Brand Settings → Workflow to **full-auto**.

## Legacy CLI (Lixen.AI)

`python main.py --mode dry-run|run-now|schedule|webhook|setup` all work as
before; `/ghl/*` webhook endpoints are mounted in the unified server too.

## Tests

```bash
pytest tests/
```
