# Augur UX Rethink — Product Views Architecture

> This plan replaces ad-hoc view fixes with a strategic UX architecture.

## The Problem

We have TWO conflicting approaches:
1. **Old MiroFish views** — rich data (graph, entities, profiles, simulation logs, reports, chat) but dated dark UI
2. **New Augur views** — clean light theme but stripped of data richness

**What users actually need:** A SINGLE cohesive experience that shows ALL the data beautifully.

## Product Insight

Augur's value isn't just "we ran a simulation." It's the **depth of insight** users can explore:
- **WHO** are the agents? (profiles, backgrounds, motivations)
- **WHAT** did they do? (posts, comments, debates, reactions)
- **WHY** did they react that way? (relationships, influence chains)
- **SO WHAT?** (report with evidence, trends, risks)
- **NOW WHAT?** (chat with agents, ask follow-ups, drill deeper)

Every piece of data the system generates should be explorable. Hiding it makes the product feel shallow.

## New View Architecture

### View 1: Prediction Progress (`/predict/:taskId`)
**Purpose:** Show the prediction building in real-time. Already done, but needs the graph.
**Keep as-is** with the live graph addition.

### View 2: Prediction Workspace (`/workspace/:projectId`) — NEW
**Purpose:** The main view after a prediction completes. This is where users spend 80% of their time.

**Layout: Three-panel workspace**

```
┌──────────────────────────────────────────────────────────────┐
│  AUGUR    Prediction: "GPT-5 Impact"    [Share] [Download]   │
├────────────┬─────────────────────────────┬───────────────────┤
│            │                             │                   │
│  Navigation│     Main Content Area       │   Detail Panel    │
│            │                             │                   │
│  📊 Report │  (changes based on nav)     │ (context detail)  │
│  🔗 Graph  │                             │                   │
│  👥 Agents │                             │                   │
│  💬 Chat   │                             │                   │
│  📋 Data   │                             │                   │
│            │                             │                   │
│  ──────── │                             │                   │
│  Settings  │                             │                   │
│            │                             │                   │
├────────────┴─────────────────────────────┴───────────────────┤
│  Status: Completed · 108 entities · 72 relationships · 5 rounds │
└──────────────────────────────────────────────────────────────┘
```

**Left Sidebar (Navigation):**
- Report (default view)
- Knowledge Graph
- Agents (profiles + activity)
- Chat (report agent + individual agents)
- Raw Data (simulation logs, actions, timeline)

**Main Content (changes based on nav selection):**

#### Tab: Report
- Full prediction report with sections
- Each section expandable/collapsible
- Blockquotes highlighted with agent attribution
- Download buttons (MD, HTML)
- "Ask about this" button → opens chat with context

#### Tab: Knowledge Graph
- Full D3.js graph visualization (the one users love)
- Entity type color legend
- Click node → Detail Panel shows entity info + related facts
- Click edge → Detail Panel shows relationship details
- Zoom, pan, search within graph
- Toggle: show/hide edge labels

#### Tab: Agents
- Grid of agent profile cards
```
┌─────────────────────────┐
│  Sarah Chen              │
│  Senior Developer        │
│  ────────────────────── │
│  "I'm both thrilled     │
│   and terrified..."      │
│                         │
│  Posts: 12 · Likes: 8   │
│  Sentiment: 😊 Positive  │
│                         │
│  [Chat with Sarah →]    │
└─────────────────────────┘
```
- Filter by: role, sentiment, activity level
- Click agent → Detail Panel shows full profile + all posts
- "Interview Agent" button → opens 1:1 chat

#### Tab: Chat
- Report Agent chat (already built)
- Agent selector dropdown to chat with specific agents
- Conversation history preserved
- "Send Survey" — ask all agents the same question

#### Tab: Raw Data
- Simulation timeline: scrollable list of all actions by round
```
Round 3 · Twitter
├── Sarah_Chen posted: "GPT-5 is a game changer..."
├── Prof_Williams replied: "But what about education?"
├── RegulatorWatch retweeted Sarah_Chen
└── InvestorMike liked Prof_Williams
```
- Agent action summary: table of who did what
- Platform comparison: Twitter vs Reddit sentiment
- Export: CSV download of all simulation data

