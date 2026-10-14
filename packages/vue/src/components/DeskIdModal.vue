<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import type { DeskIdClient } from '@deskid/core'

interface Props {
  modelValue: boolean
  client: DeskIdClient
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const modalContentRef = ref<HTMLElement | null>(null)
let previousActiveElement: HTMLElement | null = null

// Form mode: 'password' | 'otp'
const mode = ref<'password' | 'otp'>('password')

// State
const email = ref('')
const password = ref('')
const otpCode = ref('')
const otpStep = ref<'request' | 'verify'>('request')
const isLoading = ref(false)
const errorMessage = ref('')
const resendCooldown = ref(0)
let cooldownTimer: any = null

function close() {
  emit('update:modelValue', false)
}

function handleKeydown(e: KeyboardEvent) {
  if (!props.modelValue) return
  if (e.key === 'Escape') {
    close()
    return
  }

  // Focus trap
  if (e.key === 'Tab' && modalContentRef.value) {
    const focusable = modalContentRef.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    if (focusable.length === 0) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey && document.activeElement === first) {
      last.focus()
      e.preventDefault()
    } else if (!e.shiftKey && document.activeElement === last) {
      first.focus()
      e.preventDefault()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (cooldownTimer) clearInterval(cooldownTimer)
})

watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    previousActiveElement = document.activeElement as HTMLElement | null
    errorMessage.value = ''
    await nextTick()
    if (modalContentRef.value) {
      const input = modalContentRef.value.querySelector<HTMLElement>('input')
      if (input) input.focus()
    }
  } else {
    if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
      previousActiveElement.focus()
      previousActiveElement = null
    }
  }
})

