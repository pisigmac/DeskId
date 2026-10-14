<script setup lang="ts">
import { ref } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

interface Props {
  modelValue?: string | number | null
  type?: string
  label?: string
  placeholder?: string
  error?: string
  hint?: string
  disabled?: boolean
  required?: boolean
  id?: string
  name?: string
  autocomplete?: string
}

withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  label: '',
  placeholder: '',
  error: '',
  hint: '',
  disabled: false,
  required: false,
  id: () => `input-${Math.random().toString(36).substring(2, 9)}`,
  name: '',
  autocomplete: 'off'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const showPassword = ref(false)

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="w-full">
    <label
      v-if="label"
      :for="id"
      class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
    >
      {{ label }}
      <span v-if="required" class="text-rose-500">*</span>
    </label>

    <div class="relative rounded-lg shadow-sm">
      <div
        v-if="$slots['icon-left']"
        class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500"
      >
        <slot name="icon-left" />
      </div>

      <input
        :id="id"
        :name="name || id"
        :type="type === 'password' ? (showPassword ? 'text' : 'password') : type"
        :value="modelValue ?? ''"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :autocomplete="autocomplete"
        :aria-invalid="Boolean(error)"
        :aria-describedby="error ? `${id}-error` : (hint ? `${id}-hint` : undefined)"
        @input="handleInput"
        :class="[
          'block w-full rounded-lg border bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 text-sm transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-offset-0 disabled:opacity-50 disabled:cursor-not-allowed',
          $slots['icon-left'] ? 'pl-10' : 'pl-3.5',
          (type === 'password' || $slots['icon-right']) ? 'pr-10' : 'pr-3.5',
          'py-2.5',
          error
            ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/20 text-rose-900 dark:text-rose-200'
            : 'border-slate-300 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500/20'
        ]"
      />

      <div
        v-if="type === 'password'"
        class="absolute inset-y-0 right-0 pr-3 flex items-center"
      >
        <button
          type="button"
          :aria-label="showPassword ? 'Hide password' : 'Show password'"
          :aria-pressed="showPassword"
          :aria-controls="id"
          @click="showPassword = !showPassword"
          class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded p-1 transition-colors"
        >
          <EyeOff v-if="showPassword" class="w-4 h-4" />
          <Eye v-else class="w-4 h-4" />
        </button>
      </div>
      <div
        v-else-if="$slots['icon-right']"
        class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-slate-400"
      >
        <slot name="icon-right" />
      </div>
    </div>

    <p
      v-if="error"
      :id="`${id}-error`"
      role="alert"
      class="mt-1.5 text-xs text-rose-600 dark:text-rose-400 font-medium"
    >
      {{ error }}
    </p>
    <p
      v-else-if="hint"
      :id="`${id}-hint`"
      class="mt-1.5 text-xs text-slate-500 dark:text-slate-400"
    >
      {{ hint }}
    </p>
  </div>
</template>
