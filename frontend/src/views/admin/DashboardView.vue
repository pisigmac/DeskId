<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Badge from '@/components/common/Badge.vue'
import {
  Users,
  Building2,
  Server,
  ShieldCheck,
  Activity,
  ArrowRight,
  Database,
  KeyRound,
  RefreshCw
} from 'lucide-vue-next'

const admin = useAdminStore()

async function loadData() {
  await Promise.all([
    admin.fetchSystemStats(),
    admin.fetchUsers('', 0, 5),
    admin.fetchOrganizations(),
    admin.fetchServices(),
    admin.fetchAuditLogs({ limit: 5, offset: 0 })
  ])
}

onMounted(() => {
  loadData()
})

function formatDate(iso: string) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return iso
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Platform Overview
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Real-time metrics, system health, tenant statistics, and cryptographic event stream.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :loading="admin.systemLoading || admin.auditLoading"
          @click="loadData"
        >
          <template #icon-left>
            <RefreshCw class="w-4 h-4" />
          </template>
          Refresh Data
        </Button>
      </div>
    </div>

    <!-- Stat Metric Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Users -->
      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Total Users</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {{ admin.totalUsers }}
          </p>
          <router-link
            :to="{ name: 'admin-users' }"
            class="text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center gap-1 mt-2"
          >
            Manage directory
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </div>
        <div class="p-3 rounded-2xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400">
          <Users class="w-6 h-6" />
        </div>
      </div>

      <!-- Organizations -->
      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Tenants & Orgs</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {{ admin.organizations.length }}
          </p>
          <router-link
            :to="{ name: 'admin-organizations' }"
            class="text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center gap-1 mt-2"
          >
            View tenancies
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </div>
        <div class="p-3 rounded-2xl bg-sky-50 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400">
          <Building2 class="w-6 h-6" />
        </div>
      </div>

      <!-- Registered Services -->
      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Integrated Services</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {{ admin.totalServices }}
          </p>
          <router-link
            :to="{ name: 'admin-services' }"
            class="text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center gap-1 mt-2"
          >
            Manage registry
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </div>
        <div class="p-3 rounded-2xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
          <Server class="w-6 h-6" />
        </div>
      </div>

      <!-- Audit Stream Events -->
      <div class="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
        <div>
          <p class="text-xs font-medium text-slate-500 dark:text-slate-400">Chained Audit Events</p>
          <p class="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">
            {{ admin.totalAuditEvents }}
          </p>
          <router-link
            :to="{ name: 'admin-audit' }"
            class="text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center gap-1 mt-2"
          >
            Inspect audit chain
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </div>
        <div class="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
          <ShieldCheck class="w-6 h-6" />
        </div>
      </div>
    </div>

    <!-- Health & Security Status Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- System Health Card -->
      <Card title="System Diagnostics" class="lg:col-span-1">
        <div class="space-y-4">
          <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-2.5">
              <Database class="w-4 h-4 text-slate-500" />
              <span class="text-xs font-semibold text-slate-800 dark:text-slate-200">Database Connection</span>
            </div>
            <Badge :variant="admin.health?.checks.database ? 'success' : 'danger'" size="sm">
              {{ admin.health?.checks.database ? 'Connected' : 'Unhealthy' }}
            </Badge>
          </div>

          <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-2.5">
              <KeyRound class="w-4 h-4 text-slate-500" />
              <span class="text-xs font-semibold text-slate-800 dark:text-slate-200">Cryptographic Key Material</span>
            </div>
            <Badge :variant="admin.health?.checks.keys ? 'success' : 'danger'" size="sm">
              {{ admin.health?.checks.keys ? 'Loaded (Ed25519/RS256)' : 'Missing' }}
            </Badge>
          </div>

          <div class="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
            <div class="flex items-center gap-2.5">
              <Activity class="w-4 h-4 text-slate-500" />
              <span class="text-xs font-semibold text-slate-800 dark:text-slate-200">Overall Cluster Health</span>
            </div>
            <Badge :variant="admin.health?.status === 'ok' ? 'success' : 'warning'" size="sm">
              {{ admin.health?.status?.toUpperCase() || 'UNKNOWN' }}
            </Badge>
          </div>
        </div>
      </Card>

      <!-- Recent Audit Logs Preview Card -->
      <Card
        title="Live Cryptographic Audit Feed"
        description="Latest immutable hash-chained security events emitted by the platform."
        class="lg:col-span-2"
      >
        <template #actions>
          <router-link
            :to="{ name: 'admin-audit' }"
            class="text-xs font-semibold text-brand-600 hover:text-brand-700 dark:text-brand-400 inline-flex items-center gap-1"
          >
            View all logs
            <ArrowRight class="w-3 h-3" />
          </router-link>
        </template>

        <div v-if="admin.auditEvents.length === 0" class="py-6 text-center text-xs text-slate-500">
          No audit log events recorded yet.
        </div>

        <div v-else class="divide-y divide-slate-100 dark:divide-slate-800">
          <div
            v-for="event in admin.auditEvents"
            :key="event.id"
            class="py-3 flex items-center justify-between gap-4 text-xs"
          >
            <div class="flex items-center gap-3 min-w-0">
              <span class="font-mono text-[10px] text-slate-400 shrink-0">
                {{ formatDate(event.occurred_at) }}
              </span>
              <div class="truncate">
                <span class="font-bold text-slate-900 dark:text-slate-100">
                  {{ event.action }}
                </span>
                <span class="text-slate-500 dark:text-slate-400 ml-2">
                  resource: {{ event.resource_type }} ({{ event.resource_id || 'system' }})
                </span>
              </div>
            </div>

            <div class="shrink-0 flex items-center gap-2">
              <span class="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded" :title="`Hash: ${event.integrity_hash}`">
                {{ event.integrity_hash ? event.integrity_hash.substring(0, 8) + '...' : 'none' }}
              </span>
              <Badge variant="purple" size="sm">
                {{ event.actor_type }}
              </Badge>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>
