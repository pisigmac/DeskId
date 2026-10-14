<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'success' | 'danger' | 'warning' | 'info' | 'neutral' | 'purple'
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'neutral',
  size: 'md'
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'success':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800/60'
    case 'danger':
      return 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-800/60'
    case 'warning':
      return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800/60'
    case 'info':
      return 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-400 dark:border-sky-800/60'
    case 'purple':
      return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-400 dark:border-purple-800/60'
    case 'neutral':
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'
  }
})

const sizeClasses = computed(() => {
  return props.size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-full border gap-1.5 shrink-0',
      variantClasses,
      sizeClasses
    ]"
  >
    <slot name="dot">
      <span
        v-if="variant === 'success'"
        class="w-1.5 h-1.5 rounded-full bg-emerald-500"
      />
      <span
        v-else-if="variant === 'danger'"
        class="w-1.5 h-1.5 rounded-full bg-rose-500"
      />
      <span
        v-else-if="variant === 'warning'"
        class="w-1.5 h-1.5 rounded-full bg-amber-500"
      />
    </slot>
    <slot />
  </span>
</template>
