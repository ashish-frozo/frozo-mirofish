<template>
  <div class="dashboard-page">
    <!-- Trial Expired Banner -->
    <div v-if="auth.isTrialExpired" class="trial-expired-banner">
      <span class="banner-icon">!</span>
      Trial Expired -- Upgrade to continue
      <router-link to="/pricing" class="upgrade-link">Upgrade Now</router-link>
    </div>

    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-left">
        <div class="brand">AUGUR</div>
        <h1 class="greeting">Welcome back, {{ auth.user?.name || 'User' }}</h1>
      </div>
      <div class="header-right">
        <span
          v-if="auth.user?.plan === 'trial' && !auth.isTrialExpired"
          class="trial-badge"
          :class="trialBadgeClass"
        >
          Trial: {{ auth.trialDaysLeft }} days left
        </span>
        <span v-if="auth.currentPlan === 'starter'" style="background: #DBEAFE; color: #1D4ED8; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 500;">Starter Plan</span>
        <span v-else-if="auth.currentPlan === 'pro'" style="background: #EDE9FE; color: #6D28D9; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 500;">Pro Plan</span>
        <button v-if="auth.currentPlan !== 'trial'" @click="handleManageSubscription" style="background: transparent; border: 1px solid #d1d5db; color: #6b7280; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
          Manage Subscription
        </button>
        <button class="logout-btn" @click="handleLogout" aria-label="Sign out">
          Sign Out
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="dashboard-main">
      <!-- Payment Success Toast -->
      <div v-if="paymentSuccess" style="background: #059669; color: white; padding: 12px 24px; border-radius: 8px; margin-bottom: 24px; text-align: center; font-weight: 500;">
        Payment successful! Your plan is now active.
      </div>

      <!-- Upgrade Banner (when trial expired or no active plan) -->
      <div v-if="auth.isTrialExpired || (!auth.canCreateProjects && auth.isAuthenticated)" style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; padding: 24px; margin-bottom: 24px; text-align: center;">
        <h3 style="font-size: 18px; font-weight: 600; color: #991B1B; margin-bottom: 8px;">Your trial has expired</h3>
        <p style="color: #B91C1C; margin-bottom: 16px;">Upgrade to continue creating predictions.</p>
        <div style="display: flex; gap: 12px; justify-content: center;">
          <button @click="handleUpgrade('starter')" :disabled="upgrading" style="background: #2563EB; color: white; padding: 10px 24px; border-radius: 8px; font-weight: 600; border: none; cursor: pointer;">
            {{ upgrading ? 'Loading...' : 'Starter — $19/mo' }}
          </button>
          <button @click="handleUpgrade('pro')" :disabled="upgrading" style="background: #2563EB; color: white; padding: 10px 24px; border-radius: 8px; font-weight: 600; border: none; cursor: pointer;">
            {{ upgrading ? 'Loading...' : 'Pro — $49/mo' }}
          </button>
        </div>
      </div>

      <!-- New Prediction CTA -->
      <section class="cta-section">
        <button class="new-prediction-btn" @click="router.push('/new')">
          <span class="btn-plus">+</span>
          <span class="btn-text">New Prediction</span>
          <span class="btn-arrow">-></span>
        </button>
      </section>

      <!-- Projects Section -->
      <section class="projects-section">
        <div class="section-header">
          <h2 class="section-title">Your Projects</h2>
          <button class="refresh-btn" @click="fetchProjects" :disabled="loading" aria-label="Refresh projects">
            <svg
              class="refresh-icon"
              :class="{ spinning: loading }"
              width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            >
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading && projects.length === 0" class="loading-state">
          <div class="loading-spinner"></div>
          <p class="loading-text">Loading projects...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <p class="error-text">{{ error }}</p>
          <button class="empty-cta" @click="fetchProjects">Try Again</button>
        </div>

        <!-- Empty State -->
        <div v-else-if="projects.length === 0" class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <rect x="6" y="10" width="36" height="28" rx="4" stroke="#4a4a6a" stroke-width="2" fill="none"/>
              <path d="M6 18h36" stroke="#4a4a6a" stroke-width="2"/>
              <circle cx="12" cy="14" r="1.5" fill="#4a4a6a"/>
              <circle cx="17" cy="14" r="1.5" fill="#4a4a6a"/>
              <circle cx="22" cy="14" r="1.5" fill="#4a4a6a"/>
              <path d="M18 28h12M21 24h6" stroke="#4a4a6a" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
          <p class="empty-title">No projects yet</p>
          <p class="empty-desc">Start your first prediction to see it here.</p>
          <button class="empty-cta" @click="router.push('/new')">
            Create Your First Prediction
          </button>
        </div>

        <!-- Project Cards Grid -->
        <div v-else class="projects-grid">
          <div
            v-for="project in projects"
            :key="project.project_id"
            class="project-card"
          >
            <div class="card-header">
              <h3 class="card-title">{{ project.name || project.simulation_requirement || 'Untitled Project' }}</h3>
              <span class="status-badge" :class="'status-' + getStatusCategory(project.status)">
                <span class="status-dot"></span>
                {{ getStepInfo(project.status).label }}
              </span>
            </div>
            <div class="card-body">
              <div class="step-indicator">
                <div
                  v-for="step in 5"
                  :key="step"
                  class="step-pip"
                  :class="{
                    active: step <= getStepInfo(project.status).step,
                    current: step === getStepInfo(project.status).step
                  }"
                >
                  {{ step }}
                </div>
              </div>
              <div class="card-date">{{ formatDate(project.created_at) }}</div>
            </div>
            <div class="card-footer">
              <button
                class="resume-btn"
                @click="router.push(`/process/${project.project_id}`)"
              >
                Resume
              </button>
              <button
                class="delete-btn"
                @click="confirmDelete(project)"
                :disabled="deleting === project.project_id"
              >
                {{ deleting === project.project_id ? 'Deleting...' : 'Delete' }}
              </button>
            </div>
          </div>
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
  if (days > 7) return 'badge-green'
  if (days >= 3) return 'badge-yellow'
  return 'badge-red'
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
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
.dashboard-page {
  min-height: 100vh;
  background: #0a0a1a;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  color: #e0e0f0;
}

