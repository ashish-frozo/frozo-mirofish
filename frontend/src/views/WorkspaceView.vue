<template>
  <div class="workspace-page">
    <!-- Sidebar Navigation -->
    <aside class="workspace-sidebar">
      <div class="sidebar-header">
        <h1 class="sidebar-brand">AUGUR</h1>
        <p class="sidebar-subtitle">AI Workspace</p>
      </div>
      <nav class="sidebar-nav">
        <a
          v-for="tab in tabs"
          :key="tab.id"
          href="#"
          class="sidebar-link"
          :class="{ 'sidebar-link--active': activeTab === tab.id }"
          @click.prevent="activeTab = tab.id"
        >
          <span class="material-symbols-outlined">{{ tab.icon }}</span>
          {{ tab.label }}
        </a>
      </nav>
    </aside>

    <!-- Top Navigation Bar -->
    <header class="workspace-topbar">
      <h2 class="topbar-title">{{ project?.simulation_requirement || 'Loading...' }}</h2>
      <div class="topbar-actions">
        <button class="topbar-btn topbar-btn--text" @click="goBack">
          <span class="material-symbols-outlined">arrow_back</span>
          Back
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="workspace-main">
      <!-- Loading State -->
      <div v-if="loading" class="workspace-loading">
        <span class="material-symbols-outlined workspace-loading__icon">hourglass_top</span>
        <p>Loading workspace...</p>
      </div>

      <!-- Report Tab -->
      <div v-else-if="activeTab === 'report'" class="tab-content tab-report">
        <article class="report-article">
          <header class="report-header">
            <div class="report-phase-badge">
              <span class="report-phase-dot"></span>
              <span class="report-phase-label">Prediction Report</span>
            </div>
            <h1 class="report-title">{{ project?.simulation_requirement || 'Untitled Prediction' }}</h1>
            <p class="report-subtitle">
              Generated from swarm intelligence simulation with {{ graphData?.nodes?.length || 0 }} entities analyzed.
            </p>
          </header>

          <section class="report-body">
            <!-- Actual report content -->
            <div v-if="reportData && reportData.markdown_content" class="report-summary-card">
              <div class="report-rendered-content" v-html="renderMarkdown(reportData.markdown_content)"></div>
            </div>
            <div v-else-if="reportData && reportData.outline" class="report-summary-card">
              <h3 class="report-section-title">{{ reportData.title || 'Report Outline' }}</h3>
              <p v-if="reportData.summary" class="report-summary-content">{{ reportData.summary }}</p>
              <div v-for="(section, idx) in reportData.outline.sections" :key="idx" class="report-section-item">
                <h4>{{ section.title }}</h4>
              </div>
            </div>
            <div v-else class="report-summary-card">
              <h3 class="report-section-title">Executive Summary</h3>
              <div class="report-summary-content">
                <p v-if="project?.step_data?.report_content">{{ project.step_data.report_content }}</p>
                <p v-else class="report-placeholder">
                  Report not yet available. Complete the simulation and report generation steps first.
                </p>
              </div>
            </div>

            <!-- Download actions -->
            <div v-if="reportData && project?.report_id" class="report-actions">
              <button @click="downloadReport('md')" class="report-action-btn">
                <span class="material-symbols-outlined">description</span>
                Download Markdown
              </button>
              <button @click="downloadReport('html')" class="report-action-btn">
                <span class="material-symbols-outlined">code</span>
                Download HTML
              </button>
            </div>

            <div class="report-stats-row">
              <div class="report-stat-card report-stat-card--primary">
                <h4 class="report-stat-label">Entities Analyzed</h4>
                <span class="report-stat-value">{{ graphData?.nodes?.length || 0 }}</span>
              </div>
              <div class="report-stat-card">
                <h4 class="report-stat-label">Relationships</h4>
                <span class="report-stat-value">{{ graphData?.edges?.length || 0 }}</span>
              </div>
              <div class="report-stat-card">
                <h4 class="report-stat-label">Simulation Rounds</h4>
                <span class="report-stat-value">{{ totalRounds }}</span>
              </div>
            </div>
          </section>
        </article>
      </div>

      <!-- Graph Tab -->
      <div v-else-if="activeTab === 'graph'" class="tab-content tab-graph">
        <GraphPanel
          v-if="graphData"
          :graphData="graphData"
          :loading="false"
        />
        <div v-else class="tab-empty">
          <span class="material-symbols-outlined tab-empty__icon">hub</span>
          <p>No graph data available. Build a knowledge graph first.</p>
        </div>
      </div>

      <!-- Agents Tab -->
      <div v-else-if="activeTab === 'agents'" class="tab-content tab-agents">
        <div class="agents-header">
          <h3 class="agents-title">Agents Directory</h3>
          <span class="agents-count">{{ agents.length }} agents</span>
        </div>
        <div class="agents-grid">
          <div
            v-for="(agent, index) in agents"
            :key="index"
            class="agent-card"
          >
            <div class="agent-card__header">
              <div class="agent-card__avatar" :style="{ backgroundColor: agentColors[index % agentColors.length] }">
                {{ getInitials(agent.name || agent.agent_name || `Agent ${index + 1}`) }}
              </div>
              <div class="agent-card__info">
                <h4 class="agent-card__name">{{ agent.name || agent.agent_name || `Agent ${index + 1}` }}</h4>
                <p class="agent-card__role">{{ agent.role || agent.persona || 'Simulation Agent' }}</p>
              </div>
            </div>
            <div v-if="agent.description || agent.bio" class="agent-card__quote">
              <span class="agent-card__quote-mark">"</span>
              {{ truncate(agent.description || agent.bio, 120) }}
            </div>
            <div class="agent-card__stats">
              <div class="agent-card__stat">
                <span class="agent-card__stat-label">Posts</span>
                <span class="agent-card__stat-value">{{ agent.post_count || '--' }}</span>
              </div>
              <div class="agent-card__stat">
                <span class="agent-card__stat-label">Likes</span>
                <span class="agent-card__stat-value">{{ agent.like_count || '--' }}</span>
              </div>
              <div class="agent-card__stat">
                <span class="agent-card__stat-label">Sentiment</span>
                <span class="agent-card__stat-value agent-card__stat-value--sentiment">
                  <span class="sentiment-dot" :class="'sentiment-dot--' + (agent.sentiment || 'neutral')"></span>
                  {{ agent.sentiment || 'Neutral' }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="agents.length === 0" class="tab-empty">
            <span class="material-symbols-outlined tab-empty__icon">group</span>
            <p>No agent profiles available. Run a simulation to generate agents.</p>
          </div>
        </div>
      </div>

      <!-- Chat Tab -->
      <div v-else-if="activeTab === 'chat'" class="tab-content tab-chat">
        <div class="chat-container">
          <div class="chat-header">
            <span class="chat-header__label">Active Persona</span>
            <h3 class="chat-header__agent">Report Agent</h3>
          </div>
          <div class="chat-messages" ref="chatMessagesEl">
            <div class="chat-message chat-message--agent">
              <div class="chat-message__avatar">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">smart_toy</span>
              </div>
              <div class="chat-message__body">
                <span class="chat-message__sender">Report Agent</span>
                <div class="chat-message__bubble chat-message__bubble--agent">
                  <p>Welcome to the prediction workspace. I can help you explore the simulation results, analyze agent behaviors, and dive deeper into the prediction outcomes. What would you like to know?</p>
                </div>
              </div>
            </div>
            <div
              v-for="(msg, idx) in chatMessages"
              :key="idx"
              class="chat-message"
              :class="msg.role === 'user' ? 'chat-message--user' : 'chat-message--agent'"
            >
              <div class="chat-message__avatar">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">
                  {{ msg.role === 'user' ? 'person' : 'smart_toy' }}
                </span>
              </div>
              <div class="chat-message__body">
                <span class="chat-message__sender">{{ msg.role === 'user' ? 'You' : 'Report Agent' }}</span>
                <div class="chat-message__bubble" :class="msg.role === 'user' ? 'chat-message__bubble--user' : 'chat-message__bubble--agent'">
                  <p>{{ msg.content }}</p>
                </div>
              </div>
            </div>
            <div v-if="chatLoading" class="chat-message chat-message--agent">
              <div class="chat-message__avatar">
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">smart_toy</span>
              </div>
              <div class="chat-message__body">
                <span class="chat-message__sender">Report Agent</span>
                <div class="chat-message__bubble chat-message__bubble--agent">
                  <p class="chat-typing">Thinking...</p>
                </div>
              </div>
            </div>
          </div>
          <div v-if="project?.simulation_id" class="chat-input">
            <div class="chat-input__wrapper">
              <button class="chat-input__attach">
                <span class="material-symbols-outlined">attach_file</span>
              </button>
              <input
                v-model="chatInput"
                type="text"
                class="chat-input__field"
                placeholder="Ask anything about this prediction..."
                @keydown.enter="sendChat"
              />
              <button class="chat-input__send" :disabled="!chatInput.trim() || chatLoading" @click="sendChat">
                <span class="chat-input__send-label">Send</span>
                <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">send</span>
              </button>
            </div>
          </div>
          <div v-else class="chat-unavailable">
            <span class="material-symbols-outlined">info</span>
            <p>Chat is available after the simulation completes.</p>
          </div>
        </div>
      </div>

      <!-- Data Tab -->
      <div v-else-if="activeTab === 'data'" class="tab-content tab-data">
        <div class="data-header">
          <h3 class="data-title">Raw Simulation Data</h3>
          <div class="data-filters">
            <div class="data-filter-group">
              <button class="data-filter-btn data-filter-btn--active">Both</button>
              <button class="data-filter-btn">Twitter</button>
              <button class="data-filter-btn">Reddit</button>
            </div>
          </div>
        </div>
        <div class="data-timeline">
          <div class="tab-empty">
            <span class="material-symbols-outlined tab-empty__icon">table_chart</span>
            <p>Raw simulation data will appear here after a simulation completes.</p>
            <p class="tab-empty__sub">Timeline view with agent interactions grouped by round and platform.</p>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer Status Bar -->
    <footer class="workspace-footer">
      <div class="footer-stats">
        <span class="footer-status">
          <span class="footer-status__dot" :class="statusDotClass"></span>
          {{ statusLabel }}
        </span>
        <span class="footer-divider"></span>
        <span>{{ graphData?.nodes?.length || 0 }} entities</span>
        <span class="footer-divider"></span>
        <span>{{ graphData?.edges?.length || 0 }} relationships</span>
        <span class="footer-divider"></span>
        <span>{{ totalRounds }} rounds</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, getGraphData } from '../api/graph'
