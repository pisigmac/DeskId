<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import { useUiStore } from '@/stores/ui'
import { api } from '@/api/client'
import type { Org } from '@/api/types'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import Modal from '@/components/common/Modal.vue'
import {
  Building2,
  Plus,
  Users,
  Trash2,
  UserPlus,
  UserMinus,
  RefreshCw,
  Crown
} from 'lucide-vue-next'

const admin = useAdminStore()
const ui = useUiStore()

const showCreateModal = ref(false)
const newOrgName = ref('')
const isCreating = ref(false)

// Manage Members Modal
const selectedOrg = ref<Org | null>(null)
const showMembersModal = ref(false)
const membersList = ref<Array<{ user_id: string; role: string; workspace_id?: string | null }>>([])
const isLoadingMembers = ref(false)

// Add Member Form
const addUserId = ref('')
const addRole = ref('member')
const addWorkspaceId = ref('')
const isAddingMember = ref(false)

// Delete Org
const showDeleteModal = ref(false)
const orgToDelete = ref<Org | null>(null)
const isDeletingOrg = ref(false)

async function loadOrganizations() {
  await admin.fetchOrganizations()
}

onMounted(() => {
  loadOrganizations()
})

async function handleCreateOrg() {
  if (!newOrgName.value.trim()) return
  isCreating.value = true
  try {
    await admin.createOrganization(newOrgName.value.trim())
    showCreateModal.value = false
    newOrgName.value = ''
  } finally {
    isCreating.value = false
  }
}

async function openMembersModal(org: Org) {
  selectedOrg.value = org
  showMembersModal.value = true
  isLoadingMembers.value = true
  try {
    const res = await api.getOrgMembers(org.id)
    membersList.value = res.members
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to load members',
      message: err?.error || 'Could not fetch organization membership list'
    })
  } finally {
    isLoadingMembers.value = false
  }
}

async function handleAddMember() {
  if (!selectedOrg.value || !addUserId.value.trim()) return
  isAddingMember.value = true
  try {
    await api.addOrgMember(selectedOrg.value.id, {
      user_id: addUserId.value.trim(),
      role: addRole.value,
      workspace_id: addWorkspaceId.value.trim() || undefined
    })
    ui.showToast({
      type: 'success',
      title: 'Member Added',
      message: `User assigned as ${addRole.value} in ${selectedOrg.value.name}`
    })
    addUserId.value = ''
    addWorkspaceId.value = ''
    // Refresh members
    const res = await api.getOrgMembers(selectedOrg.value.id)
    membersList.value = res.members
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to add member',
      message: err?.error || 'Could not add member to organization'
    })
  } finally {
    isAddingMember.value = false
  }
}

async function handleRemoveMember(userId: string) {
  if (!selectedOrg.value) return
  try {
    await api.removeOrgMember(selectedOrg.value.id, userId)
    membersList.value = membersList.value.filter(m => m.user_id !== userId)
    ui.showToast({
      type: 'success',
      title: 'Member Removed',
      message: 'User removed from organization.'
    })
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Action Failed',
      message: err?.error || 'Cannot remove user'
    })
  }
}

function promptDeleteOrg(org: Org) {
  orgToDelete.value = org
  showDeleteModal.value = true
}

