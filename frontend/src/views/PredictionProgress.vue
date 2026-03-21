<template>
  <div class="prediction-page">
    <!-- Top Navigation Bar -->
    <header class="top-nav">
      <div class="top-nav__inner">
        <div class="top-nav__brand" @click="$router.push('/dashboard')">AUGUR</div>
        <div class="top-nav__right">
          <button
            v-if="data.status === 'running'"
            class="cancel-btn"
            @click="handleCancel"
            :disabled="cancelling"
          >
            {{ cancelling ? 'Cancelling...' : 'Cancel' }}
          </button>
          <button class="top-nav__avatar" @click="$router.push('/dashboard')">
            <span class="material-symbols-outlined">account_circle</span>
          </button>
        </div>
      </div>
    </header>

    <main class="main-content">
      <!-- Hero Progress Section -->
      <section class="hero-section">
        <div class="hero-title-row">
          <h1 class="hero-title">Building Your Prediction</h1>
          <span
            v-if="data.status === 'running'"
            class="material-symbols-outlined hero-spinner"
          >progress_activity</span>
        </div>

        <!-- Progress Bar Container -->
        <div class="progress-container">
          <div class="progress-info">
            <div class="progress-status">
              <span class="progress-status__label">Status</span>
              <p class="progress-status__text">
                <template v-if="data.status === 'running' && data.message">{{ data.message }}</template>
                <template v-else-if="data.status === 'completed'">Prediction Complete</template>
                <template v-else-if="data.status === 'failed'">Prediction Failed</template>
                <template v-else>Initializing...</template>
              </p>
            </div>
            <span class="progress-percent">{{ data.progress || 0 }}%</span>
          </div>
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{ width: (data.progress || 0) + '%' }"
            ></div>
          </div>
        </div>

        <!-- Steps Checklist -->
        <div class="steps-list">
          <div
            v-for="(step, index) in steps"
            :key="step.key"
            class="step-row"
            :class="{
              'step-row--last': index === steps.length - 1
            }"
          >
            <!-- Connector line -->
            <div v-if="index < steps.length - 1" class="step-connector"></div>

            <!-- Step icon -->
            <div class="step-icon-wrap">
              <span
                v-if="step.status === 'completed'"
                class="material-symbols-outlined step-icon step-icon--completed"
                style="font-variation-settings: 'FILL' 1;"
              >check_circle</span>
              <span
                v-else-if="step.status === 'active' && data.status !== 'failed'"
                class="material-symbols-outlined step-icon step-icon--active"
              >hourglass_empty</span>
              <span
                v-else-if="data.status === 'failed' && step.status === 'active'"
                class="material-symbols-outlined step-icon step-icon--failed"
                style="font-variation-settings: 'FILL' 1;"
              >cancel</span>
              <span
                v-else
                class="material-symbols-outlined step-icon step-icon--pending"
              >radio_button_unchecked</span>
            </div>

            <!-- Step info -->
            <div class="step-info">
              <h3
                class="step-name"
                :class="{
                  'step-name--active': step.status === 'active' && data.status !== 'failed',
                  'step-name--pending': step.status === 'pending',
                  'step-name--failed': data.status === 'failed' && step.status === 'active'
                }"
              >{{ step.label }}</h3>
              <p
                class="step-detail"
                :class="{
                  'step-detail--pending': step.status === 'pending'
                }"
              >
                <template v-if="step.status === 'completed' && step.stats">{{ step.stats }}</template>
                <template v-else-if="step.status === 'active' && step.stats">{{ step.stats }}</template>
                <template v-else-if="step.status === 'active' && data.message">{{ data.message }}</template>
                <template v-else-if="step.status === 'pending'">Waiting...</template>
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Error Card -->
      <div class="error-card" v-if="data.status === 'failed' && data.error">
        <div class="error-card__icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="10" fill="#FEE2E2"/>
            <path d="M10 6v4M10 13h.01" stroke="#EF4444" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="error-card__body">
          <div class="error-card__title">Prediction Failed</div>
          <div class="error-card__message">{{ data.error }}</div>
        </div>
      </div>

      <!-- Result Action Cards -->
      <div v-if="data.status === 'completed' && data.result" class="result-section">
        <h3 class="result-section__title">Prediction Complete!</h3>
        <p class="result-section__desc">Your prediction is ready. Explore the results:</p>

        <div class="action-cards">
          <button class="action-card" @click="goToReport">
            <div class="action-card__icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect x="3" y="2" width="14" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/>
                <path d="M7 7h6M7 10h6M7 13h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="action-card__text">
              <strong>View Report</strong>
              <span>Read the full prediction analysis</span>
            </div>
          </button>

          <button class="action-card" @click="goToInteraction">
            <div class="action-card__icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M4 4h12a1 1 0 011 1v8a1 1 0 01-1 1H7l-3 3V5a1 1 0 011-1z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="7.5" cy="9" r="0.75" fill="currentColor"/>
                <circle cx="10" cy="9" r="0.75" fill="currentColor"/>
                <circle cx="12.5" cy="9" r="0.75" fill="currentColor"/>
              </svg>
            </div>
            <div class="action-card__text">
              <strong>Chat with Agents</strong>
              <span>Interview simulated agents</span>
            </div>
          </button>

          <button class="action-card" @click="goToProject">
            <div class="action-card__icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="5" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="5" cy="15" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="15" cy="15" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                <path d="M8.5 7l-2 5.5M11.5 7l2 5.5M7.5 15h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="action-card__text">
              <strong>Full Workspace</strong>
              <span>Graph, simulation details, and more</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Retry Button -->
      <div class="retry-section" v-if="data.status === 'failed'">
        <button class="retry-btn" @click="$router.push('/new')">
          Retry
        </button>
      </div>

      <!-- Live Graph Visualization -->
      <div v-if="showGraph && graphData" class="graph-section">
        <div class="graph-header">
          <h3 class="graph-header__title">Knowledge Graph</h3>
          <span class="graph-header__stats" v-if="graphData.node_count !== undefined">
            {{ graphData.node_count }} entities &middot; {{ graphData.edge_count }} relationships
          </span>
        </div>
        <div class="graph-container">
          <GraphPanel
            :graphData="graphData"
            :loading="graphLoading"
            :currentPhase="graphPhase"
          />
        </div>
      </div>

      <!-- Live Visualization Placeholder -->
      <section
        v-if="data.status === 'running' && !showGraph"
        class="viz-placeholder"
      >
        <div class="viz-placeholder__bg"></div>
        <div class="viz-placeholder__content">
          <div class="viz-bars">
            <div class="viz-bar" style="height: 48px; opacity: 0.4;"></div>
            <div class="viz-bar" style="height: 64px; opacity: 0.6;"></div>
            <div class="viz-bar" style="height: 80px; opacity: 1;"></div>
            <div class="viz-bar" style="height: 56px; opacity: 0.7;"></div>
            <div class="viz-bar" style="height: 40px; opacity: 0.3;"></div>
          </div>
          <p class="viz-placeholder__label">Visualizing Real-time Neural Clusters</p>
        </div>
      </section>

      <!-- Completion Summary -->
      <div class="summary-card" v-if="data.status === 'completed' && data.result">
        <div class="summary-card__title">Prediction Complete</div>
        <div class="summary-grid">
          <div class="summary-item" v-if="data.result.graph_id">
            <span class="summary-item__label">Graph ID</span>
            <span class="summary-item__value summary-item__value--mono">{{ data.result.graph_id }}</span>
          </div>
          <div class="summary-item" v-if="data.result.simulation_id">
            <span class="summary-item__label">Simulation ID</span>
            <span class="summary-item__value summary-item__value--mono">{{ data.result.simulation_id }}</span>
          </div>
          <div class="summary-item" v-if="graphStats">
            <span class="summary-item__label">Knowledge Graph</span>
            <span class="summary-item__value">{{ graphStats }}</span>
          </div>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="footer-action" v-if="data.status === 'running'">
        <button
          class="footer-cancel-btn"
          @click="handleCancel"
          :disabled="cancelling"
        >
          Cancel
        </button>
      </div>
    </main>

    <!-- Footer -->
    <footer class="page-footer">
      <div class="page-footer__links">
        <a href="#">Privacy</a>
        <a href="#">Terms</a>
        <a href="#">Support</a>
      </div>
      <p class="page-footer__copy">&copy; 2024 Augur AI. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPredictionStatus, cancelPrediction } from '../api/predict'