import { getReport, chatWithReport, downloadReport as apiDownloadReport } from '../api/report'
import service from '../api/index'
import GraphPanel from '../components/GraphPanel.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.projectId

const project = ref(null)
const graphData = ref(null)
const agents = ref([])
const activeTab = ref('report')
const loading = ref(true)
const reportData = ref(null)
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatMessagesEl = ref(null)

const tabs = [
  { id: 'report', label: 'Report', icon: 'description' },
  { id: 'graph', label: 'Knowledge Graph', icon: 'account_tree' },
  { id: 'agents', label: 'Agents', icon: 'smart_toy' },
  { id: 'chat', label: 'Chat', icon: 'forum' },
  { id: 'data', label: 'Raw Data', icon: 'database' },
]

const agentColors = [
  '#e0e7ff', '#fef3c7', '#fce7f3', '#dcfce7', '#e0f2fe', '#fde68a', '#ddd6fe', '#fed7aa'
]

const statusLabel = computed(() => {
  const status = project.value?.status
  if (status === 'completed' || status === 'interacting') return 'COMPLETED'
  if (status === 'reporting') return 'REPORTING'
  if (status === 'simulating') return 'SIMULATING'
  return status?.toUpperCase() || 'LOADING'
})

const statusDotClass = computed(() => {
  const status = project.value?.status
  if (status === 'completed' || status === 'interacting') return 'footer-status__dot--completed'
  if (status === 'simulating') return 'footer-status__dot--simulating'
  return 'footer-status__dot--default'
})

