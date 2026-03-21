<template>
  <div class="prediction-container">
    <!-- Header -->
    <nav class="prediction-nav">
      <div class="nav-brand" @click="$router.push('/dashboard')">AUGUR</div>
      <button
        v-if="data.status === 'running'"
        class="cancel-btn"
        @click="handleCancel"
        :disabled="cancelling"
      >
        {{ cancelling ? 'Cancelling...' : 'Cancel' }}
      </button>
    </nav>

    <div class="prediction-content">
      <!-- Title + Progress -->
      <div class="prediction-header">
        <h1 class="prediction-title">Building Your Prediction</h1>
        <div class="progress-section">
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{ width: (data.progress || 0) + '%' }"
            ></div>
          </div>
          <span class="progress-percent">{{ data.progress || 0 }}%</span>
        </div>
      </div>

      <!-- Step Checklist Card -->
      <div class="steps-card">
        <div
          v-for="(step, index) in steps"
          :key="step.key"
          class="step-row"
          :class="{
            'step-completed': step.status === 'completed',
            'step-active': step.status === 'active',
            'step-pending': step.status === 'pending',
            'step-failed': data.status === 'failed' && step.status === 'active'
          }"
        >
          <div class="step-indicator">
            <span v-if="step.status === 'completed'" class="step-check">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="8" fill="#10B981"/>
                <path d="M5 8l2 2 4-4" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
            <span v-else-if="step.status === 'active' && data.status !== 'failed'" class="step-spinner"></span>
            <span v-else-if="data.status === 'failed' && step.status === 'active'" class="step-error-icon">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="8" fill="#EF4444"/>
                <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </span>
            <span v-else class="step-circle"></span>
          </div>
          <div class="step-info">
            <span class="step-name">{{ step.label }}</span>
            <span class="step-stats" v-if="step.status === 'completed' && step.stats">{{ step.stats }}</span>
            <span class="step-stats" v-else-if="step.status === 'active' && data.message">{{ data.message }}</span>
            <span class="step-stats step-waiting" v-else-if="step.status === 'pending'">Waiting...</span>
          </div>
        </div>
      </div>

      <!-- Current Status Message -->
      <p class="current-status" v-if="data.status === 'running' && data.message">
        Current: {{ data.message }}
      </p>

      <!-- Error Card -->
      <div class="error-card" v-if="data.status === 'failed' && data.error">
        <div class="error-icon">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="10" fill="#FEE2E2"/>
            <path d="M10 6v4M10 13h.01" stroke="#EF4444" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="error-body">
          <div class="error-title">Prediction Failed</div>
          <div class="error-message">{{ data.error }}</div>
        </div>
      </div>

      <!-- Result Action Cards -->
      <div v-if="data.status === 'completed' && data.result" class="result-actions">
        <h3>Prediction Complete!</h3>
        <p>Your prediction is ready. Explore the results:</p>

        <div class="action-cards">
          <button class="action-card" @click="goToReport">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect x="3" y="2" width="14" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/>
                <path d="M7 7h6M7 10h6M7 13h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="action-text">
              <strong>View Report</strong>
              <span>Read the full prediction analysis</span>
            </div>
          </button>

          <button class="action-card" @click="goToInteraction">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M4 4h12a1 1 0 011 1v8a1 1 0 01-1 1H7l-3 3V5a1 1 0 011-1z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="7.5" cy="9" r="0.75" fill="currentColor"/>
                <circle cx="10" cy="9" r="0.75" fill="currentColor"/>
                <circle cx="12.5" cy="9" r="0.75" fill="currentColor"/>
              </svg>
            </div>
            <div class="action-text">
              <strong>Chat with Agents</strong>
              <span>Interview simulated agents</span>
            </div>
          </button>

          <button class="action-card" @click="goToProject">
            <div class="action-icon">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="5" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="5" cy="15" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                <circle cx="15" cy="15" r="2.5" stroke="currentColor" stroke-width="1.5"/>
                <path d="M8.5 7l-2 5.5M11.5 7l2 5.5M7.5 15h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="action-text">
              <strong>Full Workspace</strong>
              <span>Graph, simulation details, and more</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Retry Button -->
      <div class="action-section" v-if="data.status === 'failed'">
        <button
          class="retry-btn"
          @click="$router.push('/new')"
        >
          Retry
        </button>
      </div>

      <!-- Live Graph Visualization -->
      <div v-if="showGraph && graphData" class="graph-section">
        <div class="graph-header">
          <h3>Knowledge Graph</h3>
          <span class="graph-stats" v-if="graphData.node_count !== undefined">
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

      <!-- Completion Summary -->
      <div class="summary-card" v-if="data.status === 'completed' && data.result">
        <div class="summary-title">Prediction Complete</div>
        <div class="summary-grid">
          <div class="summary-item" v-if="data.result.graph_id">
            <span class="summary-label">Graph ID</span>
            <span class="summary-value mono">{{ data.result.graph_id }}</span>
          </div>
          <div class="summary-item" v-if="data.result.simulation_id">
            <span class="summary-label">Simulation ID</span>
            <span class="summary-value mono">{{ data.result.simulation_id }}</span>
          </div>
          <div class="summary-item" v-if="graphStats">
            <span class="summary-label">Knowledge Graph</span>
            <span class="summary-value">{{ graphStats }}</span>
          </div>
        </div>
      </div>
    </div>
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
      // Show in-progress stats for active steps
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

    // Extract graph_id from result or stage stats
    const result = d.result || {}
    const stages = d.stages || {}
    const gid = result.graph_id || stages.graph_build?.stats?.graph_id

    if (gid && gid !== graphId.value) {
      graphId.value = gid
      showGraph.value = true
    }

    // Refresh graph data every poll if we have a graph_id
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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

