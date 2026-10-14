<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import TopNav from '@/components/layout/TopNav.vue'

const isSidebarOpen = ref(false)
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col antialiased">
    <!-- Skip to main content link (WCAG 2.4.1 Bypass Blocks) -->
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand-600 focus:text-white focus:text-xs focus:font-semibold focus:rounded-xl focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-2"
    >
      Skip to main content
    </a>

    <!-- Desktop Sidebar -->
    <div class="hidden lg:fixed lg:inset-y-0 lg:z-40 lg:flex lg:w-64 lg:flex-col">
      <Sidebar />
    </div>

    <!-- Mobile Sidebar Drawer -->
    <div v-if="isSidebarOpen" class="relative z-50 lg:hidden">
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-slate-950/60 backdrop-blur-sm transition-opacity"
        @click="isSidebarOpen = false"
      />
      <div class="fixed inset-y-0 left-0 flex max-w-full">
        <Sidebar @close="isSidebarOpen = false" />
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="lg:pl-64 flex flex-col flex-1 min-w-0">
      <TopNav @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />

      <main id="main-content" tabindex="-1" class="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto focus:outline-none">
        <router-view />
      </main>
    </div>
  </div>
</template>