async function confirmDeleteOrg() {
  if (!orgToDelete.value) return
  isDeletingOrg.value = true
  try {
    await admin.deleteOrganization(orgToDelete.value.id)
    showDeleteModal.value = false
    orgToDelete.value = null
  } finally {
    isDeletingOrg.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Organizations & Tenancy
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Manage tenant isolation workspaces, organization ownership, and team memberships.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :loading="admin.orgsLoading"
          @click="loadOrganizations"
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
          Create Organization
        </Button>
      </div>
    </div>

    <!-- Organizations Cards Grid -->
    <div v-if="admin.orgsLoading" class="p-12 text-center text-xs text-slate-500">
      Loading organizations...
    </div>

    <div v-else-if="admin.organizations.length === 0" class="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
      <div class="p-3 bg-slate-100 dark:bg-slate-800 rounded-2xl text-slate-400 dark:text-slate-500 max-w-fit mx-auto mb-3">
        <Building2 class="w-6 h-6" />
      </div>
      <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">No organizations found</h3>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">Get started by provisioning your first tenant workspace.</p>
      <div class="mt-4">
        <Button size="sm" @click="showCreateModal = true">
          <template #icon-left>
            <Plus class="w-4 h-4" />
          </template>
          Create Organization
        </Button>
      </div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="org in admin.organizations"
        :key="org.id"
      >
        <template #header>
          <div class="flex items-start gap-3 min-w-0">
            <div class="p-2.5 rounded-xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 shrink-0">
              <Building2 class="w-5 h-5" />
            </div>
            <div class="min-w-0">
              <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">
                {{ org.name }}
              </h3>
              <p class="text-[11px] font-mono text-slate-400 truncate mt-0.5">
                ID: {{ org.id }}
              </p>
            </div>
          </div>
        </template>

        <template #actions>
          <Badge :variant="org.role === 'owner' ? 'purple' : 'neutral'" size="sm">
            <Crown v-if="org.role === 'owner'" class="w-3 h-3" />
            {{ org.role }}
          </Badge>
        </template>

        <div class="space-y-3">
          <div class="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
            <span>Workspace ID:</span>
            <span class="font-mono text-slate-800 dark:text-slate-200 truncate max-w-[140px]">
              {{ org.workspace_id || org.id }}
            </span>
          </div>
        </div>

        <template #footer>
          <Button
            variant="outline"
            size="sm"
            @click="openMembersModal(org)"
          >
            <template #icon-left>
              <Users class="w-3.5 h-3.5" />
            </template>
            Members
          </Button>

          <Button
            v-if="org.role === 'owner'"
            variant="ghost"
            size="sm"
            @click="promptDeleteOrg(org)"
          >
            <Trash2 class="w-4 h-4 text-rose-500" />
          </Button>
        </template>
      </Card>
    </div>

    <!-- Create Organization Modal -->
    <Modal
      v-model="showCreateModal"
      title="Create New Organization"
      description="Provision a new tenant workspace."
    >
      <form @submit.prevent="handleCreateOrg" class="space-y-4">
        <Input
          v-model="newOrgName"
          label="Organization Name"
          placeholder="e.g. Engineering Cloud"
          required
        />
        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="showCreateModal = false">
            Cancel
          </Button>
          <Button type="submit" :loading="isCreating" :disabled="!newOrgName.trim()">
            Create
          </Button>
        </div>
      </form>
    </Modal>

    <!-- Manage Members Modal -->
    <Modal
      v-model="showMembersModal"
      :title="`Members — ${selectedOrg?.name}`"
      description="Add or remove members and adjust tenant roles."
      maxWidth="lg"
    >
      <div class="space-y-6">
        <!-- Add Member Subform -->
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800 space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
            <UserPlus class="w-3.5 h-3.5 text-brand-500" />
            Add Organization Member
          </h4>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div class="sm:col-span-2">
              <Input
                v-model="addUserId"
                placeholder="User UUID (from user directory)"
                required
              />
            </div>
            <div>
              <select
                v-model="addRole"
                class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
                <option value="owner">Owner</option>
              </select>
            </div>
          </div>

          <div class="flex justify-end">
            <Button
              size="sm"
              :loading="isAddingMember"
              :disabled="!addUserId.trim()"
              @click="handleAddMember"
            >
              Add Member
            </Button>
          </div>
        </div>

        <!-- Members Table -->
        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Active Members ({{ membersList.length }})
          </h4>

          <div v-if="isLoadingMembers" class="text-xs text-slate-500 py-4 text-center">
            Loading members...
          </div>

          <div v-else-if="membersList.length === 0" class="text-xs text-slate-500 py-4 text-center">
            No members in this organization.
          </div>

          <div v-else class="divide-y divide-slate-100 dark:divide-slate-800 border rounded-xl overflow-hidden">
            <div
              v-for="member in membersList"
              :key="member.user_id"
              class="p-3 flex items-center justify-between gap-4 text-xs hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors"
            >
              <div class="min-w-0">
                <div class="font-mono text-slate-900 dark:text-slate-100 font-semibold truncate">
                  {{ member.user_id }}
                </div>
                <div class="text-[11px] text-slate-400">
                  Workspace: {{ member.workspace_id || 'default' }}
                </div>
              </div>

              <div class="flex items-center gap-2 shrink-0">
                <Badge :variant="member.role === 'owner' ? 'purple' : member.role === 'admin' ? 'info' : 'neutral'" size="sm">
                  {{ member.role }}
                </Badge>
                <button
                  type="button"
                  @click="handleRemoveMember(member.user_id)"
                  class="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                  title="Remove member"
                >
                  <UserMinus class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <Button variant="outline" @click="showMembersModal = false">
          Close
        </Button>
      </template>
    </Modal>

    <!-- Delete Org Modal -->
    <Modal
      v-model="showDeleteModal"
      title="Delete Organization"
      description="This will permanently delete the organization workspace and remove all memberships."
    >
      <p class="text-xs text-rose-600 dark:text-rose-400 mb-4">
        Are you sure you want to delete <span class="font-bold">{{ orgToDelete?.name }}</span>?
      </p>

      <div class="flex justify-end gap-3">
        <Button variant="outline" @click="showDeleteModal = false">
          Cancel
        </Button>
        <Button
          variant="danger"
          :loading="isDeletingOrg"
          @click="confirmDeleteOrg"
        >
          Confirm Delete
        </Button>
      </div>
    </Modal>
  </div>
</template>