/* Trial Expired Banner */
.trial-expired-banner {
  background: rgba(239, 68, 68, 0.15);
  border-bottom: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  padding: 12px 40px;
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.banner-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(239, 68, 68, 0.25);
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.upgrade-link {
  color: #f87171;
  text-decoration: underline;
  font-weight: 600;
  margin-left: 4px;
}

.upgrade-link:hover {
  color: #fca5a5;
}

/* Header */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 40px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.1rem;
  letter-spacing: 2px;
  color: #fff;
}

.greeting {
  font-size: 1.1rem;
  font-weight: 400;
  color: #9393b0;
  margin: 0;
  padding-left: 24px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Trial Badge */
.trial-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.3px;
  font-family: 'JetBrains Mono', monospace;
}

.badge-green {
  background: rgba(34, 197, 94, 0.12);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.badge-yellow {
  background: rgba(234, 179, 8, 0.12);
  border: 1px solid rgba(234, 179, 8, 0.3);
  color: #facc15;
}

.badge-red {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.logout-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 8px 18px;
  font-size: 0.85rem;
  color: #9393b0;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
  font-family: inherit;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.2);
  color: #e0e0f0;
}

/* Main Content */
.dashboard-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 40px;
}

/* CTA Section */
.cta-section {
  margin-bottom: 48px;
}

.new-prediction-btn {
  width: 100%;
  background: #4a7cff;
  color: #fff;
  border: none;
  border-radius: 12px;
  padding: 22px 32px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: background 0.2s, transform 0.15s, box-shadow 0.2s;
  font-family: inherit;
}

.new-prediction-btn:hover {
  background: #3a6aee;
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(74, 124, 255, 0.25);
}

.new-prediction-btn:active {
  transform: translateY(0);
}

.btn-plus {
  font-size: 1.4rem;
  font-weight: 300;
  line-height: 1;
}

.btn-text {
  flex: 1;
  text-align: left;
}

