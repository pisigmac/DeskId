<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { Loader2, AlertCircle } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

const errorMessage = ref('')

onMounted(async () => {
  // Check URL fragment for tokens e.g. #access_token=...&refresh_token=...&expires_in=...
  const hash = window.location.hash.substring(1)
  const params = new URLSearchParams(hash)

  const accessToken = params.get('access_token')
  const refreshToken = params.get('refresh_token')
  const expiresIn = params.get('expires_in')
  const tokenType = params.get('token_type') || 'bearer'

  if (accessToken && refreshToken) {
    try {
      await auth.handleAuthTokens({
        access_token: accessToken,
        refresh_token: refreshToken,
        token_type: tokenType,
        expires_in: parseInt(expiresIn || '3600', 10)
      })

      ui.showToast({
        type: 'success',
        title: 'Authentication Successful',
        message: `Welcome back, ${auth.user?.display_name || auth.user?.email}`
      })

      if (auth.isPlatformAdmin) {
        router.replace('/admin')
      } else {
        router.replace('/account/profile')
      }
    } catch (err: any) {
      errorMessage.value = err?.error || 'Failed to authenticate via OAuth provider.'
    }
  } else {
    errorMessage.value = 'Missing authentication tokens from OAuth provider.'
  }
})
</script>

<template>
  <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl p-8 text-center">
    <div v-if="!errorMessage" class="py-6">
      <Loader2 class="w-10 h-10 text-brand-600 animate-spin mx-auto mb-4" />
      <h2 class="text-base font-semibold text-slate-900 dark:text-slate-100">
        Completing Authentication...
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
        Please wait while we establish your secure session.
      </p>
    </div>

    <div v-else class="py-4">
      <div class="w-12 h-12 bg-rose-50 dark:bg-rose-950/50 rounded-2xl flex items-center justify-center mx-auto text-rose-600 dark:text-rose-400 mb-3">
        <AlertCircle class="w-6 h-6" />
      </div>
      <h2 class="text-base font-bold text-slate-900 dark:text-slate-100">
        Sign In Failed
      </h2>
      <p class="text-xs text-rose-600 dark:text-rose-400 mt-1 mb-4">
        {{ errorMessage }}
      </p>
      <router-link
        :to="{ name: 'login' }"
        class="inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
      >
        Return to Sign In
      </router-link>
    </div>
  </div>
</template>
