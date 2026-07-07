# @rennewme — Instagram Reactivation & Growth Strategy

**Positioning:** personal growth × AI leverage. You're the person who escaped being
stuck — partly by using AI as a thinking partner — and you're documenting the system
in public. Nobody else in the self-improvement niche is showing *practical* AI
workflows for personal growth; that intersection is the moat.

**Goal (growth phase):** attention + followers. No selling, no links-in-bio pushes,
no products. Monetization (coaching, digital products, brand deals) comes after the
audience exists. Every post earns exactly one of: follow, comment, save, share.

**Proof it works:** your TikTok post about "being stuck = avoiding action" pulled
~29K likes. That's the brand's core thesis and pillar #1.

---

## Content Pillars

| # | Pillar | What it is | Role |
|---|--------|-----------|------|
| 1 | **Getting Unstuck** | Hard truths + reframes: you're not stuck, you're avoiding the action you already know | The proven winner — weighted 2× on TikTok |
| 2 | **AI Leverage** | Exact prompts, tool walkthroughs, "I use Claude to plan my week" | The differentiator — save-magnet |
| 3 | **Build In Public** | Real experiments with real numbers ("I automated my content for 30 days") | Trust + story arc that makes people follow |
| 4 | **Frameworks** | 3-step systems, checklists, "do this tonight" | Saves + shares |
| 5 | **Engagement** | Questions, hot takes, relatable POVs, polls | Comments → reach |

## Voice Rules

- First person, raw, direct — like texting a friend the hard truth
- Short punchy lines, generous line breaks, one idea per line
- Specificity beats inspiration: "I asked Claude these 3 questions" > "AI can change your life"
- Banned: "manifest", "grindset", "sigma", "game-changer", "unlock your potential", corporate AI hype
- Vulnerable but never self-pitying; confident but never guru

## Posting Cadence (reactivation)

**Instagram — 4×/week** (dormant account: consistency > volume, reels > everything)

| Day | Time (ET) | Format | Pillar |
|-----|-----------|--------|--------|
| Mon | 6:00 PM | Reel | Getting Unstuck |
| Wed | 6:00 PM | Carousel | Frameworks |
| Fri | 12:00 PM | Reel | AI Leverage |
| Sun | 7:00 PM | Quote/Caption | Engagement / Build In Public |

**TikTok — 5×/week** (algorithm rewards frequency; Getting Unstuck weighted 2×)

| Day | Time (ET) | Pillar |
|-----|-----------|--------|
| Mon | 7:00 PM | Getting Unstuck |
| Tue | 7:00 PM | AI Leverage |
| Thu | 7:00 PM | Getting Unstuck |
| Fri | 7:00 PM | Build In Public |
| Sat | 7:00 PM | Frameworks |

These slots are seeded in the app (Brand Settings → Posting slots) and drive
auto-scheduling when you approve posts.

## Hook Library (30 starters)

**Getting Unstuck**
1. You're not stuck. You're avoiding the one thing you already know you should do.
2. Nobody tells you this about feeling behind at 25.
3. You don't need more answers. You need to stop negotiating with yourself.
4. The version of you that has it together isn't more motivated. They just decide faster.
5. Being lost isn't your problem. Staying comfortable while lost is.
6. You've watched 100 videos about fixing your life. That's the problem.

**AI Leverage**
7. I asked AI to fix my life for 30 days. Here's what happened.
8. This one Claude prompt replaced my therapist, coach, and planner. (Half joking.)
9. You're using AI to write emails. I use it to interrogate my excuses.
10. The exact prompt I use every Sunday to plan my week in 10 minutes.
11. AI won't take your job. But someone using this workflow might.
12. Stop asking AI for advice. Start asking it these 3 questions.

**Build In Public**
13. I automated my entire content system with AI. Day 1 results:
14. I posted every day for 30 days. Here's what nobody tells you.
15. My first month rebuilding my life in public. The honest numbers:
16. I built an AI agent that runs my social media. Here's the stack.
17. Everyone shows the wins. Here's what failing for 3 weeks looked like.
18. 0 to my first 1,000 followers: what actually moved the needle.

**Frameworks**
19. The 3-question audit I run every time I feel behind.
20. Do this tonight if your life feels like a browser with 47 tabs open.
21. The 5-minute rule that killed my procrastination. Steal it.
22. How to restart your life in 90 days (the boring version that works).
23. One notebook page. Four boxes. This is how I stopped drifting.
24. If you can't focus, stop fixing your focus. Fix this instead.

**Engagement**
25. Hot take: your 5am routine is procrastination with better branding.
26. What's the one habit you know would change everything if you actually did it?
27. POV: it's Sunday night and you're promising yourself next week is different.
28. Unpopular opinion: discipline is overrated. Environment is everything.
29. Rate your last 30 days out of 10. Be honest in the comments.
30. Tell me you're rebuilding your life without telling me you're rebuilding your life.

## First Two Weeks (reactivation calendar)

**Week 1 — re-entry.** Lead with your strongest pillar so the algorithm re-learns
who you are:
- Mon: TikTok + IG Reel — Getting Unstuck (hook #1 energy, your proven winner)
- Tue: TikTok — AI Leverage (hook #10 — the Sunday planning prompt, fully shown)
- Wed: IG Carousel — Frameworks (hook #19)
- Thu: TikTok — Getting Unstuck (hook #3)
- Fri: IG Reel — AI Leverage (hook #7 — announce the 30-day AI experiment: this
  doubles as the Build In Public arc opener)
- Sat: TikTok — Frameworks (hook #21)
- Sun: IG Caption — Engagement (hook #26)

**Week 2 — the arc.** The "30 days of AI-powered renewal" experiment becomes the
spine: every Build In Public post reports real numbers from *this very system*
(posts generated, videos rendered, followers gained). Meta enough to be
irresistible in both niches.

## KPI Checkpoints

- **Week 2:** posting consistency 100% (the system's job), baseline reach recorded
- **Week 4:** ≥1 post >10K views (hook iteration: double down on what pops)
- **Week 8:** follower growth trending +10%/week on at least one platform;
  comment keywords ("PROMPT") building a DM pipeline for later monetization
- **Week 12:** monetization gate — if IG >3K and TikTok >10K followers, introduce
  the first product test (a $27–47 "AI renewal system" template pack or a
  waitlist for coaching)

## How the App Executes This

Everything above is encoded in the platform (`app/prompts/rennewme.py` + seeded
brand row): Claude writes in this voice against these pillars, the scheduler fills
these slots, reel scripts are auto-rendered into vertical videos with AI voiceover,
and you approve everything from the dashboard queue until you're ready to flip
the brand to full-auto.
