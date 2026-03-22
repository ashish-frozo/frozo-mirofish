<template>
  <div class="dashboard-page">
    <!-- Trial Expired Banner -->
    <div v-if="auth.isTrialExpired" class="trial-expired-banner">
      <span class="banner-icon">!</span>
      Trial Expired -- Upgrade to continue
      <router-link to="/pricing" class="upgrade-link">Upgrade Now</router-link>
    </div>

    <!-- Main Content Canvas -->
    <main class="main-canvas">
      <!-- Top Navigation Bar -->
      <header class="top-bar">
        <div class="top-bar-left">
          <span class="top-bar-brand">AUGUR</span>
          <div class="search-box">
            <span class="material-symbols-outlined search-icon">search</span>
            <input
              type="text"
              class="search-input"
              placeholder="Search insights..."
            />
          </div>
        </div>
        <div class="top-bar-right">
          <div
            v-if="auth.user?.plan === 'trial' && !auth.isTrialExpired"
            class="trial-indicator"
            :class="trialBadgeClass"
          >
            <span class="material-symbols-outlined trial-icon">calendar_today</span>
            <span>{{ auth.trialDaysLeft }} days left</span>
          </div>
          <button
            v-if="auth.currentPlan !== 'trial'"
            class="topbar-btn"
            @click="handleManageSubscription"
          >
            Manage Subscription
          </button>
          <button class="topbar-btn" @click="handleLogout" aria-label="Sign out">
            Sign Out
          </button>
        </div>
      </header>

      <!-- Dashboard Body -->
      <div class="dashboard-body">
        <!-- Payment Success Toast -->
        <transition name="toast">
          <div v-if="paymentSuccess" class="payment-toast" role="status">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Payment successful! Your plan is now active.
          </div>
        </transition>

        <!-- Greeting Section -->
        <div class="greeting-section">
          <h1 class="greeting-title">Welcome back, {{ auth.user?.name || 'User' }}</h1>
          <p class="greeting-subtitle">Your AI prediction workspace.</p>
        </div>

        <!-- Upgrade Banner -->
        <div
          v-if="auth.isTrialExpired || (!auth.canCreateProjects && auth.isAuthenticated)"
          class="upgrade-banner"
        >
          <h3 class="upgrade-banner__title">Your trial has expired</h3>
          <p class="upgrade-banner__desc">Upgrade to continue creating predictions.</p>
          <div class="upgrade-banner__actions">
            <button class="btn-upgrade" @click="handleUpgrade('starter')" :disabled="upgrading">
              {{ upgrading ? 'Loading...' : 'Starter -- $19/mo' }}
            </button>
            <button class="btn-upgrade" @click="handleUpgrade('pro')" :disabled="upgrading">
              {{ upgrading ? 'Loading...' : 'Pro -- $49/mo' }}
            </button>
          </div>
        </div>

        <!-- Action Grid (Bento Style) -->
        <div class="action-grid">
          <!-- New Prediction Card -->
          <button
            class="new-prediction-card"
            @click="router.push('/new')"
            @keydown.enter="router.push('/new')"
          >
            <div class="new-prediction-card__content">
              <div>
                <div class="new-prediction-card__icon">
                  <span class="material-symbols-outlined">add</span>
                </div>
                <h3 class="new-prediction-card__title">New Prediction</h3>
                <p class="new-prediction-card__desc">Upload documents and run a swarm intelligence simulation.</p>
              </div>
              <div class="new-prediction-card__cta">
                START PREDICTION
                <span class="material-symbols-outlined new-prediction-card__arrow">arrow_forward</span>
              </div>
            </div>
            <div class="new-prediction-card__glow"></div>
          </button>

          <!-- Status Summary -->
          <div class="status-summary">
            <div class="status-summary__stats">
              <div>
                <p class="stat-label">In Progress</p>
                <p class="stat-value stat-value--primary">{{ runningCount }}</p>
              </div>
              <div>
                <p class="stat-label">Total Predictions</p>
                <p class="stat-value">{{ projects.length }}</p>
              </div>
              <div>
                <p class="stat-label">Completed</p>
                <p class="stat-value">{{ completedCount }}</p>
              </div>
            </div>
            <div class="status-summary__chart">
              <div class="mini-bar" style="height: 40%;"></div>
              <div class="mini-bar" style="height: 60%;"></div>
              <div class="mini-bar" style="height: 20%;"></div>
              <div class="mini-bar" style="height: 100%;"></div>
              <div class="mini-bar" style="height: 80%;"></div>
            </div>
          </div>
        </div>

        <!-- Predictions List Header -->
        <div class="predictions-header">
          <div class="predictions-header__left">
            <h2 class="predictions-header__title">Your Predictions</h2>
            <span class="predictions-header__count">{{ String(projects.length).padStart(2, '0') }}</span>
          </div>
          <button
            class="refresh-btn"
            @click="fetchProjects"
            :disabled="loading"
            aria-label="Refresh predictions"
          >
            <span
              class="material-symbols-outlined refresh-icon"
              :class="{ spinning: loading }"
            >refresh</span>
            Refresh Data
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading && projects.length === 0" class="state-panel">
          <div class="loading-spinner"></div>
          <p class="state-text">Loading predictions...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="state-panel state-panel--error">
          <p class="state-text state-text--error">{{ error }}</p>
          <button class="btn-ghost" @click="fetchProjects">Try Again</button>
        </div>

        <!-- Empty State -->
        <div v-else-if="projects.length === 0" class="state-panel">
          <div class="empty-icon" aria-hidden="true">
            <span class="material-symbols-outlined empty-icon__symbol">inbox</span>
          </div>
          <p class="empty-title">No predictions yet</p>
          <p class="empty-desc">Start your first prediction to see it here.</p>
          <button class="btn-ghost btn-ghost--primary" @click="router.push('/new')">
            Create Your First Prediction
          </button>
        </div>

        <!-- Project Cards Grid -->
        <div v-else class="projects-grid">
          <article
            v-for="project in projects"
            :key="project.project_id"
            class="project-card"
          >
            <div class="project-card__top">
              <div>
                <div class="project-card__status">
                  <span
                    class="status-dot"
                    :class="'status-dot--' + getStatusCategory(project.status)"
                  ></span>
                  <span
                    class="status-label"
                    :class="'status-label--' + getStatusCategory(project.status)"
                  >{{ getStepInfo(project.status).label }}</span>
                </div>
                <h3 class="project-card__title">{{ project.name || project.simulation_requirement || 'Untitled Project' }}</h3>
              </div>
              <p class="project-card__date">{{ formatDate(project.created_at) }}</p>
            </div>

            <div class="project-card__progress-section">
              <div class="project-card__progress-header">
                <span class="progress-label">Inference Progress</span>
                <span
                  class="progress-value"
                  :class="'progress-value--' + getStatusCategory(project.status)"
                >{{ getStepInfo(project.status).step }} / 5 Cycles</span>
              </div>
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :class="'progress-fill--' + getStatusCategory(project.status)"
                  :style="{ width: (getStepInfo(project.status).step / 5 * 100) + '%' }"
                ></div>
              </div>
            </div>

            <div class="project-card__footer">
              <div v-if="getStatusCategory(project.status) === 'failed'" class="project-card__error-msg">
                Prediction failed
              </div>
              <div v-else class="project-card__spacer"></div>
              <div class="project-card__actions">
                <button
                  v-if="getStatusCategory(project.status) === 'failed'"
                  class="btn-card btn-card--retry"
                  @click="handleProjectAction(project)"
                >
                  Retry
                </button>
                <button
                  v-else-if="getStatusCategory(project.status) === 'completed'"
                  class="btn-card btn-card--secondary"
                  @click="handleProjectAction(project)"
                >
                  View Results
                </button>
                <button
                  v-else
                  class="btn-card btn-card--primary"
                  @click="handleProjectAction(project)"
                >
                  Resume
                </button>
                <button
                  class="btn-card btn-card--delete"
                  @click="confirmDelete(project)"
                  :disabled="deleting === project.project_id"
                >
                  {{ deleting === project.project_id ? 'Deleting...' : 'Delete' }}
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>

      <!-- Footer -->
      <footer class="dashboard-footer">
        <div class="dashboard-footer__inner">
          <p class="dashboard-footer__copy">&copy; 2026 Augur AI. All rights reserved.</p>
          <div class="dashboard-footer__links">
            <a href="mailto:mirofish@shanda.com">Contact</a>
            <a href="https://github.com/666ghj/MiroFish" target="_blank" rel="noopener">GitHub</a>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { listProjects, deleteProject } from '../api/projects'
