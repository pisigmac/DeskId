<script setup lang="ts">
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-brand-600 hover:bg-brand-700 text-white shadow-sm border border-transparent focus-visible:ring-brand-500'
    case 'secondary':
      return 'bg-slate-100 hover:bg-slate-200 text-slate-900 border border-transparent dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-100 focus-visible:ring-slate-400'
    case 'danger':
      return 'bg-rose-600 hover:bg-rose-700 text-white shadow-sm border border-transparent focus-visible:ring-rose-500'
    case 'outline':
      return 'bg-transparent hover:bg-slate-100 border border-slate-300 text-slate-700 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800 focus-visible:ring-brand-500'
    case 'ghost':
      return 'bg-transparent hover:bg-slate-100 text-slate-700 dark:hover:bg-slate-800 dark:text-slate-300 focus-visible:ring-brand-500'
  }
})

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'px-2.5 py-1.5 text-xs rounded-md gap-1.5'
    case 'md':
      return 'px-4 py-2 text-sm rounded-lg gap-2'
    case 'lg':
      return 'px-5 py-2.5 text-base rounded-lg gap-2.5'
  }
})
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none',
      variantClasses,
      sizeClasses,
      fullWidth ? 'w-full' : ''
    ]"
  >
    <Loader2 v-if="loading" class="animate-spin -ml-1 shrink-0" :class="size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'" />
    <slot name="icon-left" v-if="!loading" />
    <slot />
    <slot name="icon-right" />
  </button>
</template>
