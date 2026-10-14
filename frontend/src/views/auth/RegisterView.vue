<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'
import PasswordRequirements from '@/components/common/PasswordRequirements.vue'
import { getHumanErrorMessage } from '@/utils/errors'
import { Mail, Lock, User, KeyRound, UserPlus, AlertCircle, CheckCircle2, ChevronDown } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const displayName = ref('')
const bootstrapToken = ref('')
const showBootstrap = ref(false)
const isPasswordValid = ref(false)

const isLoading = ref(false)
const errorMessage = ref('')
const isVerificationRequired = ref(false)

async function handleRegister() {
  if (!email.value || !password.value || !isPasswordValid.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    const res = await auth.register({
      email: email.value.trim(),
      password: password.value,
      display_name: displayName.value.trim() || undefined,
      bootstrap_token: bootstrapToken.value.trim() || undefined
    })

    if (res.verificationRequired) {
      isVerificationRequired.value = true
    } else {
      if (auth.isPlatformAdmin) {
        router.push('/admin')
      } else {
        router.push('/account/profile')
      }
    }
  } catch (err: any) {
    errorMessage.value = getHumanErrorMessage(err, { context: 'register' })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-6 sm:p-8">
    <!-- Verification Sent Screen -->
    <div v-if="isVerificationRequired" class="text-center py-4">
      <div class="w-14 h-14 bg-emerald-50 dark:bg-emerald-950/50 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400 mb-4 shadow-inner">
        <CheckCircle2 class="w-8 h-8" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Verify your email address
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-2 max-w-sm mx-auto leading-relaxed">
        We've sent a verification link to <span class="font-semibold text-slate-800 dark:text-slate-200">{{ email }}</span>. Please click the link to activate your account.
      </p>
      <div class="mt-6">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center justify-center px-4 py-2 text-xs font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          Return to Sign In
        </router-link>
      </div>
    </div>

    <!-- Registration Form -->
    <div v-else>
      <div class="mb-6 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Create an Account
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
          Get started with enterprise identity management & IAM on DeskID
        </p>
      </div>

      <!-- Error Banner -->
      <div
        v-if="errorMessage"
        role="alert"
        aria-live="assertive"
        class="mb-5 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs flex items-start gap-2.5"
      >
        <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
        <span class="leading-relaxed">{{ errorMessage }}</span>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <Input
          v-model="displayName"
          label="Full Name / Display Name"
          placeholder="e.g. Jane Doe"
        >
          <template #icon-left>
            <User class="w-4 h-4" />
          </template>
        </Input>

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
          <Input
            v-model="password"
            label="Password"
            type="password"
            placeholder="Minimum 8 characters"
            required
            autocomplete="new-password"
          >
            <template #icon-left>
              <Lock class="w-4 h-4" />
            </template>
          </Input>

          <!-- Proactive Password Strength & Requirement Checklist -->
          <PasswordRequirements
            v-if="password.length > 0"
            :password="password"
            @valid="isPasswordValid = $event"
          />
        </div>

        <!-- Bootstrap Token Accordion (For Initial Setup) -->
        <div class="pt-1">
          <button
            type="button"
            @click="showBootstrap = !showBootstrap"
            class="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <KeyRound class="w-3.5 h-3.5" />
            <span>Initial Platform Admin Setup?</span>
            <ChevronDown
              class="w-3.5 h-3.5 transition-transform"
              :class="showBootstrap ? 'rotate-180' : ''"
            />
          </button>

          <div v-if="showBootstrap" class="mt-2.5 p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
            <Input
              v-model="bootstrapToken"
              label="Bootstrap Admin Secret Token"
              type="password"
              placeholder="Paste DESKID_BOOTSTRAP_TOKEN here"
              hint="Required only when initializing the very first admin account."
            />
          </div>
        </div>

        <Button
          type="submit"
          fullWidth
          :loading="isLoading"
          :disabled="!email || !password || !isPasswordValid"
        >
          <template #icon-left>
            <UserPlus class="w-4 h-4" />
          </template>
          Create Account
        </Button>
      </form>

      <!-- Footer Sign In Link -->
      <div class="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
        Already have an account?
        <router-link
          :to="{ name: 'login' }"
          class="font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 ml-1"
        >
          Sign in
        </router-link>
      </div>
    </div>
  </div>
</template>