import { createCheckout, createPortal } from '../api/billing'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const projects = ref([])
const loading = ref(false)
const error = ref(null)
const deleting = ref(null)
const upgrading = ref(false)
const paymentSuccess = ref(false)

const STATUS_MAP = {
  created:             { step: 1, label: 'Created' },
  ontology_generated:  { step: 1, label: 'Ontology Ready' },
  graph_building:      { step: 1, label: 'Building Graph' },
  graph_completed:     { step: 1, label: 'Graph Complete' },
  env_setup:           { step: 2, label: 'Setting Up' },
  simulating:          { step: 3, label: 'Simulating' },
  reporting:           { step: 4, label: 'Generating Report' },
  interacting:         { step: 5, label: 'Interactive' },
  completed:           { step: 5, label: 'Completed' },
  failed:              { step: 0, label: 'Failed' },
}

function getStepInfo(status) {
  return STATUS_MAP[status] || { step: 1, label: status || 'Unknown' }
}

function getStatusCategory(status) {
  if (status === 'failed') return 'failed'
  if (status === 'completed') return 'completed'
  if (['graph_building', 'env_setup', 'simulating', 'reporting'].includes(status)) return 'running'
  return 'created'
}

const runningCount = computed(() => {
  return projects.value.filter(p => getStatusCategory(p.status) === 'running').length
})

