<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import { Fingerprint, Sun, Moon } from 'lucide-vue-next'

const ui = useUiStore()
</script>

<template>
  <div class="min-h-screen flex flex-col justify-between bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-brand-500 selection:text-white relative overflow-hidden">
    <!-- Background subtle gradient decor -->
    <div class="absolute -top-40 -right-40 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
    <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

    <!-- Top header with logo & theme toggle -->
    <header class="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-10">
      <router-link :to="{ path: '/' }" class="flex items-center gap-2.5 group">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-brand-500/25 group-hover:scale-105 transition-transform">
          <Fingerprint class="w-5 h-5" />
        </div>
        <span class="font-bold text-lg tracking-tight">
          DeskID
        </span>
      </router-link>

      <button
        type="button"
        @click="ui.toggleTheme"
        class="p-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 transition-colors shadow-sm"
      >
        <Sun v-if="ui.theme === 'dark'" class="w-4 h-4 text-amber-400" />
        <Moon v-else class="w-4 h-4 text-slate-600" />
      </button>
    </header>

    <!-- Main Auth Content Area -->
    <main class="flex-1 flex items-center justify-center px-4 sm:px-6 py-10 z-10">
      <div class="w-full max-w-md">
        <router-view />
      </div>
    </main>

    <!-- Footer -->
    <footer class="w-full max-w-7xl mx-auto px-6 py-4 text-center text-xs text-slate-500 dark:text-slate-500 z-10">
      &copy; 2026 DeskID Identity & Access Management. Enterprise cryptographic security.
    </footer>
  </div>
</template>
