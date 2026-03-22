<template>
  <div class="accuracy-dashboard">
    <div class="dashboard-header">
      <h2>Prediction Accuracy</h2>
      <div class="overall-score" v-if="data">
        <span class="score-value">{{ data.overall_accuracy }}%</span>
        <span class="score-label">Overall Accuracy</span>
      </div>
    </div>

    <div class="stats-row" v-if="data">
      <div class="stat-card">
        <span class="stat-number">{{ data.validated_count }}</span>
        <span class="stat-label">Validated</span>
      </div>
      <div class="stat-card">
        <span class="stat-number">{{ data.total_predictions - data.validated_count }}</span>
        <span class="stat-label">Pending</span>
      </div>
    </div>

    <div class="validations-list" v-if="data && data.recent_validations.length">
      <h3>Recent Validations</h3>
      <div class="validation-item" v-for="v in data.recent_validations" :key="v.prediction_task_id">
        <div class="validation-score">{{ v.accuracy_score }}%</div>
        <div class="validation-details">
          <span class="validation-date">{{ formatDate(v.validated_at) }}</span>
          <span class="validation-predictions" v-if="Array.isArray(v.per_prediction)">
            {{ v.per_prediction.filter(p => p.outcome).length }}/{{ v.per_prediction.length }} correct
          </span>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else-if="data">
      <p>No validated predictions yet. Predictions will be validated automatically after the prediction horizon passes.</p>
    </div>

    <div class="loading" v-else>
      <p>Loading accuracy data...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAccuracy } from '../api/predict'

const data = ref(null)

onMounted(async () => {
  try {
    const resp = await getAccuracy()
    data.value = resp.data
  } catch (e) {
    console.warn('Failed to load accuracy data:', e)
  }
})

function formatDate(isoStr) {
  if (!isoStr) return '\u2014'
  return new Date(isoStr).toLocaleDateString()
}
</script>

<style scoped>
.accuracy-dashboard {
  padding: 1.5rem;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.overall-score {
  text-align: center;
}
.score-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--primary, #3525cd);
}
.score-label {
  display: block;
  font-size: 0.875rem;
  color: var(--outline, #777);
}
.stats-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.stat-card {
  flex: 1;
  padding: 1rem;
  background: var(--surface-container, #eceef0);
  border-radius: 0.75rem;
  text-align: center;
}
.stat-number {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
}
.stat-label {
  font-size: 0.75rem;
  color: var(--outline, #777);
}
.validations-list h3 {
  margin-bottom: 0.75rem;
}
.validation-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--outline-variant, #c7c4d8);
}
.validation-score {
  font-size: 1.25rem;
  font-weight: 600;
  min-width: 3rem;
}
.validation-date {
  font-size: 0.875rem;
  color: var(--outline, #777);
}
.empty-state, .loading {
  text-align: center;
  padding: 2rem;
  color: var(--outline, #777);
}
</style>