const completedCount = computed(() => {
  return projects.value.filter(p => getStatusCategory(p.status) === 'completed').length
})

async function fetchProjects() {
  loading.value = true
  error.value = null
  try {
    const res = await listProjects()
    projects.value = res.data || []
  } catch (err) {
    error.value = err.message || 'Failed to load projects'
  } finally {
    loading.value = false
  }
}

async function confirmDelete(project) {
  const name = project.name || project.simulation_requirement || 'this project'
  if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) return

  deleting.value = project.project_id
  try {
    await deleteProject(project.project_id)
    projects.value = projects.value.filter(p => p.project_id !== project.project_id)
  } catch (err) {
    alert('Failed to delete project: ' + (err.message || 'Unknown error'))
  } finally {
    deleting.value = null
  }
}

const trialBadgeClass = computed(() => {
  const days = auth.trialDaysLeft
  if (days === null) return ''
  if (days > 7) return 'trial-indicator--green'
  if (days >= 3) return 'trial-indicator--yellow'
  return 'trial-indicator--red'
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

function handleProjectAction(project) {
  const status = project.status
  const projectId = project.project_id
  const reportId = project.report_id
  const predictionTaskId = project.prediction_task_id

  // If project failed, offer to start over
  if (status === 'failed') {
    router.push('/new')
    return
  }

  // If there's an active prediction task and project isn't completed, go to progress view
  if (predictionTaskId && status !== 'completed' && status !== 'interacting') {
    router.push(`/predict/${predictionTaskId}`)
    return
  }

  // Completed predictions go to workspace
  if ((status === 'completed' || status === 'interacting') && projectId) {
    router.push(`/workspace/${projectId}`)
    return
  }

  // Fallback to workspace if we have a project ID
  router.push(`/workspace/${projectId}`)
}

async function handleLogout() {
  await auth.logoutAction()
  router.push('/login')
}

async function handleUpgrade(plan) {
  upgrading.value = true
  try {
    const res = await createCheckout(plan)
    const url = res?.checkout_url || res?.data?.checkout_url
    if (url) {
      window.location.href = url
    }
  } catch (e) {
    console.error('Checkout failed:', e)
    alert('Failed to start checkout. Please try again.')
  } finally {
    upgrading.value = false
  }
}

async function handleManageSubscription() {
  try {
    const res = await createPortal()
    const url = res?.portal_url || res?.data?.portal_url
    if (url) {
      window.location.href = url
    }
  } catch (e) {
    console.error('Portal failed:', e)
  }
}

onMounted(async () => {
  if (route.query.payment === 'success') {
    paymentSuccess.value = true
    await auth.fetchUser()
    router.replace({ path: '/dashboard' })
    setTimeout(() => { paymentSuccess.value = false }, 5000)
  }
  fetchProjects()
})
</script>

<style scoped>
/* ── Base ── */
.dashboard-page {
  min-height: 100vh;
  background: #f7f9fb;
  font-family: 'Inter', system-ui, sans-serif;
  color: #191c1e;
}

/* ── Sidebar ── */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 256px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  padding: 32px 16px;
  z-index: 40;
  border-right: 1px solid #f1f5f9;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  margin-bottom: 40px;
}

.sidebar-brand-icon {
  color: #4F46E5;
  font-size: 24px;
}

.sidebar-brand-name {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #4338CA;
  margin: 0;
  line-height: 1.2;
}

.sidebar-brand-tagline {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 700;
  color: #94A3B8;
  margin: 2px 0 0 0;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #64748B;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 200ms ease;
}

.sidebar-link:hover {
  color: #4F46E5;
  background: #EEF2FF;
}

.sidebar-link--active {
  color: #4338CA;
  font-weight: 700;
  background: #EEF2FF;
  border-right: 4px solid #4F46E5;
}

.sidebar-link .material-symbols-outlined {
  font-size: 20px;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
}

.sidebar-user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #E2DFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3525CD;
  font-weight: 700;
  font-size: 0.875rem;
}

