<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api/client'
import { CheckCircle2, XCircle, Loader2, ArrowRight } from 'lucide-vue-next'

const route = useRoute()

const isVerifying = ref(true)
const isSuccess = ref(false)
const userEmail = ref('')
const errorMessage = ref('')

async function verify() {
  const token = (route.query.token as string) || ''
  if (!token) {
    isVerifying.value = false
    isSuccess.value = false
    errorMessage.value = 'Verification token is missing in the request URL.'
    return
  }

  try {
    const res = await api.verifyEmail(token)
    isSuccess.value = true
    userEmail.value = res.email || ''
  } catch (err: any) {
    isSuccess.value = false
    errorMessage.value = err?.error || 'Invalid or expired verification token.'
  } finally {
    isVerifying.value = false
  }
}

onMounted(() => {
  verify()
})
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-6 sm:p-8 text-center">
    <!-- Loading State -->
    <div v-if="isVerifying" class="py-8">
      <Loader2 class="w-10 h-10 text-brand-600 animate-spin mx-auto mb-4" />
      <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">
        Verifying your email...
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
        Please wait while we confirm your email address.
      </p>
    </div>

    <!-- Success State -->
    <div v-else-if="isSuccess" class="py-4">
      <div class="w-14 h-14 bg-emerald-50 dark:bg-emerald-950/50 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400 mb-4 shadow-inner">
        <CheckCircle2 class="w-8 h-8" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Email Verified Successfully!
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-2 max-w-sm mx-auto leading-relaxed">
        Your email address <span v-if="userEmail" class="font-semibold text-slate-800 dark:text-slate-200">{{ userEmail }}</span> has been verified. Your DeskID account is now active.
      </p>
      <div class="mt-6">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors shadow-sm"
        >
          Proceed to Sign In
          <ArrowRight class="w-4 h-4" />
        </router-link>
      </div>
    </div>

    <!-- Error State -->
    <div v-else class="py-4">
      <div class="w-14 h-14 bg-rose-50 dark:bg-rose-950/50 rounded-2xl flex items-center justify-center mx-auto text-rose-600 dark:text-rose-400 mb-4 shadow-inner">
        <XCircle class="w-8 h-8" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Verification Failed
      </h2>
      <p class="text-xs text-rose-600 dark:text-rose-400 mt-2 max-w-sm mx-auto leading-relaxed">
        {{ errorMessage }}
      </p>
      <div class="mt-6 flex justify-center gap-3">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
        >
          Return to Sign In
        </router-link>
      </div>
    </div>
  </div>
</template>
