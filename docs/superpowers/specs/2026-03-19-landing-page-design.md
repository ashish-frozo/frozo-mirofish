# MiroFish Landing Page Design

**Date:** 2026-03-19
**Status:** Approved
**Scope:** Sub-project #5 — Marketing landing page

## 1. Overview

A standalone, high-performance landing page for MiroFish targeting business decision-makers (C-suite, strategy teams, policy analysts). Clean corporate design, professional tone, full conversion funnel with 10 sections.

### Goals
- Communicate the value of AI-powered prediction to non-technical buyers
- Drive two actions: "Start Free Trial" (primary) and "Book a Demo" (secondary)
- Load in < 1.5s, SEO-optimized, mobile-responsive
- Professional, trustworthy aesthetic (not tech-bro)

### Non-Goals
- No user authentication on the landing page
- No interactive product demo (just screenshots/video)
- No blog or content marketing (separate effort)

## 2. Technical Architecture

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Stack | Plain HTML + Tailwind CSS (CDN) + vanilla JS | Fast, no build step, SEO-friendly |
| Directory | `landing/` at project root | Separate from Vue app |
| Files | `index.html`, `styles.css`, `script.js` | Minimal footprint |
| Fonts | Inter (Google Fonts) | Clean, professional, widely used in SaaS |
| Icons | Lucide icons (CDN) or inline SVG | Lightweight, consistent |
| Deployment | Flask serves `landing/index.html` at `/` | Same Railway service |
| Performance | < 100KB total page weight | No frameworks, optimized images |

### Routing Changes

```
/              → landing/index.html (static, no auth)
/login         → Vue app (Login.vue)
/signup        → Vue app (Signup.vue)
/dashboard     → Vue app (auth required)
/process/*     → Vue app (auth required)
```

Flask routing priority: landing page at `/` takes precedence over the Vue catch-all. Other routes fall through to the Vue SPA.

## 3. Design System

### Colors
- **Background:** `#FFFFFF` (white) with `#F9FAFB` alternate sections
- **Text primary:** `#111827`
- **Text secondary:** `#6B7280`
- **Accent/CTA:** `#2563EB` (blue-600)
- **Accent hover:** `#1D4ED8` (blue-700)
- **Badge background:** `#EFF6FF` (blue-50)
- **Badge text:** `#2563EB`
- **Border:** `#E5E7EB`
- **Success green:** `#059669` (for checkmarks, "included" markers)

### Typography
- **Headings:** Inter, 800 weight
- **Body:** Inter, 400/500 weight
- **Sizes:** Hero h1: 56px, Section h2: 40px, Body: 18px, Small: 14px

### Spacing
- **Section padding:** 96px vertical (desktop), 64px (mobile)
- **Max content width:** 1200px, centered
- **Card gap:** 24px

## 4. Page Sections (10 total)

### 4.1 Navigation Bar (sticky)
- Left: MiroFish logo (text)
- Center: Features | Use Cases | Pricing | FAQ (smooth scroll links)
- Right: "Login" (text link) + "Start Free Trial" (blue button)
- Sticky on scroll with subtle shadow

### 4.2 Hero Section (split layout)
- **Left side (55%):**
  - Badge: "Powered by Swarm Intelligence"
  - H1: "Rehearse the Future Before It Happens"
  - Subtitle: "MiroFish builds digital parallel worlds with autonomous AI agents to predict how people will react to your scenarios — before you commit."
  - Primary CTA: "Start Free Trial" (blue, solid)
  - Secondary CTA: "Book a Demo" (outlined)
  - Microcopy: "14-day free trial. No credit card required."
