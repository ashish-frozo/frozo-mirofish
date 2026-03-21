<template>
  <div class="prediction-container">
    <!-- Header -->
    <nav class="prediction-nav">
      <div class="nav-brand" @click="$router.push('/dashboard')">AUGUR</div>
      <div class="nav-status">
        <span class="status-badge" :class="statusClass">{{ statusLabel }}</span>
      </div>
    </nav>

    <div class="prediction-content">
      <!-- Title -->
      <div class="prediction-header">
        <h1 class="prediction-title">Prediction Pipeline</h1>
        <p class="prediction-subtitle">Orchestrating all 5 steps automatically</p>
      </div>

      <!-- Overall Progress Bar -->
      <div class="progress-section">
        <div class="progress-label">
          <span class="progress-text">Overall Progress</span>
          <span class="progress-percent">{{ data.progress || 0 }}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: (data.progress || 0) + '%' }"></div>
        </div>
        <div class="progress-message" v-if="data.message">{{ data.message }}</div>
      </div>

      <!-- Step Checklist -->
      <div class="steps-checklist">
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
            <span v-if="step.status === 'completed'" class="step-check">&#10003;</span>
            <span v-else-if="step.status === 'active'" class="step-spinner"></span>
            <span v-else class="step-circle"></span>
          </div>
          <div class="step-details">
            <div class="step-name">
              <span class="step-number">{{ String(index + 1).padStart(2, '0') }}</span>
              {{ step.label }}
            </div>
            <div class="step-desc">{{ step.description }}</div>
            <div class="step-stats" v-if="step.stats">{{ step.stats }}</div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div class="error-section" v-if="data.status === 'failed' && data.error">
        <div class="error-title">Pipeline Failed</div>
        <div class="error-message">{{ data.error }}</div>
      </div>

      <!-- Action Buttons -->
      <div class="action-section">
        <button
          v-if="data.status === 'running'"
          class="cancel-btn"
          @click="handleCancel"
          :disabled="cancelling"
        >
          {{ cancelling ? 'Cancelling...' : 'Cancel Prediction' }}
        </button>

        <button
          v-if="data.status === 'completed' && data.result"
          class="explore-btn"
          @click="handleExplore"
        >
          Explore Results
          <span class="btn-arrow">&#8594;</span>
        </button>

        <button
          v-if="data.status === 'failed'"
          class="retry-btn"
          @click="$router.push('/new')"
        >
          Try Again
        </button>
      </div>

      <!-- Completion Summary -->
      <div class="summary-section" v-if="data.status === 'completed' && data.result">
        <div class="summary-title">Prediction Complete</div>
        <div class="summary-grid">
          <div class="summary-item" v-if="data.result.graph_id">
            <div class="summary-label">Graph ID</div>
            <div class="summary-value mono">{{ data.result.graph_id }}</div>
          </div>
          <div class="summary-item" v-if="data.result.simulation_id">
            <div class="summary-label">Simulation ID</div>
            <div class="summary-value mono">{{ data.result.simulation_id }}</div>
          </div>
          <div class="summary-item" v-if="graphStats">
            <div class="summary-label">Knowledge Graph</div>
            <div class="summary-value">{{ graphStats }}</div>
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

const props = defineProps({
  taskId: { type: String, required: true }
})

const router = useRouter()
const cancelling = ref(false)
let pollTimer = null

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
  { key: 'ontology',    label: 'Ontology Extraction',  description: 'Analyzing documents and generating entity/relationship types' },
  { key: 'graph_build', label: 'Knowledge Graph',      description: 'Building Zep knowledge graph from extracted ontology' },
  { key: 'env_setup',   label: 'Environment Setup',    description: 'Generating agent profiles and simulation configuration' },
  { key: 'simulation',  label: 'Run Simulation',       description: 'Executing dual-platform parallel simulation' },
  { key: 'report',      label: 'Report Generation',    description: 'ReACT agent generating prediction insights' },
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
      // Build stats string
      if (def_.key === 'graph_build' && stageData.stats) {
        stats = `${stageData.stats.nodes} nodes, ${stageData.stats.edges} edges`
      }
    } else if (def_.key === currentStage) {
      status = 'active'
      reachedCurrent = true
    } else if (!reachedCurrent && data.status === 'running') {
      // Steps before current that aren't marked completed are still pending
    }

    // Special case: interaction ready
    if (def_.key === 'report' && data.stages.interaction?.status === 'ready') {
      status = 'completed'
    }

    return { ...def_, status, stats }
  })
})

const statusClass = computed(() => {
  if (data.status === 'completed') return 'status-completed'
  if (data.status === 'failed') return 'status-failed'
  return 'status-running'
})

const statusLabel = computed(() => {
  if (data.status === 'completed') return 'COMPLETED'
  if (data.status === 'failed') return 'FAILED'
  if (data.status === 'running') return 'RUNNING'
  return 'PENDING'
})

const graphStats = computed(() => {
  const gs = data.stages?.graph_build?.stats
  if (!gs) return null
  return `${gs.nodes} nodes, ${gs.edges} edges`
})