const totalRounds = computed(() => {
  return project.value?.step_data?.rounds ||
         project.value?.step_data?.num_rounds ||
         graphData.value?.rounds ||
         '--'
})

function renderMarkdown(md) {
  if (!md) return ''
  let html = md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
  return '<p>' + html + '</p>'
}

async function downloadReport(format) {
  try {
    await apiDownloadReport(project.value.report_id, format)
  } catch (e) {
    console.error('Download failed:', e)
  }
}

async function sendChat() {
  if (!chatInput.value.trim() || chatLoading.value) return
  const userMsg = chatInput.value.trim()
  chatMessages.value.push({ role: 'user', content: userMsg })
  chatInput.value = ''
  chatLoading.value = true

  await nextTick()
  if (chatMessagesEl.value) {
    chatMessagesEl.value.scrollTop = chatMessagesEl.value.scrollHeight
  }

  try {
    const res = await chatWithReport({
      simulation_id: project.value?.simulation_id,
      message: userMsg,
      chat_history: chatMessages.value.slice(0, -1),
    })
    if (res.response) {
      chatMessages.value.push({ role: 'agent', content: res.response })
    } else if (res.data?.response) {
      chatMessages.value.push({ role: 'agent', content: res.data.response })
    }
  } catch (e) {
    chatMessages.value.push({ role: 'agent', content: 'Sorry, I could not process your request.' })
  } finally {
    chatLoading.value = false
    await nextTick()
    if (chatMessagesEl.value) {
      chatMessagesEl.value.scrollTop = chatMessagesEl.value.scrollHeight
    }
  }
}

