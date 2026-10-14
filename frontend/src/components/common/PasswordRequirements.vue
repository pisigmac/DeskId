<script setup lang="ts">
import { computed, watch } from 'vue'
import { Check, Circle } from 'lucide-vue-next'

interface Props {
  password: string
  minChars?: number
  requireNumbers?: boolean
  requireUppercase?: boolean
  requireLowercase?: boolean
  requireSpecial?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  password: '',
  minChars: 8,
  requireNumbers: true,
  requireUppercase: true,
  requireLowercase: true,
  requireSpecial: false
})

const emit = defineEmits<{
  (e: 'valid', isValid: boolean): void
}>()

interface Rule {
  id: string
  label: string
  passed: boolean
  required: boolean
}

const rules = computed<Rule[]>(() => {
  const pwd = props.password || ''
  return [
    {
      id: 'length',
      label: `At least ${props.minChars} characters`,
      passed: pwd.length >= props.minChars,
      required: true
    },
    {
      id: 'number',
      label: 'At least 1 number (0–9)',
      passed: /\d/.test(pwd),
      required: props.requireNumbers
    },
    {
      id: 'lowercase',
      label: 'At least 1 lowercase letter (a–z)',
      passed: /[a-z]/.test(pwd),
      required: props.requireLowercase
    },
    {
      id: 'uppercase',
      label: 'At least 1 uppercase letter (A–Z)',
      passed: /[A-Z]/.test(pwd),
      required: props.requireUppercase
    },
    {
      id: 'special',
      label: 'At least 1 special character (!@#$%^&*)',
      passed: /[^A-Za-z0-9]/.test(pwd),
      required: props.requireSpecial
    }
  ]
})

const passedCount = computed(() => {
  return rules.value.filter(r => r.passed).length
})

const allRequiredPassed = computed(() => {
  return rules.value.filter(r => r.required).every(r => r.passed)
})

watch(
  allRequiredPassed,
  (valid) => {
    emit('valid', valid)
  },
  { immediate: true }
)

const strengthLabel = computed(() => {
  if (!props.password) return 'Enter password'
  if (passedCount.value <= 1) return 'Weak'
  if (passedCount.value === 2) return 'Fair'
  if (passedCount.value === 3) return 'Good'
  return 'Strong'
})

const strengthColorClass = computed(() => {
  if (!props.password) return 'text-slate-400 dark:text-slate-500'
  if (passedCount.value <= 1) return 'text-rose-500'
  if (passedCount.value === 2) return 'text-amber-500'
  if (passedCount.value === 3) return 'text-sky-500'
  return 'text-emerald-500'
})

function getSegmentClass(index: number) {
  if (index >= passedCount.value) {
    return 'bg-slate-200 dark:bg-slate-800'
  }
  if (passedCount.value <= 1) {
    return 'bg-rose-500'
  }
  if (passedCount.value === 2) {
    return 'bg-amber-500'
  }
  if (passedCount.value === 3) {
    return 'bg-sky-500'
  }
  return 'bg-emerald-500'
}
</script>

<template>
  <div class="mt-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 text-xs">
    <!-- Strength Header & Segments Bar -->
    <div class="flex items-center justify-between mb-2">
      <span class="font-medium text-slate-600 dark:text-slate-400 text-[11px] uppercase tracking-wider">
        Password Strength:
        <span :class="['font-semibold ml-1 transition-colors', strengthColorClass]">
          {{ strengthLabel }}
        </span>
      </span>
      <span class="text-[11px] text-slate-400 font-mono" aria-hidden="true">
        {{ passedCount }}/{{ rules.length }}
      </span>
    </div>

    <!-- Segmented Progress Bar -->
    <div
      class="grid grid-cols-5 gap-1.5 h-1.5 rounded-full overflow-hidden mb-3"
      role="progressbar"
      :aria-valuenow="passedCount"
      :aria-valuemin="0"
      :aria-valuemax="rules.length"
      :aria-label="`Password strength is ${strengthLabel}`"
    >
      <div
        v-for="i in 5"
        :key="i"
        class="h-full rounded-full transition-all duration-300"
        :class="getSegmentClass(i - 1)"
      />
    </div>

    <!-- Live Checklist with ARIA -->
    <ul
      class="space-y-1.5"
      role="list"
      aria-live="polite"
    >
      <li
        v-for="rule in rules"
        :key="rule.id"
        class="flex items-center gap-2 text-xs transition-colors"
        :class="rule.passed ? 'text-slate-900 dark:text-slate-100 font-medium' : 'text-slate-400 dark:text-slate-500'"
      >
        <span
          class="w-4 h-4 rounded-full flex items-center justify-center shrink-0 transition-colors"
          :class="rule.passed ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400' : 'bg-slate-200 dark:bg-slate-800 text-slate-400'"
        >
          <Check v-if="rule.passed" class="w-2.5 h-2.5 stroke-[3]" />
          <Circle v-else class="w-2 h-2 text-slate-400" />
        </span>
        <span>
          {{ rule.label }}
          <span v-if="rule.required" class="text-slate-400 text-[10px] ml-0.5">(required)</span>
        </span>
      </li>
    </ul>
  </div>
</template>
