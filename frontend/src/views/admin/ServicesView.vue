<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import { useAdminStore } from '@/stores/admin'
import { useUiStore } from '@/stores/ui'
import type { ServiceDefinition, ServiceConfigResponse } from '@/api/types'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import Modal from '@/components/common/Modal.vue'
import {
  Server,
  Plus,
  Edit2,
  Trash2,
  KeyRound,
  RefreshCw,
  Clock,
  FileCode,
  Download,
  Copy,
  Check
} from 'lucide-vue-next'

const admin = useAdminStore()
const ui = useUiStore()

const COMMON_ROLES = ['admin', 'editor', 'operator', 'viewer', 'auditor']

// Create Service Modal
const showCreateModal = ref(false)
const createId = ref('')
const createName = ref('')
const createDesc = ref('')
const createSelectedRoles = ref<string[]>(['admin', 'editor', 'viewer'])
const createCustomRoleInput = ref('')
const createDefaultRole = ref('editor')
const isCreating = ref(false)

function toggleCreateRole(role: string) {
  const index = createSelectedRoles.value.indexOf(role)
  if (index >= 0) {
    if (createSelectedRoles.value.length === 1) {
      ui.showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'At least one allowed role must remain selected.'
      })
      return
    }
    createSelectedRoles.value.splice(index, 1)
    if (createDefaultRole.value === role) {
      createDefaultRole.value = createSelectedRoles.value[0] || ''
    }
  } else {
    createSelectedRoles.value.push(role)
    if (!createDefaultRole.value) {
      createDefaultRole.value = role
    }
  }
}

function addCreateCustomRole() {
  const trimmed = createCustomRoleInput.value.trim().toLowerCase()
  if (!trimmed) return
  if (!createSelectedRoles.value.includes(trimmed)) {
    createSelectedRoles.value.push(trimmed)
    if (!createDefaultRole.value) {
      createDefaultRole.value = trimmed
    }
  }
  createCustomRoleInput.value = ''
}

function removeCreateRole(role: string) {
  if (createSelectedRoles.value.length === 1) {
    ui.showToast({
      type: 'error',
      title: 'Validation Error',
      message: 'At least one allowed role must remain selected.'
    })
    return
  }
  createSelectedRoles.value = createSelectedRoles.value.filter(r => r !== role)
  if (createDefaultRole.value === role) {
    createDefaultRole.value = createSelectedRoles.value[0] || ''
  }
}

// Edit Service Modal
const showEditModal = ref(false)
const editingService = ref<ServiceDefinition | null>(null)
const editName = ref('')
const editDesc = ref('')
const editSelectedRoles = ref<string[]>([])
const editCustomRoleInput = ref('')
const editDefaultRole = ref('')
const isUpdating = ref(false)

function toggleEditRole(role: string) {
  const index = editSelectedRoles.value.indexOf(role)
  if (index >= 0) {
    if (editSelectedRoles.value.length === 1) {
      ui.showToast({
        type: 'error',
        title: 'Validation Error',
        message: 'At least one allowed role must remain selected.'
      })
      return
    }
    editSelectedRoles.value.splice(index, 1)
    if (editDefaultRole.value === role) {
      editDefaultRole.value = editSelectedRoles.value[0] || ''
    }
  } else {
    editSelectedRoles.value.push(role)
    if (!editDefaultRole.value) {
      editDefaultRole.value = role
    }
  }
}

function addEditCustomRole() {
  const trimmed = editCustomRoleInput.value.trim().toLowerCase()
  if (!trimmed) return
  if (!editSelectedRoles.value.includes(trimmed)) {
    editSelectedRoles.value.push(trimmed)
    if (!editDefaultRole.value) {
      editDefaultRole.value = trimmed
    }
  }
  editCustomRoleInput.value = ''
}

function removeEditRole(role: string) {
  if (editSelectedRoles.value.length === 1) {
    ui.showToast({
      type: 'error',
      title: 'Validation Error',
      message: 'At least one allowed role must remain selected.'
    })
    return
  }
  editSelectedRoles.value = editSelectedRoles.value.filter(r => r !== role)
  if (editDefaultRole.value === role) {
    editDefaultRole.value = editSelectedRoles.value[0] || ''
  }
}