.sidebar-user-info {
  overflow: hidden;
}

.sidebar-user-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #191c1e;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-user-plan {
  font-size: 0.75rem;
  color: #64748B;
  margin: 0;
}

/* ── Trial Expired Banner ── */
.trial-expired-banner {
  position: fixed;
  top: 0;
  left: 256px;
  right: 0;
  background: #FEF2F2;
  border-bottom: 1px solid #FECACA;
  color: #DC2626;
  padding: 10px 40px;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  z-index: 50;
}

.banner-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FEE2E2;
  font-size: 0.7rem;
  font-weight: 700;
  color: #DC2626;
}

.upgrade-link {
  color: #DC2626;
  text-decoration: underline;
  font-weight: 600;
}

/* ── Main Canvas ── */
.main-canvas {
  margin-left: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  flex: 1;
}

/* ── Top Bar ── */
.top-bar {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.top-bar-brand {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 800;
  font-size: 1.1rem;
  color: #4F46E5;
  letter-spacing: 1.5px;
}

.search-box {
  display: flex;
  align-items: center;
  background: #f1f5f9;
  border-radius: 8px;
  padding: 6px 12px;
  gap: 8px;
}

.search-icon {
  color: #94A3B8;
  font-size: 18px;
}

.search-input {
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.875rem;
  width: 256px;
  color: #191c1e;
  font-family: inherit;
}

.search-input::placeholder {
  color: #94A3B8;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.trial-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #4338CA;
}

.trial-icon {
  font-size: 18px;
}

.trial-indicator--green { color: #059669; }
.trial-indicator--yellow { color: #D97706; }
.trial-indicator--red { color: #DC2626; }

.topbar-btn {
  color: #64748B;
  font-weight: 500;
  background: none;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  font-family: inherit;
  transition: background 200ms, color 200ms;
}

.topbar-btn:hover {
  background: #f1f5f9;
  color: #191c1e;
}

/* ── Dashboard Body ── */
.dashboard-body {
  padding: 40px;
  max-width: 1120px;
  width: 100%;
  margin: 0 auto;
  flex: 1;
}

/* ── Payment Toast ── */
.payment-toast {
  background: #10B981;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  text-align: center;
  font-weight: 500;
  font-size: 0.9375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 400ms, transform 400ms;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── Greeting ── */
.greeting-section {
  margin-bottom: 48px;
}

.greeting-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 3rem;
  font-weight: 800;
  color: #191c1e;
  letter-spacing: -1px;
  margin: 0 0 8px 0;
  line-height: 1.1;
}

.greeting-subtitle {
  color: #64748B;
  font-size: 1.125rem;
  margin: 0;
}

/* ── Upgrade Banner ── */
.upgrade-banner {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 28px;
  text-align: center;
}

.upgrade-banner__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: #991B1B;
  margin: 0 0 6px 0;
}

.upgrade-banner__desc {
  color: #B91C1C;
  font-size: 0.9375rem;
  margin: 0 0 16px 0;
}

.upgrade-banner__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-upgrade {
  background: #4F46E5;
  color: white;
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9375rem;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: background 200ms;
}

.btn-upgrade:hover { background: #4338CA; }
.btn-upgrade:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Action Grid ── */
.action-grid {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 24px;
  margin-bottom: 48px;
}

/* New Prediction Card */
.new-prediction-card {
  position: relative;
  overflow: hidden;
  background: #ffffff;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.04);
  border: none;
  border-left: 6px solid #4F46E5;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: transform 200ms;
}

.new-prediction-card:hover {
  transform: scale(1.01);
}

.new-prediction-card:active {
  opacity: 0.8;
}

.new-prediction-card__content {
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.new-prediction-card__icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #EEF2FF;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4F46E5;
  margin-bottom: 24px;
  transition: background 200ms, color 200ms;
}

.new-prediction-card:hover .new-prediction-card__icon {
  background: #4F46E5;
  color: #ffffff;
}

.new-prediction-card__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0 0 8px 0;
}

.new-prediction-card__desc {
  color: #64748B;
  line-height: 1.6;
  margin: 0;
  font-size: 0.9375rem;
}

.new-prediction-card__cta {
  margin-top: 32px;
  display: flex;
  align-items: center;
  color: #4F46E5;
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: 0.5px;
}

.new-prediction-card__arrow {
  font-size: 14px;
  margin-left: 8px;
}

.new-prediction-card__glow {
  position: absolute;
  right: -16px;
  bottom: -16px;
  width: 128px;
  height: 128px;
  background: rgba(238, 242, 255, 0.5);
  border-radius: 50%;
  filter: blur(48px);
  transition: background 200ms;
}

.new-prediction-card:hover .new-prediction-card__glow {
  background: rgba(238, 242, 255, 0.8);
}

/* Status Summary */
.status-summary {
  background: #f2f4f6;
  border-radius: 12px;
  padding: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-summary__stats {
  display: flex;
  gap: 48px;
}

.stat-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 700;
  color: #94A3B8;
  margin: 0 0 8px 0;
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0;
}

.stat-value--primary {
  color: #4338CA;
}

.status-summary__chart {
  height: 64px;
  width: 128px;
  background: rgba(238, 242, 255, 0.5);
  border-radius: 8px;
  display: flex;
  align-items: flex-end;
  padding: 8px;
  gap: 4px;
  overflow: hidden;
}

.mini-bar {
  background: #4F46E5;
  width: 100%;
  border-radius: 2px 2px 0 0;
  opacity: 0.6;
}

.mini-bar:nth-child(3) { opacity: 0.3; }
.mini-bar:nth-child(4) { opacity: 1; }
.mini-bar:nth-child(5) { opacity: 0.8; }

/* ── Predictions Header ── */
.predictions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.predictions-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.predictions-header__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #191c1e;
  letter-spacing: -0.5px;
  margin: 0;
}

.predictions-header__count {
  background: rgba(226, 232, 240, 0.5);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #64748B;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: inherit;
  transition: color 200ms, background 200ms;
}

.refresh-btn:hover:not(:disabled) {
  color: #4F46E5;
  background: #ffffff;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-icon {
  font-size: 18px;
  transition: transform 300ms;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── State Panels ── */
.state-panel {
  background: #ffffff;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  padding: 64px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.04);
}

.state-panel--error {
  border-color: #FECACA;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #E2E8F0;
  border-top-color: #4F46E5;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

.state-text {
  font-size: 0.9375rem;
  color: #64748B;
  margin: 0;
}

.state-text--error {
  color: #DC2626;
  margin-bottom: 20px;
}

.empty-icon {
  margin-bottom: 20px;
}

.empty-icon__symbol {
  font-size: 48px;
  color: #CBD5E1;
}

.empty-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: #191c1e;
  margin: 0 0 6px 0;
}

.empty-desc {
  font-size: 0.9375rem;
  color: #64748B;
  margin: 0 0 24px 0;
}

.btn-ghost {
  background: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 0.9375rem;
  color: #191c1e;
  cursor: pointer;
  transition: background 200ms, border-color 200ms;
  font-family: inherit;
  font-weight: 500;
}

.btn-ghost:hover {
  background: #f7f9fb;
  border-color: #CBD5E1;
}

.btn-ghost--primary {
  border-color: #4F46E5;
  color: #4F46E5;
}

.btn-ghost--primary:hover {
  background: #EEF2FF;
}

/* ── Projects Grid ── */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* ── Project Card ── */
.project-card {
  background: #ffffff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.04);
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: transform 200ms;
}

.project-card:hover {
  transform: translateY(-4px);
}

.project-card__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.project-card__status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot--created { background: #94A3B8; }
.status-dot--running { background: #4F46E5; }
.status-dot--completed { background: #10B981; }
.status-dot--failed { background: #EF4444; }

.status-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 700;
}

.status-label--created { color: #94A3B8; }
.status-label--running { color: #4F46E5; }
.status-label--completed { color: #059669; }
.status-label--failed { color: #DC2626; }

.project-card__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-card__date {
  font-size: 0.75rem;
  color: #94A3B8;
  font-weight: 500;
  white-space: nowrap;
  margin: 0;
}

/* Progress Section */
.project-card__progress-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.project-card__progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #94A3B8;
}

.progress-value {
  font-size: 0.75rem;
  font-weight: 700;
}

.progress-value--created { color: #94A3B8; }
.progress-value--running { color: #4F46E5; }
.progress-value--completed { color: #059669; }
.progress-value--failed { color: #DC2626; }

.progress-track {
  width: 100%;
  height: 6px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 600ms cubic-bezier(0.16, 1, 0.3, 1);
}

.progress-fill--created { background: #94A3B8; }
.progress-fill--running { background: #4F46E5; }
.progress-fill--completed { background: #10B981; }
.progress-fill--failed { background: #EF4444; }

/* Card Footer */
.project-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.project-card__error-msg {
  font-size: 0.75rem;
  color: #EF4444;
  font-style: italic;
}

.project-card__spacer {
  flex: 1;
}

.project-card__actions {
  display: flex;
  gap: 8px;
}

.btn-card {
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 8px;
  cursor: pointer;
  border: none;
  transition: opacity 200ms, background 200ms;
}

.btn-card--primary {
  background: #4F46E5;
  color: #ffffff;
}

.btn-card--primary:hover {
  opacity: 0.9;
}

.btn-card--secondary {
  background: #f1f5f9;
  color: #475569;
}

.btn-card--secondary:hover {
  background: #E2E8F0;
}

.btn-card--retry {
  background: #FEF2F2;
  color: #DC2626;
}

.btn-card--retry:hover {
  background: #FEE2E2;
}

.btn-card--delete {
  background: transparent;
  color: #94A3B8;
  padding: 10px 12px;
  font-weight: 500;
}

.btn-card--delete:hover:not(:disabled) {
  color: #DC2626;
  background: #FEF2F2;
}

.btn-card--delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Footer ── */
.dashboard-footer {
  width: 100%;
  margin-top: auto;
  padding: 32px;
  background: #f8fafc;
  border-top: 1px solid rgba(226, 232, 240, 0.2);
}

.dashboard-footer__inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1120px;
  margin: 0 auto;
}

.dashboard-footer__copy {
  color: #94A3B8;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 600;
  margin: 0;
}

.dashboard-footer__links {
  display: flex;
  gap: 32px;
}

.dashboard-footer__links a {
  color: #94A3B8;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: 600;
  text-decoration: none;
  transition: color 200ms;
}

.dashboard-footer__links a:hover {
  color: #4F46E5;
  text-decoration: underline;
  text-underline-offset: 4px;
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .sidebar {
    display: none;
  }

  .main-canvas {
    margin-left: 0;
  }

  .trial-expired-banner {
    left: 0;
  }

  .action-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-body {
    padding: 24px 16px;
  }

  .greeting-title {
    font-size: 2rem;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }

  .top-bar {
    padding: 12px 16px;
    flex-wrap: wrap;
    gap: 12px;
  }

  .search-input {
    width: 160px;
  }

  .status-summary__stats {
    gap: 24px;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .status-summary__chart {
    display: none;
  }

  .dashboard-footer__inner {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }

  .upgrade-banner__actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>
