import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  title: string
  message?: string
  timeout?: number
}

export const useUiStore = defineStore('ui', () => {
  // Theme management
  const savedTheme = localStorage.getItem('deskid_theme') as 'light' | 'dark' | null
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const theme = ref<'light' | 'dark'>(savedTheme || (prefersDark ? 'dark' : 'light'))

  function applyTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
    localStorage.setItem('deskid_theme', newTheme)
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function toggleTheme() {
    applyTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  // Initialize theme on store instantiation
  applyTheme(theme.value)

  // Toast Notifications
  const toasts = ref<ToastMessage[]>([])

  function showToast(toast: Omit<ToastMessage, 'id'>) {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: ToastMessage = {
      id,
      timeout: 4000,
      ...toast
    }
    toasts.value.push(newToast)

    if (newToast.timeout && newToast.timeout > 0) {
      setTimeout(() => {
        removeToast(id)
      }, newToast.timeout)
    }
  }

  function removeToast(id: string) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  // Global loading overlay indicator
  const isGlobalLoading = ref(false)
  function setGlobalLoading(loading: boolean) {
    isGlobalLoading.value = loading
  }

  return {
    theme,
    toggleTheme,
    applyTheme,
    toasts,
    showToast,
    removeToast,
    isGlobalLoading,
    setGlobalLoading
  }
})
