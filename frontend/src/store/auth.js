import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshTokenValue = ref(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value)
  const isTrialExpired = computed(() => {
    if (!user.value || user.value.plan !== 'trial') return false
    return new Date(user.value.trial_ends_at) < new Date()
  })
  const trialDaysLeft = computed(() => {
    if (!user.value || user.value.plan !== 'trial') return null
    const diff = new Date(user.value.trial_ends_at) - new Date()
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)))
  })

  const canCreateProjects = computed(() => {
    if (!user.value) return false
    const u = user.value
    if (['starter', 'pro', 'enterprise'].includes(u.plan) && u.subscription_status === 'active') return true
    if (['starter', 'pro'].includes(u.plan) && u.subscription_status === 'cancelled' && u.current_period_end) {
      return new Date(u.current_period_end) > new Date()
    }
    if (u.plan === 'trial') return !isTrialExpired.value
    return false
  })

  const currentPlan = computed(() => user.value?.plan || 'trial')
  const subscriptionStatus = computed(() => user.value?.subscription_status || null)

  function setTokens(access, refresh) {
    accessToken.value = access
    refreshTokenValue.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearTokens() {
    accessToken.value = null
    refreshTokenValue.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async function signupAction(email, name, password) {
    const res = await authApi.signup({ email, name, password })
    setTokens(res.access_token, res.refresh_token)
    user.value = res.user
  }

  async function loginAction(email, password) {
    const res = await authApi.login({ email, password })
    setTokens(res.access_token, res.refresh_token)
    user.value = res.user
  }

  async function logoutAction() {
    try {
      if (refreshTokenValue.value) {
        await authApi.logout({ refresh_token: refreshTokenValue.value })
      }
    } catch (e) { /* ignore logout errors */ }
    clearTokens()
  }

  async function fetchUser() {
    try {
      const res = await authApi.getMe()
      user.value = res.user || res
    } catch (e) {
      clearTokens()
    }
  }

  async function refreshAccessToken() {
    if (!refreshTokenValue.value) throw new Error('No refresh token')
    const res = await authApi.refreshToken(refreshTokenValue.value)
    setTokens(res.access_token, res.refresh_token)
  }

  return {
    user, accessToken, refreshTokenValue,
    isAuthenticated, isTrialExpired, trialDaysLeft, canCreateProjects, currentPlan, subscriptionStatus,
    signupAction, loginAction, logoutAction, fetchUser, refreshAccessToken, clearTokens, setTokens
  }
})
