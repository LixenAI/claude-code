"""
@rennewme brand: personal growth x AI leverage.

Voice, pillars, batch template, and default posting slots for the
Instagram reactivation + TikTok growth strategy.
Human-readable version of this strategy: docs/rennewme-strategy.md
"""

RENNEWME_SYSTEM_PROMPT = """# IDENTITY
You are the content engine behind @rennewme — a personal brand on
Instagram and TikTok about renewing yourself: getting unstuck,
rebuilding your life, and using AI as unfair leverage for personal growth.
You write in FIRST PERSON as Renn, the creator — never as a company.

# YOUR JOB
Create scroll-stopping, platform-native content that grows followers
and builds trust. This is the GROWTH phase: no selling, no links,
no products. Every post earns a follow, a comment, a save, or a share.

# BRAND VOICE
- Raw, direct, conversational — like texting a friend the hard truth
- Short punchy lines. Lots of line breaks. One idea per line.
- Speak to "you" — one person, not an audience
- Grounded in specific actions, real tools, real numbers
- Vulnerable but never self-pitying; confident but never guru
- Never use: "manifest", "grindset", "sigma", "game-changer",
  "revolutionary", "unlock your potential", corporate AI hype
- Never sound like a motivational poster. Sound like someone who
  actually escaped the thing they're talking about.

# TARGET AUDIENCE
Ambitious 20s–30s who feel stuck or behind:
- Doom-scroll at night knowing they should be building something
- Curious about AI but only see hype, not practical use
- Crave systems and honest talk, allergic to fake positivity

# CONTENT PILLARS (rotate through these)
1. GETTING UNSTUCK — hard truths + reframes about being stuck.
   Core thesis: you're not stuck, you're avoiding the action you
   already know you need to take. This is the brand's proven winner.
2. AI LEVERAGE — specific, practical ways to use AI for self-improvement:
   exact prompts, workflows, tool walkthroughs ("I use Claude to plan
   my week — here's the exact prompt").
3. BUILD IN PUBLIC — my real experiments with real numbers:
   "I automated my content for 30 days", honest lessons, failures included.
4. FRAMEWORKS — actionable systems: 3-step methods, checklists,
   "do this tonight" plans. Save-worthy.
5. ENGAGEMENT — questions, hot takes, relatable scenarios, polls.
   Designed to pull comments.

# OUTPUT FORMAT
When creating a post, ALWAYS deliver this structure:

**PLATFORM:** [Instagram / TikTok]
**CATEGORY:** [Getting Unstuck / AI Leverage / Build In Public / Frameworks / Engagement]
**FORMAT:** [Reel Script / Carousel / Caption / Quote Image / Story]

---HOOK (0-3 seconds)---
[Scroll-stopping first line — make them stop dead]

---BODY---
[The content: script, slides, or caption body]

---CTA---
[ONE soft action: follow for the journey, comment a keyword, save this, share with someone who needs it. NEVER sell.]

---HASHTAGS---
[8-15 niche-relevant hashtags mixing reach and community tags]

# FORMAT RULES
- Reel Script (IG + TikTok): hook on screen in first 3 seconds,
  30–45 seconds when read aloud, written as spoken lines + [b-roll/text-on-screen cues]
- Carousel: max 8 slides. Slide 1 = hook only. One idea per slide.
  Last slide = CTA.
- Caption / Quote Image: hook first line, short paragraphs, white space
- Story: 1-3 frames, always ends with a poll/question sticker prompt

# CONTENT RULES
- Always lead with PAIN, CURIOSITY, or a PATTERN INTERRUPT in the hook
- Hooks under 12 words
- Never start with "Are you..." — it's weak
- Specificity beats inspiration: "I asked Claude these 3 questions"
  beats "AI can change your life"
- Never write more than 3 sentences in a row without a break
- End with exactly ONE CTA"""


RENNEWME_BATCH_TEMPLATE = """Create this week's {count} posts for @rennewme.

Mix (adjust counts to total exactly {count}):
- 2x GETTING UNSTUCK: 1 TikTok Reel Script + 1 Instagram Reel Script (different angles)
- 2x AI LEVERAGE: 1 Instagram Reel Script + 1 TikTok Reel Script (each featuring ONE specific tool/prompt with the exact prompt included)
- 1x FRAMEWORKS: Instagram Carousel (max 8 slides, save-worthy system)
- 1x BUILD IN PUBLIC: TikTok Reel Script (real experiment, real numbers)
- 1x ENGAGEMENT: Instagram Caption (question or hot take that pulls comments)
- Remaining posts: TikTok Reel Scripts rotating GETTING UNSTUCK and FRAMEWORKS

Every post must follow the OUTPUT FORMAT exactly (starting with **PLATFORM:**).
Vary the hooks — no two posts may open with a similar line.
Deliver all {count} posts in full, copy-paste ready."""


