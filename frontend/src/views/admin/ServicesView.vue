<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useUiStore } from '@/stores/ui'
import type { ServiceDefinition } from '@/api/types'
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
  Clock
} from 'lucide-vue-next'

const admin = useAdminStore()
const ui = useUiStore()

// Create Service Modal
const showCreateModal = ref(false)
const createId = ref('')
const createName = ref('')
const createDesc = ref('')
const createRoles = ref('admin, operator, viewer')
const createDefaultRole = ref('viewer')
const isCreating = ref(false)

// Edit Service Modal
const showEditModal = ref(false)
const editingService = ref<ServiceDefinition | null>(null)
const editName = ref('')
const editDesc = ref('')
const editRoles = ref('')
const editDefaultRole = ref('')
const isUpdating = ref(false)

// Delete Service Modal
const showDeleteModal = ref(false)
const serviceToDelete = ref<ServiceDefinition | null>(null)
const isDeleting = ref(false)

async function loadServices() {
  await admin.fetchServices()
}

onMounted(() => {
  loadServices()
})

async function handleCreateService() {
  if (!createId.value.trim() || !createName.value.trim()) return

  const roles = createRoles.value
    .split(',')
    .map(r => r.trim())
    .filter(Boolean)

  if (!roles.length) {
    ui.showToast({
      type: 'error',
      title: 'Validation Error',
      message: 'At least one allowed role must be provided.'
    })
    return
  }

  isCreating.value = true
  try {
    await admin.createService({
      id: createId.value.trim(),
      name: createName.value.trim(),
      description: createDesc.value.trim() || undefined,
      allowed_roles: roles,
      default_role: createDefaultRole.value.trim() || undefined
    })

    showCreateModal.value = false
    createId.value = ''
    createName.value = ''
    createDesc.value = ''
    createRoles.value = 'admin, operator, viewer'
    createDefaultRole.value = 'viewer'
  } finally {
    isCreating.value = false
  }
}

function openEditModal(svc: ServiceDefinition) {
  editingService.value = svc
  editName.value = svc.name
  editDesc.value = svc.description || ''
  editRoles.value = svc.allowed_roles.join(', ')
  editDefaultRole.value = svc.default_role || ''
  showEditModal.value = true
}

async function handleUpdateService() {
  if (!editingService.value || !editName.value.trim()) return

  const roles = editRoles.value
    .split(',')
    .map(r => r.trim())
    .filter(Boolean)

  isUpdating.value = true
  try {
    await admin.updateService(editingService.value.id, {
      name: editName.value.trim(),
      description: editDesc.value.trim() || null,
      allowed_roles: roles.length ? roles : undefined,
      default_role: editDefaultRole.value.trim() || null
    })
    showEditModal.value = false
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

        <Input
          v-model="createRoles"
          label="Allowed Roles (comma-separated)"
          placeholder="admin, operator, viewer"
          required
          hint="Comma-separated list of RBAC roles."
        />

        <Input
          v-model="createDefaultRole"
          label="Default Fallback Role"
          placeholder="viewer"
          hint="Must be one of the allowed roles specified above."
        />

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

        <Input
          v-model="editRoles"
          label="Allowed Roles (comma-separated)"
          required
        />

        <Input
          v-model="editDefaultRole"
          label="Default Role"
        />

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
  </div>
</template>
