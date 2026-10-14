<script setup lang="ts">
import { useDeskId } from '../context'

interface Props {
  mode?: 'modal' | 'redirect'
  redirectUrl?: string
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'modal',
  redirectUrl: '',
  className: ''
})

const deskId = useDeskId()

function handleClick() {
  if (props.mode === 'modal') {
    deskId.openSignInModal()
  } else {
    const url = props.redirectUrl || '/login'
    window.location.href = url
  }
}
</script>

<template>
  <button
    type="button"
    @click="handleClick"
    :class="['deskid-btn deskid-btn-signin', className]"
  >
    <slot>Sign In</slot>
  </button>
</template>

<style scoped>
.deskid-btn-signin {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.5rem;
  background-color: #4f46e5;
  color: #ffffff;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  font-family: inherit;
}

.deskid-btn-signin:hover {
  background-color: #4338ca;
}

.deskid-btn-signin:focus-visible {
  outline: 2px solid #6366f1;
  outline-offset: 2px;
}
</style>