async function handlePasswordLogin() {
  if (!email.value || !password.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    await props.client.login({
      email: email.value.trim(),
      password: password.value
    })
    close()
  } catch (err: any) {
    errorMessage.value = err?.error || err?.detail || 'Incorrect email or password. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function handleRequestOtp() {
  if (!email.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    await props.client.requestMagicLink(email.value.trim())
    otpStep.value = 'verify'
    startCooldown(60)
  } catch (err: any) {
    errorMessage.value = err?.error || 'Failed to send sign-in link. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function handleVerifyOtp() {
  if (!email.value || otpCode.value.length !== 6) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    await props.client.verifyOtp(email.value.trim(), otpCode.value.trim())
    close()
  } catch (err: any) {
    errorMessage.value = err?.error || 'Incorrect code. Please check your email or request a new code.'
  } finally {
    isLoading.value = false
  }
}

function startCooldown(seconds: number) {
  resendCooldown.value = seconds
  if (cooldownTimer) clearInterval(cooldownTimer)
  cooldownTimer = setInterval(() => {
    if (resendCooldown.value > 0) {
      resendCooldown.value -= 1
    } else {
      clearInterval(cooldownTimer)
      cooldownTimer = null
    }
  }, 1000)
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="deskid-modal-backdrop"
      @click.self="close"
    >
      <div
        ref="modalContentRef"
        role="dialog"
        aria-modal="true"
        aria-labelledby="deskid-modal-title"
        class="deskid-modal-card"
      >
        <!-- Modal Header -->
        <div class="deskid-modal-header">
          <div>
            <h2 id="deskid-modal-title" class="deskid-modal-title">Sign In</h2>
            <p class="deskid-modal-subtitle">Authenticate via DeskID secure identity</p>
          </div>
          <button
            type="button"
            aria-label="Close dialog"
            @click="close"
            class="deskid-modal-close"
          >
            &times;
          </button>
        </div>

        <!-- Mode Selector Tabs -->
        <div class="deskid-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'password'"
            @click="mode = 'password'; errorMessage = ''"
            :class="['deskid-tab', mode === 'password' ? 'active' : '']"
          >
            Password
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'otp'"
            @click="mode = 'otp'; errorMessage = ''"
            :class="['deskid-tab', mode === 'otp' ? 'active' : '']"
          >
            Email Link / OTP
          </button>
        </div>

        <!-- Error Message -->
        <div
          v-if="errorMessage"
          role="alert"
          aria-live="assertive"
          class="deskid-alert-error"
        >
          {{ errorMessage }}
        </div>

        <!-- Password Mode Form -->
        <div v-if="mode === 'password'">
          <form @submit.prevent="handlePasswordLogin" class="deskid-form">
            <div class="deskid-field">
              <label class="deskid-label" for="deskid-email">Email Address</label>
              <input
                id="deskid-email"
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="name@company.com"
                class="deskid-input"
              />
            </div>

            <div class="deskid-field">
              <label class="deskid-label" for="deskid-password">Password</label>
              <input
                id="deskid-password"
                v-model="password"
                type="password"
                required
                autocomplete="current-password"
                placeholder="••••••••"
                class="deskid-input"
              />
            </div>

            <button
              type="submit"
              :disabled="isLoading || !email || !password"
              class="deskid-submit-btn"
            >
              <span v-if="isLoading">Signing in...</span>
              <span v-else>Sign In</span>
            </button>
          </form>
        </div>

        <!-- OTP / Magic Link Form -->
        <div v-else>
          <!-- Step 1: Request -->
          <div v-if="otpStep === 'request'">
            <form @submit.prevent="handleRequestOtp" class="deskid-form">
              <div class="deskid-field">
                <label class="deskid-label" for="deskid-otp-email">Email Address</label>
                <input
                  id="deskid-otp-email"
                  v-model="email"
                  type="email"
                  required
                  autocomplete="email"
                  placeholder="name@company.com"
                  class="deskid-input"
                />
              </div>

              <button
                type="submit"
                :disabled="isLoading || !email"
                class="deskid-submit-btn"
              >
                <span v-if="isLoading">Sending Link...</span>
                <span v-else>Send Sign-in Link & Code</span>
              </button>
            </form>
          </div>

          <!-- Step 2: Verify Code -->
          <div v-else>
            <div class="deskid-info-box">
              Code sent to <strong>{{ email }}</strong>. Check your inbox!
            </div>

            <form @submit.prevent="handleVerifyOtp" class="deskid-form">
              <div class="deskid-field">
                <label class="deskid-label" for="deskid-otp-code">6-Digit Code</label>
                <input
                  id="deskid-otp-code"
                  v-model="otpCode"
                  type="text"
                  maxlength="6"
                  required
                  autocomplete="one-time-code"
                  placeholder="123456"
                  class="deskid-input deskid-input-code"
                />
              </div>

              <button
                type="submit"
                :disabled="isLoading || otpCode.length !== 6"
                class="deskid-submit-btn"
              >
                <span v-if="isLoading">Verifying...</span>
                <span v-else>Verify & Sign In</span>
              </button>

              <div class="deskid-actions">
                <button
                  type="button"
                  @click="otpStep = 'request'"
                  class="deskid-link-btn"
                >
                  Change email
                </button>

                <button
                  type="button"
                  @click="handleRequestOtp"
                  :disabled="resendCooldown > 0 || isLoading"
                  class="deskid-link-btn"
                >
                  <span v-if="resendCooldown > 0">Resend in {{ resendCooldown }}s</span>
                  <span v-else>Resend code</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.deskid-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background-color: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  font-family: system-ui, -apple-system, sans-serif;
}

.deskid-modal-card {
  position: relative;
  width: 100%;
  max-width: 26rem;
  background-color: #ffffff;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  border: 1px solid #e2e8f0;
  padding: 1.5rem;
  overflow: hidden;
}

.deskid-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.deskid-modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.deskid-modal-subtitle {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
  margin-bottom: 0;
}

.deskid-modal-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: #94a3b8;
  cursor: pointer;
  line-height: 1;
  padding: 0.25rem;
  border-radius: 0.375rem;
}

.deskid-modal-close:hover {
  color: #334155;
  background-color: #f1f5f9;
}

.deskid-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.25rem;
  background-color: #f1f5f9;
  padding: 0.25rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.deskid-tab {
  background: transparent;
  border: none;
  padding: 0.375rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.deskid-tab.active {
  background-color: #ffffff;
  color: #0f172a;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.deskid-alert-error {
  padding: 0.625rem;
  border-radius: 0.5rem;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  font-size: 0.75rem;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.deskid-info-box {
  padding: 0.625rem;
  border-radius: 0.5rem;
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
  font-size: 0.75rem;
  margin-bottom: 1rem;
}

.deskid-form {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.deskid-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.deskid-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #334155;
}

.deskid-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border-radius: 0.5rem;
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  color: #0f172a;
  outline: none;
  box-sizing: border-box;
}

.deskid-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.deskid-input-code {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 1.125rem;
  letter-spacing: 0.25em;
  text-align: center;
}

.deskid-submit-btn {
  width: 100%;
  padding: 0.625rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background-color: #4f46e5;
  color: #ffffff;
  border: none;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.deskid-submit-btn:hover:not(:disabled) {
  background-color: #4338ca;
}

.deskid-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.deskid-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.deskid-link-btn {
  background: transparent;
  border: none;
  font-size: 0.75rem;
  color: #4f46e5;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.deskid-link-btn:disabled {
  color: #94a3b8;
  cursor: not-allowed;
  text-decoration: none;
}
</style>
