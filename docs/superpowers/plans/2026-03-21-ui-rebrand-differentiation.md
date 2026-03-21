# UI Rebrand & Differentiation Plan

> Deferred — implement after end-to-end flow is validated.

**Goal:** Make the app visually distinct from the original MiroFish repo so it doesn't look like a fork. New brand identity, color scheme, typography, and layout refinements following Enterprise SaaS design principles.

## Design System (Generated via UI/UX Pro Max)

### Style: Enterprise SaaS + Soft UI Evolution
- **Pattern:** Data-dense dashboard with professional trust signals
- **Mood:** Professional, trustworthy, clean, approachable, data-forward
- **Performance:** Excellent | **Accessibility:** WCAG AA+
- **Complexity:** Medium

### Color Palette

| Role | MiroFish (old) | Frozo (new) | Notes |
|------|---------------|-------------|-------|
| Primary | Black #000000 | Indigo #4F46E5 | Enterprise trust color |
| Secondary | — | Violet #7C3AED | Gradient accent for CTAs |
| CTA/Accent | Orange #FF4500 | Blue #2563EB | Professional, high-conversion |
| CTA Hover | — | #1D4ED8 | Darker blue |
| Success | Green #4CAF50 | Emerald #10B981 | Status: completed |
| Warning | Amber #FF9800 | Amber #F59E0B | Status: processing |
| Error | Red #F44336 | Rose #EF4444 | Status: failed |
| Background | White #FFFFFF | Slate #F8FAFC | Softer, easier on eyes |
| Surface | Gray #F5F5F5 | White #FFFFFF | Cards, panels |
| Text Primary | Black #000000 | Slate #0F172A | High contrast, not harsh |
| Text Muted | Gray #666666 | Slate #64748B | Secondary text |
| Border | #E5E5E5 | #E2E8F0 | Subtle separation |
| Card Shadow | — | rgba(79,70,229,0.08) | Indigo-tinted, branded |

**CSS Variables:**
```css
:root {
  --bg: #F8FAFC;
  --surface: #FFFFFF;
  --text: #0F172A;
  --muted: #64748B;
  --primary: #4F46E5;
  --secondary: #7C3AED;
  --cta: #2563EB;
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --border: #E2E8F0;
  --radius-card: 16px;
  --radius-button: 8px;
  --radius-input: 8px;
  --radius-pill: 999px;
  --shadow-card: 0 1px 3px rgba(79,70,229,0.08);
  --shadow-elevated: 0 4px 12px rgba(79,70,229,0.12);
}
```

### Typography

| Role | MiroFish (old) | Frozo (new) |
|------|---------------|-------------|
| Brand/Headings | Space Grotesk | Plus Jakarta Sans (600-800) |
| Body | Space Grotesk | Inter (400-500) |
| Code/Data | JetBrains Mono | Fira Code (400-600) |
| Chinese | Noto Sans SC | Removed (globalized) |

