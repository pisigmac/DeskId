<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  align?: 'left' | 'right'
  width?: string
}

const props = withDefaults(defineProps<Props>(), {
  align: 'right',
  width: 'w-56'
})

const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

defineExpose({ close, toggle })
</script>

<template>
  <div class="relative inline-block text-left" ref="dropdownRef">
    <div @click="toggle">
      <slot name="trigger" :isOpen="isOpen" />
    </div>

    <Transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        :class="[
          'absolute z-50 mt-2 rounded-xl bg-white dark:bg-slate-900 shadow-xl border border-slate-200 dark:border-slate-800 focus:outline-none overflow-hidden py-1 divide-y divide-slate-100 dark:divide-slate-800',
          props.align === 'right' ? 'right-0 origin-top-right' : 'left-0 origin-top-left',
          props.width
        ]"
        @click="close"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>
