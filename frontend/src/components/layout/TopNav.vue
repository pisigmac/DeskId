<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { api } from '@/api/client'
import type { SystemHealth } from '@/api/types'
import {
  Menu,
  Sun,
  Moon,
  User,
  ShieldCheck,
  Laptop,
  LogOut,
  ChevronDown,
  Activity
} from 'lucide-vue-next'
import Dropdown from '@/components/common/Dropdown.vue'
import OrgSwitcher from './OrgSwitcher.vue'

defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

const health = ref<SystemHealth | null>(null)

async function checkHealth() {
  try {
    health.value = await api.getHealth()
  } catch {
    health.value = null
  }
}

onMounted(() => {
  checkHealth()
})

async function handleLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header
    class="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/80 dark:border-slate-800/80 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 sm:px-6"
  >
    <!-- Left: Mobile menu toggle + Org Switcher -->
    <div class="flex items-center gap-3">
      <button
        type="button"
        @click="$emit('toggle-sidebar')"
        class="p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 lg:hidden"
      >
        <Menu class="w-5 h-5" />
      </button>

      <OrgSwitcher />
    </div>

    <!-- Right: Health Status + Theme Toggle + User Menu -->
    <div class="flex items-center gap-2 sm:gap-3">
      <!-- Health status indicator -->
      <div
        class="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border"
        :class="
          health?.status === 'ok'
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800/60'
            : 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800/60'
        "
        :title="`Backend status: ${health?.status || 'Unknown'} (DB: ${health?.checks.database ? 'OK' : 'Error'}, Keys: ${health?.checks.keys ? 'OK' : 'Error'})`"
      >
        <Activity class="w-3.5 h-3.5 animate-pulse" />
        <span>{{ health?.status === 'ok' ? 'System Healthy' : 'Degraded' }}</span>
      </div>

      <!-- Theme Switcher Button -->
      <button
        type="button"
        @click="ui.toggleTheme"
        class="p-2 rounded-xl text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800 transition-colors"
        :title="ui.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
      >
        <Sun v-if="ui.theme === 'dark'" class="w-4 h-4 text-amber-400" />
        <Moon v-else class="w-4 h-4 text-slate-600" />
      </button>

      <!-- User Dropdown Menu -->
      <Dropdown align="right" width="w-56">
        <template #trigger="{ isOpen }">
          <button
            type="button"
            :class="[
              'flex items-center gap-2 p-1.5 pl-2 rounded-xl border transition-all',
              isOpen
                ? 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700'
                : 'border-transparent hover:bg-slate-100 dark:hover:bg-slate-800'
            ]"
          >
            <div class="w-7 h-7 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 text-white font-bold text-xs flex items-center justify-center shadow-sm">
              {{ (auth.user?.display_name || auth.user?.email || 'U').charAt(0).toUpperCase() }}
            </div>
            <div class="hidden sm:block text-left max-w-[120px] truncate">
              <div class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                {{ auth.user?.display_name || auth.user?.email }}
              </div>
            </div>
            <ChevronDown class="w-3.5 h-3.5 text-slate-400" />
          </button>
        </template>

        <div class="px-4 py-3 border-b border-slate-100 dark:border-slate-800">
          <p class="text-xs text-slate-400">Signed in as</p>
          <p class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate mt-0.5">
            {{ auth.user?.email }}
          </p>
          <div v-if="auth.isPlatformAdmin" class="mt-2">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-950/80 dark:text-purple-300">
              <ShieldCheck class="w-3 h-3" />
              Platform Admin
            </span>
          </div>
        </div>

        <div class="py-1">
          <router-link
            :to="{ name: 'account-profile' }"
            class="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <User class="w-3.5 h-3.5 text-slate-400" />
            Profile & Security
          </router-link>

          <router-link
            :to="{ name: 'account-sessions' }"
            class="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <Laptop class="w-3.5 h-3.5 text-slate-400" />
            Active Sessions
          </router-link>
        </div>

        <div class="py-1 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            @click="handleLogout"
            class="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-left font-medium"
          >
            <LogOut class="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </Dropdown>
    </div>
  </header>
</template>