function getInitials(name) {
  return name
    .split(/\s+/)
    .map(w => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function truncate(text, maxLen) {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

function goBack() {
  router.push('/dashboard')
}

onMounted(async () => {
  try {
    const res = await getProject(projectId)
    if (res.success) {
      project.value = res.data
      // Load graph data
      if (res.data.graph_id) {
        const gRes = await getGraphData(res.data.graph_id)
        if (gRes.success) graphData.value = gRes.data
      }
      // Load report if report_id exists
      if (res.data.report_id) {
        try {
          const reportRes = await getReport(res.data.report_id)
          if (reportRes.success !== false) {
            reportData.value = reportRes.data || reportRes
          }
        } catch (e) {
          console.warn('Could not load report:', e.message)
        }
      }
      // Load agent profiles if simulation exists
      if (res.data.simulation_id) {
        try {
          const profileRes = await service.get(`/api/simulation/${res.data.simulation_id}/profiles`)
          if (profileRes?.profiles) {
            agents.value = profileRes.profiles
          } else if (profileRes?.data?.profiles) {
            agents.value = profileRes.data.profiles
          }
        } catch (e) {
          console.warn('Could not load agent profiles:', e.message)
        }
      }
    }
  } catch (e) {
    console.error('Failed to load project:', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
/* ========================================
   Workspace Layout
   ======================================== */
.workspace-page {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 56px 1fr 32px;
  grid-template-areas:
    "sidebar topbar"
    "sidebar main"
    "sidebar footer";
  height: 100vh;
  overflow: hidden;
  background: var(--bg-surface, #f7f9fb);
  font-family: 'Inter', sans-serif;
}

/* ========================================
   Sidebar
   ======================================== */
.workspace-sidebar {
  grid-area: sidebar;
  background: linear-gradient(to bottom, #f7f9fb, #f2f4f6);
  border-right: 1px solid transparent;
  display: flex;
  flex-direction: column;
  z-index: 40;
}

.sidebar-header {
  padding: 32px 24px 24px;
}

.sidebar-brand {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: #4f46e5;
  margin: 0;
}

.sidebar-subtitle {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  font-weight: 600;
  color: #777587;
  margin: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 12px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 500;
  font-size: 0.875rem;
  letter-spacing: -0.01em;
  color: #64748b;
  text-decoration: none;
  transition: all 0.2s;
  border-left: 2px solid transparent;
}

.sidebar-link:hover {
  background: #f1f5f9;
}

.sidebar-link--active {
  color: #4338ca;
  background: rgba(79, 70, 229, 0.05);
  border-left-color: #4f46e5;
  font-weight: 600;
  opacity: 0.9;
}

.sidebar-link .material-symbols-outlined {
  font-size: 20px;
}

/* ========================================
   Top Bar
   ======================================== */
.workspace-topbar {
  grid-area: topbar;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  z-index: 30;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.topbar-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 600;
  font-size: 1rem;
  color: #191c1e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 60%;
  margin: 0;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
  padding: 6px 12px;
}

.topbar-btn--text {
  background: none;
  color: #64748b;
}

.topbar-btn--text:hover {
  color: #4f46e5;
  background: rgba(79, 70, 229, 0.05);
}

/* ========================================
   Main Content
   ======================================== */
.workspace-main {
  grid-area: main;
  overflow-y: auto;
  padding: 32px;
}

.workspace-main::-webkit-scrollbar {
  width: 4px;
}
.workspace-main::-webkit-scrollbar-track {
  background: transparent;
}
.workspace-main::-webkit-scrollbar-thumb {
  background: #e0e3e5;
  border-radius: 10px;
}

.tab-content {
  min-height: 100%;
}

/* Loading */
.workspace-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #777587;
  gap: 12px;
}

.workspace-loading__icon {
  font-size: 40px;
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Empty State */
.tab-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 24px;
  color: #777587;
  text-align: center;
  gap: 8px;
}

.tab-empty__icon {
  font-size: 48px;
  opacity: 0.4;
  margin-bottom: 8px;
}

.tab-empty__sub {
  font-size: 0.8125rem;
  opacity: 0.7;
}

/* ========================================
   Report Tab
   ======================================== */
.report-article {
  max-width: 900px;
}

.report-header {
  margin-bottom: 40px;
}

.report-phase-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: #eaddff;
  color: #25005a;
  border-radius: 9999px;
  margin-bottom: 20px;
}

.report-phase-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #712ae2;
}

.report-phase-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.report-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: #191c1e;
  margin: 0 0 16px;
}

.report-subtitle {
  font-size: 1.0625rem;
  color: #464555;
  line-height: 1.6;
  max-width: 640px;
  margin: 0;
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.report-summary-card {
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.04);
}

.report-section-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.125rem;
  font-weight: 700;
  margin: 0 0 16px;
  color: #191c1e;
}

.report-summary-content {
  line-height: 1.7;
  color: #464555;
}

.report-placeholder {
  color: #777587;
  font-style: italic;
}

.report-rendered-content {
  line-height: 1.8;
  color: #464555;
}

.report-rendered-content h1 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.75rem;
  font-weight: 700;
  color: #191c1e;
  margin: 32px 0 16px;
}

.report-rendered-content h2 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.375rem;
  font-weight: 700;
  color: #191c1e;
  margin: 28px 0 12px;
}

.report-rendered-content h3 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.125rem;
  font-weight: 700;
  color: #191c1e;
  margin: 24px 0 8px;
}

.report-rendered-content blockquote {
  border-left: 3px solid #4f46e5;
  padding-left: 16px;
  margin: 16px 0;
  color: #64748b;
  font-style: italic;
}

.report-rendered-content li {
  margin-left: 20px;
  margin-bottom: 4px;
}

.report-rendered-content strong {
  color: #191c1e;
}

.report-section-item {
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.report-section-item:last-child {
  border-bottom: none;
}

.report-section-item h4 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 600;
  font-size: 0.9375rem;
  color: #191c1e;
  margin: 0;
}

.report-actions {
  display: flex;
  gap: 12px;
}

.report-action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #4f46e5;
  background: rgba(79, 70, 229, 0.06);
  border: 1px solid rgba(79, 70, 229, 0.15);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.report-action-btn:hover {
  background: rgba(79, 70, 229, 0.12);
  transform: translateY(-1px);
}

.report-action-btn .material-symbols-outlined {
  font-size: 18px;
}

.report-stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.report-stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.04);
}