import { getGraphData } from '../api/graph'
import GraphPanel from '../components/GraphPanel.vue'

const props = defineProps({
  taskId: { type: String, required: true }
})

const router = useRouter()
const cancelling = ref(false)
let pollTimer = null

const graphData = ref(null)
const graphId = ref(null)
const showGraph = ref(false)
const graphLoading = ref(false)

const data = reactive({
  status: 'pending',
  progress: 0,
  message: '',
  stage: '',
  stages: {},
  result: null,
  error: null,
})

const STEP_DEFS = [
  { key: 'ontology',    label: 'Knowledge Graph',       description: 'Analyzing documents and building entity graph' },
  { key: 'graph_build', label: 'Graph Enrichment',       description: 'Enriching Zep knowledge graph with relationships' },
  { key: 'env_setup',   label: 'Agent Profiles',         description: 'Generating agent profiles and simulation config' },
  { key: 'simulation',  label: 'Simulation',             description: 'Running dual-platform parallel simulation' },
  { key: 'report',      label: 'Report Generation',      description: 'Generating prediction insights' },
]

const steps = computed(() => {
  const currentStage = data.stage
  let reachedCurrent = false

  return STEP_DEFS.map(def_ => {
    const stageData = data.stages[def_.key]
    let status = 'pending'
    let stats = null

    if (stageData && stageData.status === 'completed') {
      status = 'completed'
      if (def_.key === 'ontology' && stageData.stats) {
        const s = stageData.stats
        if (s.concepts) stats = `${s.concepts} concepts extracted`
      }
      if (def_.key === 'graph_build' && stageData.stats) {
        stats = `${stageData.stats.nodes} entities \u00b7 ${stageData.stats.edges} relationships`
      }
      if (def_.key === 'env_setup' && stageData.stats?.agents) {
        stats = `${stageData.stats.agents} agents configured`
      }
      if (def_.key === 'simulation' && stageData.stats) {
        const s = stageData.stats
        if (s.total_rounds) {
          stats = `${s.total_rounds} rounds \u00b7 ${s.actions || 0} actions`
        } else if (s.rounds) {
          stats = `${s.rounds} rounds completed`
        }
      }
      if (def_.key === 'report') {
        stats = 'Analysis complete'
      }
    } else if (stageData && stageData.status === 'running') {
      status = 'active'
      reachedCurrent = true
      if (def_.key === 'simulation' && stageData.stats) {
        const s = stageData.stats
        if (s.round && s.total_rounds) {
          stats = `Round ${s.round}/${s.total_rounds}` + (s.actions ? ` \u00b7 ${s.actions} actions so far` : '')
        }
      }
      if (def_.key === 'report' && stageData.stats) {
        const s = stageData.stats
        if (s.section && s.total_sections) {
          stats = `Section ${s.section}/${s.total_sections} generating...`
        }
      }
    } else if (def_.key === currentStage) {
      status = 'active'
      reachedCurrent = true
    } else if (!reachedCurrent && data.status === 'running') {
      // Steps before current that aren't marked completed are still pending
    }

    if (def_.key === 'report' && data.stages.interaction?.status === 'ready') {
      status = 'completed'
      if (!stats) stats = 'Analysis complete'
    }

    return { ...def_, status, stats }
  })
})

