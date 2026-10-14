<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import { useUiStore } from '@/stores/ui'
import type { Session } from '@/api/types'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Badge from '@/components/common/Badge.vue'
import {
  Laptop,
  Smartphone,
  Globe,
  Clock,
  Trash2,
  RefreshCw,
  CheckCircle2
} from 'lucide-vue-next'

const ui = useUiStore()

const sessions = ref<Session[]>([])
const isLoading = ref(false)
const isRevokingAll = ref(false)
const revokingId = ref<string | null>(null)

async function fetchSessions() {
  isLoading.value = true
  try {
    sessions.value = await api.getSessions()
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to load sessions',
      message: err?.error || 'Could not retrieve active sessions'
    })
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchSessions()
})

async function handleRevokeSession(sessionId: string) {
  revokingId.value = sessionId
  try {
    await api.revokeSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    ui.showToast({
      type: 'success',
      title: 'Session Revoked',
      message: 'The selected session was terminated.'
    })
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Revocation failed',
      message: err?.error || 'Could not revoke session'
    })
  } finally {
    revokingId.value = null
  }
}

async function handleRevokeAll() {
  isRevokingAll.value = true
  try {
    const res = await api.revokeAllSessions()
    await fetchSessions()
    ui.showToast({
      type: 'success',
      title: 'Sessions Revoked',
      message: `Successfully terminated ${res.revoked} active sessions.`
    })
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Action failed',
      message: err?.error || 'Could not revoke all sessions'
    })
  } finally {
    isRevokingAll.value = false
  }
}

function formatDate(iso: string) {
  if (!iso) return 'N/A'
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return iso
  }
}

function getDeviceIcon(userAgent?: string | null) {
  if (!userAgent) return Globe
  const ua = userAgent.toLowerCase()
  if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
    return Smartphone
  }
  return Laptop
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Active Sessions
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Review and manage browser sessions and API refresh tokens currently active for your identity.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :loading="isLoading"
          @click="fetchSessions"
        >
          <template #icon-left>
            <RefreshCw class="w-4 h-4" />
          </template>
          Refresh
        </Button>
        <Button
          variant="danger"
          size="sm"
          :loading="isRevokingAll"
          :disabled="sessions.length <= 1"
          @click="handleRevokeAll"
        >
          <template #icon-left>
            <Trash2 class="w-4 h-4" />
          </template>
          Revoke Other Sessions
        </Button>
      </div>
    </div>

    <!-- Sessions List -->
    <Card noPadding>
      <div v-if="isLoading" class="p-8 text-center text-xs text-slate-500">
        Loading active sessions...
      </div>

      <div v-else-if="sessions.length === 0" class="p-8 text-center text-xs text-slate-500">
        No active sessions found.
      </div>

      <div v-else class="divide-y divide-slate-100 dark:divide-slate-800">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-800/20 transition-colors"
        >
          <div class="flex items-start gap-4 min-w-0">
            <div class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 shrink-0 mt-0.5">
              <component :is="getDeviceIcon(session.user_agent)" class="w-5 h-5" />
            </div>

            <div class="min-w-0 space-y-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-bold text-slate-900 dark:text-slate-100 truncate max-w-sm">
                  {{ session.user_agent || 'Unknown Client Browser' }}
                </span>
                <Badge v-if="!session.revoked" variant="success" size="sm">
                  <CheckCircle2 class="w-3 h-3" />
                  Active
                </Badge>
                <Badge v-else variant="danger" size="sm">
                  Revoked
                </Badge>
              </div>

              <div class="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
                <span v-if="session.ip_address" class="flex items-center gap-1 font-mono">
                  <Globe class="w-3.5 h-3.5" />
                  {{ session.ip_address }}
                </span>
                <span class="flex items-center gap-1">
                  <Clock class="w-3.5 h-3.5" />
                  Created: {{ formatDate(session.created_at) }}
                </span>
                <span>
                  Expires: {{ formatDate(session.expires_at) }}
                </span>
              </div>
            </div>
          </div>

          <div class="shrink-0">
            <Button
              variant="outline"
              size="sm"
              :disabled="session.revoked"
              :loading="revokingId === session.id"
              @click="handleRevokeSession(session.id)"
            >
              <template #icon-left>
                <Trash2 class="w-3.5 h-3.5 text-rose-500" />
              </template>
              Revoke
            </Button>
          </div>
        </div>
      </div>
    </Card>
  </div>
</template>
