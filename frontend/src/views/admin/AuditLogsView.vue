<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import type { AuditLogEvent } from '@/api/types'
import DataTable, { type Column } from '@/components/common/DataTable.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import Modal from '@/components/common/Modal.vue'
import {
  ShieldCheck,
  Search,
  RefreshCw,
  Eye,
  Filter,
  Terminal,
  Clock,
  Lock
} from 'lucide-vue-next'

const admin = useAdminStore()

const filterAction = ref('')
const filterActorId = ref('')
const filterResourceType = ref('')
const autoRefresh = ref(false)
let refreshInterval: any = null

const selectedEvent = ref<AuditLogEvent | null>(null)
const showDetailsModal = ref(false)

const columns: Column[] = [
  { key: 'timestamp', label: 'Timestamp' },
  { key: 'action', label: 'Action' },
  { key: 'actor', label: 'Actor' },
  { key: 'resource', label: 'Resource Target' },
  { key: 'hashes', label: 'Integrity Hash Chain' },
  { key: 'actions', label: 'Details', align: 'right' }
]

async function loadLogs(offset: number = 0) {
  await admin.fetchAuditLogs({
    action: filterAction.value.trim() || undefined,
    actor_id: filterActorId.value.trim() || undefined,
    resource_type: filterResourceType.value.trim() || undefined,
    offset,
    limit: 25
  })
}

function handleFilter() {
  loadLogs(0)
}

function handleResetFilters() {
  filterAction.value = ''
  filterActorId.value = ''
  filterResourceType.value = ''
  loadLogs(0)
}

function handlePageChange(newOffset: number) {
  loadLogs(newOffset)
}

function openEventDetails(event: AuditLogEvent) {
  selectedEvent.value = event
  showDetailsModal.value = true
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refreshInterval = setInterval(() => {
      loadLogs(0)
    }, 5000)
  } else {
    if (refreshInterval) clearInterval(refreshInterval)
  }
}