const graphPhase = computed(() => {
  const stage = data.stage
  if (stage === 'ontology' || stage === 'graph_build') return 1
  if (stage === 'simulation') return 3
  return 2
})

const graphStats = computed(() => {
  const gs = data.stages?.graph_build?.stats
  if (!gs) return null
  return `${gs.nodes} entities \u00b7 ${gs.edges} relationships`
})

async function poll() {
  try {
    const res = await getPredictionStatus(props.taskId)
    const d = res.data
    Object.assign(data, d)

    const result = d.result || {}
    const stages = d.stages || {}
    const gid = result.graph_id || stages.graph_build?.stats?.graph_id

    if (gid && gid !== graphId.value) {
      graphId.value = gid
      showGraph.value = true
    }

    if (graphId.value) {
      try {
        graphLoading.value = true
        const gRes = await getGraphData(graphId.value)
        const gData = gRes.data
        if (gData && (gData.nodes || gData.edges)) {
          graphData.value = gData
        }
      } catch (e) {
        // Graph data might not be ready yet, ignore
      } finally {
        graphLoading.value = false
      }
    }

    if (d.status === 'completed' || d.status === 'failed') {
      clearInterval(pollTimer)
      pollTimer = null
    }
  } catch (err) {
    console.error('Poll error:', err)
  }
}

