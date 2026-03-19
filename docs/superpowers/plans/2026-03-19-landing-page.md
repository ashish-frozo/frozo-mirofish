# Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a high-converting, standalone landing page for MiroFish targeting business decision-makers, with 10 sections, clean corporate design, and < 1.5s load time.

**Architecture:** Static HTML + Tailwind CSS (CDN) + vanilla JS in a `landing/` directory. Flask serves it at `/`. No build step, no frameworks. The Vue app handles all other routes (`/login`, `/signup`, `/dashboard`, etc.).

**Tech Stack:** HTML5, Tailwind CSS 3 (CDN), Inter font (Google Fonts), vanilla JavaScript, inline SVGs

**Spec:** `docs/superpowers/specs/2026-03-19-landing-page-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `landing/index.html` | Full landing page — all 10 sections, nav, footer |
| `landing/styles.css` | Custom styles beyond Tailwind (animations, custom components) |
| `landing/script.js` | Scroll animations, FAQ accordion, mobile menu, sticky nav |

### Modified Files

| File | Change |
|------|--------|
| `backend/app/__init__.py` | Serve `landing/index.html` at `/`, landing assets at `/landing/*` |

---

## Task 1: Create Landing Page HTML — Nav + Hero + Social Proof

**Files:**
- Create: `landing/index.html`
- Create: `landing/styles.css`

- [ ] **Step 1: Create the HTML file with head, nav, hero, and social proof sections**

Create `landing/index.html` with:
- Full HTML5 doctype with SEO meta tags (title, description, OG tags)
- Tailwind CSS CDN link + Google Fonts (Inter) link
- Link to `styles.css`
- **Sticky nav:** Logo left, nav links center (Features, Use Cases, Pricing, FAQ — anchor links), Login + Start Free Trial right
- **Hero section (split layout):** Left side has badge ("Powered by Swarm Intelligence"), h1 ("Rehearse the Future Before It Happens"), subtitle, dual CTAs (Start Free Trial blue + Book a Demo outlined), microcopy. Right side has a gradient card with an SVG network graph visualization (nodes + edges, abstract agent network)
- **Social proof bar:** "Backed by" + Shanda Group text, GitHub stars badge, "Built on OASIS" attribution

Design system:
- Background: white `#FFFFFF`, alternate sections `#F9FAFB`
- Text: `#111827` primary, `#6B7280` secondary
- Accent: `#2563EB` blue
- Max width: 1200px centered
- Section padding: `py-24` (96px)

Create `landing/styles.css` with:
- Smooth scroll behavior
- Custom animation keyframes for fade-in-up on scroll
- Sticky nav shadow on scroll
- Hero network graph subtle float animation

- [ ] **Step 2: Preview locally**

Open `landing/index.html` directly in browser to verify layout.

- [ ] **Step 3: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add landing/ && git commit -m "feat: add landing page — nav, hero, and social proof sections

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Problem Statement + How It Works + Features Grid

**Files:**
- Modify: `landing/index.html`

- [ ] **Step 1: Add the three content sections after social proof**

**Problem Statement section** (`#features` anchor):
- H2: "Traditional Forecasting Wasn't Built for a Complex World"
- 3-column grid with icons + titles + descriptions:
  - Spreadsheet Models — "Statistical models can't capture how real people react, organize, and influence each other."
  - Focus Groups — "Small samples, slow timelines, and inherent bias. By the time you have results, the moment has passed."
  - Market Research — "Backward-looking data tells you what happened, not what will happen under new conditions."

**How It Works section:**
- H2: "From Scenario to Prediction in Minutes"
- 3 numbered steps, horizontal cards:
  1. Upload Your Scenario (document icon)
  2. AI Agents Simulate the Future (network icon)
  3. Get Actionable Predictions (chart icon)
- Each card has number badge, title, description paragraph

**Features Grid section:**
- H2: "Everything You Need to Predict Anything"
- 2x3 responsive grid of feature cards with icon + title + description:
  1. Swarm Intelligence Engine
  2. Knowledge Graph Builder
  3. Dual-Platform Simulation
  4. ReACT Report Agent
  5. Deep Agent Interaction
  6. Resume Anytime

Use inline SVG icons (simple line icons — brain, network, chat, etc.) or Tailwind heroicons CDN.

- [ ] **Step 2: Verify all three sections render correctly**

- [ ] **Step 3: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add landing/index.html && git commit -m "feat: add problem, how-it-works, and features sections to landing page

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Use Cases + Product Screenshots + Pricing

**Files:**
- Modify: `landing/index.html`

- [ ] **Step 1: Add use cases, screenshots, and pricing sections**

**Use Cases section** (`#use-cases` anchor):
- H2: "Trusted Across Industries"
- 4 cards in 2x2 grid:
  1. Policy Impact Analysis
  2. Product Launch Prediction
  3. Crisis Communication
  4. Market Sentiment Forecasting
- Each card: colored icon, title, 2-line scenario description

**Product Screenshots section:**
- H2: "See MiroFish in Action"
- Grid of 3 screenshot placeholders (use the existing screenshots at `static/image/Screenshot/screenshot_1-6.png`)
- Reference them as `/static/image/Screenshot/screenshot_1.png` etc.
- Light border, rounded corners, subtle shadow
- Caption below each: "Knowledge Graph", "Simulation Running", "Prediction Report"

**Pricing section** (`#pricing` anchor):
- H2: "Simple, Transparent Pricing"
- 3 tier cards side by side:
  - Starter ($19/mo): 5 sims, 20 agents, 10 rounds, email support
  - Pro ($49/mo, highlighted "Most Popular"): 20 sims, 50 agents, 40 rounds, priority support, API access
  - Enterprise (Custom): Unlimited, custom agents, dedicated support, SSO, SLA
- Each card: tier name, price, feature list with checkmarks, CTA button
- Pro card has blue border + "Most Popular" badge
- All show "14-day free trial" note

- [ ] **Step 2: Verify pricing cards align and are responsive**

- [ ] **Step 3: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add landing/index.html && git commit -m "feat: add use cases, screenshots, and pricing sections

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: FAQ + Final CTA + Footer

**Files:**
- Modify: `landing/index.html`

- [ ] **Step 1: Add FAQ accordion, final CTA, and footer**

**FAQ section** (`#faq` anchor):
- H2: "Frequently Asked Questions"
- 6 accordion items, each with question (clickable) and answer (hidden, expands on click):
  1. How accurate are the predictions?
  2. What kind of data do I need to upload?
  3. Is my data secure?
  4. Can I use my own LLM?
  5. How many agents can I simulate?
  6. What happens after my trial ends?
- Use `<details>/<summary>` for zero-JS fallback, enhanced with JS for smooth animation

**Final CTA section:**
- Dark background (`bg-gray-900` / `#111827`)
- H2 (white): "Ready to Rehearse the Future?"
- Subtitle (gray-300): "Join teams using MiroFish to make better decisions with AI-powered prediction."
- Dual CTAs: "Start Free Trial" (blue) + "Book a Demo" (white outlined)

**Footer:**
- 4-column layout: Product | Resources | Company | Legal
- Bottom bar: copyright 2026 MiroFish + social icons (GitHub, X, Discord, Instagram)

- [ ] **Step 2: Verify accordion opens/closes and footer links work**

- [ ] **Step 3: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add landing/index.html && git commit -m "feat: add FAQ, final CTA, and footer sections

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: JavaScript — Scroll Animations, Mobile Menu, Interactions

**Files:**
- Create: `landing/script.js`
- Modify: `landing/index.html` (add script tag)

- [ ] **Step 1: Create script.js with all interactions**

```javascript
// 1. Scroll-triggered fade-in animations using IntersectionObserver
// 2. FAQ accordion smooth toggle
// 3. Mobile hamburger menu toggle
// 4. Sticky nav shadow on scroll
// 5. Smooth scroll for anchor links
```

Implementation:
- **Scroll animations:** Add `.animate-on-scroll` class to all section containers. Observer adds `.animated` class when 20% visible. CSS handles the transition (opacity 0→1, translateY 20px→0).
- **FAQ:** Click handler on `<summary>` elements. Toggle `open` attribute. CSS transition on max-height.
- **Mobile menu:** Toggle hidden class on nav links container. Hamburger icon → X icon transition.
- **Sticky nav:** `scroll` event listener. Add `shadow-md` class when `scrollY > 50`.
- **Smooth scroll:** `querySelectorAll('a[href^="#"]')` → `scrollIntoView({ behavior: 'smooth' })`.

- [ ] **Step 2: Add `<script src="script.js"></script>` before closing `</body>` in index.html**

- [ ] **Step 3: Test all interactions**

- [ ] **Step 4: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add landing/script.js landing/index.html && git commit -m "feat: add scroll animations, FAQ accordion, and mobile menu

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Flask Routing — Serve Landing Page at /

**Files:**
- Modify: `backend/app/__init__.py`

- [ ] **Step 1: Read current __init__.py**

Check the current static file serving logic near the bottom of `create_app()`.

- [ ] **Step 2: Add landing page route BEFORE the Vue SPA catch-all**

Add this block before the frontend_dist serving block:

```python
    # Serve landing page at /
    landing_dir = os.path.join(os.path.dirname(__file__), '../../landing')
    if os.path.isdir(landing_dir):
        from flask import send_from_directory as send_landing

        @app.route('/')
        def serve_landing():
            return send_from_directory(landing_dir, 'index.html')

        @app.route('/landing/<path:path>')
        def serve_landing_assets(path):
            return send_from_directory(landing_dir, path)

        if should_log_startup:
            logger.info(f"Serving landing page from {landing_dir}")
```

Also need to serve the existing `static/image/` directory for screenshots:

```python
    # Serve static images
    static_dir = os.path.join(os.path.dirname(__file__), '../../static')
    if os.path.isdir(static_dir):
        @app.route('/static/<path:path>')
        def serve_static(path):
            return send_from_directory(static_dir, path)
```

- [ ] **Step 3: Update the Vue SPA catch-all to NOT match /**

The existing catch-all `@app.route('/', defaults={'path': ''})` will conflict. Modify it to only catch non-root paths:

```python
    # Serve frontend SPA for all non-root, non-API, non-landing routes
    if os.path.isdir(frontend_dist):
        @app.route('/<path:path>')
        def serve_frontend(path):
            # Skip API routes and landing assets
            if path.startswith('api/') or path.startswith('landing/') or path.startswith('static/'):
                return  # Let other handlers deal with it
            file_path = os.path.join(frontend_dist, path)
            if os.path.isfile(file_path):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, 'index.html')
```

- [ ] **Step 4: Verify locally**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish/backend && uv run python -c "from app import create_app; app = create_app(); print('App OK')"
```

- [ ] **Step 5: Commit**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git add backend/app/__init__.py && git commit -m "feat: serve landing page at / via Flask, static assets routing

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Deploy and Verify

- [ ] **Step 1: Push to GitHub**

```bash
cd /Users/ashishdhiman/WORK/miro-fish/MiroFish && git push frozo main
```

- [ ] **Step 2: Deploy to Railway**

```bash
railway up --detach
```

- [ ] **Step 3: Verify landing page loads**

```bash
curl -s https://frozo-mirofish-production.up.railway.app/ | head -20
```

Expected: HTML with `<title>MiroFish` and the hero section content.

- [ ] **Step 4: Verify app routes still work**

```bash
curl -s https://frozo-mirofish-production.up.railway.app/health
curl -s https://frozo-mirofish-production.up.railway.app/api/auth/me -H "Authorization: Bearer invalid" | head -5
```

Expected: Health OK, auth returns 401.

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Nav + Hero + Social Proof | `landing/index.html`, `landing/styles.css` |
| 2 | Problem + How It Works + Features | `landing/index.html` |
| 3 | Use Cases + Screenshots + Pricing | `landing/index.html` |
| 4 | FAQ + Final CTA + Footer | `landing/index.html` |
| 5 | JavaScript interactions | `landing/script.js`, `landing/index.html` |
| 6 | Flask routing | `backend/app/__init__.py` |
| 7 | Deploy and verify | Push + Railway |
