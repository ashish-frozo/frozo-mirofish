<template>
  <div class="dashboard-page">
    <!-- Trial Expired Banner -->
    <div v-if="auth.isTrialExpired" class="trial-expired-banner">
      <span class="banner-icon">!</span>
      Trial Expired -- Upgrade to continue
      <router-link to="/pricing" class="upgrade-link">Upgrade Now</router-link>
    </div>

    <!-- Navigation Bar -->
    <nav class="dashboard-nav">
      <div class="nav-brand">AUGUR</div>
      <div class="nav-right">
        <span
          v-if="auth.user?.plan === 'trial' && !auth.isTrialExpired"
          class="trial-badge"
          :class="trialBadgeClass"
        >
          Trial: {{ auth.trialDaysLeft }} days left
        </span>
        <span v-if="auth.currentPlan === 'starter'" class="plan-badge plan-badge--starter">Starter Plan</span>
        <span v-else-if="auth.currentPlan === 'pro'" class="plan-badge plan-badge--pro">Pro Plan</span>
        <button
          v-if="auth.currentPlan !== 'trial'"
          class="nav-btn"
          @click="handleManageSubscription"
        >
          Manage Subscription
        </button>
        <button class="nav-btn nav-btn--logout" @click="handleLogout" aria-label="Sign out">
          Sign Out
        </button>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="dashboard-main">
      <!-- Payment Success Toast -->
      <transition name="toast">
        <div v-if="paymentSuccess" class="payment-toast" role="status">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Payment successful! Your plan is now active.
        </div>
      </transition>

      <!-- Greeting -->
      <h1 class="greeting">Welcome back, {{ auth.user?.name || 'User' }}</h1>

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

      <!-- New Prediction CTA Card -->
      <section class="cta-card" @click="router.push('/new')" role="button" tabindex="0" @keydown.enter="router.push('/new')">
        <div class="cta-card__left">
          <span class="cta-card__plus">+</span>
          <div>
            <div class="cta-card__title">New Prediction</div>
            <div class="cta-card__desc">Upload documents and predict the future</div>
          </div>
        </div>
        <svg class="cta-card__arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <line x1="5" y1="12" x2="19" y2="12"/>
          <polyline points="12 5 19 12 12 19"/>
        </svg>
      </section>

      <!-- Projects Section -->
      <section class="projects-section">
        <div class="section-header">
          <h2 class="section-title">Your Predictions</h2>
          <button class="refresh-btn" @click="fetchProjects" :disabled="loading" aria-label="Refresh predictions">
            <svg
              class="refresh-icon"
              :class="{ spinning: loading }"
              width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              aria-hidden="true"
            >
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Refresh
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
            <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
              <rect x="8" y="12" width="40" height="32" rx="6" stroke="var(--border-hover)" stroke-width="2" fill="none"/>
              <path d="M8 22h40" stroke="var(--border-hover)" stroke-width="2"/>
              <circle cx="15" cy="17" r="1.5" fill="var(--muted)"/>
              <circle cx="20" cy="17" r="1.5" fill="var(--muted)"/>
              <circle cx="25" cy="17" r="1.5" fill="var(--muted)"/>
              <path d="M22 33h12M25 29h6" stroke="var(--border-hover)" stroke-width="2" stroke-linecap="round"/>
            </svg>
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
            <div class="project-card__header">
              <span class="status-badge" :class="'status-badge--' + getStatusCategory(project.status)">
                <span class="status-badge__dot"></span>
                {{ getStepInfo(project.status).label }}
              </span>
            </div>

            <h3 class="project-card__title">{{ project.name || project.simulation_requirement || 'Untitled Project' }}</h3>

            <div class="project-card__meta">
              <span class="project-card__step">Step {{ getStepInfo(project.status).step }}/5</span>
              <span class="project-card__date">{{ formatDate(project.created_at) }}</span>
            </div>

            <!-- Progress bar -->
            <div class="progress-bar">
              <div
                class="progress-bar__fill"
                :class="'progress-bar__fill--' + getStatusCategory(project.status)"
                :style="{ width: (getStepInfo(project.status).step / 5 * 100) + '%' }"
              ></div>
            </div>

            <div class="project-card__footer">
              <button
                class="btn-action"
                @click="handleProjectAction(project)"
              >
                {{ getStatusCategory(project.status) === 'completed' ? 'View Results' : 'Resume' }}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12"/>
                  <polyline points="12 5 19 12 12 19"/>
                </svg>
              </button>
              <button
                class="btn-delete"
                @click="confirmDelete(project)"
                :disabled="deleting === project.project_id"
              >
                {{ deleting === project.project_id ? 'Deleting...' : 'Delete' }}
              </button>
            </div>
          </article>
        </div>
      </section>
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
  if (days > 7) return 'trial-badge--green'
  if (days >= 3) return 'trial-badge--yellow'
  return 'trial-badge--red'
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
  const simulationId = project.simulation_id

  if ((status === 'completed' || status === 'interacting') && reportId) {
    // Go to interaction view (has report + agent chat)
    router.push(`/interaction/${reportId}`)
  } else if (status === 'reporting' && reportId) {
    // Go to report view
    router.push(`/report/${reportId}`)
  } else if ((status === 'simulating') && simulationId) {
    // Go to simulation run view
    router.push(`/simulation/${simulationId}/start`)
  } else {
    // Default: go to process view
    router.push(`/process/${projectId}`)
  }
}

