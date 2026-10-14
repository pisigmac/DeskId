<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-vue-next'

const ui = useUiStore()

function getIcon(type: string) {
  switch (type) {
    case 'success':
      return CheckCircle2
    case 'error':
      return AlertCircle
    case 'warning':
      return AlertTriangle
    case 'info':
    default:
      return Info
  }
}

function getIconClass(type: string) {
  switch (type) {
    case 'success':
      return 'text-emerald-500'
    case 'error':
      return 'text-rose-500'
    case 'warning':
      return 'text-amber-500'
    case 'info':
    default:
      return 'text-sky-500'
  }
}
</script>

<template>
  <div
    class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none p-4"
    role="status"
    aria-live="polite"
    aria-atomic="false"
  >
    <TransitionGroup
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-for="toast in ui.toasts"
        :key="toast.id"
        class="pointer-events-auto flex items-start gap-3 p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-900/10 text-slate-900 dark:text-slate-100"
      >
        <component
          :is="getIcon(toast.type)"
          :class="['w-5 h-5 shrink-0 mt-0.5', getIconClass(toast.type)]"
        />

        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold">{{ toast.title }}</p>
          <p v-if="toast.message" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 break-words">
            {{ toast.message }}
          </p>
        </div>

        <button
          type="button"
          aria-label="Dismiss notification"
          @click="ui.removeToast(toast.id)"
          class="shrink-0 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>
