<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">MIROFISH</div>
      <h1 class="auth-title">Welcome back</h1>
      <p class="auth-subtitle">Sign in to continue to your dashboard</p>

      <div v-if="error" class="auth-error">{{ error }}</div>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email" class="form-label">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            class="form-input"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password" class="form-label">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="Enter your password"
            required
            autocomplete="current-password"
          />
        </div>

        <button type="submit" class="auth-btn" :disabled="loading">
          <span v-if="!loading">Sign In</span>
          <span v-else class="btn-loading">Signing in...</span>
        </button>
      </form>

      <div class="auth-divider">
        <span>or</span>
      </div>

      <button class="google-btn" type="button">
        <svg class="google-icon" viewBox="0 0 24 24" width="18" height="18">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign in with Google
      </button>

      <p class="auth-footer">
        Don't have an account?
        <router-link to="/signup" class="auth-link">Sign up</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.loginAction(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.error || e.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #0a0a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  background: #12122a;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 40px 36px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.auth-brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.1rem;
  letter-spacing: 2px;
  color: #fff;
  margin-bottom: 32px;
}

.auth-title {
  font-size: 1.6rem;
  font-weight: 600;
  color: #f0f0f0;
  margin: 0 0 8px 0;
}

.auth-subtitle {
  font-size: 0.9rem;
  color: #6b6b8a;
  margin: 0 0 28px 0;
}

.auth-error {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 20px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #9393b0;
  letter-spacing: 0.3px;
}

.form-input {
  background: #1a1a34;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.95rem;
  color: #e0e0f0;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}

.form-input::placeholder {
  color: #4a4a6a;
}

.form-input:focus {
  border-color: #4a7cff;
  box-shadow: 0 0 0 3px rgba(74, 124, 255, 0.15);
}

.auth-btn {
  margin-top: 4px;
  background: #4a7cff;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 13px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  font-family: inherit;
}

.auth-btn:hover:not(:disabled) {
  background: #3a6aee;
}

.auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
}

.auth-divider span {
  padding: 0 14px;
  font-size: 0.8rem;
  color: #5a5a7a;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.google-btn {
  width: 100%;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 12px;
  font-size: 0.9rem;
  color: #c0c0d8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: background 0.2s, border-color 0.2s;
  font-family: inherit;
}

.google-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.2);
}

.google-icon {
  flex-shrink: 0;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 0.85rem;
  color: #6b6b8a;
}

.auth-link {
  color: #4a7cff;
  text-decoration: none;
  font-weight: 500;
}

.auth-link:hover {
  text-decoration: underline;
}

@media (max-width: 480px) {
  .auth-card {
    padding: 32px 24px;
  }
}
</style>
