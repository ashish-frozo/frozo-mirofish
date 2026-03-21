<template>
  <div class="login-page">
    <!-- Decorative Background Elements -->
    <div class="bg-orb bg-orb--top"></div>
    <div class="bg-orb bg-orb--bottom"></div>

    <!-- Brand Header -->
    <header class="login-header">
      <h1 class="login-brand">AUGUR</h1>
    </header>

    <!-- Main Login Canvas -->
    <main class="login-main">
      <div class="login-card">
        <div class="login-card__header">
          <h2 class="login-card__title">Welcome back</h2>
          <p class="login-card__subtitle">Predict what's next with Augur AI.</p>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="login-error" role="alert">{{ error }}</div>

        <!-- Login Form -->
        <form class="login-form" @submit.prevent="handleLogin">
          <!-- Email Field -->
          <div class="form-field">
            <label class="form-label" for="email">Email Address</label>
            <div class="input-wrap">
              <input
                id="email"
                v-model="email"
                type="email"
                class="form-input"
                placeholder="name@company.com"
                required
                autocomplete="email"
              />
            </div>
          </div>

          <!-- Password Field -->
          <div class="form-field">
            <div class="form-label-row">
              <label class="form-label" for="password">Password</label>
              <a href="#" class="forgot-link">Forgot?</a>
            </div>
            <div class="input-wrap">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                placeholder="Enter your password"
                required
                autocomplete="current-password"
              />
              <button
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
              >
                <span class="material-symbols-outlined toggle-password__icon">
                  {{ showPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <!-- Primary CTA -->
          <button type="submit" class="login-btn" :disabled="loading">
            <span v-if="!loading">Sign In</span>
            <span v-else class="btn-loading">Signing in...</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="login-divider">
          <div class="login-divider__line"></div>
          <span class="login-divider__text">Or continue with</span>
          <div class="login-divider__line"></div>
        </div>

        <!-- Social Auth -->
        <button class="google-btn" type="button">
          <svg class="google-icon" viewBox="0 0 24 24" width="18" height="18">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span>Sign in with Google</span>
        </button>
      </div>

      <!-- Secondary Navigation -->
      <div class="login-secondary">
        <p>
          Don't have an account?
          <router-link to="/signup" class="signup-link">Sign up</router-link>
        </p>
      </div>
    </main>

    <!-- Footer -->
    <footer class="login-footer">
      <a href="#">Terms</a>
      <a href="#">Privacy</a>
      <a href="#">Help</a>
    </footer>
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
const showPassword = ref(false)

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
/* ── Page Shell ── */
.login-page {
  min-height: 100vh;
  background: #F8FAFC;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: 'Inter', system-ui, sans-serif;
  color: #191c1e;
  position: relative;
  overflow: hidden;
}

/* ── Decorative Background ── */
.bg-orb {
  position: fixed;
  width: 384px;
  height: 384px;
  border-radius: 50%;
  filter: blur(48px);
  pointer-events: none;
}

.bg-orb--top {
  top: -96px;
  left: -96px;
  background: rgba(53, 37, 205, 0.05);
}

.bg-orb--bottom {
  bottom: -96px;
  right: -96px;
  background: rgba(113, 42, 226, 0.05);
}

/* ── Brand Header ── */
.login-header {
  margin-bottom: 40px;
  text-align: center;
}

.login-brand {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.875rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #3525CD;
  margin: 0;
}

/* ── Login Main ── */
.login-main {
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
}

/* ── Login Card ── */
.login-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.06);
  padding: 32px 40px;
}

.login-card__header {
  margin-bottom: 32px;
}

.login-card__title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  color: #191c1e;
  margin: 0 0 4px 0;
}

.login-card__subtitle {
  font-size: 0.875rem;
  color: #464555;
  margin: 0;
}

/* ── Error ── */
.login-error {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  color: #DC2626;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 20px;
}

/* ── Form ── */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #464555;
  margin: 0;
}

.form-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forgot-link {
  font-size: 10px;
  font-weight: 700;
  color: #3525CD;
  text-decoration: none;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: color 200ms;
}

.forgot-link:hover {
  color: #4F46E5;
}

.input-wrap {
  position: relative;
}

.form-input {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  background: #ffffff;
  border: none;
  box-shadow: inset 0 0 0 1px rgba(199, 196, 216, 0.2);
  border-radius: 12px;
  font-size: 0.875rem;
  color: #191c1e;
  font-family: inherit;
  outline: none;
  transition: box-shadow 200ms;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: rgba(119, 117, 135, 0.5);
}

.form-input:focus {
  box-shadow: inset 0 0 0 2px #3525CD;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #464555;
  transition: color 200ms;
}

.toggle-password:hover {
  color: #3525CD;
}

.toggle-password__icon {
  font-size: 20px;
}

/* ── Login Button ── */
.login-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #3525CD 0%, #4F46E5 100%);
  color: #ffffff;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-weight: 700;
  font-size: 0.9375rem;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(53, 37, 205, 0.2);
  transition: transform 200ms, opacity 200ms;
}

.login-btn:hover:not(:disabled) {
  transform: scale(0.98);
}

.login-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* ── Divider ── */
.login-divider {
  display: flex;
  align-items: center;
  margin: 32px 0;
  gap: 12px;
}

.login-divider__line {
  flex: 1;
  height: 1px;
  background: #eceef0;
}

.login-divider__text {
  font-size: 0.75rem;
  color: #464555;
  font-weight: 500;
  white-space: nowrap;
}

/* ── Google Button ── */
.google-btn {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #ffffff;
  border: 1px solid rgba(199, 196, 216, 0.3);
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  color: #191c1e;
  font-family: inherit;
  transition: background 200ms;
}

.google-btn:hover {
  background: #f2f4f6;
}

.google-icon {
  flex-shrink: 0;
}

/* ── Secondary ── */
.login-secondary {
  margin-top: 32px;
  text-align: center;
}

.login-secondary p {
  font-size: 0.875rem;
  color: #464555;
  margin: 0;
}

.signup-link {
  color: #3525CD;
  font-weight: 600;
  text-decoration: none;
  margin-left: 4px;
}

.signup-link:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
  text-decoration-thickness: 2px;
}

/* ── Footer ── */
.login-footer {
  position: fixed;
  bottom: 32px;
  display: flex;
  gap: 24px;
}

.login-footer a {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #94A3B8;
  text-decoration: none;
  transition: color 200ms;
}

.login-footer a:hover {
  color: #4F46E5;
}

/* ── Responsive ── */
@media (max-width: 480px) {
  .login-card {
    padding: 28px 24px;
  }

  .login-brand {
    font-size: 1.5rem;
  }

  .login-footer {
    position: relative;
    bottom: auto;
    margin-top: 48px;
  }
}
</style>