.report-stat-card--primary {
  background: #4f46e5;
  color: #fff;
}

.report-stat-card--primary .report-stat-label {
  color: rgba(255, 255, 255, 0.8);
}

.report-stat-card--primary .report-stat-value {
  color: #fff;
}

.report-stat-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #777587;
  margin-bottom: 8px;
}

.report-stat-value {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #191c1e;
}

/* ========================================
   Graph Tab
   ======================================== */
.tab-graph {
  height: calc(100vh - 56px - 32px - 32px - 32px);
}

/* ========================================
   Agents Tab
   ======================================== */
.agents-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.agents-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0;
}

.agents-count {
  font-size: 0.875rem;
  font-weight: 500;
  color: #777587;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.agent-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.06);
  transition: transform 0.2s;
}

.agent-card:hover {
  transform: translateY(-4px);
}

.agent-card__header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.agent-card__avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  color: #4338ca;
  flex-shrink: 0;
}

.agent-card__name {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 700;
  font-size: 0.9375rem;
  color: #191c1e;
  margin: 0;
}

.agent-card__role {
  font-size: 0.75rem;
  font-weight: 500;
  color: #777587;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: 0;
}

.agent-card__quote {
  background: #f2f4f6;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-style: italic;
  font-size: 0.875rem;
  color: #464555;
  position: relative;
}

.agent-card__quote-mark {
  position: absolute;
  top: -4px;
  left: 16px;
  font-size: 1.5rem;
  color: #4f46e5;
  opacity: 0.3;
  font-family: serif;
}

