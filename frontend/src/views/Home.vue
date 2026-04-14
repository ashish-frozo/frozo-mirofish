<template>
  <div class="home-page">
    <!-- Top Navigation Bar -->
    <nav class="top-nav">
      <div class="top-nav__brand">AUGUR</div>
      <div class="top-nav__right">
        <router-link to="/dashboard" class="top-nav__link">
          <span class="material-symbols-outlined top-nav__link-icon">arrow_back</span>
          Back to Dashboard
        </router-link>
      </div>
    </nav>

    <!-- Main Content Canvas -->
    <main class="main-content">
      <div class="content-inner">
        <!-- Header Section -->
        <header class="page-header">
          <h1 class="page-title">Create a New Prediction</h1>
          <p class="page-subtitle">Describe what you want to predict. Adding documents is optional — they make predictions more grounded.</p>
        </header>

        <!-- Creation Form -->
        <section class="creation-form">
          <!-- Upload Zone -->
          <div class="form-section">
            <div class="section-label-row">
              <label class="section-label">Context Documents <span class="optional-tag">Optional</span></label>
              <span class="section-hint">Skip to run in Quick Mode</span>
            </div>
            <div
              class="upload-zone"
              :class="{
                'upload-zone--hover': isDragOver,
                'upload-zone--filled': files.length > 0
              }"
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
                class="upload-zone__input"
                :disabled="predicting"
              />

              <div v-if="files.length === 0" class="upload-placeholder">
                <span class="material-symbols-outlined upload-placeholder__icon" style="font-variation-settings: 'FILL' 1;">cloud_upload</span>
                <p class="upload-placeholder__title">Drag & drop files here or click to browse</p>
                <p class="upload-placeholder__hint">PDF, TXT, MD — or skip to let the LLM synthesize a brief from your prompt</p>
              </div>
            </div>

            <!-- File Chips -->
            <div v-if="files.length > 0" class="file-chips">
              <div
                v-for="(file, index) in files"
                :key="index"
                class="file-chip"
              >
                <span class="material-symbols-outlined file-chip__icon">description</span>
                <span class="file-chip__name">{{ file.name }}</span>
                <button
                  class="file-chip__remove"
                  @click="removeFile(index)"
                  :aria-label="'Remove ' + file.name"
                >
                  <span class="material-symbols-outlined file-chip__remove-icon">close</span>
                </button>
              </div>
              <button class="file-chip file-chip--add" @click="triggerFileInput">
                <span class="material-symbols-outlined file-chip__icon">add</span>
                Add more
              </button>
            </div>
          </div>

          <!-- URL Input -->
          <div class="form-section">
            <div class="section-label-row">
              <label class="section-label" for="source-urls">Source URLs <span class="optional-tag">Optional</span></label>
              <span class="section-hint">Up to 5 article URLs — we'll fetch and extract the text</span>
            </div>
            <textarea
              id="source-urls"
              v-model="formData.urls"
              class="url-textarea"
              placeholder="https://example.com/article-1&#10;https://example.com/article-2"
              rows="3"
              :disabled="predicting"
            ></textarea>
            <p v-if="invalidUrlCount > 0" class="field-warning">
              {{ invalidUrlCount }} line(s) don't look like http(s) URLs and will be ignored.
            </p>
          </div>

          <!-- Text Area Input -->
          <div class="form-section">
            <div class="section-label-row">
              <label class="section-label" for="prediction-query">What do you want to predict?</label>
              <span class="char-count">{{ formData.simulationRequirement.length }} / 5000</span>
            </div>
            <textarea
              id="prediction-query"
              v-model="formData.simulationRequirement"
              class="prediction-textarea"
              placeholder="e.g. How will developers, investors, and regulators react to the GPT-5 release over the next 30 days?"
              rows="5"
              :disabled="predicting"
            ></textarea>

            <!-- Example Prompt Chips -->
            <div class="example-chips">
              <span class="example-chips__label">Examples:</span>
              <button
                v-for="(prompt, i) in examplePrompts"
                :key="i"
                class="example-chip"
                @click="formData.simulationRequirement = prompt"
              >{{ prompt }}</button>
            </div>
          </div>

          <!-- Action Button -->
          <div class="action-section">
            <button
              class="submit-btn"
              @click="startOneClickPredict"
              :disabled="!canSubmit || predicting"
            >
              <span v-if="!predicting">{{ isQuickMode ? 'Start Prediction (Quick Mode)' : 'Start Prediction' }}</span>
              <span v-else>Starting...</span>
              <span v-if="!predicting" class="material-symbols-outlined submit-btn__icon">auto_awesome</span>
              <span v-else class="spinner"></span>
            </button>
            <p class="action-hint">
              <template v-if="isQuickMode">
                Quick Mode: we'll synthesize a brief from your prompt. For more grounded predictions, attach documents or add URLs.
              </template>
              <template v-else>
                Using {{ files.length }} file(s) and {{ parsedUrls.length }} URL(s). Processing typically takes 3-10 minutes — we'll email you when it's ready.
              </template>
            </p>
          </div>

          <!-- Error Message -->
          <p v-if="error" class="error-msg">{{ error }}</p>
        </section>
      </div>
    </main>

    <!-- Bottom Decorative Gradient -->
    <div class="bottom-gradient"></div>
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
  simulationRequirement: '',
  urls: ''
})

