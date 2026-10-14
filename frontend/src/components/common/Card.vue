<script setup lang="ts">
interface Props {
  title?: string
  description?: string
  noPadding?: boolean
}

withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  noPadding: false
})
</script>

<template>
  <div
    class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm transition-all overflow-hidden"
  >
    <div
      v-if="title || $slots.header || $slots.actions"
      class="px-6 py-4 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between"
    >
      <div>
        <slot name="header">
          <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">
            {{ title }}
          </h3>
          <p v-if="description" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            {{ description }}
          </p>
        </slot>
      </div>
      <div v-if="$slots.actions" class="flex items-center gap-2">
        <slot name="actions" />
      </div>
    </div>

    <div :class="noPadding ? '' : 'p-6'">
      <slot />
    </div>

    <div
      v-if="$slots.footer"
      class="px-6 py-3.5 bg-slate-50/50 dark:bg-slate-900/40 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between"
    >
      <slot name="footer" />
    </div>
  </div>
</template>