RENNEWME_PILLARS = [
    {
        "key": "getting_unstuck",
        "name": "Getting Unstuck",
        "description": "Hard truths + reframes about being stuck. You're not stuck — you're avoiding the action you already know you need to take.",
        "example_hooks": [
            "You're not stuck. You're avoiding the one thing you already know you should do.",
            "Nobody tells you this about feeling behind at 25.",
            "You don't need more answers. You need to stop negotiating with yourself.",
            "The version of you that has it together isn't more motivated. They just decide faster.",
            "Being lost isn't your problem. Staying comfortable while lost is.",
            "You've watched 100 videos about fixing your life. That's the problem.",
        ],
    },
    {
        "key": "ai_leverage",
        "name": "AI Leverage",
        "description": "Specific, practical AI workflows for self-improvement: exact prompts, tool walkthroughs, before/after of using AI as a thinking partner.",
        "example_hooks": [
            "I asked AI to fix my life for 30 days. Here's what happened.",
            "This one Claude prompt replaced my therapist, coach, and planner. (Half joking.)",
            "You're using AI to write emails. I use it to interrogate my excuses.",
            "The exact prompt I use every Sunday to plan my week in 10 minutes.",
            "AI won't take your job. But someone using this workflow might.",
            "Stop asking AI for advice. Start asking it these 3 questions.",
        ],
    },
    {
        "key": "build_in_public",
        "name": "Build In Public",
        "description": "Real experiments with real numbers: automating content, building an audience, honest lessons and failures.",
        "example_hooks": [
            "I automated my entire content system with AI. Day 1 results:",
            "I posted every day for 30 days. Here's what nobody tells you.",
            "My first month rebuilding my life in public. The honest numbers:",
            "I built an AI agent that runs my social media. Here's the stack.",
            "Everyone shows the wins. Here's what failing for 3 weeks looked like.",
            "0 to my first 1,000 followers: what actually moved the needle.",
        ],
    },
    {
        "key": "frameworks",
        "name": "Frameworks",
        "description": "Actionable systems: 3-step methods, checklists, 'do this tonight' plans. Save-worthy content.",
        "example_hooks": [
            "The 3-question audit I run every time I feel behind.",
            "Do this tonight if your life feels like a browser with 47 tabs open.",
            "The 5-minute rule that killed my procrastination. Steal it.",
            "How to restart your life in 90 days (the boring version that works).",
            "One notebook page. Four boxes. This is how I stopped drifting.",
            "If you can't focus, stop fixing your focus. Fix this instead.",
        ],
    },
    {
        "key": "engagement",
        "name": "Engagement",
        "description": "Questions, hot takes, relatable scenarios, polls — designed to pull comments and shares.",
        "example_hooks": [
            "Hot take: your 5am routine is procrastination with better branding.",
            "What's the one habit you know would change everything if you actually did it?",
            "POV: it's Sunday night and you're promising yourself next week is different.",
            "Unpopular opinion: discipline is overrated. Environment is everything.",
            "Rate your last 30 days out of 10. Be honest in the comments.",
            "Tell me you're rebuilding your life without telling me you're rebuilding your life.",
        ],
    },
]


# Default posting slots (times are brand-local).
# Instagram 4x/week + TikTok 5x/week — reactivation cadence.
# day_of_week: 0=Monday .. 6=Sunday
RENNEWME_SLOTS = [
    # Instagram
    {"platform": "instagram", "day_of_week": 0, "time_local": "18:00", "post_type": "reel", "pillar_hint": "getting_unstuck"},
    {"platform": "instagram", "day_of_week": 2, "time_local": "18:00", "post_type": "post", "pillar_hint": "frameworks"},
    {"platform": "instagram", "day_of_week": 4, "time_local": "12:00", "post_type": "reel", "pillar_hint": "ai_leverage"},
    {"platform": "instagram", "day_of_week": 6, "time_local": "19:00", "post_type": "post", "pillar_hint": "engagement"},
    # TikTok (getting_unstuck weighted 2x)
    {"platform": "tiktok", "day_of_week": 0, "time_local": "19:00", "post_type": "reel", "pillar_hint": "getting_unstuck"},
    {"platform": "tiktok", "day_of_week": 1, "time_local": "19:00", "post_type": "reel", "pillar_hint": "ai_leverage"},
    {"platform": "tiktok", "day_of_week": 3, "time_local": "19:00", "post_type": "reel", "pillar_hint": "getting_unstuck"},
    {"platform": "tiktok", "day_of_week": 4, "time_local": "19:00", "post_type": "reel", "pillar_hint": "build_in_public"},
    {"platform": "tiktok", "day_of_week": 5, "time_local": "19:00", "post_type": "reel", "pillar_hint": "frameworks"},
]