// Parse URLs: split on newline/comma/space, keep only http(s), cap at 5
const parsedUrls = computed(() => {
  const lines = (formData.value.urls || '')
    .split(/[\s,]+/)
    .map(s => s.trim())
    .filter(Boolean)
  const valid = lines.filter(l => /^https?:\/\//i.test(l))
  return valid.slice(0, 5)
})

const invalidUrlCount = computed(() => {
  const lines = (formData.value.urls || '')
    .split(/[\s,]+/)
    .map(s => s.trim())
    .filter(Boolean)
  return lines.length - lines.filter(l => /^https?:\/\//i.test(l)).length
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

// Computed: can submit — prompt is required; files are optional (Quick Mode)
const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== ''
})

// Quick Mode = no grounding sources (neither files nor URLs)
const isQuickMode = computed(() => files.value.length === 0 && parsedUrls.value.length === 0)

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
    if (parsedUrls.value.length > 0) {
      fd.append('urls', parsedUrls.value.join('\n'))
    }

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
/* ── Page Shell ── */
.home-page {
  min-height: 100vh;
  background: #F8FAFC;
  font-family: 'Inter', system-ui, sans-serif;
  color: #191c1e;
}

/* ── Top Navigation ── */
.top-nav {
  position: fixed;
  top: 0;
  width: 100%;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 64px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.06);
}

.top-nav__brand {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: #4338CA;
  text-transform: uppercase;
}

.top-nav__right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.top-nav__link {
  color: #475569;
  font-weight: 500;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: color 200ms;
  font-size: 0.875rem;
}

.top-nav__link:hover {
  color: #4F46E5;
}

.top-nav__link-icon {
  font-size: 18px;
}

/* ── Main Content ── */
.main-content {
  padding-top: 128px;
  padding-bottom: 96px;
  padding-left: 24px;
  padding-right: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.content-inner {
  width: 100%;
  max-width: 640px;
}

/* ── Page Header ── */
.page-header {
  margin-bottom: 48px;
  text-align: center;
}

.page-title {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  color: #191c1e;
  letter-spacing: -1px;
  margin: 0 0 16px 0;
  line-height: 1.1;
}

.page-subtitle {
  font-size: 1.125rem;
  color: #464555;
  font-weight: 500;
  margin: 0;
}

/* ── Creation Form ── */
.creation-form {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-label {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #464555;
  display: block;
}

.section-label-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.char-count {
  font-size: 0.75rem;
  font-weight: 500;
  color: #777587;
}

.optional-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 6px;
  background: #EEF2FF;
  color: #4338CA;
  font-size: 0.625rem;
  font-weight: 600;
  border-radius: 3px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.section-hint {
  font-size: 0.75rem;
  font-weight: 500;
  color: #777587;
}

.url-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #D9D7E1;
  border-radius: 8px;
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.8125rem;
  resize: vertical;
  background: #FFF;
  color: #191c1e;
  box-sizing: border-box;
  transition: border-color 0.15s;
}

.url-textarea:focus {
  outline: none;
  border-color: #4338CA;
}

.url-textarea:disabled {
  background: #F5F5F7;
  cursor: not-allowed;
}

.field-warning {
  margin-top: 6px;
  font-size: 0.75rem;
  color: #B45309;
}

/* ── Upload Zone ── */
.upload-zone {
  position: relative;
  width: 100%;
  height: 192px;
  border-radius: 12px;
  border: 2px dashed rgba(199, 196, 216, 0.4);
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 300ms;
}

.upload-zone:hover {
  background: rgba(226, 223, 255, 0.2);
  border-color: #4F46E5;
}

.upload-zone--hover {
  background: rgba(226, 223, 255, 0.3);
  border-color: #4F46E5;
  border-style: solid;
}

.upload-zone--filled {
  height: auto;
  min-height: 80px;
  border-style: solid;
  border-color: rgba(199, 196, 216, 0.4);
  background: transparent;
  cursor: default;
}

.upload-zone__input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  pointer-events: none;
}

.upload-placeholder__icon {
  font-size: 2.5rem;
  color: #4F46E5;
  margin-bottom: 12px;
}

.upload-placeholder__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #191c1e;
  margin: 0;
}

