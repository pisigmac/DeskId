<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api/client'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'
import { getHumanErrorMessage } from '@/utils/errors'
import { Mail, ArrowLeft, Send, CheckCircle2, AlertCircle } from 'lucide-vue-next'

const email = ref('')
const isLoading = ref(false)
const isSubmitted = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (!email.value) return
  isLoading.value = true
  errorMessage.value = ''

  try {
    await api.forgotPassword(email.value.trim())
    isSubmitted.value = true
  } catch (err: any) {
    errorMessage.value = getHumanErrorMessage(err, { context: 'forgot-password' })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-6 sm:p-8">
    <div v-if="isSubmitted" class="text-center py-4">
      <div class="w-14 h-14 bg-emerald-50 dark:bg-emerald-950/50 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400 mb-4">
        <CheckCircle2 class="w-8 h-8" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Reset link sent
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-2 max-w-sm mx-auto leading-relaxed">
        If an account exists for <span class="font-semibold text-slate-800 dark:text-slate-200">{{ email }}</span>, you will receive password reset instructions shortly.
      </p>
      <div class="mt-6">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          <ArrowLeft class="w-4 h-4" />
          Back to Sign In
        </router-link>
      </div>
    </div>

    <div v-else>
      <div class="mb-6 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Reset Password
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
          Enter your registered email address and we'll send you a recovery link
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

      <form @submit.prevent="handleSubmit" class="space-y-4">
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

        <Button
          type="submit"
          fullWidth
          :loading="isLoading"
          :disabled="!email"
        >
          <template #icon-left>
            <Send class="w-4 h-4" />
          </template>
          Send Reset Link
        </Button>
      </form>

      <div class="mt-6 text-center">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
        >
          <ArrowLeft class="w-3.5 h-3.5" />
          Back to Sign In
        </router-link>
      </div>
    </div>
  </div>
</template>
