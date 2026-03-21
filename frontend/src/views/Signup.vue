<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">AUGUR</div>
      <h1 class="auth-title">Create your account</h1>
      <p class="auth-subtitle">Get started with Augur simulation engine</p>

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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

.auth-page {
  min-height: 100vh;
  background: #F8FAFC;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: 'Inter', system-ui, sans-serif;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 4px 24px rgba(79, 70, 229, 0.08);
}

.auth-brand {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-weight: 800;
  font-size: 1.5rem;
  letter-spacing: 1.5px;
  color: #4F46E5;
  margin-bottom: 28px;
}

.auth-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 8px 0;
}

.auth-subtitle {
  font-size: 0.9rem;
  color: #64748B;
  margin: 0 0 28px 0;
  line-height: 1.5;
}

.auth-error {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #DC2626;
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
  color: #64748B;
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-hint {
  font-size: 0.75rem;
  color: #94A3B8;
  font-weight: 400;
  transition: color 0.2s;
}

.label-hint.valid {
  color: #16A34A;
}

.form-input {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.95rem;
  color: #0F172A;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  font-family: inherit;
}

.form-input::placeholder {
  color: #94A3B8;
}

.form-input:focus {
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
}

.auth-btn {
  margin-top: 4px;
  background: #4F46E5;
  color: #FFFFFF;
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
  background: #4338CA;
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
  color: #64748B;
}

.auth-link {
  color: #4F46E5;
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
