# UI Rebrand & Differentiation Plan

> Deferred — implement after end-to-end flow is validated.

**Goal:** Make the app visually distinct from the original MiroFish repo so it doesn't look like a fork. New brand identity, color scheme, typography, and layout refinements.

## Current State (MiroFish Original)

- **Colors:** Black/white/orange (#FF4500 accent)
- **Fonts:** JetBrains Mono + Space Grotesk + Noto Sans SC
- **Brand:** "MIROFISH" in monospace, diamond icons
- **Layout:** Two-column split (graph left, workbench right)
- **Style:** Minimalist monochrome, developer-oriented
- **No UI library** — all custom CSS, ad-hoc per component

## Differentiation Strategy

### 1. New Brand Identity

| Element | MiroFish (original) | Frozo (ours) |
|---------|-------------------|-------------|
| Name | MIROFISH | FROZO |
| Logo | Fish icon + monospace text | Modern geometric mark + clean sans-serif |
| Tagline | "Predict Everything" | "See Tomorrow, Today" or "Predict What's Next" |
| Tone | Developer/academic | Professional/business |

**Tasks:**
- [ ] Replace all "MiroFish" text with "Frozo" across frontend
- [ ] Design new logo (can use AI-generated for now)
- [ ] Update favicon, og:image, page titles
- [ ] Update landing page branding

### 2. New Color System

| Role | MiroFish | Frozo |
|------|---------|-------|
| Primary | Black #000000 | Deep Navy #0F172A |
| Accent | Orange #FF4500 | Electric Blue #3B82F6 |
| Secondary accent | — | Violet #8B5CF6 |
| Success | Green #4CAF50 | Emerald #10B981 |
| Warning | Amber #FF9800 | Amber #F59E0B |
| Error | Red #F44336 | Rose #EF4444 |
| Background | White #FFFFFF | Slate #F8FAFC |
| Surface | Gray #F5F5F5 | White #FFFFFF |
| Text primary | Black #000000 | Slate #0F172A |
| Text secondary | Gray #666666 | Slate #64748B |
| Border | #E5E5E5 | #E2E8F0 |

**Rationale:** Navy + blue + violet is professional, trustworthy (finance/enterprise), and visually distinct from MiroFish's black/orange hacker aesthetic.

**Tasks:**
- [ ] Create `frontend/src/assets/globals.css` with CSS custom properties
- [ ] Replace all hardcoded colors across all Vue components
- [ ] Update auth pages (Login/Signup/Dashboard) to match new scheme

### 3. New Typography

| Role | MiroFish | Frozo |
|------|---------|-------|
| Brand | JetBrains Mono | Plus Jakarta Sans (800) |
| Headings | Space Grotesk | Plus Jakarta Sans (600-700) |
| Body | Space Grotesk | Inter (400-500) |
| Code/Data | JetBrains Mono | JetBrains Mono (keep) |
| Chinese | Noto Sans SC | Remove (globalized) |

**Tasks:**
- [ ] Swap Google Fonts imports in `index.html`
- [ ] Update font-family declarations across components
- [ ] Remove Noto Sans SC (no longer needed after globalization)

### 4. Layout Refinements

**Navigation bar overhaul:**
- MiroFish: Black bar, monospace brand, minimal
- Frozo: Navy gradient bar, logo + wordmark, breadcrumb-style step indicator, user avatar dropdown

**Step workflow redesign:**
- MiroFish: Two-column split with graph always visible
- Frozo: Full-width wizard steps with a collapsible graph panel
  - Step indicator as a horizontal progress bar (not just text)
  - Each step gets full screen width
  - Graph panel slides in from the side when needed

**Dashboard:**
- MiroFish: Simple list
- Frozo: Card grid with project thumbnails, status timeline, quick stats

**Home/Upload page:**
- MiroFish: Text-heavy, developer console aesthetic
- Frozo: Clean centered layout, drag-drop prominent, example prompts

**Tasks:**
- [ ] Redesign nav bar component
- [ ] Add horizontal step progress indicator
- [ ] Update Dashboard with card grid layout
- [ ] Redesign upload page with cleaner UX

### 5. Graph Visualization Styling

| Element | MiroFish | Frozo |
|---------|---------|-------|
| Node colors | Single orange | Multi-color by entity type (blue, purple, emerald, amber) |
| Node shape | Circles | Circles with gradient fills |
| Edge style | Thin gray lines | Curved lines with directional arrows |
| Labels | Plain text | Pill badges with background |
| Background | White | Subtle dot grid pattern |
| Hover | Basic highlight | Glow effect + connected nodes highlight |

**Tasks:**
- [ ] Update D3.js node rendering in GraphPanel.vue
- [ ] Add color mapping for entity types
- [ ] Add dot grid background
- [ ] Enhance hover interactions

### 6. Component Polish

**Cards:**
- Add subtle shadow + rounded corners (12px)
- Hover elevation effect
- Consistent padding (24px)

**Buttons:**
- Primary: Blue gradient (#3B82F6 → #2563EB)
- Secondary: Outlined with border
- Ghost: Text only with hover background
- Consistent sizing (sm/md/lg)

**Inputs:**
- Rounded (8px)
- Focus ring in blue
- Label above, not placeholder-only

**Status badges:**
- Pill shape with icon + text
- Color-coded per status

**Tasks:**
- [ ] Create reusable component styles in globals.css
- [ ] Standardize button styles
- [ ] Standardize input styles
- [ ] Standardize card styles

### 7. Dark Mode (Optional — Phase 2)

The auth pages already use dark theme. Consider offering a toggle:
- Light mode: Default (professional, clean)
- Dark mode: Deep navy (#0F172A) background

### 8. Micro-Interactions & Polish

- Page transitions: Fade-in on route change
- Loading states: Skeleton screens instead of spinners
- Toast notifications: Slide-in from top-right
- Step transitions: Smooth accordion/slide animations
- Graph: Node entrance animation on data load

## Implementation Order

| Phase | What | Effort |
|-------|------|--------|
| **A. Brand swap** | Replace MiroFish → Frozo, update logo, titles, favicons | 2 hours |
| **B. Color system** | Create globals.css, update all components | 4 hours |
| **C. Typography** | Swap fonts, update declarations | 1 hour |
| **D. Nav + step indicator** | Redesign navigation and workflow progress | 3 hours |
| **E. Component polish** | Buttons, cards, inputs, badges | 3 hours |
| **F. Graph styling** | Multi-color nodes, enhanced interactions | 2 hours |
| **G. Dashboard + upload** | Card grid, cleaner upload UX | 3 hours |
| **H. Micro-interactions** | Transitions, skeletons, toasts | 2 hours |
| **Total** | | **~20 hours** |

## Priority

**Phase A (brand swap) is CRITICAL** — this is what makes it not look like a fork. Everything else is polish that improves the product but isn't blocking for launch.

Recommended order: A → B → C → D → E → F → G → H

## Files Affected

### Global
- `frontend/index.html` — fonts, favicon, title
- `frontend/src/assets/globals.css` (NEW) — CSS custom properties
- `frontend/src/App.vue` — import globals.css

### All Vue components (~15 files)
- Every component in `views/` and `components/` needs color + font updates
- `GraphPanel.vue` — node rendering overhaul
- `MainView.vue` — nav bar redesign
- `Home.vue` — upload page redesign
- `Dashboard.vue` — card grid layout

### Landing page
- `landing/index.html` — already uses Tailwind, update brand name + colors
- `landing/styles.css` — minimal changes

### Static assets
- `static/image/` — new logo files
- `frontend/public/` — new favicon