.btn-arrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  opacity: 0.7;
}

/* Projects Section */
.projects-section {
  /* container */
}

.section-header {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #f0f0f0;
  margin: 0;
}

/* Refresh Button */
.refresh-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 6px 10px;
  color: #9393b0;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.04);
  color: #e0e0f0;
  border-color: rgba(255, 255, 255, 0.2);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.refresh-icon {
  transition: transform 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Loading State */
.loading-state {
  background: #12122a;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 64px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(74, 124, 255, 0.15);
  border-top-color: #4a7cff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

.loading-text {
  font-size: 0.95rem;
  color: #9393b0;
  margin: 0;
}

/* Error State */
.error-state {
  background: #12122a;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  padding: 48px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.error-text {
  font-size: 0.95rem;
  color: #f87171;
  margin: 0 0 20px 0;
}

/* Empty State */
.empty-state {
  background: #12122a;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 64px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  margin-bottom: 20px;
  opacity: 0.6;
}

.empty-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: #9393b0;
  margin: 0 0 8px 0;
}

.empty-desc {
  font-size: 0.9rem;
  color: #5a5a7a;
  margin: 0 0 28px 0;
}

.empty-cta {
  background: transparent;
  border: 1px solid rgba(74, 124, 255, 0.4);
  border-radius: 8px;
  padding: 10px 24px;
  font-size: 0.9rem;
  color: #4a7cff;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  font-family: inherit;
  font-weight: 500;
}

.empty-cta:hover {
  background: rgba(74, 124, 255, 0.08);
  border-color: #4a7cff;
}

/* Projects Grid */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.project-card {
  background: #12122a;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.project-card:hover {
  border-color: rgba(74, 124, 255, 0.25);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #f0f0f0;
  margin: 0;
  line-height: 1.4;
}

/* Status Badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: capitalize;
  white-space: nowrap;
  font-family: 'JetBrains Mono', monospace;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-created {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
}

.status-created .status-dot {
  background: #94a3b8;
}

.status-running {
  background: rgba(74, 124, 255, 0.1);
  color: #4a7cff;
}

.status-running .status-dot {
  background: #4a7cff;
  animation: pulse-dot 1.5s infinite;
}

.status-completed {
  background: rgba(34, 197, 94, 0.1);
  color: #4ade80;
}

.status-completed .status-dot {
  background: #4ade80;
}

.status-failed {
  background: rgba(239, 68, 68, 0.1);
  color: #f87171;
}

.status-failed .status-dot {
  background: #f87171;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Step Indicator */
.card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-indicator {
  display: flex;
  gap: 4px;
}

.step-pip {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  background: rgba(255, 255, 255, 0.04);
  color: #4a4a6a;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.step-pip.active {
  background: rgba(74, 124, 255, 0.15);
  color: #4a7cff;
  border-color: rgba(74, 124, 255, 0.3);
}

.step-pip.current {
  background: #4a7cff;
  color: #fff;
  border-color: #4a7cff;
}

.card-date {
  font-size: 0.78rem;
  color: #5a5a7a;
  font-family: 'JetBrains Mono', monospace;
}

/* Card Footer */
.card-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.resume-btn {
  background: transparent;
  border: 1px solid rgba(74, 124, 255, 0.3);
  border-radius: 8px;
  padding: 8px 20px;
  font-size: 0.85rem;
  color: #4a7cff;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  font-family: inherit;
  font-weight: 500;
}

.resume-btn:hover {
  background: rgba(74, 124, 255, 0.08);
  border-color: #4a7cff;
}

.delete-btn {
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 0.85rem;
  color: #f87171;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  font-family: inherit;
  font-weight: 500;
}

.delete-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.4);
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 20px 24px;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .greeting {
    padding-left: 0;
    border-left: none;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .dashboard-main {
    padding: 32px 24px;
  }

  .new-prediction-btn {
    padding: 18px 24px;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }

  .trial-expired-banner {
    padding: 12px 24px;
    font-size: 0.8rem;
    flex-wrap: wrap;
  }
}
</style>
