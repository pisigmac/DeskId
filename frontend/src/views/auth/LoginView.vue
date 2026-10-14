<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api/client'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'
import { getHumanErrorMessage } from '@/utils/errors'
import {
  Mail,
  Lock,
  LogIn,
  AlertCircle,
  Sparkles,
  KeyRound,
  CheckCircle2,
  ArrowLeft,
  RotateCw
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// Modes: 'password' | 'passwordless'
const authMode = ref<'password' | 'passwordless'>('password')

// Password mode state
const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

// Passwordless (Magic Link / OTP) state
const otpEmail = ref('')
const otpCode = ref('')
const otpStep = ref<'request' | 'verify'>('request')
const isOtpLoading = ref(false)
const resendCooldown = ref(0)
let cooldownTimer: number | null = null

function getRedirectPath() {
  return (route.query.redirect as string) || (auth.isPlatformAdmin ? '/admin' : '/account/profile')
}

// ---------------------------------------------------------------------------
// Password Authentication
// ---------------------------------------------------------------------------
async function handlePasswordLogin() {
  if (!email.value || !password.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    await auth.login({
      email: email.value.trim(),
      password: password.value
    })
    router.push(getRedirectPath())
  } catch (err: any) {
    errorMessage.value = getHumanErrorMessage(err, { context: 'login' })
  } finally {
    isLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Passwordless Authentication (Magic Link & OTP)
// ---------------------------------------------------------------------------
function startResendCooldown(seconds: number = 60) {
  resendCooldown.value = seconds
  if (cooldownTimer) clearInterval(cooldownTimer)
  cooldownTimer = window.setInterval(() => {
    if (resendCooldown.value > 0) {
      resendCooldown.value -= 1
    } else {
      if (cooldownTimer) clearInterval(cooldownTimer)
      cooldownTimer = null
    }
  }, 1000)
}

async function handleRequestMagicLink() {
  if (!otpEmail.value) return
  isOtpLoading.value = true
  errorMessage.value = ''

  try {
    await api.requestMagicLink(otpEmail.value.trim())
    otpStep.value = 'verify'
    startResendCooldown(60)
  } catch (err: any) {
    errorMessage.value = getHumanErrorMessage(err, { context: 'magic-link' })
  } finally {
    isOtpLoading.value = false
  }
}

async function handleVerifyOtp() {
  if (!otpEmail.value || otpCode.value.length !== 6) return
  isOtpLoading.value = true
  errorMessage.value = ''

  try {
    await auth.loginWithOtp(otpEmail.value.trim(), otpCode.value.trim())
    router.push(getRedirectPath())
  } catch (err: any) {
    errorMessage.value = getHumanErrorMessage(err, { context: 'otp' })
  } finally {
    isOtpLoading.value = false
  }
}

function handleResendOtp() {
  if (resendCooldown.value > 0 || isOtpLoading.value) return
  handleRequestMagicLink()
}

function handleResetOtpFlow() {
  otpStep.value = 'request'
  otpCode.value = ''
  errorMessage.value = ''
}

function startOAuth(provider: 'google' | 'github') {
  window.location.href = `/v1/oauth/${provider}/start`
}

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-6 sm:p-8">
    <div class="mb-6 text-center">
      <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
        Sign in to DeskID
      </h1>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
        Enter your credentials or use passwordless authentication to access your console
      </p>
    </div>

    <!-- Mode Selector Tabs (WCAG 2.1 Tablist) -->
    <div
      role="tablist"
      aria-label="Sign-in methods"
      class="mb-6 p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl grid grid-cols-2 gap-1"
    >
      <button
        type="button"
        role="tab"
        :aria-selected="authMode === 'password'"
        @click="authMode = 'password'; errorMessage = ''"
        :class="[
          'flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all',
          authMode === 'password'
            ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm'
            : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
        ]"
      >
        <KeyRound class="w-3.5 h-3.5" />
        <span>Password</span>
      </button>

      <button
        type="button"
        role="tab"
        :aria-selected="authMode === 'passwordless'"
        @click="authMode = 'passwordless'; errorMessage = ''"
        :class="[
          'flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all',
          authMode === 'passwordless'
            ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm'
            : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200'
        ]"
      >
        <Sparkles class="w-3.5 h-3.5 text-brand-500" />
        <span>Email Link / OTP</span>
      </button>
    </div>

    <!-- Error Banner (Screen Reader Alert) -->
    <div
      v-if="errorMessage"
      role="alert"
      aria-live="assertive"
      class="mb-5 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs flex items-start gap-2.5"
    >
      <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
      <span class="leading-relaxed">{{ errorMessage }}</span>
    </div>

    <!-- TAB 1: Traditional Password Login -->
    <div v-if="authMode === 'password'">
      <form @submit.prevent="handlePasswordLogin" class="space-y-4">
        <Input
          v-model="email"
          label="Email Address"
          type="email"
          placeholder="name@company.com"
          required
          autocomplete="email"
        >
          <template #icon-left>
            <Mail class="w-4 h-4" />
          </template>
        </Input>

        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Password <span class="text-rose-500">*</span>
            </label>
            <router-link
              :to="{ name: 'forgot-password' }"
              class="text-xs font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
            >
              Forgot password?
            </router-link>
          </div>
          <Input
            v-model="password"
            type="password"
            placeholder="••••••••"
            required
            autocomplete="current-password"
          >
            <template #icon-left>
              <Lock class="w-4 h-4" />
            </template>
          </Input>
        </div>

        <Button
          type="submit"
          fullWidth
          :loading="isLoading"
          :disabled="!email || !password"
        >
          <template #icon-left>
            <LogIn class="w-4 h-4" />
          </template>
          Sign In
        </Button>
      </form>
    </div>

    <!-- TAB 2: Passwordless (Email Magic Link & 6-Digit OTP) -->
    <div v-else>
      <!-- Step 1: Request Magic Link & Code -->
      <div v-if="otpStep === 'request'">
        <form @submit.prevent="handleRequestMagicLink" class="space-y-4">
          <Input
            v-model="otpEmail"
            label="Email Address"
            type="email"
            placeholder="name@company.com"
            required
            autocomplete="email"
            hint="We'll send a one-click magic sign-in link and a 6-digit code to this address."
          >
            <template #icon-left>
              <Mail class="w-4 h-4" />
            </template>
          </Input>

          <Button
            type="submit"
            fullWidth
            :loading="isOtpLoading"
            :disabled="!otpEmail"
          >
            <template #icon-left>
              <Sparkles class="w-4 h-4" />
            </template>
            Send Sign-in Link & Code
          </Button>
        </form>
      </div>

      <!-- Step 2: Enter 6-digit OTP Code -->
      <div v-else class="space-y-4">
        <!-- Success dispatch banner -->
        <div class="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-800 dark:text-emerald-300 text-xs flex items-start gap-2.5">
          <CheckCircle2 class="w-4 h-4 shrink-0 mt-0.5 text-emerald-600 dark:text-emerald-400" />
          <div class="leading-relaxed">
            Sign-in link and 6-digit code sent to <strong class="font-semibold">{{ otpEmail }}</strong>. You can click the link in your email or enter the code below.
          </div>
        </div>

        <form @submit.prevent="handleVerifyOtp" class="space-y-4">
          <Input
            v-model="otpCode"
            label="6-Digit Verification Code"
            type="text"
            placeholder="••••••"
            required
            autocomplete="one-time-code"
            hint="Check your email inbox or spam folder for your 6-digit code."
          >
            <template #icon-left>
              <Lock class="w-4 h-4" />
            </template>
          </Input>

          <Button
            type="submit"
            fullWidth
            :loading="isOtpLoading"
            :disabled="otpCode.length !== 6"
          >
            <template #icon-left>
              <LogIn class="w-4 h-4" />
            </template>
            Verify & Sign In
          </Button>

          <!-- Action Links: Resend & Change Email -->
          <div class="flex items-center justify-between text-xs pt-1">
            <button
              type="button"
              @click="handleResetOtpFlow"
              class="flex items-center gap-1 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
            >
              <ArrowLeft class="w-3.5 h-3.5" />
              <span>Change email</span>
            </button>

            <button
              type="button"
              @click="handleResendOtp"
              :disabled="resendCooldown > 0 || isOtpLoading"
              class="flex items-center gap-1 font-medium transition-colors"
              :class="resendCooldown > 0 ? 'text-slate-400 cursor-not-allowed' : 'text-brand-600 hover:text-brand-700 dark:text-brand-400'"
            >
              <RotateCw class="w-3 h-3" :class="isOtpLoading ? 'animate-spin' : ''" />
              <span v-if="resendCooldown > 0">Resend code in {{ resendCooldown }}s</span>
              <span v-else>Resend code</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Social OAuth Divider -->
    <div class="relative my-6">
      <div class="absolute inset-0 flex items-center">
        <div class="w-full border-t border-slate-200 dark:border-slate-800" />
      </div>
      <div class="relative flex justify-center text-xs uppercase">
        <span class="bg-white dark:bg-slate-900 px-3 text-slate-400 dark:text-slate-500 font-medium">
          Or continue with
        </span>
      </div>
    </div>

    <!-- OAuth Buttons with Accessible Names -->
    <div class="grid grid-cols-2 gap-3">
      <button
        type="button"
        @click="startOAuth('google')"
        aria-label="Sign in with Google"
        class="flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <svg class="w-4 h-4 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
          <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
          <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
          <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
        </svg>
        <span>Google</span>
      </button>

      <button
        type="button"
        @click="startOAuth('github')"
        aria-label="Sign in with GitHub"
        class="flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
      >
        <svg class="w-4 h-4 fill-current shrink-0" viewBox="0 0 24 24" aria-hidden="true">
          <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
        </svg>
        <span>GitHub</span>
      </button>
    </div>

    <!-- Footer Register Link -->
    <div class="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
      Don't have an account?
      <router-link
        :to="{ name: 'register' }"
        class="font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 ml-1"
      >
        Create an account
      </router-link>
    </div>
  </div>
</template>