**Google Fonts Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&family=Fira+Code:wght@400;500;600&display=swap');
```

**Scale:** 12 / 14 / 16 / 18 / 24 / 32 / 40 / 48px

### Effects & Interactions

| Element | Spec |
|---------|------|
| Button hover | Scale 1.02 + shadow elevation, 200ms ease-out |
| Button press | Scale 0.97, 100ms |
| Card hover | Shadow elevation increase, 200ms |
| Page transitions | Fade-in 300ms ease-out |
| Loading | Skeleton shimmer (indigo tint), not spinners |
| Toasts | Slide-in from top-right, auto-dismiss 4s |
| Focus ring | 2px offset, indigo outline |
| Reduced motion | Respect prefers-reduced-motion |

### Anti-Patterns to Avoid
- No emojis as icons (use Lucide SVGs)
- No ornate/decorative design
- No mixing flat and skeuomorphic
- No gray-on-gray text
- No raw hex in components (use CSS variables)
- No placeholder-only labels on inputs

---

## Current State (MiroFish Original)

- **Colors:** Black/white/orange (#FF4500 accent)
- **Fonts:** JetBrains Mono + Space Grotesk + Noto Sans SC
- **Brand:** "MIROFISH" in monospace, diamond icons
- **Layout:** Two-column split (graph left, workbench right)
- **Style:** Minimalist monochrome, developer-oriented
- **No UI library** — all custom CSS, ad-hoc per component

## Differentiation Strategy

### 1. Brand Identity Swap

| Element | MiroFish (original) | Frozo (ours) |
|---------|-------------------|-------------|
| Name | MIROFISH | FROZO |
| Logo | Fish icon + monospace text | Geometric mark + Plus Jakarta Sans |
| Tagline | "Predict Everything" | "See Tomorrow, Today" |
| Tone | Developer/academic | Professional/business |
| Favicon | Fish | Geometric "F" mark |

**Tasks:**
- [ ] Replace all "MiroFish" text with "Frozo" across all frontend files
- [ ] Design new logo (AI-generated geometric mark)
- [ ] Update favicon, og:image, page titles
- [ ] Update landing page branding
- [ ] Remove all fish references, diamond icons

### 2. Color System Implementation

**Tasks:**
- [ ] Create `frontend/src/assets/globals.css` with CSS custom properties (above)
- [ ] Import globals.css in `App.vue`
- [ ] Replace all hardcoded hex colors in all 15+ Vue components
- [ ] Update auth pages (Login/Signup/Dashboard) to use new variables
- [ ] Update landing page colors (already uses Tailwind — remap to indigo/violet)

### 3. Typography Swap

**Tasks:**
- [ ] Replace Google Fonts imports in `frontend/index.html`
- [ ] Update all `font-family` declarations across components
- [ ] Remove Noto Sans SC (Chinese font — no longer needed)
- [ ] Apply type scale consistently: 16px body, 24-48px headings

### 4. Navigation Redesign

**MiroFish:** Black bar, monospace brand text, view mode switcher
**Frozo:** Slate/white nav, Plus Jakarta brand, breadcrumb step indicator, user avatar dropdown

**Tasks:**
- [ ] Redesign `MainView.vue` top nav
- [ ] Add horizontal step progress bar (1→2→3→4→5)
- [ ] Add user avatar + dropdown menu (profile, billing, logout)
- [ ] Make nav responsive (hamburger on mobile)

### 5. Step Workflow UX Improvements

**MiroFish:** Fixed two-column split with graph always visible
**Frozo:** Full-width wizard steps with collapsible graph panel

**Tasks:**
- [ ] Step indicator as colored progress bar across top
- [ ] Each step gets full-width layout
- [ ] Graph panel slides in/out as an overlay or side panel
- [ ] Clear "Next Step" / "Back" navigation between steps
- [ ] Skeleton loading states for each step

### 6. Dashboard Upgrade

**MiroFish:** Simple list with basic styling
**Frozo:** Card grid with rich project cards

**Project card design:**
```
┌─────────────────────────────────────┐
│ [Status Badge]           [3 days ago] │
│                                       │
│ GPT-5 Impact Analysis                 │
│ Step 3/5 ████████░░ 60%               │
│                                       │
│ 42 entities · 78 relationships        │
│                                       │
│ [Resume →]              [⋮ More]      │
└─────────────────────────────────────┘
```

**Tasks:**
- [ ] Redesign project cards with status, progress bar, stats
- [ ] 2-column grid on desktop, 1-column on mobile
- [ ] Add project search/filter
- [ ] Empty state with illustration

### 7. Graph Visualization Styling

| Element | MiroFish | Frozo |
|---------|---------|-------|
| Node colors | Single orange | Multi-color by type (indigo, violet, emerald, amber) |
| Node shape | Plain circles | Circles with soft gradient + white border |
| Edge style | Thin gray lines | Curved with directional arrows, labeled |
| Labels | Plain text | Pill badges with background |
| Background | Plain white | Subtle dot grid pattern (#E2E8F0 dots) |
| Hover | Basic | Glow effect + dim non-connected nodes |
| Selected | Orange highlight | Indigo ring + info panel slide-in |

**Tasks:**
- [ ] Update `GraphPanel.vue` D3.js node rendering
- [ ] Add entity type → color mapping
- [ ] Add dot grid background pattern
- [ ] Enhanced hover: glow + connected node highlighting
- [ ] Edge labels and directional arrows

### 8. Component Library Standardization

**Buttons:**
```css
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--secondary)); }
.btn-secondary { border: 1px solid var(--border); color: var(--text); }
.btn-ghost { color: var(--primary); background: transparent; }
.btn-danger { background: var(--error); color: white; }
```
Sizes: sm (32px), md (40px), lg (48px)

**Cards:**
```css
.card { background: var(--surface); border-radius: var(--radius-card); box-shadow: var(--shadow-card); }
.card:hover { box-shadow: var(--shadow-elevated); }
```

**Inputs:**
```css
.input { border-radius: var(--radius-input); border: 1px solid var(--border); }
.input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(79,70,229,0.2); }
```

**Status Badges:**
```css
.badge-active { background: #ECFDF5; color: #059669; }
.badge-running { background: #EFF6FF; color: #2563EB; }
.badge-failed { background: #FEF2F2; color: #DC2626; }
.badge-completed { background: #F0FDF4; color: #15803D; }
```

**Tasks:**
- [ ] Create reusable CSS classes in globals.css
- [ ] Standardize all buttons across components
- [ ] Standardize all inputs/forms
- [ ] Standardize all status badges
- [ ] Standardize all card layouts

### 9. Upload Page Redesign

**MiroFish:** Text-heavy console aesthetic, developer-focused
**Frozo:** Clean centered layout, prominent drag-drop, example prompts

**Tasks:**
- [ ] Centered card layout with drag-drop zone
- [ ] Example prediction prompts as clickable chips
- [ ] File type indicators (PDF, TXT, MD icons)
- [ ] Cleaner requirement textarea with character count
- [ ] "Launch Prediction" button with gradient + arrow icon

### 10. Micro-Interactions & Polish

**Tasks:**
- [ ] Skeleton loading screens (indigo shimmer) for all async operations
- [ ] Page route transitions (fade 300ms)
- [ ] Toast notification system (slide-in, color-coded)
- [ ] Button press feedback (scale 0.97)
- [ ] Step transition animations (slide + fade)
- [ ] Graph node entrance animation on data load

---

## Implementation Phases

| Phase | What | Effort | Priority |
|-------|------|--------|----------|
| **A. Brand Swap** | MiroFish → Frozo everywhere, new logo/favicon/titles | 2h | CRITICAL |
| **B. CSS Variables + Colors** | Create globals.css, replace all hardcoded colors | 4h | HIGH |
| **C. Typography** | Swap fonts, update declarations, remove Chinese fonts | 1h | HIGH |
| **D. Nav + Step Indicator** | Redesign top nav, horizontal progress bar | 3h | HIGH |
| **E. Component Library** | Buttons, cards, inputs, badges standardized | 3h | MEDIUM |
| **F. Dashboard Cards** | Rich project cards with progress and stats | 2h | MEDIUM |
| **G. Graph Visualization** | Multi-color nodes, dot grid, enhanced hover | 2h | MEDIUM |
| **H. Upload Page** | Cleaner layout, example prompts, drag-drop | 2h | MEDIUM |
| **I. Micro-Interactions** | Skeletons, transitions, toasts, press feedback | 2h | LOW |
| **Total** | | **~21h** | |

**Recommended order:** A → B → C → D → E → F → G → H → I

---

## Pre-Delivery Checklist (per UI/UX Pro Max)

### Visual Quality
- [ ] No emojis used as icons (Lucide SVGs throughout)
- [ ] All icons from consistent family (Lucide)
- [ ] CSS variables used everywhere (no hardcoded hex)
- [ ] Consistent border-radius scale (8px inputs, 16px cards)
- [ ] Consistent shadow scale (card, elevated)

### Interaction
- [ ] All clickable elements have cursor-pointer
- [ ] Hover states with 150-300ms transitions
- [ ] Touch targets ≥44px on mobile
- [ ] Disabled states visually distinct (opacity 0.5)
- [ ] Focus rings visible for keyboard nav

### Contrast & Accessibility
- [ ] Primary text contrast ≥4.5:1 (#0F172A on #F8FAFC = 15.4:1 ✓)
- [ ] Muted text contrast ≥3:1 (#64748B on #FFFFFF = 4.6:1 ✓)
- [ ] Color not sole indicator (icons + text for status)
- [ ] prefers-reduced-motion respected
- [ ] All form inputs have visible labels

### Layout & Responsive
- [ ] Mobile-first: 375px → 768px → 1024px → 1440px
- [ ] No horizontal scroll on any breakpoint
- [ ] 8px spacing rhythm throughout
- [ ] Safe area respected on mobile
- [ ] Max content width 1280px centered

## Files Affected

### New Files
- `frontend/src/assets/globals.css` — CSS custom properties + reusable classes
- `frontend/public/favicon.svg` — New Frozo favicon

### All Vue Components (~15 files)
- Every file in `views/` and `components/` — color + font + style updates
- `GraphPanel.vue` — D3.js rendering overhaul
- `MainView.vue` — nav bar redesign
- `Home.vue` — upload page redesign
- `Dashboard.vue` — card grid layout

### Landing Page
- `landing/index.html` — brand name + color updates
- `landing/styles.css` — minimal changes (already Tailwind)

### Static Assets
- `static/image/` — new logo files
- `frontend/public/` — new favicon
- `frontend/index.html` — font imports, title