async function poll() {
  try {
    const res = await getPredictionStatus(props.taskId)
    const d = res.data
    Object.assign(data, d)

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

function handleExplore() {
  const result = data.result
  if (result?.report_id) {
    router.push({ name: 'Report', params: { reportId: result.report_id } })
  } else if (result?.project_id) {
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
/* Variables */
:root {
  --bg-primary: #0a0a1a;
  --bg-secondary: #111128;
  --bg-card: #161632;
  --text-primary: #e8e8f0;
  --text-secondary: #8888aa;
  --text-muted: #555570;
  --accent: #FF4500;
  --accent-glow: rgba(255, 69, 0, 0.3);
  --success: #22c55e;
  --error: #ef4444;
  --border: #222244;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', system-ui, sans-serif;
}

.prediction-container {
  min-height: 100vh;
  background: #0a0a1a;
  color: #e8e8f0;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

/* Navigation */
.prediction-nav {
  height: 60px;
  background: #08081a;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  border-bottom: 1px solid #222244;
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  letter-spacing: 1px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.status-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 4px 12px;
  border-radius: 3px;
}

.status-running {
  background: rgba(255, 69, 0, 0.15);
  color: #FF4500;
  border: 1px solid rgba(255, 69, 0, 0.3);
  animation: pulse-status 2s ease-in-out infinite;
}

.status-completed {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.status-failed {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

@keyframes pulse-status {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Content */
.prediction-content {
  max-width: 700px;
  margin: 0 auto;
  padding: 60px 24px;
}

.prediction-header {
  margin-bottom: 48px;
}

.prediction-title {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.prediction-subtitle {
  font-size: 0.95rem;
  color: #8888aa;
  margin: 0;
}

/* Progress Bar */
.progress-section {
  margin-bottom: 48px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.progress-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #8888aa;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.progress-percent {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  color: #FF4500;
}

.progress-track {
  height: 4px;
  background: #222244;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #FF4500, #ff6b35);
  border-radius: 2px;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 0 12px rgba(255, 69, 0, 0.4);
}

.progress-message {
  margin-top: 10px;
  font-size: 0.85rem;
  color: #8888aa;
  font-family: 'JetBrains Mono', monospace;
}

/* Steps Checklist */
.steps-checklist {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 48px;
}

.step-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 20px;
  border-radius: 6px;
  background: transparent;
  transition: background 0.3s;
}

.step-row.step-active {
  background: #161632;
  border: 1px solid #222244;
}

.step-row.step-completed {
  opacity: 0.85;
}

.step-row.step-pending {
  opacity: 0.4;
}

.step-row.step-failed {
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

/* Indicators */
.step-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.step-check {
  color: #22c55e;
  font-size: 1rem;
  font-weight: 700;
}

.step-circle {
  width: 10px;
  height: 10px;
  border: 2px solid #555570;
  border-radius: 50%;
}

.step-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #222244;
  border-top-color: #FF4500;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Step Details */
.step-details {
  flex: 1;
}

.step-name {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.step-number {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #555570;
  margin-right: 10px;
}

.step-desc {
  font-size: 0.8rem;
  color: #8888aa;
  line-height: 1.5;
}

.step-stats {
  margin-top: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #22c55e;
}

/* Error Section */
.error-section {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  padding: 20px;
  margin-bottom: 32px;
}

.error-title {
  font-weight: 700;
  color: #ef4444;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.error-message {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #ff8888;
  line-height: 1.5;
  word-break: break-word;
}

/* Action Buttons */
.action-section {
  display: flex;
  gap: 16px;
  margin-bottom: 48px;
}

.cancel-btn,
.explore-btn,
.retry-btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 14px 28px;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 10px;
}

.cancel-btn {
  background: transparent;
  color: #8888aa;
  border: 1px solid #333355;
}

.cancel-btn:hover:not(:disabled) {
  border-color: #ef4444;
  color: #ef4444;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.explore-btn {
  background: #FF4500;
  color: #fff;
  flex: 1;
  justify-content: center;
}

.explore-btn:hover {
  background: #e63e00;
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(255, 69, 0, 0.3);
}

.btn-arrow {
  font-size: 1.1rem;
}

.retry-btn {
  background: #222244;
  color: #e8e8f0;
  border: 1px solid #333355;
}

.retry-btn:hover {
  border-color: #FF4500;
  color: #FF4500;
}

/* Summary Section */
.summary-section {
  background: #161632;
  border: 1px solid #222244;
  border-radius: 6px;
  padding: 24px;
}

.summary-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #22c55e;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: 'JetBrains Mono', monospace;
}

.summary-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #222244;
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-label {
  font-size: 0.8rem;
  color: #8888aa;
}

.summary-value {
  font-size: 0.85rem;
  font-weight: 600;
}

.summary-value.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #8888aa;
}

/* Responsive */
@media (max-width: 768px) {
  .prediction-content {
    padding: 40px 16px;
  }

  .prediction-title {
    font-size: 1.6rem;
  }

  .prediction-nav {
    padding: 0 20px;
  }
}
</style>
