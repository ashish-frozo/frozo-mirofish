<template>
  <div class="admin-costs">
    <nav class="top-nav">
      <div class="top-nav__brand">ADMIN</div>
      <div class="top-nav__right">
        <router-link to="/dashboard" class="top-nav__link">
          <span class="material-symbols-outlined top-nav__link-icon">arrow_back</span>
          Back to Dashboard
        </router-link>
      </div>
    </nav>

    <main class="content">
      <header class="page-header">
        <h1 class="page-title">Prediction Costs</h1>
        <p class="page-subtitle">LLM spend per prediction, aggregated from the in-process cost tracker (ontology, report, profiles) and OASIS subprocess counters.</p>
      </header>

      <div class="filters">
        <label class="filter">
          <span class="filter__label">Filter by user email</span>
          <input
            v-model="userEmail"
            class="filter__input"
            type="email"
            placeholder="alice@example.com"
            @keyup.enter="load"
          />
        </label>
        <label class="filter">
          <span class="filter__label">Limit</span>
          <input v-model.number="limit" class="filter__input filter__input--sm" type="number" min="1" max="500" @change="load" />
        </label>
        <label class="filter filter--check">
          <input v-model="includeRunning" type="checkbox" @change="load" />
          <span>Include running</span>
        </label>
        <button class="btn" :disabled="loading" @click="load">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? 'Loading…' : 'Refresh' }}
        </button>
      </div>

      <section v-if="totals" class="totals">
        <div class="totals__card">
          <span class="totals__label">Predictions</span>
          <span class="totals__value">{{ count }}</span>
        </div>
        <div class="totals__card">
          <span class="totals__label">LLM Calls</span>
          <span class="totals__value">{{ totals.calls.toLocaleString() }}</span>
        </div>
        <div class="totals__card">
          <span class="totals__label">Tokens (in / out)</span>
          <span class="totals__value">{{ totals.prompt_tokens.toLocaleString() }} / {{ totals.completion_tokens.toLocaleString() }}</span>
        </div>
        <div class="totals__card totals__card--accent">
          <span class="totals__label">Total Cost</span>
          <span class="totals__value">${{ totals.cost_usd.toFixed(4) }}</span>
        </div>
      </section>

      <p v-if="error" class="error-msg">{{ error }}</p>

      <section class="table-wrap">
        <table v-if="rows.length" class="data-table">
          <thead>
            <tr>
              <th>Created</th>
              <th>Status</th>
              <th>User</th>
              <th>Prompt</th>
              <th class="num">Calls</th>
              <th class="num">In tokens</th>
              <th class="num">Out tokens</th>
              <th class="num">Cost</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.task_id" :class="{ 'row--running': row.status === 'running', 'row--failed': row.status === 'failed' }">
              <td class="nowrap">{{ formatDate(row.created_at) }}</td>
              <td><span class="badge" :class="'badge--' + row.status">{{ row.status }}</span></td>
              <td>
                <div class="user">
                  <span class="user__name">{{ row.user_name || '—' }}</span>
                  <span class="user__email">{{ row.user_email }}</span>
                </div>
              </td>
              <td class="prompt-cell">{{ row.simulation_requirement || '—' }}</td>
              <td class="num">{{ row.calls.toLocaleString() }}</td>
              <td class="num">{{ row.prompt_tokens.toLocaleString() }}</td>
              <td class="num">{{ row.completion_tokens.toLocaleString() }}</td>
              <td class="num strong">${{ row.cost_usd.toFixed(4) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else-if="!loading" class="empty">No predictions match the current filters.</div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listPredictionCosts } from '../api/admin'

const loading = ref(false)
const error = ref('')
const rows = ref([])
const totals = ref(null)
const count = ref(0)

const limit = ref(50)
const userEmail = ref('')
const includeRunning = ref(true)

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = { limit: limit.value, include_running: includeRunning.value }
    if (userEmail.value.trim()) params.user_email = userEmail.value.trim()
    const res = await listPredictionCosts(params)
    rows.value = res.data.rows || []
    totals.value = res.data.totals || null
    count.value = res.data.count || 0
  } catch (err) {
    error.value = err?.response?.data?.error || err.message || 'Failed to load costs'
    rows.value = []
    totals.value = null
  } finally {
    loading.value = false
  }
}

const formatDate = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString(undefined, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>

<style scoped>
.admin-costs {
  min-height: 100vh;
  background: #F8FAFC;
  font-family: 'Inter', system-ui, sans-serif;
  color: #191c1e;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #FFF;
  border-bottom: 1px solid #EAEAEA;
}
.top-nav__brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  letter-spacing: 1.5px;
}
.top-nav__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #464555;
  text-decoration: none;
  font-size: 0.875rem;
}
.top-nav__link-icon { font-size: 1rem; }

.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}
.page-header { margin-bottom: 1.5rem; }
.page-title { font-size: 1.75rem; font-weight: 700; margin: 0 0 0.5rem 0; }
.page-subtitle { font-size: 0.875rem; color: #555; margin: 0; max-width: 720px; line-height: 1.45; }

.filters {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}
.filter { display: flex; flex-direction: column; gap: 4px; }
.filter--check { flex-direction: row; align-items: center; gap: 6px; padding-bottom: 0.5rem; }
.filter__label { font-size: 0.6875rem; color: #777587; letter-spacing: 0.5px; text-transform: uppercase; font-weight: 600; }
.filter__input {
  border: 1px solid #D9D7E1;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  min-width: 240px;
  background: #FFF;
}
.filter__input--sm { min-width: 80px; }
.filter__input:focus { outline: none; border-color: #4338CA; }

.btn {
  background: #000;
  color: #FFF;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.8125rem;
  cursor: pointer;
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
.btn:disabled { background: #AAA; cursor: not-allowed; }
.spinner {
  width: 12px; height: 12px;
  border: 2px solid #FFF; border-top-color: transparent;
  border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.totals {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.totals__card {
  background: #FFF;
  border: 1px solid #EAEAEA;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.totals__card--accent { border-color: #4338CA; background: #EEF2FF; }
.totals__label { font-size: 0.6875rem; color: #777587; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
.totals__value { font-size: 1.25rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

.table-wrap { background: #FFF; border: 1px solid #EAEAEA; border-radius: 8px; overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.data-table th {
  text-align: left; padding: 0.75rem 1rem; background: #FAFAFA;
  border-bottom: 1px solid #EAEAEA;
  font-weight: 600; color: #464555; font-size: 0.6875rem;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.data-table td { padding: 0.75rem 1rem; border-bottom: 1px solid #F0F0F2; vertical-align: top; }
.data-table tr:last-child td { border-bottom: none; }
.data-table .num { text-align: right; font-family: 'JetBrains Mono', monospace; }
.data-table .strong { font-weight: 700; }
.nowrap { white-space: nowrap; }

.row--running { background: #FFFBEB; }
.row--failed { background: #FEF2F2; }

.user { display: flex; flex-direction: column; gap: 2px; }
.user__name { font-weight: 600; }
.user__email { font-size: 0.75rem; color: #777587; }

.prompt-cell {
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #333;
}

.badge {
  display: inline-block;
  font-size: 0.6875rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.badge--completed { background: #E8F5E9; color: #2E7D32; }
.badge--running { background: #FFF3E0; color: #E65100; }
.badge--failed { background: #FFEBEE; color: #C62828; }
.badge--pending { background: #F5F5F5; color: #777; }

.empty { padding: 2rem; text-align: center; color: #777587; font-size: 0.875rem; }
.error-msg { color: #C62828; background: #FFEBEE; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.8125rem; margin-bottom: 1rem; }
</style>
