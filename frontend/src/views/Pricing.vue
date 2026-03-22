<template>
  <div class="pricing-page">
    <header class="pricing-header">
      <router-link to="/dashboard" class="back-link">
        <span class="material-symbols-outlined">arrow_back</span>
        Dashboard
      </router-link>
    </header>

    <main class="pricing-main">
      <div class="pricing-hero">
        <h1 class="pricing-title">Choose Your Plan</h1>
        <p class="pricing-subtitle">Scale your predictions with the right plan for your needs.</p>
      </div>

      <div class="plans-grid">
        <!-- Trial -->
        <div class="plan-card" :class="{ 'plan-card--current': currentPlan === 'trial' }">
          <div class="plan-card__badge" v-if="currentPlan === 'trial'">Current Plan</div>
          <h3 class="plan-card__name">Trial</h3>
          <div class="plan-card__price">
            <span class="plan-card__amount">Free</span>
            <span class="plan-card__period">14 days</span>
          </div>
          <ul class="plan-card__features">
            <li><span class="material-symbols-outlined feat-icon">check</span> 3 simulations / month</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 20 agents</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 5 rounds</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Email report delivery</li>
          </ul>
          <div v-if="currentPlan === 'trial' && !isTrialExpired" class="plan-card__status">
            {{ trialDaysLeft }} days remaining
          </div>
          <div v-else-if="isTrialExpired" class="plan-card__status plan-card__status--expired">
            Trial expired
          </div>
        </div>

        <!-- Starter -->
        <div class="plan-card" :class="{ 'plan-card--current': currentPlan === 'starter' }">
          <div class="plan-card__badge" v-if="currentPlan === 'starter'">Current Plan</div>
          <h3 class="plan-card__name">Starter</h3>
          <div class="plan-card__price">
            <span class="plan-card__amount">$19</span>
            <span class="plan-card__period">/ month</span>
          </div>
          <ul class="plan-card__features">
            <li><span class="material-symbols-outlined feat-icon">check</span> 5 simulations / month</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 20 agents</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 5 rounds</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Email report delivery</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Priority support</li>
          </ul>
          <button
            v-if="currentPlan !== 'starter'"
            class="plan-card__cta"
            :disabled="upgrading"
            @click="handleUpgrade('starter')"
          >
            {{ upgrading ? 'Loading...' : 'Get Starter' }}
          </button>
          <button
            v-else
            class="plan-card__cta plan-card__cta--manage"
            @click="handleManage"
          >
            Manage Subscription
          </button>
        </div>

        <!-- Pro -->
        <div class="plan-card plan-card--featured" :class="{ 'plan-card--current': currentPlan === 'pro' }">
          <div class="plan-card__badge" v-if="currentPlan === 'pro'">Current Plan</div>
          <div class="plan-card__badge plan-card__badge--popular" v-else>Most Popular</div>
          <h3 class="plan-card__name">Pro</h3>
          <div class="plan-card__price">
            <span class="plan-card__amount">$49</span>
            <span class="plan-card__period">/ month</span>
          </div>
          <ul class="plan-card__features">
            <li><span class="material-symbols-outlined feat-icon">check</span> 20 simulations / month</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 50 agents</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 10 rounds</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Email report delivery</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Priority support</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Extended simulation hours</li>
          </ul>
          <button
            v-if="currentPlan !== 'pro'"
            class="plan-card__cta plan-card__cta--primary"
            :disabled="upgrading"
            @click="handleUpgrade('pro')"
          >
            {{ upgrading ? 'Loading...' : 'Get Pro' }}
          </button>
          <button
            v-else
            class="plan-card__cta plan-card__cta--manage"
            @click="handleManage"
          >
            Manage Subscription
          </button>
        </div>

        <!-- Enterprise -->
        <div class="plan-card" :class="{ 'plan-card--current': currentPlan === 'enterprise' }">
          <div class="plan-card__badge" v-if="currentPlan === 'enterprise'">Current Plan</div>
          <h3 class="plan-card__name">Enterprise</h3>
          <div class="plan-card__price">
            <span class="plan-card__amount">Custom</span>
            <span class="plan-card__period">contact us</span>
          </div>
          <ul class="plan-card__features">
            <li><span class="material-symbols-outlined feat-icon">check</span> Unlimited simulations</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 200 agents</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Up to 20 rounds</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Dedicated support</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> Custom integrations</li>
            <li><span class="material-symbols-outlined feat-icon">check</span> SLA guarantee</li>
          </ul>
          <a href="mailto:support@augur.email" class="plan-card__cta plan-card__cta--outline">
            Contact Sales
          </a>
        </div>
      </div>

      <!-- Usage Stats -->
      <div v-if="usage" class="usage-section">
        <h3 class="usage-title">Current Usage</h3>
        <div class="usage-bar-wrap">
          <div class="usage-bar-label">
            <span>Simulations this month</span>
            <span>{{ usage.simulations_used }} / {{ usage.simulations_limit }}</span>
          </div>
          <div class="usage-bar-track">
            <div
              class="usage-bar-fill"
              :style="{ width: Math.min(100, (usage.simulations_used / usage.simulations_limit) * 100) + '%' }"
              :class="{ 'usage-bar-fill--warn': usage.simulations_used >= usage.simulations_limit * 0.8 }"
            ></div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { createCheckout, createPortal, getBillingStatus } from '../api/billing'

