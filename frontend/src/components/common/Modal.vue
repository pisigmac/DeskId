<script setup lang="ts">
import { watch, onMounted, onUnmounted, ref, nextTick } from 'vue'
import { X } from 'lucide-vue-next'

interface Props {
  modelValue: boolean
  title?: string
  description?: string
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  title: '',
  description: '',
  maxWidth: 'md'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const modalContentRef = ref<HTMLElement | null>(null)
let previousActiveElement: HTMLElement | null = null
const titleId = `modal-title-${Math.random().toString(36).substring(2, 9)}`
const descId = `modal-desc-${Math.random().toString(36).substring(2, 9)}`

function close() {
  emit('update:modelValue', false)
}

function handleKeydown(e: KeyboardEvent) {
  if (!props.modelValue) return

  if (e.key === 'Escape') {
    close()
    return
  }

  // Focus trap inside modal
  if (e.key === 'Tab' && modalContentRef.value) {
    const focusable = modalContentRef.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    if (focusable.length === 0) return

    const first = focusable[0]
    const last = focusable[focusable.length - 1]

    if (e.shiftKey && document.activeElement === first) {
      last.focus()
      e.preventDefault()
    } else if (!e.shiftKey && document.activeElement === last) {
      first.focus()
      e.preventDefault()
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(() => props.modelValue, async (isOpen) => {
  if (isOpen) {
    previousActiveElement = document.activeElement as HTMLElement | null
    document.body.style.overflow = 'hidden'
    await nextTick()
    if (modalContentRef.value) {
      const focusable = modalContentRef.value.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )
      if (focusable.length > 0) {
        focusable[0].focus()
      }
    }
  } else {
    document.body.style.overflow = ''
    if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
      previousActiveElement.focus()
      previousActiveElement = null
    }
  }
})

const maxWidthClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  '2xl': 'max-w-2xl'
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 overflow-y-auto bg-slate-950/60 backdrop-blur-sm p-4 sm:p-6 flex items-center justify-center min-h-screen"
        @click.self="close"
      >
        <div
          ref="modalContentRef"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="title ? titleId : undefined"
          :aria-describedby="description ? descId : undefined"
          :class="[
            'relative w-full bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 transform transition-all overflow-hidden my-8',
            maxWidthClasses[maxWidth]
          ]"
        >
          <!-- Header -->
          <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <div>
              <h3 v-if="title" :id="titleId" class="text-base font-semibold text-slate-900 dark:text-slate-100">
                {{ title }}
              </h3>
              <p v-if="description" :id="descId" class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {{ description }}
              </p>
            </div>
            <button
              type="button"
              aria-label="Close dialog"
              @click="close"
              class="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Body -->
          <div class="px-6 py-4">
            <slot />
          </div>

          <!-- Footer -->
          <div
            v-if="$slots.footer"
            class="px-6 py-3.5 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-3"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