// Delete Service Modal
const showDeleteModal = ref(false)
const serviceToDelete = ref<ServiceDefinition | null>(null)
const isDeleting = ref(false)

// Config Export Modal
const showConfigModal = ref(false)
const selectedConfigService = ref<ServiceDefinition | null>(null)
const configData = ref<ServiceConfigResponse | null>(null)
const configLoading = ref(false)
const copied = ref(false)

async function openConfigModal(svc: ServiceDefinition) {
  selectedConfigService.value = svc
  showConfigModal.value = true
  configLoading.value = true
  copied.value = false
  try {
    const data = await api.getServiceConfig(svc.id)
    configData.value = data
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to load configuration',
      message: err?.error || err.message || 'Could not fetch service integration details.'
    })
  } finally {
    configLoading.value = false
  }
}

function copyEnv() {
  if (!configData.value?.env_content) return
  navigator.clipboard.writeText(configData.value.env_content)
  copied.value = true
  ui.showToast({
    type: 'success',
    title: 'Copied to clipboard',
    message: `.env configuration for ${selectedConfigService.value?.id} copied.`
  })
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

function downloadEnv() {
  if (!configData.value?.env_content || !selectedConfigService.value) return
  const blob = new Blob([configData.value.env_content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedConfigService.value.id}.env`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function loadServices() {
  await admin.fetchServices()
}

onMounted(() => {
  loadServices()
})

async function handleCreateService() {
  if (!createId.value.trim() || !createName.value.trim()) return

  if (!createSelectedRoles.value.length) {
    ui.showToast({
      type: 'error',
      title: 'Validation Error',
      message: 'At least one allowed role must be selected.'
    })
    return
  }

  isCreating.value = true
  try {
    await admin.createService({
      id: createId.value.trim(),
      name: createName.value.trim(),
      description: createDesc.value.trim() || undefined,
      allowed_roles: createSelectedRoles.value,
      default_role: createDefaultRole.value.trim() || undefined
    })

    showCreateModal.value = false
    createId.value = ''
    createName.value = ''
    createDesc.value = ''
    createSelectedRoles.value = ['admin', 'editor', 'viewer']
    createCustomRoleInput.value = ''
    createDefaultRole.value = 'editor'
  } finally {
    isCreating.value = false
  }
}

function openEditModal(svc: ServiceDefinition) {
  editingService.value = svc
  editName.value = svc.name
  editDesc.value = svc.description || ''
  editSelectedRoles.value = [...(svc.allowed_roles || [])]
  editCustomRoleInput.value = ''
  editDefaultRole.value = svc.default_role || editSelectedRoles.value[0] || ''
  showEditModal.value = true
}

async function handleUpdateService() {
  if (!editingService.value || !editName.value.trim()) return

  if (!editSelectedRoles.value.length) {
    ui.showToast({
      type: 'error',
      title: 'Validation Error',
      message: 'At least one allowed role must be selected.'
    })
    return
  }

  isUpdating.value = true
  try {
    await admin.updateService(editingService.value.id, {
      name: editName.value.trim(),
      description: editDesc.value.trim() || null,
      allowed_roles: editSelectedRoles.value,
      default_role: editDefaultRole.value.trim() || null
    })
    showEditModal.value = false
    editingService.value = null
  } finally {
    isUpdating.value = false
  }
}

function promptDelete(svc: ServiceDefinition) {
  serviceToDelete.value = svc
  showDeleteModal.value = true
}

async function confirmDeleteService() {
  if (!serviceToDelete.value) return
  isDeleting.value = true
  try {
    await admin.deleteService(serviceToDelete.value.id)
    showDeleteModal.value = false
    serviceToDelete.value = null
  } finally {
    isDeleting.value = false
  }
}

function formatDate(iso: string) {
  if (!iso) return 'N/A'
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
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
          Service Registry
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Register audience IDs and define custom RBAC role vocabularies for downstream microservices.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :loading="admin.servicesLoading"
          @click="loadServices"
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
          Register Service
        </Button>
      </div>
    </div>

    <!-- Services Grid -->
    <div v-if="admin.servicesLoading" class="p-12 text-center text-xs text-slate-500">
      Loading services registry...
    </div>

    <div v-else-if="admin.services.length === 0" class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
      <div class="p-3 bg-slate-100 dark:bg-slate-800 rounded-2xl text-slate-400 dark:text-slate-500 max-w-fit mx-auto mb-3">
        <Server class="w-6 h-6" />
      </div>
      <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">No services registered</h3>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Add your first microservice to configure audience roles and JWT claim validation.</p>
      <div class="mt-4">
        <Button size="sm" @click="showCreateModal = true">
          <template #icon-left>
            <Plus class="w-4 h-4" />
          </template>
          Register Service
        </Button>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="svc in admin.services"
        :key="svc.id"
      >
        <template #header>
          <div class="flex items-start gap-3 min-w-0">
            <div class="p-2.5 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400 shrink-0">
              <Server class="w-5 h-5" />
            </div>
            <div class="min-w-0">
              <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">
                {{ svc.name }}
              </h3>
              <p class="text-[11px] font-mono text-brand-600 dark:text-brand-400 truncate mt-0.5">
                Audience: {{ svc.id }}
              </p>
            </div>
          </div>
        </template>

        <div class="space-y-4">
          <p class="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 min-h-[32px]">
            {{ svc.description || 'No description provided.' }}
          </p>

          <div>
            <div class="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5 flex items-center gap-1">
              <KeyRound class="w-3 h-3 text-slate-400" />
              Allowed Roles ({{ svc.allowed_roles.length }})
            </div>
            <div class="flex flex-wrap gap-1.5">
              <Badge
                v-for="role in svc.allowed_roles"
                :key="role"
                :variant="role === svc.default_role ? 'purple' : 'neutral'"
                size="sm"
              >
                {{ role }}
                <span v-if="role === svc.default_role" class="text-[9px] opacity-75">(default)</span>
              </Badge>
            </div>
          </div>

          <div class="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
            <span class="flex items-center gap-1">
              <Clock class="w-3 h-3" />
              Created {{ formatDate(svc.created_at) }}
            </span>
          </div>
        </div>

        <template #footer>
          <div class="flex items-center justify-between w-full">
            <Button
              variant="outline"
              size="sm"
              class="border-purple-200 dark:border-purple-800 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/40"
              @click="openConfigModal(svc)"
            >
              <template #icon-left>
                <FileCode class="w-3.5 h-3.5" />
              </template>
              Client Config
            </Button>

            <div class="flex items-center gap-1.5">
              <Button
                variant="outline"
                size="sm"
                @click="openEditModal(svc)"
              >
                <template #icon-left>
                  <Edit2 class="w-3.5 h-3.5" />
                </template>
                Edit
              </Button>

              <Button
                variant="ghost"
                size="sm"
                @click="promptDelete(svc)"
              >
                <Trash2 class="w-4 h-4 text-rose-500" />
              </Button>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Register Service Modal -->
    <Modal
      v-model="showCreateModal"
      title="Register Microservice"
      description="Define service audience identifier and role hierarchy."
    >
      <form @submit.prevent="handleCreateService" class="space-y-4">
        <Input
          v-model="createId"
          label="Audience ID"
          placeholder="e.g. billing-service"
          required
          hint="Unique identifier matched in JWT aud claim."
        />

        <Input
          v-model="createName"
          label="Service Name"
          placeholder="e.g. Billing & Invoicing Engine"
          required
        />

        <Input
          v-model="createDesc"
          label="Description"
          placeholder="Optional service summary"
        />

        <!-- Allowed Roles Checklist & Custom Tag Input -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Allowed Roles
          </label>
          <p class="text-[11px] text-slate-500 dark:text-slate-400 mb-2">
            Select standard roles or add custom roles for this service.
          </p>

          <!-- Common Standard Roles Checklist -->
          <div class="flex flex-wrap gap-1.5 mb-2.5">
            <button
              v-for="role in COMMON_ROLES"
              :key="role"
              type="button"
              @click="toggleCreateRole(role)"
              :class="[
                'px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition-all',
                createSelectedRoles.includes(role)
                  ? 'bg-purple-50 dark:bg-purple-950/60 border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 font-semibold shadow-xs'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'
              ]"
            >
              <Check v-if="createSelectedRoles.includes(role)" class="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
              <span v-else class="w-3.5 h-3.5 rounded border border-slate-300 dark:border-slate-700 inline-block"></span>
              {{ role }}
            </button>
          </div>

          <!-- Custom Role Input -->
          <div class="flex items-center gap-2">
            <input
              v-model="createCustomRoleInput"
              type="text"
              placeholder="Add custom role (e.g. data-reader)..."
              class="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
              @keydown.enter.prevent="addCreateCustomRole"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              :disabled="!createCustomRoleInput.trim()"
              @click="addCreateCustomRole"
            >
              <template #icon-left>
                <Plus class="w-3.5 h-3.5" />
              </template>
              Add
            </Button>
          </div>

          <!-- Active Roles Summary -->
          <div class="mt-2.5 flex flex-wrap gap-1.5 items-center">
            <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider mr-1">Selected Roles ({{ createSelectedRoles.length }}):</span>
            <span
              v-for="role in createSelectedRoles"
              :key="role"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
            >
              {{ role }}
              <button
                type="button"
                @click="removeCreateRole(role)"
                class="hover:text-rose-500 text-slate-400 hover:text-slate-600 dark:hover:text-rose-400 transition-colors ml-0.5"
                title="Remove role"
              >
                &times;
              </button>
            </span>
          </div>
        </div>

        <!-- Default Role Dropdown -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Default Role
          </label>
          <select
            v-model="createDefaultRole"
            class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option
              v-for="role in createSelectedRoles"
              :key="role"
              :value="role"
            >
              {{ role }}
            </option>
          </select>
          <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Assigned when granting access without an explicit role.
          </p>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="showCreateModal = false">
            Cancel
          </Button>
          <Button type="submit" :loading="isCreating" :disabled="!createId.trim() || !createName.trim()">
            Register Service
          </Button>
        </div>
      </form>
    </Modal>

    <!-- Edit Service Modal -->
    <Modal
      v-model="showEditModal"
      :title="`Edit Service — ${editingService?.id}`"
      description="Update service configuration and allowed role set."
    >
      <form @submit.prevent="handleUpdateService" class="space-y-4">
        <Input
          v-model="editName"
          label="Service Name"
          required
        />

        <Input
          v-model="editDesc"
          label="Description"
        />

        <!-- Allowed Roles Checklist & Custom Tag Input -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Allowed Roles
          </label>
          <p class="text-[11px] text-slate-500 dark:text-slate-400 mb-2">
            Select standard roles or add custom roles for this service.
          </p>

          <!-- Common Standard Roles Checklist -->
          <div class="flex flex-wrap gap-1.5 mb-2.5">
            <button
              v-for="role in COMMON_ROLES"
              :key="role"
              type="button"
              @click="toggleEditRole(role)"
              :class="[
                'px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition-all',
                editSelectedRoles.includes(role)
                  ? 'bg-purple-50 dark:bg-purple-950/60 border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 font-semibold shadow-xs'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300'
              ]"
            >
              <Check v-if="editSelectedRoles.includes(role)" class="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
              <span v-else class="w-3.5 h-3.5 rounded border border-slate-300 dark:border-slate-700 inline-block"></span>
              {{ role }}
            </button>
          </div>

          <!-- Custom Role Input -->
          <div class="flex items-center gap-2">
            <input
              v-model="editCustomRoleInput"
              type="text"
              placeholder="Add custom role (e.g. data-reader)..."
              class="flex-1 px-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
              @keydown.enter.prevent="addEditCustomRole"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              :disabled="!editCustomRoleInput.trim()"
              @click="addEditCustomRole"
            >
              <template #icon-left>
                <Plus class="w-3.5 h-3.5" />
              </template>
              Add
            </Button>
          </div>

          <!-- Active Roles Summary -->
          <div class="mt-2.5 flex flex-wrap gap-1.5 items-center">
            <span class="text-[10px] uppercase font-bold text-slate-400 tracking-wider mr-1">Selected Roles ({{ editSelectedRoles.length }}):</span>
            <span
              v-for="role in editSelectedRoles"
              :key="role"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
            >
              {{ role }}
              <button
                type="button"
                @click="removeEditRole(role)"
                class="hover:text-rose-500 text-slate-400 hover:text-slate-600 dark:hover:text-rose-400 transition-colors ml-0.5"
                title="Remove role"
              >
                &times;
              </button>
            </span>
          </div>
        </div>

        <!-- Default Role Dropdown -->
        <div>
          <label class="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
            Default Role
          </label>
          <select
            v-model="editDefaultRole"
            class="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option
              v-for="role in editSelectedRoles"
              :key="role"
              :value="role"
            >
              {{ role }}
            </option>
          </select>
          <p class="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Assigned when granting access without an explicit role.
          </p>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="showEditModal = false">
            Cancel
          </Button>
          <Button type="submit" :loading="isUpdating">
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>

    <!-- Delete Service Modal -->
    <Modal
      v-model="showDeleteModal"
      title="Delete Service Definition"
      description="Are you sure you want to remove this service definition from DeskID?"
    >
      <p class="text-xs text-rose-600 dark:text-rose-400 mb-4">
        Removing <span class="font-bold">{{ serviceToDelete?.name }}</span> ({{ serviceToDelete?.id }}) will invalidate audience checks for new token requests.
      </p>

      <div class="flex justify-end gap-3">
        <Button variant="outline" @click="showDeleteModal = false">
          Cancel
        </Button>
        <Button
          variant="danger"
          :loading="isDeleting"
          @click="confirmDeleteService"
        >
          Confirm Delete
        </Button>
      </div>
    </Modal>

    <!-- Client Config / Integration Modal -->
    <Modal
      v-model="showConfigModal"
      :title="`Client Integration Config — ${selectedConfigService?.name || selectedConfigService?.id}`"
      description="Ready-to-use client credentials, endpoints, and environment variables."
    >
      <div v-if="configLoading" class="p-8 text-center text-xs text-slate-500">
        Generating configuration files...
      </div>
      <div v-else-if="configData" class="space-y-4">
        <!-- Server File Path Indicator -->
        <div class="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-slate-700 dark:text-slate-300">Auto-Generated File on DeskID:</span>
            <span class="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <Check class="w-3 h-3" /> Saved to disk
            </span>
          </div>
          <p class="font-mono text-[11px] text-slate-500 truncate">
            {{ configData.files.env_path }}
          </p>
        </div>

        <!-- Code Block -->
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-xs font-semibold text-slate-700 dark:text-slate-300">Client .env Configuration</span>
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="text-xs text-brand-600 hover:text-brand-700 dark:text-brand-400 flex items-center gap-1 font-medium"
                @click="copyEnv"
              >
                <Check v-if="copied" class="w-3.5 h-3.5 text-emerald-500" />
                <Copy v-else class="w-3.5 h-3.5" />
                {{ copied ? 'Copied!' : 'Copy .env' }}
              </button>
            </div>
          </div>
          <pre class="p-3 bg-slate-950 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto leading-relaxed border border-slate-800">{{ configData.env_content }}</pre>
        </div>

        <div class="flex items-center justify-between pt-2">
          <Button
            variant="outline"
            size="sm"
            @click="downloadEnv"
          >
            <template #icon-left>
              <Download class="w-3.5 h-3.5" />
            </template>
            Download {{ selectedConfigService?.id }}.env
          </Button>

          <Button variant="outline" size="sm" @click="showConfigModal = false">
            Close
          </Button>
        </div>
      </div>
    </Modal>
  </div>
</template>