const router = useRouter()
const auth = useAuthStore()
const upgrading = ref(false)
const usage = ref(null)

const currentPlan = computed(() => auth.isAuthenticated ? auth.currentPlan : null)
const isTrialExpired = computed(() => auth.isAuthenticated ? auth.isTrialExpired : false)
const trialDaysLeft = computed(() => auth.isAuthenticated ? auth.trialDaysLeft : null)

onMounted(async () => {
  if (!auth.isAuthenticated) return
  try {
    const res = await getBillingStatus()
    if (res?.usage) {
      usage.value = res.usage
    } else if (res?.data?.usage) {
      usage.value = res.data.usage
    }
  } catch { /* ignore */ }
})

async function handleUpgrade(plan) {
  if (!auth.isAuthenticated) {
    router.push('/signup')
    return
  }
  upgrading.value = true
  try {
    const res = await createCheckout(plan)
    const url = res?.checkout_url || res?.data?.checkout_url
    if (url) {
      window.location.href = url
    }
  } catch (e) {
    console.error('Checkout failed:', e)
  } finally {
    upgrading.value = false
  }
}

async function handleManage() {
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
</script>

<style scoped>
.pricing-page {
  min-height: 100vh;
  background: #f7f9fb;
  font-family: 'Inter', sans-serif;
}

.pricing-header {
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-decoration: none;
  transition: color 0.2s;
}

.back-link:hover {
  color: #4f46e5;
}

.back-link .material-symbols-outlined {
  font-size: 18px;
}

.pricing-main {
  max-width: 1120px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

.pricing-hero {
  text-align: center;
  margin-bottom: 48px;
}

.pricing-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #191c1e;
  margin: 0 0 12px;
}

.pricing-subtitle {
  font-size: 1.0625rem;
  color: #64748b;
  margin: 0;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 48px;
}

@media (max-width: 1024px) {
  .plans-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}

.plan-card {
  background: #fff;
  border-radius: 16px;
  padding: 32px 24px;
  box-shadow: 0 4px 24px rgba(79, 70, 229, 0.04);
  position: relative;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s;
}

.plan-card:hover {
  transform: translateY(-4px);
}

.plan-card--featured {
  border: 2px solid #4f46e5;
}

.plan-card--current {
  border: 2px solid #059669;
}

.plan-card__badge {
  position: absolute;
  top: -10px;
  left: 24px;
  background: #059669;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 4px 10px;
  border-radius: 9999px;
}

.plan-card__badge--popular {
  background: #4f46e5;
}

.plan-card__name {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1.25rem;
  font-weight: 700;
  color: #191c1e;
  margin: 8px 0 16px;
}

.plan-card__price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 24px;
}

.plan-card__amount {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: #191c1e;
}

.plan-card__period {
  font-size: 0.875rem;
  color: #64748b;
}

.plan-card__features {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-card__features li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: #464555;
}

.feat-icon {
  font-size: 16px;
  color: #059669;
}

.plan-card__status {
  text-align: center;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #059669;
  padding: 10px;
  background: #ecfdf5;
  border-radius: 8px;
}

.plan-card__status--expired {
  color: #dc2626;
  background: #fef2f2;
}

.plan-card__cta {
  display: block;
  width: 100%;
  padding: 12px 20px;
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  text-decoration: none;
  background: #191c1e;
  color: #fff;
}

.plan-card__cta:hover {
  background: #333;
  transform: translateY(-1px);
}

.plan-card__cta--primary {
  background: #4f46e5;
}

.plan-card__cta--primary:hover {
  background: #4338ca;
}

.plan-card__cta--manage {
  background: transparent;
  color: #4f46e5;
  border: 1px solid rgba(79, 70, 229, 0.3);
}

.plan-card__cta--manage:hover {
  background: rgba(79, 70, 229, 0.05);
}

.plan-card__cta--outline {
  background: transparent;
  color: #191c1e;
  border: 1px solid #e0e3e5;
}

.plan-card__cta--outline:hover {
  background: #f7f9fb;
}

.plan-card__cta:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Usage Section */
.usage-section {
  max-width: 500px;
  margin: 0 auto;
  background: #fff;
  border-radius: 16px;
  padding: 28px 32px;
  box-shadow: 0 4px 24px rgba(79, 70, 229, 0.04);
}

.usage-title {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0 0 16px;
}

.usage-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: #464555;
  margin-bottom: 8px;
}

.usage-bar-track {
  height: 8px;
  background: #e0e3e5;
  border-radius: 9999px;
  overflow: hidden;
}

.usage-bar-fill {
  height: 100%;
  background: #4f46e5;
  border-radius: 9999px;
  transition: width 0.5s ease;
}

.usage-bar-fill--warn {
  background: #dc2626;
}
</style>