- **Right side (45%):**
  - Product screenshot showing the knowledge graph visualization
  - Or: animated SVG network graph with floating agent nodes
  - Subtle gradient background (#EFF6FF → #E0E7FF)

### 4.3 Social Proof Bar
- Light gray background (#F9FAFB)
- "Backed by" + Shanda Group logo
- GitHub stars badge (live count)
- "Built on OASIS by CAMEL-AI" attribution
- Horizontal layout, centered

### 4.4 Problem Statement
- H2: "Traditional Forecasting Wasn't Built for a Complex World"
- Three columns, each with icon + title + description:
  1. **Spreadsheet Models** — "Statistical models can't capture how real people react, organize, and influence each other."
  2. **Focus Groups** — "Small samples, slow timelines, and inherent bias. By the time you have results, the moment has passed."
  3. **Market Research** — "Backward-looking data tells you what happened, not what will happen under new conditions."

### 4.5 How It Works — 3 Steps
- H2: "From Scenario to Prediction in Minutes"
- Three numbered cards, horizontal layout:
  1. **Upload Your Scenario** — "Feed in any seed material — news articles, policy drafts, product plans, financial signals. MiroFish extracts entities and builds a knowledge graph."
  2. **AI Agents Simulate the Future** — "Hundreds of autonomous agents with distinct personalities interact on simulated social platforms. They argue, agree, organize, and evolve — just like real people."
  3. **Get Actionable Predictions** — "A ReACT-powered agent analyzes the simulation and delivers a prediction report with evidence, quotes, and trends you can act on."
- Below: light screenshot strip showing Graph → Simulation → Report

### 4.6 Key Features Grid
- H2: "Everything You Need to Predict Anything"
- 2x3 grid of feature cards:
  1. **Swarm Intelligence Engine** — "Hundreds of AI agents with memory, personality, and social behavior simulate realistic group dynamics."
  2. **Knowledge Graph Builder** — "Automatically extract entities and relationships from any document to build a structured world model."
  3. **Dual-Platform Simulation** — "Run predictions on simulated Twitter and Reddit simultaneously for multi-perspective insights."
  4. **ReACT Report Agent** — "An AI analyst that reasons, retrieves evidence, and writes comprehensive prediction reports."
  5. **Deep Agent Interaction** — "Interview any simulated agent. Ask follow-up questions. Explore alternative perspectives."
  6. **Resume Anytime** — "Pick up any project where you left off. All data persists across sessions."

### 4.7 Use Cases
- H2: "Trusted Across Industries"
- 4 cards with icon + title + scenario + outcome:
  1. **Policy Impact Analysis** — "A university policy team simulates the public reaction to a new campus regulation before announcing it."
  2. **Product Launch Prediction** — "A startup predicts how developers, media, and competitors will respond to their new AI tool release."
  3. **Crisis Communication** — "A PR team rehearses different crisis response strategies and measures predicted public sentiment for each."
  4. **Market Sentiment Forecasting** — "An investment firm models how retail investors and analysts will react to an earnings surprise."

### 4.8 Product Screenshots / Demo
- H2: "See MiroFish in Action"
- Screenshot carousel or static grid showing:
  - Knowledge graph visualization
  - Simulation running with agent actions
  - Generated prediction report
  - Agent interview chat
- Optional: embedded video (Bilibili/YouTube link)

### 4.9 Pricing
- H2: "Simple, Transparent Pricing"
- 3 tier cards:
  - **Starter ($19/mo):** 5 simulations/month, 20 agents per sim, 10 rounds, email support
  - **Pro ($49/mo):** 20 simulations/month, 50 agents, 40 rounds, priority support, API access
  - **Enterprise (Custom):** Unlimited simulations, custom agent count, dedicated support, SSO, SLA
- All tiers: "14-day free trial" badge
- Pro card highlighted as "Most Popular"
- CTA: "Start Free Trial" on Starter/Pro, "Contact Sales" on Enterprise

### 4.10 FAQ Accordion
- H2: "Frequently Asked Questions"
- 6 items, click to expand:
  1. "How accurate are the predictions?" — "MiroFish doesn't predict with certainty — it reveals plausible futures. By simulating hundreds of diverse agents, it surfaces trends, risks, and reactions that traditional analysis misses."
  2. "What kind of data do I need to upload?" — "Any text document: news articles, policy drafts, product specs, financial reports, even novel chapters. PDF, TXT, and Markdown are supported."
  3. "Is my data secure?" — "Your data is encrypted in transit and at rest. Each user's projects are completely isolated. We never train AI models on your data."
  4. "Can I use my own LLM?" — "Yes. MiroFish supports any OpenAI-compatible API, including Claude, GPT-4, Qwen, and self-hosted models."
  5. "How many agents can I simulate?" — "Depends on your plan. Starter supports 20, Pro supports 50, and Enterprise is unlimited."
  6. "What happens after my trial ends?" — "Your projects and reports are preserved. You can still view them, but creating new simulations requires an active plan."

### 4.11 Final CTA
- Dark background (#111827) for contrast
- H2: "Ready to Rehearse the Future?"
- Subtitle: "Join teams using MiroFish to make better decisions with AI-powered prediction."
- Dual CTAs: "Start Free Trial" + "Book a Demo"

### 4.12 Footer
- 4 columns: Product (Features, Pricing, Use Cases, Changelog) | Resources (Documentation, API Reference, Blog) | Company (About, Contact, Careers) | Legal (Privacy, Terms)
- Bottom: copyright + social links (X, Discord, GitHub, Instagram)

## 5. Interactions & Animations

- **Scroll animations:** Sections fade in on scroll (IntersectionObserver, vanilla JS)
- **Sticky nav:** Shadow appears on scroll
- **FAQ accordion:** Smooth height transition on click
- **CTA hover:** Scale + shadow transition
- **Hero network graph:** Optional subtle CSS animation (floating nodes)
- **No JavaScript frameworks** — all vanilla for performance

## 6. Mobile Responsive

- Nav collapses to hamburger menu at 768px
- Hero splits to stacked (text on top, visual below)
- Feature grid: 2x3 → 1 column
- Pricing: horizontal → stacked cards
- All text sizes scale down proportionally

## 7. SEO

```html
<title>MiroFish — AI Prediction Engine | Rehearse the Future Before It Happens</title>
<meta name="description" content="MiroFish builds digital parallel worlds with autonomous AI agents to predict how people will react to your scenarios. Try free for 14 days.">
<meta property="og:title" content="MiroFish — Rehearse the Future Before It Happens">
<meta property="og:description" content="AI-powered swarm intelligence engine for predicting public reaction, market sentiment, and policy impact.">
<meta property="og:image" content="/landing/og-image.png">
<meta property="og:type" content="website">
```

## 8. Files to Create

```
landing/
  index.html       — Full page HTML with all 10 sections
  styles.css       — Custom styles beyond Tailwind
  script.js        — Scroll animations, FAQ accordion, mobile menu
  images/          — Screenshots, og-image.png
```

## 9. Flask Routing Change

In `backend/app/__init__.py`, update the static file serving to prioritize the landing page:

```python
# Serve landing page at /
landing_dir = os.path.join(os.path.dirname(__file__), '../../landing')
if os.path.isdir(landing_dir):
    @app.route('/')
    def serve_landing():
        return send_from_directory(landing_dir, 'index.html')

    @app.route('/landing/<path:path>')
    def serve_landing_assets(path):
        return send_from_directory(landing_dir, path)
```

The Vue SPA catch-all continues to handle `/login`, `/signup`, `/dashboard`, etc.

## 10. Success Criteria

- [ ] Page loads in < 1.5s on 3G connection
- [ ] All 10 sections render correctly on desktop and mobile
- [ ] "Start Free Trial" navigates to `/signup`
- [ ] "Book a Demo" opens a contact form or Calendly link
- [ ] FAQ accordion works smoothly
- [ ] Scroll animations trigger on section entry
- [ ] SEO meta tags present and correct
- [ ] Mobile hamburger menu works
- [ ] No JavaScript errors in console
