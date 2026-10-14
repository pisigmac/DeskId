<script setup lang="ts">
interface Props {
  modelValue: boolean
  label?: string
  description?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  label: '',
  description: '',
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

function toggle() {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}
</script>

<template>
  <div class="flex items-center justify-between cursor-pointer" @click="toggle">
    <div v-if="label || description" class="flex flex-col select-none pr-4">
      <span v-if="label" class="text-sm font-medium text-slate-800 dark:text-slate-200">
        {{ label }}
      </span>
      <span v-if="description" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
        {{ description }}
      </span>
    </div>

    <button
      type="button"
      role="switch"
      :aria-checked="modelValue"
      :disabled="disabled"
      :class="[
        'relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2',
        disabled ? 'opacity-50 cursor-not-allowed' : '',
        modelValue ? 'bg-brand-600' : 'bg-slate-300 dark:bg-slate-700'
      ]"
    >
      <span
        :class="[
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out',
          modelValue ? 'translate-x-5' : 'translate-x-0'
        ]"
      />
    </button>
  </div>
</template>
