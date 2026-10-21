<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard,
  Users,
  Building2,
  KeyRound,
  Server,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  Laptop,
  Fingerprint,
  ExternalLink,
  X
} from 'lucide-vue-next'

defineEmits<{
  (e: 'close'): void
}>()

const route = useRoute()
const auth = useAuthStore()

interface NavItem {
  label: string
  to: { name: string }
  icon: any
  adminOnly?: boolean
}

const adminNavItems: NavItem[] = [
  { label: 'Platform Dashboard', to: { name: 'admin-dashboard' }, icon: LayoutDashboard },
  { label: 'User Directory', to: { name: 'admin-users' }, icon: Users },
  { label: 'Organizations & Tenancy', to: { name: 'admin-organizations' }, icon: Building2 },
  { label: 'Roles & Permissions', to: { name: 'admin-roles' }, icon: ShieldAlert },
  { label: 'Product Grants', to: { name: 'admin-grants' }, icon: KeyRound },
  { label: 'Service Registry', to: { name: 'admin-services' }, icon: Server },
  { label: 'Audit Log Stream', to: { name: 'admin-audit' }, icon: ShieldCheck }
]

const userNavItems: NavItem[] = [
  { label: 'Profile & Security', to: { name: 'account-profile' }, icon: UserCheck },
  { label: 'Active Sessions', to: { name: 'account-sessions' }, icon: Laptop }
]

const isCurrentRoute = (name: string) => {
  return route.name === name
}
</script>

<template>
  <aside class="flex flex-col h-full bg-slate-900 text-slate-100 w-64 border-r border-slate-800 select-none">
    <!-- Brand Header -->
    <div class="h-16 flex items-center justify-between px-5 border-b border-slate-800">
      <router-link :to="{ path: '/' }" class="flex items-center gap-2.5 group">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform">
          <Fingerprint class="w-5 h-5" />
        </div>
        <div>
          <span class="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            DeskID
            <span class="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
              v0.1.0
            </span>
          </span>
        </div>
      </router-link>

      <button
        type="button"
        @click="$emit('close')"
        class="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
      >
        <X class="w-5 h-5" />
      </button>
    </div>

    <!-- Navigation Body -->
    <div class="flex-1 overflow-y-auto py-4 px-3 space-y-6">
      <!-- Admin Navigation Section (Visible only to Platform Admins) -->
      <div v-if="auth.isPlatformAdmin">
        <div class="px-3 mb-2 flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400">
          <span>Platform Admin</span>
          <span class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
        </div>
        <nav class="space-y-1">
          <router-link
            v-for="item in adminNavItems"
            :key="item.to.name"
            :to="item.to"
            @click="$emit('close')"
            :class="[
              'flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all group',
              isCurrentRoute(item.to.name)
                ? 'bg-brand-600 text-white shadow-sm font-semibold'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                'w-4 h-4 shrink-0 transition-transform group-hover:scale-110',
                isCurrentRoute(item.to.name) ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
              ]"
            />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </div>

      <!-- Account Navigation Section -->
      <div>
        <div class="px-3 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          User Space
        </div>
        <nav class="space-y-1">
          <router-link
            v-for="item in userNavItems"
            :key="item.to.name"
            :to="item.to"
            @click="$emit('close')"
            :class="[
              'flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all group',
              isCurrentRoute(item.to.name)
                ? 'bg-brand-600 text-white shadow-sm font-semibold'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            ]"
          >
            <component
              :is="item.icon"
              :class="[
                'w-4 h-4 shrink-0 transition-transform group-hover:scale-110',
                isCurrentRoute(item.to.name) ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
              ]"
            />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </div>
    </div>

    <!-- Sidebar Footer -->
    <div class="p-3 border-t border-slate-800">
      <a
        href="/docs"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
      >
        <span class="flex items-center gap-2">
          <span>FastAPI OpenAPI Specs</span>
        </span>
        <ExternalLink class="w-3.5 h-3.5" />
      </a>
    </div>
  </aside>
</template>
