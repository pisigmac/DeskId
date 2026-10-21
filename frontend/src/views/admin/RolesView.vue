<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api } from '@/api/client'
import { useAdminStore } from '@/stores/admin'
import { useUiStore } from '@/stores/ui'
import type { RoleOverviewItem } from '@/api/types'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import Modal from '@/components/common/Modal.vue'
import {
  Plus,
  RefreshCw,
  Search,
  Users,
  Server,
  Trash2,
  UserCheck,
  Building2,
  KeyRound
} from 'lucide-vue-next'

const admin = useAdminStore()
const ui = useUiStore()

const roles = ref<RoleOverviewItem[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedServiceFilter = ref('')

// Add Role Modal
const showCreateModal = ref(false)
const createServiceId = ref('')
const createRoleName = ref('')
const createIsDefault = ref(false)
const isCreating = ref(false)

// Drill-Down Users Modal
const showUsersModal = ref(false)
const selectedRole = ref<RoleOverviewItem | null>(null)

// Delete Role Modal
const showDeleteModal = ref(false)
const roleToDelete = ref<RoleOverviewItem | null>(null)
const isDeleting = ref(false)

async function loadRoles() {
  loading.value = true
  try {
    const res = await api.listRoles(selectedServiceFilter.value || undefined)
    roles.value = res.roles
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to load roles',
      message: err?.error || err.message || 'Could not fetch roles matrix.'
    })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    loadRoles(),
    admin.fetchServices()
  ])
  if (admin.services.length && !createServiceId.value) {
    createServiceId.value = admin.services[0].id
  }
})

const filteredRoles = computed(() => {
  let list = roles.value
  if (selectedServiceFilter.value) {
    list = list.filter(r => r.service_id === selectedServiceFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(r =>
      r.role.toLowerCase().includes(q) ||
      r.service_name.toLowerCase().includes(q) ||
      r.service_id.toLowerCase().includes(q)
    )
  }
  return list
})

const totalAssignments = computed(() => {
  return roles.value.reduce((acc, r) => acc + r.assigned_count, 0)
})

const uniqueServicesCount = computed(() => {
  const set = new Set(roles.value.map(r => r.service_id))
  return set.size
})

function openUsersModal(roleItem: RoleOverviewItem) {
  selectedRole.value = roleItem
  showUsersModal.value = true
}

function promptDeleteRole(roleItem: RoleOverviewItem) {
  roleToDelete.value = roleItem
  showDeleteModal.value = true
}

async function handleCreateRole() {
  if (!createServiceId.value || !createRoleName.value.trim()) return

  isCreating.value = true
  try {
    await api.createRole({
      service_id: createServiceId.value,
      role: createRoleName.value.trim(),
      is_default: createIsDefault.value
    })

    ui.showToast({
      type: 'success',
      title: 'Role Created',
      message: `Role '${createRoleName.value.trim()}' added to service '${createServiceId.value}'.`
    })

    showCreateModal.value = false
    createRoleName.value = ''
    createIsDefault.value = false
    await loadRoles()
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to create role',
      message: err?.error || err.message || 'Error creating role.'
    })
  } finally {
    isCreating.value = false
  }
}