**Right Panel (Detail — context-sensitive):**
- Shows details when something is selected in the main area
- Click an entity in graph → shows entity details + related facts
- Click an agent → shows profile + activity history
- Click a report quote → shows source agent + original post
- Collapses when nothing is selected

### View 3: Dashboard (`/dashboard`) — Already done
Just needs the smart navigation to `/workspace/:projectId` instead of `/process/:projectId`

### View 4: Upload (`/new`) — Already done
Clean upload form → starts prediction → goes to progress view

## Component Mapping

### Existing components to REUSE (not delete):
| Component | Where in Workspace |
|-----------|-------------------|
| `GraphPanel.vue` | Graph tab — full visualization |
| `Step4Report.vue` | Report tab — report rendering logic |
| `Step5Interaction.vue` | Chat tab — agent chat logic |
| `Step2EnvSetup.vue` (agent profiles section) | Agents tab — profile display |
| `Step3Simulation.vue` (log viewer) | Raw Data tab — simulation timeline |

### New components to create:
| Component | Purpose |
|-----------|---------|
| `WorkspaceView.vue` | Main workspace layout with sidebar + content + detail panel |
| `WorkspaceSidebar.vue` | Left navigation tabs |
| `WorkspaceDetail.vue` | Right detail panel (context-sensitive) |
| `AgentCard.vue` | Individual agent profile card |
| `SimulationTimeline.vue` | Round-by-round action timeline |
| `EntityDetail.vue` | Entity info panel (for graph click) |

## Design Principles

1. **Nothing is hidden** — all data is accessible, just organized into tabs
2. **Progressive disclosure** — overview first, click for details
3. **Context-sensitive detail** — right panel shows relevant detail for what you're looking at
4. **Consistent navigation** — sidebar is always visible, you always know where you are
5. **Cross-reference** — click an agent name in the report → jumps to their profile. Click an entity → shows in graph.
6. **Beautiful defaults** — the Report tab is the default view, most users start here

## Visual Design

Follow the Augur design system (globals.css):
- Light background (#F8FAFC)
- White content panels (#FFFFFF)
- Indigo sidebar active state
- Subtle borders (#E2E8F0)
- Plus Jakarta Sans headings, Inter body
- Consistent spacing (8px scale)

**Sidebar:**
- 240px wide, fixed
- White background
- Active tab: indigo left border + indigo text + light indigo background
- Icons + labels for each tab

**Main content:**
- Fluid width
- White card with padding
- Scroll within tab content

**Detail panel:**
- 320px wide, slides in from right
- White background with left border
- Close button
- Content scrolls independently

## Implementation Order

| Phase | What | Effort | Priority |
|-------|------|--------|----------|
| **1. WorkspaceView shell** | Layout with sidebar + content + detail panel | 4h | CRITICAL |
| **2. Report tab** | Embed existing report rendering | 2h | CRITICAL |
| **3. Graph tab** | Embed existing GraphPanel with entity click | 2h | HIGH |
| **4. Chat tab** | Embed existing interaction with agent selector | 2h | HIGH |
| **5. Agents tab** | New agent grid with profile cards | 3h | HIGH |
| **6. Raw Data tab** | Simulation timeline + exports | 3h | MEDIUM |
| **7. Detail panel** | Context-sensitive right panel | 3h | MEDIUM |
| **8. Cross-referencing** | Click agent name → profile, click entity → graph | 2h | LOW |
| **9. Route + Dashboard update** | `/workspace/:id`, dashboard navigation | 1h | CRITICAL |
| **Total** | | **~22h** |

## Route Changes

```
/workspace/:projectId          → WorkspaceView (default: Report tab)
/workspace/:projectId/graph    → WorkspaceView (Graph tab)
/workspace/:projectId/agents   → WorkspaceView (Agents tab)
/workspace/:projectId/chat     → WorkspaceView (Chat tab)
/workspace/:projectId/data     → WorkspaceView (Raw Data tab)
```

Dashboard "View Results" → `/workspace/:projectId`

## Key Insight: DON'T Delete, COMPOSE

The existing Step1-5 components contain complex working logic (D3 graph rendering, report section streaming, agent chat with tool calls, simulation log parsing). Don't rewrite them. **Embed them** in the workspace tabs with new styling wrappers.