async function handleLogout() {
  await auth.logoutAction()
  router.push('/login')
}

async function handleUpgrade(plan) {
  upgrading.value = true
  try {
    const res = await createCheckout(plan)
    window.location.href = res.checkout_url
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
    window.location.href = res.portal_url
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
/* ── Page Shell ── */
.dashboard-page {
  min-height: 100vh;
  background: var(--bg);
  font-family: var(--font-body);
  color: var(--text);
}

/* ── Trial Expired Banner ── */
.trial-expired-banner {
  background: #FEF2F2;
  border-bottom: 1px solid #FECACA;
  color: var(--error);
  padding: 10px 40px;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
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
  flex-shrink: 0;
  color: var(--error);
}

.upgrade-link {
  color: var(--error);
  text-decoration: underline;
  font-weight: 600;
  margin-left: 4px;
}

.upgrade-link:hover {
  color: #DC2626;
}

/* ── Navigation Bar ── */
.dashboard-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 40px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.nav-brand {
  font-family: var(--font-brand);
  font-weight: 800;
  font-size: 1.125rem;
  letter-spacing: 1.5px;
  color: var(--primary);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Trial Badge */
.trial-badge {
  padding: 4px 14px;
  border-radius: var(--radius-pill);
  font-size: 0.8125rem;
  font-weight: 600;
  font-family: var(--font-body);
}

.trial-badge--green {
  background: #ECFDF5;
  color: #059669;
}

.trial-badge--yellow {
  background: #FFFBEB;
  color: #D97706;
}

.trial-badge--red {
  background: #FEF2F2;
  color: var(--error);
}

/* Plan Badges */
.plan-badge {
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: 0.8125rem;
  font-weight: 500;
}

.plan-badge--starter {
  background: #DBEAFE;
  color: #1D4ED8;
}

.plan-badge--pro {
  background: #EDE9FE;
  color: #6D28D9;
}

/* Nav Buttons */
.nav-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 16px;
  font-size: 0.875rem;
  color: var(--muted);
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast), background var(--transition-fast);
  font-family: var(--font-body);
  font-weight: 500;
}

.nav-btn:hover {
  border-color: var(--border-hover);
  color: var(--text);
  background: var(--bg);
}

/* ── Main Content ── */
.dashboard-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 40px;
}

/* ── Payment Toast ── */
.payment-toast {
  background: var(--success);
  color: white;
  padding: 12px 24px;
  border-radius: var(--radius-md);
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
  transition: opacity var(--transition-slow), transform var(--transition-slow);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── Greeting ── */
.greeting {
  font-family: var(--font-brand);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 32px 0;
  line-height: 1.3;
}

/* ── Upgrade Banner ── */
.upgrade-banner {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 28px;
  text-align: center;
}

.upgrade-banner__title {
  font-family: var(--font-brand);
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
  background: var(--cta);
  color: white;
  padding: 10px 24px;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.9375rem;
  border: none;
  cursor: pointer;
  font-family: var(--font-body);
  transition: background var(--transition-fast);
}

.btn-upgrade:hover {
  background: var(--cta-hover);
}

.btn-upgrade:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── New Prediction CTA Card ── */
.cta-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 4px solid var(--primary);
  border-radius: var(--radius-xl);
  padding: 24px 28px;
  margin-bottom: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: box-shadow var(--transition-normal), border-color var(--transition-normal);
  box-shadow: var(--shadow-card);
}

.cta-card:hover {
  box-shadow: var(--shadow-hover);
  border-color: var(--primary);
}

.cta-card:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.cta-card__left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.cta-card__plus {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  background: #EEF2FF;
  color: var(--primary);
  font-size: 1.5rem;
  font-weight: 300;
  flex-shrink: 0;
}