async function handleCancel() {
  cancelling.value = true
  try {
    await cancelPrediction(props.taskId)
    data.status = 'failed'
    data.error = 'Cancelled by user'
  } catch (err) {
    console.error('Cancel error:', err)
  } finally {
    cancelling.value = false
  }
}

function goToReport() {
  const result = data.result
  if (result?.report_id) {
    router.push({ name: 'Report', params: { reportId: result.report_id } })
  }
}

function goToInteraction() {
  const result = data.result
  if (result?.report_id) {
    router.push({ name: 'Interaction', params: { reportId: result.report_id } })
  }
}

function goToProject() {
  const result = data.result
  if (result?.project_id) {
    router.push({ name: 'Process', params: { projectId: result.project_id } })
  }
}

onMounted(() => {
  poll()
  pollTimer = setInterval(poll, 3000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
/* ── Page Shell ── */
.prediction-page {
  min-height: 100vh;
  background: #f7f9fb;
  font-family: 'Inter', system-ui, sans-serif;
  color: #191c1e;
}

/* ── Top Navigation ── */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(247, 249, 251, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.06);
}

.top-nav__inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 16px 24px;
}

.top-nav__brand {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #191c1e;
  cursor: pointer;
  transition: opacity 200ms;
}

.top-nav__brand:hover {
  opacity: 0.7;
}

.top-nav__right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.top-nav__avatar {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  color: #64748B;
  transition: background 200ms;
}

.top-nav__avatar:hover {
  background: #f1f5f9;
}

.top-nav__avatar .material-symbols-outlined {
  font-size: 24px;
}

.cancel-btn {
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid #EF4444;
  background: transparent;
  color: #EF4444;
  cursor: pointer;
  transition: all 200ms;
}

.cancel-btn:hover:not(:disabled) {
  background: #FEF2F2;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Main Content ── */
.main-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 64px 24px;
}

/* ── Hero Section ── */
.hero-section {
  margin-bottom: 64px;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.hero-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -1px;
  color: #191c1e;
  margin: 0;
}

.hero-spinner {
  font-size: 1.875rem;
  color: #3525CD;
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── Progress Container ── */
.progress-container {
  background: #f2f4f6;
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 32px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
}

.progress-status__label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 600;
  color: #3525CD;
  display: block;
  margin-bottom: 4px;
}

.progress-status__text {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.25rem;
  font-weight: 600;
  color: #191c1e;
  margin: 0;
}

.progress-percent {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.875rem;
  font-weight: 700;
  color: #3525CD;
}

.progress-track {
  height: 12px;
  width: 100%;
  background: #e0e3e5;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4F46E5;
  border-radius: 9999px;
  transition: width 600ms cubic-bezier(0.16, 1, 0.3, 1);
}

/* ── Steps List ── */
.steps-list {
  display: flex;
  flex-direction: column;
}

.step-row {
  position: relative;
  display: flex;
  gap: 24px;
  padding-bottom: 32px;
}

.step-row--last {
  padding-bottom: 0;
}

.step-connector {
  width: 2px;
  background: #e0e3e5;
  position: absolute;
  top: 28px;
  bottom: 0;
  left: 11px;
}

.step-icon-wrap {
  position: relative;
  z-index: 10;
  background: #f7f9fb;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.step-icon {
  font-size: 24px;
}

.step-icon--completed {
  color: #16A34A;
}

.step-icon--active {
  color: #3525CD;
  animation: spin 1.5s linear infinite;
}

.step-icon--failed {
  color: #EF4444;
}

.step-icon--pending {
  color: #c7c4d8;
}

.step-info {
  flex: 1;
}

.step-name {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: #191c1e;
  margin: 0 0 2px 0;
}

.step-name--active {
  color: #3525CD;
}

.step-name--pending {
  color: #777587;
}

.step-name--failed {
  color: #EF4444;
}

.step-detail {
  font-size: 0.875rem;
  color: #464555;
  margin: 0;
}

.step-detail--pending {
  color: #777587;
}

/* ── Error Card ── */
.error-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 28px;
  animation: fadeIn 0.3s ease;
}

.error-card__icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.error-card__title {
  font-weight: 600;
  color: #EF4444;
  font-size: 0.9375rem;
  margin-bottom: 4px;
}

.error-card__message {
  font-size: 0.8125rem;
  color: #991B1B;
  line-height: 1.5;
  word-break: break-word;
}

