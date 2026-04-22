# CLAUDE.md — Lixen.AI

> This file is automatically read by Claude Code at the start of every session.
> Keep it updated as the project evolves.

-----

## Project Overview

**Lixen.AI** is a GoHighLevel (GHL)-based, done-for-you AI marketing and automation agency
targeting med spas, day spas, dermatologists, and salons in the LA/OC area.

- **Business Model:** Joint venture — Renn (technical architect) + Rob (sales)
- **Status:** Active build — in pre-launch / early client acquisition phase
- **Demo sub-account:** Lixen Beauty Clinic (inside GHL)

-----

## Tech Stack

- **CRM & Automation:** GoHighLevel (GHL)
- **Backend:** Node.js / JavaScript
- **Frontend:** React
- **AI Agent Platform:** OpenClaw (self-hosted on Hostinger)
- **AI Model:** Anthropic Claude Sonnet (via pay-as-you-go API key)
- **Integrations:** MCP (GoHighLevel community server), WhatsApp Business, Hostinger SMTP
- **GHL MCP Server:** `mastanley13/GoHighLevel-MCP`
  - Entry point: `/Users/rennxai/GoHighLevel-MCP/dist/server.js`

-----

## API & Integration Details

### GHL Private Integration

- **Base URL:** `https://services.leadconnectorhq.com`
- **Auth:** Bearer token only
- **Required header:** `Version: 2021-07-28`

### OpenClaw Agent

- **Agent name:** LIXEN
- **Personality:** Professional, direct, concise
- **Platform:** Hostinger (self-hosted)
- **SMTP:** smtp.hostinger.com, port 587

### Anthropic API

- **Model in use:** Claude Sonnet (pay-as-you-go — NOT Claude.ai subscription credits)
- **Cost control priorities:**
  - Context mode: Minimal (not Adaptive)
  - Heartbeat frequency: Every 30 minutes
  - Avoid unnecessary retries

-----

## Active Issues / Known Problems

- WhatsApp responses from LIXEN agent are too long — needs length control in system prompt
- No differentiation between Renn’s own messages vs. client messages in WhatsApp
  - Current workaround: prefix Renn’s messages with `RENN:` keyword trigger
  - Long-term fix: separate business number for clients

-----

## Service Tiers & Pricing

|Plan      |Setup Fee                   |Monthly   |
|----------|----------------------------|----------|
|Smart Plan|$2,999 ($1,500 launch promo)|$499/month|
|Pro Plan  |$5,999 ($3,000 launch promo)|$799/month|

-----

## Target Client Profile (ICP)

- Med spas, day spas, dermatologists, salons
- Location: LA/OC area, California
- Pain points: lead follow-up, appointment booking, client retention, online reviews

-----

## Brand Guidelines

- **Theme:** Light only — NEVER dark backgrounds
- **Hero background:** `#EEF3FB`
- **Accent blue:** `#3B7DE8`
- **CTA navy:** `#0F2D5E`
- **Body text:** `#4B5563`
- **Card background:** `#F8FAFC`

-----

## Key Documents Already Built

- 31-page Master Playbook PDF
- 23-step GHL Master Build Guide (7 phases)
- Brand strategy document
- Service agreement
- Client intake form
- Customer playbook
- Demo video scripts
- Meta ad strategy brief

-----

## Coding Standards

- Use descriptive variable names
- Comment all GHL webhook logic clearly
- All API keys and tokens in `.env` — NEVER hardcoded
- Always confirm before deleting files or making destructive changes
- Prefer JavaScript/Node.js unless another language is explicitly specified

-----

## Common Commands

```bash
# Start Claude Code in this project
cd ~/LixenAI
claude

# Run local dev server (update if different)
npm run dev

# Commit changes
git add .
git commit -m "your message"
git push origin main
```

-----

## Session Reminders for Claude

- Renn is the technical architect — she follows instructions but is not a developer by background
- Explain what you’re doing and why, not just the commands
- When suggesting terminal commands, explain each one in plain English first
- Rob handles sales only — do not include him in technical decisions
- This is a real business with real clients — be precise, not experimental

-----

*Last updated: April 2026*
