<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api/client'
import { useUiStore } from '@/stores/ui'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'
import PasswordRequirements from '@/components/common/PasswordRequirements.vue'
import { getHumanErrorMessage } from '@/utils/errors'
import { Lock, Key, CheckCircle2, AlertCircle } from 'lucide-vue-next'

const route = useRoute()
const ui = useUiStore()

const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isPasswordValid = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const isSuccess = ref(false)

const passwordsMatch = computed(() => {
  if (!confirmPassword.value) return null
  return newPassword.value === confirmPassword.value
})

onMounted(() => {
  if (route.query.token) {
    token.value = route.query.token as string
  }
})

async function handleResetPassword() {
  if (!token.value || !newPassword.value) return
  if (!isPasswordValid.value) {
    errorMessage.value = 'Please ensure your password satisfies all security requirements.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'The passwords you entered do not match. Please re-enter them carefully.'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    await api.resetPassword(token.value.trim(), newPassword.value)
    isSuccess.value = true
    ui.showToast({
      type: 'success',
      title: 'Password updated',
      message: 'Your password has been reset successfully. Please log in.'
    })
  } catch (err: any) {
    errorMessage.value = getHumanErrorMessage(err, { context: 'reset-password' })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-6 sm:p-8">
    <!-- Success State -->
    <div v-if="isSuccess" class="text-center py-4">
      <div class="w-14 h-14 bg-emerald-50 dark:bg-emerald-950/50 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400 mb-4">
        <CheckCircle2 class="w-8 h-8" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Password Reset Complete
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-2 max-w-sm mx-auto leading-relaxed">
        Your password has been successfully updated. You can now log in using your new credentials.
      </p>
      <div class="mt-6">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center justify-center px-4 py-2 text-xs font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          Sign In Now
        </router-link>
      </div>
    </div>

    <!-- Reset Form -->
    <div v-else>
      <div class="mb-6 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Set New Password
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
          Enter your new password below to secure your DeskID account
        </p>
      </div>

      <div
        v-if="errorMessage"
        role="alert"
        aria-live="assertive"
        class="mb-5 p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs flex items-start gap-2.5"
      >
        <AlertCircle class="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
        <span class="leading-relaxed">{{ errorMessage }}</span>
      </div>

      <form @submit.prevent="handleResetPassword" class="space-y-4">
        <Input
          v-if="!route.query.token"
          v-model="token"
          label="Reset Token"
          placeholder="Paste token from reset email"
          required
        >
          <template #icon-left>
            <Key class="w-4 h-4" />
          </template>
        </Input>

        <div>
          <Input
            v-model="newPassword"
            label="New Password"
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
            v-if="newPassword.length > 0"
            :password="newPassword"
            @valid="isPasswordValid = $event"
          />
        </div>

        <div>
          <Input
            v-model="confirmPassword"
            label="Confirm New Password"
            type="password"
            placeholder="Re-enter password"
            required
            autocomplete="new-password"
          >
            <template #icon-left>
              <Lock class="w-4 h-4" />
            </template>
          </Input>

          <p
            v-if="confirmPassword"
            class="mt-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors"
            :class="passwordsMatch ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-500'"
          >
            <CheckCircle2 v-if="passwordsMatch" class="w-3.5 h-3.5" />
            <AlertCircle v-else class="w-3.5 h-3.5" />
            <span>{{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}</span>
          </p>
        </div>

        <Button
          type="submit"
          fullWidth
          :loading="isLoading"
          :disabled="!token || !newPassword || !confirmPassword || !isPasswordValid || !passwordsMatch"
        >
          Reset Password
        </Button>
      </form>
    </div>
  </div>
</template>