/* ── Result Section ── */
.result-section {
  margin-top: 24px;
  margin-bottom: 32px;
  text-align: center;
  animation: fadeIn 0.4s ease;
}

.result-section__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0 0 8px 0;
}

.result-section__desc {
  color: #64748B;
  margin: 0 0 24px 0;
  font-size: 0.9375rem;
}

.action-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.action-card {
  background: #ffffff;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  text-align: left;
  transition: all 200ms;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-family: inherit;
}

.action-card:hover {
  border-color: #4F46E5;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.12);
  transform: translateY(-2px);
}

.action-card:active {
  transform: translateY(0);
}

.action-card__icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #EEF2FF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4F46E5;
}

.action-card__text strong {
  display: block;
  font-size: 0.9375rem;
  color: #191c1e;
  margin-bottom: 4px;
}

.action-card__text span {
  font-size: 0.8125rem;
  color: #64748B;
}

/* ── Retry ── */
.retry-section {
  margin-bottom: 32px;
}

.retry-btn {
  width: 100%;
  font-family: inherit;
  font-size: 0.9375rem;
  font-weight: 600;
  padding: 14px 24px;
  border-radius: 10px;
  border: 1px solid #EF4444;
  background: #ffffff;
  color: #EF4444;
  cursor: pointer;
  transition: all 200ms;
  animation: fadeIn 0.4s ease;
}

.retry-btn:hover {
  background: #FEF2F2;
}

/* ── Graph Section ── */
.graph-section {
  margin-bottom: 24px;
  background: #ffffff;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.08);
  animation: fadeIn 0.4s ease;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #E2E8F0;
}

.graph-header__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1rem;
  font-weight: 600;
  color: #191c1e;
  margin: 0;
}

.graph-header__stats {
  font-size: 0.8125rem;
  color: #64748B;
}

.graph-container {
  height: 400px;
  position: relative;
}

/* ── Visualization Placeholder ── */
.viz-placeholder {
  position: relative;
  background: #ffffff;
  border-radius: 12px;
  height: 400px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  border: 1px solid rgba(199, 196, 216, 0.2);
  margin-bottom: 48px;
}

.viz-placeholder__bg {
  position: absolute;
  inset: 0;
  opacity: 0.03;
  background-image: radial-gradient(#3525cd 1px, transparent 1px);
  background-size: 24px 24px;
}

.viz-placeholder__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.viz-bars {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  align-items: flex-end;
}

.viz-bar {
  width: 8px;
  background: #4F46E5;
  border-radius: 9999px;
}

.viz-placeholder__label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #777587;
  font-weight: 500;
  margin: 0;
}

/* ── Summary Card ── */
.summary-card {
  background: #ffffff;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.08);
  animation: fadeIn 0.4s ease;
  margin-bottom: 32px;
}

.summary-card__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #10B981;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-grid {
  display: flex;
  flex-direction: column;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #F1F5F9;
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item__label {
  font-size: 0.8125rem;
  color: #64748B;
}

.summary-item__value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #191c1e;
}

.summary-item__value--mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #64748B;
}

/* ── Footer Action ── */
.footer-action {
  display: flex;
  justify-content: center;
  margin-bottom: 48px;
}

.footer-cancel-btn {
  padding: 12px 32px;
  color: #3525CD;
  font-weight: 500;
  font-size: 0.9375rem;
  background: none;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 200ms;
  font-family: inherit;
}

.footer-cancel-btn:hover:not(:disabled) {
  background: #f2f4f6;
}

.footer-cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Page Footer ── */
.page-footer {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
  padding: 48px 24px;
}

.page-footer__links {
  display: flex;
  gap: 24px;
}

.page-footer__links a {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 500;
  color: #94A3B8;
  text-decoration: none;
  transition: color 200ms;
}

.page-footer__links a:hover {
  color: #4F46E5;
}

.page-footer__copy {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 500;
  color: #94A3B8;
  margin: 0;
}

/* ── Animations ── */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .main-content {
    padding: 36px 16px;
  }

  .hero-title {
    font-size: 1.5rem;
  }

  .progress-container {
    padding: 20px;
  }

  .progress-percent {
    font-size: 1.5rem;
  }

  .progress-status__text {
    font-size: 1rem;
  }

  .action-cards {
    grid-template-columns: 1fr;
  }

  .graph-container {
    height: 300px;
  }

  .viz-placeholder {
    height: 280px;
  }
}
</style>