.cta-card__title {
  font-family: var(--font-brand);
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2px;
}

.cta-card__desc {
  font-size: 0.875rem;
  color: var(--muted);
}

.cta-card__arrow {
  color: var(--muted);
  flex-shrink: 0;
  transition: transform var(--transition-fast), color var(--transition-fast);
}

.cta-card:hover .cta-card__arrow {
  transform: translateX(4px);
  color: var(--primary);
}

/* ── Projects Section ── */
.section-header {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-family: var(--font-brand);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

/* Refresh Button */
.refresh-btn {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 6px 14px;
  color: var(--muted);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-family: var(--font-body);
  font-weight: 500;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--bg);
  color: var(--text);
  border-color: var(--border-hover);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-icon {
  transition: transform var(--transition-slow);
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── State Panels (Loading / Error / Empty) ── */
.state-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 64px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: var(--shadow-card);
}

.state-panel--error {
  border-color: #FECACA;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

.state-text {
  font-size: 0.9375rem;
  color: var(--muted);
  margin: 0;
}

.state-text--error {
  color: var(--error);
  margin-bottom: 20px;
}

/* Empty State */
.empty-icon {
  margin-bottom: 20px;
}

.empty-title {
  font-family: var(--font-brand);
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 6px 0;
}

.empty-desc {
  font-size: 0.9375rem;
  color: var(--muted);
  margin: 0 0 24px 0;
}

/* Ghost Buttons */
.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 10px 24px;
  font-size: 0.9375rem;
  color: var(--text);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast);
  font-family: var(--font-body);
  font-weight: 500;
}

.btn-ghost:hover {
  background: var(--bg);
  border-color: var(--border-hover);
}

.btn-ghost--primary {
  border-color: var(--primary);
  color: var(--primary);
}

.btn-ghost--primary:hover {
  background: #EEF2FF;
  border-color: var(--primary-hover);
}

/* ── Projects Grid ── */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

/* ── Project Card ── */
.project-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow-card);
  transition: box-shadow var(--transition-normal), border-color var(--transition-normal);
}

.project-card:hover {
  box-shadow: var(--shadow-elevated);
  border-color: var(--border-hover);
}

.project-card__header {
  display: flex;
  justify-content: flex-start;
}

.project-card__title {
  font-family: var(--font-brand);
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-card__meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8125rem;
  color: var(--muted);
}

.project-card__step {
  font-weight: 500;
}

/* ── Status Badges ── */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-badge--created {
  background: #F8FAFC;
  color: var(--muted);
}

.status-badge--created .status-badge__dot {
  background: var(--muted);
}

.status-badge--running {
  background: #EFF6FF;
  color: var(--cta);
}

.status-badge--running .status-badge__dot {
  background: var(--cta);
  animation: pulse-dot 1.5s infinite;
}

.status-badge--completed {
  background: #ECFDF5;
  color: #059669;
}

.status-badge--completed .status-badge__dot {
  background: var(--success);
}

.status-badge--failed {
  background: #FEF2F2;
  color: #DC2626;
}

.status-badge--failed .status-badge__dot {
  background: var(--error);
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ── Progress Bar ── */
.progress-bar {
  height: 6px;
  background: var(--bg);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.progress-bar__fill {
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width var(--transition-slow);
}

.progress-bar__fill--created {
  background: var(--muted);
}

.progress-bar__fill--running {
  background: var(--cta);
}

.progress-bar__fill--completed {
  background: var(--success);
}

.progress-bar__fill--failed {
  background: var(--error);
}

/* ── Card Footer ── */
.project-card__footer {
  border-top: 1px solid var(--border);
  padding-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 2px;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid var(--primary);
  border-radius: var(--radius-md);
  padding: 7px 18px;
  font-size: 0.8125rem;
  color: var(--primary);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-body);
  font-weight: 600;
}

.btn-action:hover {
  background: var(--primary);
  color: white;
}

.btn-delete {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 7px 14px;
  font-size: 0.8125rem;
  color: var(--muted);
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-body);
  font-weight: 500;
}

.btn-delete:hover:not(:disabled) {
  background: #FEF2F2;
  border-color: #FECACA;
  color: var(--error);
}

.btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .dashboard-nav {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 16px 20px;
  }

  .nav-right {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }

  .dashboard-main {
    padding: 32px 20px;
  }

  .greeting {
    font-size: 1.375rem;
  }

  .cta-card {
    padding: 20px;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }

  .trial-expired-banner {
    padding: 10px 20px;
    font-size: 0.8125rem;
    flex-wrap: wrap;
  }

  .upgrade-banner__actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>
