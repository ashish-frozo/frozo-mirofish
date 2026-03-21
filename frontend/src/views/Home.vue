<template>
  <div class="home-page">
    <!-- Navigation Bar -->
    <nav class="nav-bar">
      <div class="nav-inner">
        <div class="nav-brand">AUGUR</div>
        <div class="nav-links">
          <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
          <router-link to="/login" class="nav-link nav-link--accent">Login</router-link>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-area">
      <div class="content-card">
        <!-- Header -->
        <div class="card-header">
          <div class="brand-icon">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="url(#icon-grad)" />
              <path d="M20 10L28 26H12L20 10Z" fill="white" opacity="0.9" />
              <circle cx="20" cy="26" r="4" fill="white" opacity="0.7" />
              <defs>
                <linearGradient id="icon-grad" x1="0" y1="0" x2="40" y2="40">
                  <stop stop-color="#4F46E5" />
                  <stop offset="1" stop-color="#7C3AED" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 class="card-title">Start a New Prediction</h1>
          <p class="card-subtitle">Upload documents and describe your scenario</p>
        </div>

        <!-- Upload Zone -->
        <div
          class="upload-zone"
          :class="{ 'upload-zone--hover': isDragOver, 'upload-zone--filled': files.length > 0 }"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
          role="button"
          tabindex="0"
          aria-label="Upload files by dragging or clicking"
          @keydown.enter="triggerFileInput"
          @keydown.space.prevent="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.md,.txt"
            @change="handleFileSelect"
            style="display: none"
            :disabled="predicting"
          />

          <div v-if="files.length === 0" class="upload-placeholder">
            <div class="upload-icon-wrap">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <div class="upload-label">Drag & drop files here</div>
            <div class="upload-hint">or click to browse</div>
            <div class="upload-formats">PDF, TXT, MD supported</div>
          </div>

          <div v-else class="file-grid" @click.stop>
            <!-- Prevent zone click when interacting with chips -->
          </div>
        </div>

        <!-- File Chips -->
        <div v-if="files.length > 0" class="file-chips">
          <div v-for="(file, index) in files" :key="index" class="file-chip">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span class="file-chip-name">{{ file.name }}</span>
            <button
              class="file-chip-remove"
              @click="removeFile(index)"
              :aria-label="'Remove ' + file.name"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <button class="file-chip file-chip--add" @click="triggerFileInput">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add more
          </button>
        </div>

        <!-- Textarea -->
        <div class="field-group">
          <label class="field-label" for="prediction-input">Prediction Requirement</label>
          <textarea
            id="prediction-input"
            v-model="formData.simulationRequirement"
            class="field-textarea"
            placeholder="Describe what you want to predict..."
            rows="4"
            :disabled="predicting"
          ></textarea>
        </div>

        <!-- Example Prompts -->
        <div class="examples">
          <span class="examples-label">Example prompts:</span>
          <div class="examples-list">
            <button
              v-for="(prompt, i) in examplePrompts"
              :key="i"
              class="example-chip"
              @click="formData.simulationRequirement = prompt"
            >{{ prompt }}</button>
          </div>
        </div>

        <!-- CTA Button -->
        <button
          class="cta-button"
          @click="startOneClickPredict"
          :disabled="!canSubmit || predicting"
        >
          <span v-if="!predicting">Start Prediction</span>
          <span v-else>Starting...</span>
          <svg v-if="!predicting" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
          <span v-else class="spinner"></span>
        </button>
        <p class="cta-hint">Runs all 5 steps automatically</p>

        <!-- Error Message -->
        <p v-if="error" class="error-msg">{{ error }}</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()

onMounted(() => {
  // Only redirect to dashboard from the public home page (/), not from /new
  if (auth.isAuthenticated && router.currentRoute.value.path === '/') {
    router.replace('/dashboard')
  }
})

// Form data
const formData = ref({
  simulationRequirement: ''
})

// File list
const files = ref([])

// State
const predicting = ref(false)
const error = ref('')
const isDragOver = ref(false)

// File input ref
const fileInput = ref(null)

// Example prompts
const examplePrompts = [
  'How will developers react to GPT-5?',
  'Impact of new EU AI regulation on startups',
  'Public sentiment on climate policy changes',
  'Market response to a major tech layoff announcement'
]

// Computed: can submit
const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== '' && files.value.length > 0
})

// Trigger file selection
const triggerFileInput = () => {
  if (!predicting.value) {
    fileInput.value?.click()
  }
}