.agent-card__stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.agent-card__stat-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  color: #777587;
  text-transform: uppercase;
}

.agent-card__stat-value {
  font-size: 0.875rem;
  font-weight: 700;
  color: #191c1e;
}

.agent-card__stat-value--sentiment {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.sentiment-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.sentiment-dot--positive,
.sentiment-dot--Positive {
  background: #10b981;
}

.sentiment-dot--negative,
.sentiment-dot--Negative {
  background: #ef4444;
}

.sentiment-dot--neutral,
.sentiment-dot--Neutral {
  background: #94a3b8;
}

/* ========================================
   Chat Tab
   ======================================== */
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - 32px - 32px - 32px);
  max-width: 800px;
}

.chat-header {
  margin-bottom: 24px;
}

.chat-header__label {
  font-size: 10px;
  font-weight: 600;
  color: #4f46e5;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 4px;
}

.chat-header__agent {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chat-message {
  display: flex;
  gap: 12px;
  max-width: 640px;
}

.chat-message__avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #e2dfff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4f46e5;
  flex-shrink: 0;
}

.chat-message__avatar .material-symbols-outlined {
  font-size: 16px;
}

.chat-message__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-message__sender {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: -0.02em;
  color: #191c1e;
}

.chat-message__bubble {
  padding: 20px;
  border-radius: 12px;
}

.chat-message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-message--user .chat-message__avatar {
  background: #4f46e5;
  color: #fff;
}

.chat-message--user .chat-message__body {
  align-items: flex-end;
}

.chat-message__bubble--user {
  background: #4f46e5;
  color: #fff;
  border-top-right-radius: 0;
}

.chat-message__bubble--user p {
  color: #fff;
}

.chat-message__bubble--agent {
  background: #fff;
  border-top-left-radius: 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
}

.chat-typing {
  color: #94a3b8 !important;
  font-style: italic;
}

.chat-message__bubble p {
  margin: 0;
  font-size: 0.9375rem;
  line-height: 1.6;
  color: #475569;
}

.chat-input {
  padding-top: 16px;
}

.chat-input__wrapper {
  background: #fff;
  padding: 8px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.chat-input__attach {
  padding: 8px;
  color: #94a3b8;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 8px;
  transition: color 0.2s;
}

.chat-input__attach:hover {
  color: #4f46e5;
}

.chat-input__field {
  flex: 1;
  background: transparent;
  border: none;
  font-size: 0.875rem;
  color: #1e293b;
  padding: 4px 8px;
  outline: none;
}

.chat-input__field::placeholder {
  color: #94a3b8;
}

.chat-input__send {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #4f46e5;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-input__send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input__send:not(:disabled):hover {
  background: #4338ca;
}

.chat-input__send-label {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.chat-input__send .material-symbols-outlined {
  font-size: 14px;
}

.chat-input__hint {
  margin: 8px 0 0;
  font-size: 0.75rem;
  color: #94a3b8;
  text-align: center;
}

.chat-unavailable {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: #64748B;
  text-align: center;
  gap: 8px;
}

/* ========================================
   Data Tab
   ======================================== */
.data-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.data-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0;
}

.data-filter-group {
  display: flex;
  gap: 4px;
  background: #e0e3e5;
  padding: 4px;
  border-radius: 12px;
}

.data-filter-btn {
  padding: 6px 16px;
  font-size: 0.75rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  background: transparent;
  color: #464555;
  transition: all 0.2s;
}

.data-filter-btn--active {
  background: #fff;
  color: #4f46e5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.data-filter-btn:hover:not(.data-filter-btn--active) {
  background: rgba(255, 255, 255, 0.5);
}

/* ========================================
   Footer Status Bar
   ======================================== */
.workspace-footer {
  grid-area: footer;
  background: #fff;
  border-top: 1px solid rgba(226, 232, 240, 0.5);
  display: flex;
  align-items: center;
  padding: 0 24px;
  z-index: 30;
}

.footer-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  font-family: 'Inter', sans-serif;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.footer-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-status__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #94a3b8;
}

.footer-status__dot--completed {
  background: #10b981;
}

.footer-status__dot--simulating {
  background: #f59e0b;
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.footer-divider {
  opacity: 0.3;
}

.footer-divider::after {
  content: '\00B7';
}
</style>
