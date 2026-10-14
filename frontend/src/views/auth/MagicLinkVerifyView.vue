<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getHumanErrorMessage } from '@/utils/errors'
import { Loader2, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isVerifying = ref(true)
const isSuccess = ref(false)
const errorMessage = ref('')

onMounted(async () => {
  const token = route.query.token as string
  if (!token) {
    isVerifying.value = false
    errorMessage.value = 'No sign-in token found in this link. Please request a new link.'
    return
  }

  try {
    await auth.loginWithMagicLink(token.trim())
    isSuccess.value = true
    isVerifying.value = false
    setTimeout(() => {
      const redirectPath = (route.query.redirect as string) || (auth.isPlatformAdmin ? '/admin' : '/account/profile')
      router.push(redirectPath)
    }, 1200)
  } catch (err: any) {
    isVerifying.value = false
    errorMessage.value = getHumanErrorMessage(err, { context: 'magic-link' })
  }
})
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-6 sm:p-8 text-center max-w-md mx-auto">
    <!-- State 1: Verifying Spinner -->
    <div v-if="isVerifying" class="py-6 space-y-4">
      <div class="w-14 h-14 bg-brand-50 dark:bg-brand-950/60 rounded-2xl flex items-center justify-center mx-auto text-brand-600 dark:text-brand-400">
        <Loader2 class="w-7 h-7 animate-spin" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Verifying your sign-in link...
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto leading-relaxed">
        Please wait a moment while we authenticate your session and prepare your identity context.
      </p>
    </div>

    <!-- State 2: Success -->
    <div v-else-if="isSuccess" class="py-6 space-y-4">
      <div class="w-14 h-14 bg-emerald-50 dark:bg-emerald-950/60 rounded-2xl flex items-center justify-center mx-auto text-emerald-600 dark:text-emerald-400">
        <CheckCircle2 class="w-7 h-7" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Authentication Successful!
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 max-w-xs mx-auto leading-relaxed">
        Redirecting you to your workspaces now...
      </p>
    </div>

    <!-- State 3: Error -->
    <div v-else class="py-6 space-y-4">
      <div class="w-14 h-14 bg-rose-50 dark:bg-rose-950/60 rounded-2xl flex items-center justify-center mx-auto text-rose-600 dark:text-rose-400">
        <AlertCircle class="w-7 h-7" />
      </div>
      <h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
        Sign-In Link Expired or Invalid
      </h2>
      <p
        role="alert"
        aria-live="assertive"
        class="text-xs text-rose-700 dark:text-rose-300 max-w-xs mx-auto leading-relaxed bg-rose-50 dark:bg-rose-950/40 p-3 rounded-xl border border-rose-200 dark:border-rose-800/60"
      >
        {{ errorMessage }}
      </p>
      <div class="pt-2">
        <router-link
          :to="{ name: 'login' }"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
        >
          <ArrowLeft class="w-4 h-4" />
          <span>Return to Sign In</span>
        </router-link>
      </div>
    </div>
  </div>
</template>