.prediction-container {
  min-height: 100vh;
  background: #F8FAFC;
  color: #0F172A;
  font-family: 'Inter', system-ui, sans-serif;
}

/* Navigation */
.prediction-nav {
  height: 56px;
  background: #FFFFFF;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  border-bottom: 1px solid #E2E8F0;
  box-shadow: 0 1px 2px rgba(79, 70, 229, 0.04);
}

.nav-brand {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-weight: 700;
  letter-spacing: 1.5px;
  font-size: 0.95rem;
  color: #4F46E5;
  cursor: pointer;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.75;
}

.cancel-btn {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid #EF4444;
  background: transparent;
  color: #EF4444;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover:not(:disabled) {
  background: #FEF2F2;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Content */
.prediction-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 56px 24px 80px;
}

/* Header */
.prediction-header {
  margin-bottom: 40px;
}

.prediction-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 28px;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 20px 0;
  letter-spacing: -0.3px;
}

/* Progress Bar */
.progress-section {
  display: flex;
  align-items: center;
  gap: 14px;
}

.progress-track {
  flex: 1;
  height: 8px;
  background: #E2E8F0;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4F46E5, #7C3AED);
  border-radius: 9999px;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.progress-percent {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: #4F46E5;
  min-width: 36px;
  text-align: right;
}

/* Steps Card */
.steps-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 8px 0;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.08);
}

.step-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  transition: background 0.25s ease, opacity 0.3s ease;
}

.step-row + .step-row {
  border-top: 1px solid #F1F5F9;
}

.step-row.step-active {
  background: #F5F3FF;
}

.step-row.step-completed {
  /* full opacity, normal */
}

.step-row.step-pending {
  opacity: 0.55;
}

.step-row.step-failed {
  background: #FEF2F2;
}

/* Step Indicator */
.step-indicator {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-check svg,
.step-error-icon svg {
  display: block;
}

.step-circle {
  width: 12px;
  height: 12px;
  border: 2px solid #CBD5E1;
  border-radius: 50%;
}

.step-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #E2E8F0;
  border-top-color: #4F46E5;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Step Info */
.step-info {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.step-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: #0F172A;
  white-space: nowrap;
}

.step-stats {
  font-size: 0.8rem;
  color: #64748B;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-waiting {
  color: #94A3B8;
}

/* Current Status */
.current-status {
  font-size: 14px;
  color: #64748B;
  margin: 0 0 32px 0;
  font-family: 'Inter', system-ui, sans-serif;
}

/* Error Card */
.error-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 28px;
  animation: fadeIn 0.3s ease;
}

.error-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.error-title {
  font-weight: 600;
  color: #EF4444;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.error-message {
  font-size: 0.8rem;
  color: #991B1B;
  line-height: 1.5;
  word-break: break-word;
}

/* Result Action Cards */
.result-actions {
  margin-top: 24px;
  margin-bottom: 32px;
  text-align: center;
  animation: fadeIn 0.4s ease;
}

.result-actions h3 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--text, #0F172A);
  margin: 0 0 8px 0;
}

.result-actions p {
  color: var(--muted, #64748B);
  margin: 0 0 24px 0;
  font-size: 15px;
}

.action-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.action-card {
  background: var(--surface, #FFFFFF);
  border: 1px solid var(--border, #E2E8F0);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
  font-family: 'Inter', system-ui, sans-serif;
}

.action-card:hover {
  border-color: var(--primary, #4F46E5);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.12);
  transform: translateY(-2px);
}

.action-card:active {
  transform: translateY(0);
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #EEF2FF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon svg {
  width: 20px;
  height: 20px;
  color: var(--primary, #4F46E5);
}

.action-text strong {
  display: block;
  font-size: 15px;
  color: var(--text, #0F172A);
  margin-bottom: 4px;
}

.action-text span {
  font-size: 13px;
  color: var(--muted, #64748B);
}

/* Action Buttons */
.action-section {
  margin-bottom: 32px;
}

.retry-btn {
  width: 100%;
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 14px 24px;
  border-radius: 10px;
  border: 1px solid #EF4444;
  background: #FFFFFF;
  color: #EF4444;
  cursor: pointer;
  transition: all 0.2s;
  animation: fadeIn 0.4s ease;
}

.retry-btn:hover {
  background: #FEF2F2;
}

/* Summary Card */
.summary-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.08);
  animation: fadeIn 0.4s ease;
}

.summary-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: #10B981;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.summary-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
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

.summary-label {
  font-size: 0.8rem;
  color: #64748B;
}

.summary-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #0F172A;
}

.summary-value.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #64748B;
}

/* Animations */
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

/* Graph Section */
.graph-section {
  margin-bottom: 24px;
  background: #FFFFFF;
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

.graph-header h3 {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 16px;
  font-weight: 600;
  color: #0F172A;
  margin: 0;
}

.graph-stats {
  font-size: 13px;
  color: #64748B;
}

.graph-container {
  height: 400px;
  position: relative;
}

/* Responsive */
@media (max-width: 768px) {
  .prediction-content {
    padding: 36px 16px 60px;
  }

  .prediction-title {
    font-size: 24px;
  }

  .prediction-nav {
    padding: 0 16px;
  }

  .step-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }

  .step-stats {
    text-align: left;
  }

  .graph-container {
    height: 300px;
  }

  .action-cards {
    grid-template-columns: 1fr;
  }
}
</style>