.upload-placeholder__hint {
  font-size: 0.875rem;
  color: #777587;
  margin: 4px 0 0 0;
}

/* ── File Chips ── */
.file-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f2f4f6;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #191c1e;
  transition: background 200ms;
  border: none;
  font-family: inherit;
}

.file-chip:hover {
  background: #e6e8ea;
}

.file-chip__icon {
  font-size: 16px;
  color: #3525CD;
}

.file-chip__name {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-chip__remove {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  margin-left: 4px;
  color: #777587;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: color 200ms;
}

.file-chip__remove:hover {
  color: #BA1A1A;
}

.file-chip__remove-icon {
  font-size: 14px;
}

.file-chip--add {
  cursor: pointer;
  color: #3525CD;
  background: transparent;
  border: 1px dashed rgba(199, 196, 216, 0.4);
}

.file-chip--add:hover {
  background: rgba(226, 223, 255, 0.2);
}

/* ── Prediction Textarea ── */
.prediction-textarea {
  width: 100%;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid rgba(199, 196, 216, 0.2);
  padding: 16px;
  font-size: 1rem;
  color: #191c1e;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 200ms, box-shadow 200ms;
  box-sizing: border-box;
  line-height: 1.6;
}

.prediction-textarea::placeholder {
  color: rgba(119, 117, 135, 0.6);
}

.prediction-textarea:focus {
  border-color: #3525CD;
  box-shadow: 0 0 0 4px #E2DFFF;
}

.prediction-textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Example Chips ── */
.example-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.example-chips__label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #c7c4d8;
  text-transform: uppercase;
  margin-right: 4px;
}

.example-chip {
  padding: 4px 12px;
  background: #EADDFF;
  color: #25005A;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: background 200ms;
}

.example-chip:hover {
  background: #D2BBFF;
}

/* ── Action Section ── */
.action-section {
  padding-top: 8px;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #4F46E5, #3525CD);
  color: #ffffff;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  font-weight: 700;
  font-size: 1.125rem;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 20px 40px rgba(79, 70, 229, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  transition: transform 200ms, opacity 200ms;
}

.submit-btn:hover:not(:disabled) {
  transform: scale(1.01);
}

.submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.submit-btn__icon {
  font-size: 20px;
}

.action-hint {
  text-align: center;
  font-size: 0.75rem;
  color: #777587;
  margin: 16px 0 0 0;
  font-weight: 500;
  font-style: italic;
}

/* ── Spinner ── */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Error ── */
.error-msg {
  text-align: center;
  font-size: 0.875rem;
  color: #BA1A1A;
  padding: 12px 16px;
  background: rgba(255, 218, 214, 0.3);
  border-radius: 8px;
  margin: 0;
}

/* ── Bottom Gradient ── */
.bottom-gradient {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(to right, transparent, rgba(79, 70, 229, 0.2), transparent);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .top-nav {
    padding: 0 16px;
  }

  .main-content {
    padding-top: 96px;
    padding-bottom: 64px;
    padding-left: 16px;
    padding-right: 16px;
  }

  .page-title {
    font-size: 1.75rem;
  }

  .page-subtitle {
    font-size: 1rem;
  }

  .upload-zone {
    height: 160px;
  }

  .file-chip__name {
    max-width: 120px;
  }

  .example-chip {
    font-size: 0.6875rem;
    padding: 4px 10px;
  }
}

@media (min-width: 769px) {
  .page-header {
    text-align: left;
  }
}
</style>