onMounted(() => {
  loadLogs(0)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

function formatDate(iso: string) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
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
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <ShieldCheck class="w-6 h-6 text-emerald-500" />
          Cryptographic Audit Stream
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Immutable SHA-256 hash-chained security event log for non-repudiation and compliance.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          :variant="autoRefresh ? 'primary' : 'outline'"
          size="sm"
          @click="toggleAutoRefresh"
        >
          <template #icon-left>
            <RefreshCw class="w-4 h-4" :class="autoRefresh ? 'animate-spin' : ''" />
          </template>
          {{ autoRefresh ? 'Live Streaming ON' : 'Live Stream' }}
        </Button>

        <Button
          variant="outline"
          size="sm"
          :loading="admin.auditLoading"
          @click="() => loadLogs(0)"
        >
          Refresh
        </Button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-center gap-3">
      <div class="w-full md:w-1/3">
        <Input
          v-model="filterAction"
          placeholder="Filter by Action (e.g. user.login, admin.set_grant)"
          @keyup.enter="handleFilter"
        >
          <template #icon-left>
            <Terminal class="w-4 h-4" />
          </template>
        </Input>
      </div>

      <div class="w-full md:w-1/3">
        <Input
          v-model="filterActorId"
          placeholder="Filter by Actor UUID"
          @keyup.enter="handleFilter"
        >
          <template #icon-left>
            <Search class="w-4 h-4" />
          </template>
        </Input>
      </div>

      <div class="w-full md:w-1/4">
        <Input
          v-model="filterResourceType"
          placeholder="Resource Type (e.g. user, org)"
          @keyup.enter="handleFilter"
        >
          <template #icon-left>
            <Filter class="w-4 h-4" />
          </template>
        </Input>
      </div>

      <div class="flex items-center gap-2 shrink-0 w-full md:w-auto justify-end">
        <Button size="md" @click="handleFilter">
          Filter
        </Button>
        <Button variant="ghost" size="md" @click="handleResetFilters">
          Reset
        </Button>
      </div>
    </div>

    <!-- Audit Log Table -->
    <DataTable
      :columns="columns"
      :items="admin.auditEvents"
      :loading="admin.auditLoading"
      :total="admin.totalAuditEvents"
      :limit="25"
      emptyTitle="No audit events recorded"
      emptyMessage="No events match the specified filter criteria."
      @page-change="handlePageChange"
    >
      <!-- Timestamp Cell -->
      <template #cell-timestamp="{ item }">
        <span class="text-xs font-mono text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
          <Clock class="w-3.5 h-3.5" />
          {{ formatDate(item.occurred_at) }}
        </span>
      </template>

      <!-- Action Cell -->
      <template #cell-action="{ item }">
        <span class="font-mono text-xs font-bold text-brand-600 dark:text-brand-400">
          {{ item.action }}
        </span>
      </template>

      <!-- Actor Cell -->
      <template #cell-actor="{ item }">
        <div class="text-xs">
          <Badge :variant="item.actor_type === 'admin' ? 'purple' : item.actor_type === 'user' ? 'info' : 'neutral'" size="sm">
            {{ item.actor_type }}
          </Badge>
          <span v-if="item.actor_id" class="font-mono text-[11px] text-slate-500 ml-1.5 truncate max-w-[100px] inline-block align-middle" :title="item.actor_id">
            {{ item.actor_id.substring(0, 8) }}...
          </span>
        </div>
      </template>

      <!-- Resource Target Cell -->
      <template #cell-resource="{ item }">
        <div class="text-xs text-slate-700 dark:text-slate-300">
          <span class="font-semibold">{{ item.resource_type }}</span>
          <span v-if="item.resource_id" class="font-mono text-[11px] text-slate-400 ml-1">
            ({{ item.resource_id }})
          </span>
        </div>
      </template>

      <!-- Hashes Cell -->
      <template #cell-hashes="{ item }">
        <div class="space-y-0.5">
          <div class="flex items-center gap-1.5 font-mono text-[10px] text-emerald-600 dark:text-emerald-400" :title="`Current Integrity Hash: ${item.integrity_hash}`">
            <Lock class="w-3 h-3 shrink-0" />
            <span>{{ item.integrity_hash.substring(0, 12) }}...</span>
          </div>
          <div v-if="item.previous_hash" class="font-mono text-[9px] text-slate-400" :title="`Previous Hash: ${item.previous_hash}`">
            prev: {{ item.previous_hash.substring(0, 10) }}...
          </div>
          <div v-else class="text-[9px] text-purple-400 font-semibold">
            genesis block
          </div>
        </div>
      </template>

      <!-- Details Action Cell -->
      <template #cell-actions="{ item }">
        <Button
          variant="outline"
          size="sm"
          @click="openEventDetails(item)"
        >
          <template #icon-left>
            <Eye class="w-3.5 h-3.5" />
          </template>
          Payload
        </Button>
      </template>
    </DataTable>

    <!-- Event Details Modal -->
    <Modal
      v-model="showDetailsModal"
      title="Audit Event Cryptographic Payload"
      :description="`Event ID: ${selectedEvent?.id}`"
      maxWidth="xl"
    >
      <div v-if="selectedEvent" class="space-y-4">
        <!-- Metadata summary -->
        <div class="grid grid-cols-2 gap-3 text-xs p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800">
          <div>
            <span class="text-slate-400 font-medium">Action:</span>
            <span class="font-mono font-bold text-slate-900 dark:text-slate-100 ml-1.5">{{ selectedEvent.action }}</span>
          </div>
          <div>
            <span class="text-slate-400 font-medium">Actor Type:</span>
            <span class="font-semibold text-slate-900 dark:text-slate-100 ml-1.5">{{ selectedEvent.actor_type }}</span>
          </div>
          <div>
            <span class="text-slate-400 font-medium">Actor ID:</span>
            <span class="font-mono text-slate-900 dark:text-slate-100 ml-1.5">{{ selectedEvent.actor_id || 'system' }}</span>
          </div>
          <div>
            <span class="text-slate-400 font-medium">IP Address:</span>
            <span class="font-mono text-slate-900 dark:text-slate-100 ml-1.5">{{ selectedEvent.ip_address || 'unknown' }}</span>
          </div>
        </div>

        <!-- Hash Chaining Verification -->
        <div class="p-3.5 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs space-y-2 border border-slate-800">
          <div class="text-[11px] text-slate-400 uppercase font-bold tracking-wider">Cryptographic Hash Verification</div>
          <div>
            <span class="text-slate-400">integrity_hash:</span>
            <div class="text-emerald-400 break-all select-all">{{ selectedEvent.integrity_hash }}</div>
          </div>
          <div>
            <span class="text-slate-400">previous_hash:</span>
            <div class="text-amber-400 break-all select-all">{{ selectedEvent.previous_hash || '0 (Genesis event)' }}</div>
          </div>
        </div>

        <!-- Details JSON Payload -->
        <div>
          <div class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
            Event Context & Details Payload
          </div>
          <pre class="p-4 rounded-xl bg-slate-900 text-emerald-300 font-mono text-xs overflow-x-auto max-h-60 border border-slate-800 select-all">{{ JSON.stringify(selectedEvent.details || {}, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <Button variant="outline" @click="showDetailsModal = false">
          Close
        </Button>
      </template>
    </Modal>
  </div>
</template>
