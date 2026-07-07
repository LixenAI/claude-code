"""
Content generator using Claude API (claude-opus-4-6) with adaptive thinking.
Generates platform-ready social media posts for Lixen.AI.
"""

import anthropic
import json

SYSTEM_PROMPT = """# IDENTITY
You are the Lixen.AI Social Media Content Creator — a senior
direct-response copywriter and social media strategist
specializing in AI products for med spas and beauty businesses.

# YOUR JOB
Create high-converting, platform-ready social media content
that attracts med spa owners, agitates their pain points, and
drives them to book a discovery call with Lixen.AI.

# BRAND VOICE
- Tone: Professional, punchy, benefit-driven, empathetic
- Style: Direct response — every word earns its place
- Never use: tech jargon, buzzwords, or vague language
- Always use: concrete outcomes, numbers, and emotional triggers

# TARGET AUDIENCE
Med spa and beauty clinic owners with:
- 1–20 staff members
- $100k+ annual revenue
- Pain points: missed calls, unread DMs, no-shows, manual booking
- Goal: Fill their calendar without adding more work

# LIXEN.AI PRODUCT CONTEXT
- Done-for-you AI operating system for med spas
- Answers calls 24/7, replies to DMs, books appointments
- Two plans: Smart (core automation) and Pro (full operating system)
- Core promise: "Never miss another booking."
- Key message: "Your AI front desk that never clocks out."

# CONTENT CATEGORIES (rotate through these)
1. PAIN AGITATION — Make them feel the cost of missed calls
2. EDUCATION — Explain AI front desk simply, no jargon
3. SOCIAL PROOF — Results, demos, case studies, before/after
4. OFFER — Smart/Pro plans, discovery call CTA, urgency
5. ENGAGEMENT — Polls, questions, relatable scenarios

# OUTPUT FORMAT
When creating a post, ALWAYS deliver this structure:

**PLATFORM:** [Instagram / TikTok / Facebook]
**CATEGORY:** [Pain / Education / Proof / Offer / Engagement]
**FORMAT:** [Reel Script / Carousel / Caption / Story]

---HOOK (0-3 seconds)---
[Scroll-stopping first line — make them stop dead]

---BODY---
[Problem → Agitate → Solution → Brief proof]

---CTA---
[One clear action — DM "AUDIT", Book a call, Comment below]

---HASHTAGS---
[10-15 relevant hashtags]

---PLATFORM VARIANTS---
[Adjust tone/length for each platform if multi-platform post]

# CONTENT RULES
✅ Always lead with PAIN or CURIOSITY in the hook
✅ Always end with ONE clear CTA
✅ Keep hooks under 10 words
✅ Write like you're talking to one person, not a crowd
✅ Reels scripts: max 45 seconds when read aloud
✅ Carousels: max 7 slides, each slide = one idea
✅ Captions: short paragraphs, lots of white space
❌ Never start with "Are you..." — it's weak
❌ Never use "game-changer", "revolutionary", or "innovative"
❌ Never write more than 3 sentences in a row without a break"""

# Weekly content batch prompt
WEEKLY_BATCH_PROMPT = """Create this week's 5 posts — one for each content category:
1. PAIN AGITATION post for Instagram (Reel Script, 30 seconds, topic: missed calls costing revenue, CTA: DM "AUDIT")
2. EDUCATION post for Facebook (Carousel, 5 slides, topic: how AI front desk works, CTA: Book a discovery call)
3. SOCIAL PROOF post for TikTok (Reel Script, 30 seconds, topic: med spa booking results, CTA: Comment "RESULTS")
4. OFFER post for Instagram (Caption, topic: Smart vs Pro plan, CTA: Link in bio)
5. ENGAGEMENT post for all platforms (Caption, topic: no-shows poll/question, CTA: Comment "NOSHOWS")

Deliver all 5 posts in full, formatted and copy-paste ready."""


def generate_post(
    prompt: str,
    streaming: bool = True,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = "claude-opus-4-6",
) -> str:
    """
    Generate a social media post using Claude with adaptive thinking.
    Uses streaming for long outputs to avoid timeouts.
    `system_prompt` defaults to the Lixen.AI prompt; pass a brand's
    prompt to generate for other brands.
    """
    client = anthropic.Anthropic()

    if streaming:
        with client.messages.stream(
            model=model,
            max_tokens=64000,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            full_text = ""
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_text += text
            print()
            return full_text
    else:
        with client.messages.stream(
            model=model,
            max_tokens=32000,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            return "".join(stream.text_stream)


def generate_weekly_batch() -> str:
    """Generate a full week of 5 posts across all categories and platforms."""
    print("Generating weekly content batch...\n")
    return generate_post(WEEKLY_BATCH_PROMPT, streaming=True)


def generate_single_post(
    category: str,
    platform: str,
    format_type: str,
    topic: str,
    cta: str,
) -> str:
    """Generate a single targeted post."""
    prompt = (
        f"Create a {format_type} for {platform}.\n"
        f"Category: {category}.\n"
        f"Topic: {topic}.\n"
        f"CTA: {cta}"
    )
    print(f"Generating {platform} {category} post...\n")
    return generate_post(prompt, streaming=True)


def parse_posts_from_batch(batch_output: str) -> list[dict]:
    """
    Extract individual posts from a batch generation output.
    Returns a list of dicts with platform, category, and content.
    """
    posts = []
    sections = batch_output.split("**PLATFORM:**")
    for section in sections[1:]:
        lines = section.strip().split("\n")
        platform_line = lines[0].strip() if lines else ""
        platform = platform_line.split("/")[0].strip()

        category = ""
        for line in lines:
            if "**CATEGORY:**" in line:
                category = line.replace("**CATEGORY:**", "").strip()
                break

        posts.append({
            "platform": platform,
            "category": category,
            "content": "**PLATFORM:**" + section.strip(),
        })
    return posts


if __name__ == "__main__":
    result = generate_weekly_batch()
    posts = parse_posts_from_batch(result)
    print(f"\n\nParsed {len(posts)} posts from batch.")
    for i, post in enumerate(posts, 1):
        print(f"  Post {i}: {post['platform']} — {post['category']}")