// Handle file selection
const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
}

// Handle drag events
const handleDragOver = () => {
  if (!predicting.value) {
    isDragOver.value = true
  }
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (e) => {
  isDragOver.value = false
  if (predicting.value) return

  const droppedFiles = Array.from(e.dataTransfer.files)
  addFiles(droppedFiles)
}

// Add files
const addFiles = (newFiles) => {
  const validFiles = newFiles.filter(file => {
    const ext = file.name.split('.').pop().toLowerCase()
    return ['pdf', 'md', 'txt'].includes(ext)
  })
  files.value.push(...validFiles)
}

// Remove file
const removeFile = (index) => {
  files.value.splice(index, 1)
}

// One-Click Predict - upload files and start full prediction pipeline
const startOneClickPredict = async () => {
  if (!canSubmit.value || predicting.value) return

  predicting.value = true
  error.value = ''
  try {
    const { startPrediction } = await import('../api/predict.js')
    const fd = new FormData()
    files.value.forEach(file => fd.append('files', file))
    fd.append('simulation_requirement', formData.value.simulationRequirement)

    const res = await startPrediction(fd)
    const taskId = res.data.task_id
    router.push({ name: 'PredictionProgress', params: { taskId } })
  } catch (err) {
    error.value = err.message || 'Failed to start prediction'
    predicting.value = false
  }
}
</script>

<style scoped>
/* ========================================
   Home Page — Augur Design System
   Clean, light, professional SaaS aesthetic
   ======================================== */

.home-page {
  min-height: 100vh;
  background: var(--bg, #F8FAFC);
  font-family: var(--font-body, 'Inter', system-ui, sans-serif);
  color: var(--text, #0F172A);
}

/* Navigation */
.nav-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--surface, #FFFFFF);
  border-bottom: 1px solid var(--border, #E2E8F0);
  backdrop-filter: blur(8px);
}

.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  font-family: var(--font-brand, 'Plus Jakarta Sans', system-ui, sans-serif);
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1.5px;
  color: var(--primary, #4F46E5);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  font-size: 14px;
  font-weight: 500;
  color: var(--muted, #64748B);
  text-decoration: none;
  padding: 6px 14px;
  border-radius: var(--radius-md, 8px);
  transition: color var(--transition-fast, 150ms ease-out), background var(--transition-fast, 150ms ease-out);
}

.nav-link:hover {
  color: var(--text, #0F172A);
  background: rgba(79, 70, 229, 0.04);
}

.nav-link--accent {
  color: var(--primary, #4F46E5);
  font-weight: 600;
}

.nav-link--accent:hover {
  background: rgba(79, 70, 229, 0.08);
  color: var(--primary-hover, #4338CA);
}

/* Main Content Area */
.main-area {
  max-width: 720px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}

/* Content Card */
.content-card {
  background: var(--surface, #FFFFFF);
  border-radius: var(--radius-xl, 16px);
  border: 1px solid var(--border, #E2E8F0);
  box-shadow: var(--shadow-card, 0 1px 3px rgba(79, 70, 229, 0.08));
  padding: 48px 40px;
}

/* Header */
.card-header {
  text-align: center;
  margin-bottom: 36px;
}

.brand-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.card-title {
  font-family: var(--font-brand, 'Plus Jakarta Sans', system-ui, sans-serif);
  font-size: 32px;
  font-weight: 700;
  color: var(--text, #0F172A);
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 16px;
  font-weight: 400;
  color: var(--muted, #64748B);
  margin: 0;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed var(--border, #E2E8F0);
  border-radius: var(--radius-xl, 16px);
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: border-color var(--transition-normal, 200ms ease-out),
              background var(--transition-normal, 200ms ease-out);
  background: var(--bg, #F8FAFC);
}

.upload-zone:hover {
  border-color: var(--primary, #4F46E5);
  background: rgba(79, 70, 229, 0.02);
}

.upload-zone--hover {
  border-color: var(--primary, #4F46E5);
  background: rgba(79, 70, 229, 0.05);
  border-style: solid;
}

.upload-zone--filled {
  padding: 20px 24px;
  border-style: solid;
  border-color: var(--border, #E2E8F0);
  background: transparent;
  cursor: default;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.upload-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: rgba(79, 70, 229, 0.08);
  color: var(--primary, #4F46E5);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.upload-label {
  font-weight: 600;
  font-size: 15px;
  color: var(--text, #0F172A);
}

.upload-hint {
  font-size: 14px;
  color: var(--muted, #64748B);
}

.upload-formats {
  font-size: 12px;
  color: #94A3B8;
  margin-top: 4px;
}

/* File Chips */
.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  margin-bottom: 4px;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg, #F8FAFC);
  border: 1px solid var(--border, #E2E8F0);
  border-radius: var(--radius-pill, 999px);
  font-size: 13px;
  font-weight: 500;
  color: var(--text, #0F172A);
  line-height: 1;
}

.file-chip svg {
  color: var(--muted, #64748B);
  flex-shrink: 0;
}

.file-chip-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-chip-remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  color: #94A3B8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast, 150ms ease-out), background var(--transition-fast, 150ms ease-out);
}

.file-chip-remove:hover {
  color: var(--error, #EF4444);
  background: rgba(239, 68, 68, 0.08);
}

.file-chip--add {
  cursor: pointer;
  color: var(--primary, #4F46E5);
  border-style: dashed;
  background: transparent;
  font-family: var(--font-body, 'Inter', system-ui, sans-serif);
  transition: background var(--transition-fast, 150ms ease-out);
}

.file-chip--add:hover {
  background: rgba(79, 70, 229, 0.04);
}

/* Textarea Field */
.field-group {
  margin-top: 24px;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text, #0F172A);
  margin-bottom: 8px;
}

.field-textarea {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--border, #E2E8F0);
  border-radius: var(--radius-md, 8px);
  font-family: var(--font-body, 'Inter', system-ui, sans-serif);
  font-size: 15px;
  line-height: 1.6;
  color: var(--text, #0F172A);
  background: var(--surface, #FFFFFF);
  resize: vertical;
  outline: none;
  transition: border-color var(--transition-fast, 150ms ease-out), box-shadow var(--transition-fast, 150ms ease-out);
  box-sizing: border-box;
}

.field-textarea::placeholder {
  color: #94A3B8;
}

.field-textarea:focus {
  border-color: var(--primary, #4F46E5);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.field-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Example Prompts */
.examples {
  margin-top: 20px;
}

.examples-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--muted, #64748B);
  display: block;
  margin-bottom: 8px;
}

.examples-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-chip {
  padding: 6px 14px;
  border: 1px solid var(--border, #E2E8F0);
  border-radius: var(--radius-pill, 999px);
  background: var(--surface, #FFFFFF);
  font-family: var(--font-body, 'Inter', system-ui, sans-serif);
  font-size: 13px;
  font-weight: 500;
  color: var(--muted, #64748B);
  cursor: pointer;
  transition: all var(--transition-fast, 150ms ease-out);
  white-space: nowrap;
}

.example-chip:hover {
  border-color: var(--primary, #4F46E5);
  color: var(--primary, #4F46E5);
  background: rgba(79, 70, 229, 0.04);
}

/* CTA Button */
.cta-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  height: 48px;
  margin-top: 32px;
  border: none;
  border-radius: var(--radius-lg, 12px);
  background: linear-gradient(135deg, var(--primary, #4F46E5) 0%, var(--secondary, #7C3AED) 100%);
  color: #FFFFFF;
  font-family: var(--font-body, 'Inter', system-ui, sans-serif);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform var(--transition-fast, 150ms ease-out),
              box-shadow var(--transition-fast, 150ms ease-out),
              opacity var(--transition-fast, 150ms ease-out);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}

.cta-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(79, 70, 229, 0.4);
}

.cta-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}

.cta-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.cta-hint {
  text-align: center;
  font-size: 13px;
  color: #94A3B8;
  margin-top: 10px;
}

/* Spinner */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #FFFFFF;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error Message */
.error-msg {
  text-align: center;
  font-size: 14px;
  color: var(--error, #EF4444);
  margin-top: 12px;
  padding: 10px 16px;
  background: rgba(239, 68, 68, 0.06);
  border-radius: var(--radius-md, 8px);
}

/* Responsive */
@media (max-width: 640px) {
  .main-area {
    padding: 24px 16px 60px;
  }

  .content-card {
    padding: 32px 20px;
  }

  .card-title {
    font-size: 26px;
  }

  .card-subtitle {
    font-size: 14px;
  }

  .upload-zone {
    padding: 32px 16px;
  }

  .example-chip {
    font-size: 12px;
    padding: 5px 12px;
  }

  .file-chip-name {
    max-width: 120px;
  }

  .nav-inner {
    padding: 0 16px;
  }
}
</style>