async function confirmDeleteRole() {
  if (!roleToDelete.value) return

  isDeleting.value = true
  try {
    await api.deleteRole(roleToDelete.value.service_id, roleToDelete.value.role)
    ui.showToast({
      type: 'success',
      title: 'Role Deleted',
      message: `Role '${roleToDelete.value.role}' removed from service '${roleToDelete.value.service_id}'.`
    })
    showDeleteModal.value = false
    roleToDelete.value = null
    await loadRoles()
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to delete role',
      message: err?.error || err.message || 'Could not delete role.'
    })
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
          Roles & Permissions
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Unified role catalog across downstream microservices, audience boundaries, and live assignment tracking.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :loading="loading"
          @click="loadRoles"
        >
          <template #icon-left>
            <RefreshCw class="w-4 h-4" />
          </template>
          Refresh
        </Button>

        <Button
          size="sm"
          @click="showCreateModal = true"
        >
          <template #icon-left>
            <Plus class="w-4 h-4" />
          </template>
          Add Role
        </Button>
      </div>
    </div>

    <!-- Stats Bar -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex items-center gap-3.5 shadow-xs">
        <div class="p-3 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
          <KeyRound class="w-5 h-5" />
        </div>
        <div>
          <div class="text-2xl font-bold text-slate-900 dark:text-slate-100">{{ roles.length }}</div>
          <div class="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Total Defined Roles</div>
        </div>
      </div>

      <div class="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex items-center gap-3.5 shadow-xs">
        <div class="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
          <UserCheck class="w-5 h-5" />
        </div>
        <div>
          <div class="text-2xl font-bold text-slate-900 dark:text-slate-100">{{ totalAssignments }}</div>
          <div class="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Active User Grants</div>
        </div>
      </div>

      <div class="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex items-center gap-3.5 shadow-xs">
        <div class="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
          <Server class="w-5 h-5" />
        </div>
        <div>
          <div class="text-2xl font-bold text-slate-900 dark:text-slate-100">{{ uniqueServicesCount }}</div>
          <div class="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Covered Services</div>
        </div>
      </div>
    </div>

    <!-- Filter & Search Controls -->
    <div class="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white dark:bg-slate-900 p-3 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
      <div class="relative w-full sm:w-80">
        <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter roles or services..."
          class="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>

      <div class="flex items-center gap-2 w-full sm:w-auto">
        <span class="text-xs text-slate-500 whitespace-nowrap">Filter Service:</span>
        <select
          v-model="selectedServiceFilter"
          @change="loadRoles"
          class="px-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-500"
        >
          <option value="">All Services</option>
          <option
            v-for="svc in admin.services"
            :key="svc.id"
            :value="svc.id"
          >
            {{ svc.name }} ({{ svc.id }})
          </option>
        </select>
      </div>
    </div>

    <!-- Roles Grid / Table -->
    <div v-if="loading" class="p-12 text-center text-xs text-slate-500">
      Loading roles catalog...
    </div>

    <div v-else-if="filteredRoles.length === 0" class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
      <div class="p-3 bg-slate-100 dark:bg-slate-800 rounded-2xl text-slate-400 dark:text-slate-500 max-w-fit mx-auto mb-3">
        <KeyRound class="w-6 h-6" />
      </div>
      <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">No roles found</h3>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Register a new role or clear search filters to view catalog.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="item in filteredRoles"
        :key="`${item.service_id}:${item.role}`"
      >
        <template #header>
          <div class="flex items-start justify-between w-full min-w-0">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 shrink-0">
                <KeyRound class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono truncate">
                  {{ item.role }}
                </h3>
                <p class="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  {{ item.service_name }}
                </p>
              </div>
            </div>

            <Badge
              v-if="item.is_default"
              variant="purple"
              size="sm"
            >
              Default
            </Badge>
          </div>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between text-xs pt-1">
            <span class="text-slate-500 dark:text-slate-400">Audience ID:</span>
            <span class="font-mono text-[11px] text-brand-600 dark:text-brand-400 font-medium">
              {{ item.service_id }}
            </span>
          </div>

          <div class="flex items-center justify-between text-xs border-t border-slate-100 dark:border-slate-800 pt-2.5">
            <span class="text-slate-500 dark:text-slate-400">Assigned Users:</span>
            <button
              type="button"
              class="font-semibold text-xs flex items-center gap-1.5 hover:underline transition-colors"
              :class="item.assigned_count > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'"
              @click="openUsersModal(item)"
            >
              <Users class="w-3.5 h-3.5" />
              {{ item.assigned_count }} {{ item.assigned_count === 1 ? 'user' : 'users' }}
            </button>
          </div>
        </div>

        <template #footer>
          <div class="flex items-center justify-between w-full">
            <Button
              variant="outline"
              size="sm"
              @click="openUsersModal(item)"
            >
              <template #icon-left>
                <Users class="w-3.5 h-3.5" />
              </template>
              View Users
            </Button>

            <Button
              variant="ghost"
              size="sm"
              title="Delete Role"
              @click="promptDeleteRole(item)"
            >
              <Trash2 class="w-4 h-4 text-rose-500" />
            </Button>
          </div>
        </template>
      </Card>
    </div>

    <!-- Assigned Users Drill-Down Modal -->
    <Modal
      v-model="showUsersModal"
      :title="`Assigned Users — ${selectedRole?.service_id}:${selectedRole?.role}`"
      description="All users who currently hold an active product grant with this role."
    >
      <div v-if="!selectedRole?.assigned_users.length" class="p-8 text-center text-xs text-slate-500">
        No users are currently assigned to this role.
      </div>
      <div v-else class="space-y-2 max-h-96 overflow-y-auto pr-1">
        <div
          v-for="u in selectedRole.assigned_users"
          :key="u.grant_id"
          class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex items-center justify-between text-xs"
        >
          <div>
            <div class="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
              {{ u.email }}
              <span v-if="u.display_name" class="text-slate-400 font-normal">({{ u.display_name }})</span>
            </div>
            <div class="text-[11px] text-slate-500 mt-0.5 flex items-center gap-1">
              <Building2 class="w-3 h-3 text-slate-400" />
              Scope: <span class="font-medium text-slate-700 dark:text-slate-300">{{ u.org_name }}</span>
            </div>
          </div>
          <span class="text-[10px] font-mono text-slate-400">
            {{ u.user_id.slice(0, 8) }}...
          </span>
        </div>
      </div>

      <div class="flex justify-end pt-3">
        <Button variant="outline" size="sm" @click="showUsersModal = false">
          Close
        </Button>
      </div>
    </Modal>

    <!-- Create Role Modal -->
    <Modal
      v-model="showCreateModal"
      title="Create New Role"
      description="Add a new custom role to an existing microservice audience."
    >
      <form @submit.prevent="handleCreateRole" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Target Service
          </label>
          <select
            v-model="createServiceId"
            class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
            required
          >
            <option
              v-for="svc in admin.services"
              :key="svc.id"
              :value="svc.id"
            >
              {{ svc.name }} ({{ svc.id }})
            </option>
          </select>
        </div>

        <Input
          v-model="createRoleName"
          label="Role Name"
          placeholder="e.g. pipeline-runner, editor, security-auditor"
          required
          hint="Unique role identifier within this service."
        />

        <div class="flex items-center gap-2 pt-1">
          <input
            id="role-is-default"
            v-model="createIsDefault"
            type="checkbox"
            class="rounded border-slate-300 text-purple-600 focus:ring-purple-500 w-4 h-4"
          />
          <label for="role-is-default" class="text-xs text-slate-700 dark:text-slate-300 font-medium">
            Set as default fallback role for this service
          </label>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="showCreateModal = false">
            Cancel
          </Button>
          <Button type="submit" :loading="isCreating" :disabled="!createRoleName.trim()">
            Create Role
          </Button>
        </div>
      </form>
    </Modal>

    <!-- Delete Role Modal -->
    <Modal
      v-model="showDeleteModal"
      title="Delete Role"
      description="Remove this role taxonomy from the service."
    >
      <p class="text-xs text-rose-600 dark:text-rose-400 mb-4">
        Are you sure you want to delete role <span class="font-bold">{{ roleToDelete?.role }}</span> from service <span class="font-bold">{{ roleToDelete?.service_id }}</span>?
        <span v-if="roleToDelete?.assigned_count" class="block mt-1 font-semibold">
          Warning: {{ roleToDelete.assigned_count }} user(s) currently hold this role grant!
        </span>
      </p>

      <div class="flex justify-end gap-3">
        <Button variant="outline" @click="showDeleteModal = false">
          Cancel
        </Button>
        <Button
          variant="danger"
          :loading="isDeleting"
          @click="confirmDeleteRole"
        >
          Confirm Delete
        </Button>
      </div>
    </Modal>
  </div>
</template>
