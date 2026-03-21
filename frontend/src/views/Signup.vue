<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">FROZO</div>
      <h1 class="auth-title">Create your account</h1>
      <p class="auth-subtitle">Get started with Frozo simulation engine</p>

      <div v-if="error" class="auth-error">{{ error }}</div>

      <form class="auth-form" @submit.prevent="handleSignup">
        <div class="form-group">
          <label for="name" class="form-label">Name</label>
          <input
            id="name"
            v-model="name"
            type="text"
            class="form-input"
            placeholder="Your full name"
            required
            autocomplete="name"
          />
        </div>

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
          <label for="password" class="form-label">
            Password
            <span class="label-hint" :class="{ valid: password.length >= 8 }">
              (min 8 characters)
            </span>
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="Create a password"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword" class="form-label">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            class="form-input"
            placeholder="Repeat your password"
            required
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="auth-btn" :disabled="loading">
          <span v-if="!loading">Create Account</span>
          <span v-else class="btn-loading">Creating account...</span>
        </button>
      </form>

      <p class="auth-footer">
        Already have an account?
        <router-link to="/login" class="auth-link">Sign in</router-link>
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
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleSignup() {
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await auth.signupAction(email.value, name.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.error || e.message || 'Signup failed'
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
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-hint {
  font-size: 0.75rem;
  color: #5a5a7a;
  font-weight: 400;
  transition: color 0.2s;
}

.label-hint.valid {
  color: #4ade80;
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

.auth-footer {
  text-align: center;
  margin-top: 28px;
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
