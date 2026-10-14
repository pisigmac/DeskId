<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '@/stores/admin'
import type { User } from '@/api/types'
import DataTable, { type Column } from '@/components/common/DataTable.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import Modal from '@/components/common/Modal.vue'
import {
  Search,
  ShieldCheck,
  Building2,
  KeyRound,
  Eye,
  CheckCircle2,
  XCircle,
  Mail
} from 'lucide-vue-next'

const admin = useAdminStore()

const searchQuery = ref('')
const selectedUser = ref<User | null>(null)
const showDetailsModal = ref(false)

const columns: Column[] = [
  { key: 'identity', label: 'User Identity' },
  { key: 'role', label: 'Platform Role' },
  { key: 'status', label: 'Status' },
  { key: 'tenancies', label: 'Organizations' },
  { key: 'grants', label: 'Grants' },
  { key: 'actions', label: 'Actions', align: 'right' }
]

async function loadUsers(offset: number = 0) {
  await admin.fetchUsers(searchQuery.value, offset, 20)
}

function handleSearch() {
  loadUsers(0)
}

function handlePageChange(newOffset: number) {
  loadUsers(newOffset)
}

function openUserDetails(user: User) {
  selectedUser.value = user
  showDetailsModal.value = true
}

async function toggleActive(user: User) {
  try {
    await admin.toggleUserActive(user.id, user.is_active)
  } catch {
    // Handled in store
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          User Directory
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Manage user accounts, platform admin permissions, account activation state, and assigned credentials.
        </p>
      </div>
    </div>

    <!-- Data Table Container -->
    <DataTable
      :columns="columns"
      :items="admin.users"
      :loading="admin.usersLoading"
      :total="admin.totalUsers"
      :offset="admin.usersOffset"
      :limit="admin.usersLimit"
      emptyTitle="No users found"
      emptyMessage="No accounts matched your search criteria."
      @page-change="handlePageChange"
    >
      <template #toolbar>
        <div class="flex items-center gap-3">
          <div class="relative flex-1 max-w-md">
            <Input
              v-model="searchQuery"
              placeholder="Search users by name or email..."
              @keyup.enter="handleSearch"
            >
              <template #icon-left>
                <Search class="w-4 h-4" />
              </template>
            </Input>
          </div>
          <Button variant="secondary" size="md" @click="handleSearch">
            Search
          </Button>
        </div>
      </template>

      <!-- Identity Cell -->
      <template #cell-identity="{ item }">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white font-bold text-xs flex items-center justify-center shrink-0">
            {{ (item.display_name || item.email || 'U').charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0">
            <div class="font-semibold text-slate-900 dark:text-slate-100 truncate max-w-[200px]">
              {{ item.display_name || 'No display name' }}
            </div>
            <div class="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px] flex items-center gap-1 font-mono">
              <Mail class="w-3 h-3 shrink-0" />
              {{ item.email }}
            </div>
          </div>
        </div>
      </template>

      <!-- Role Cell -->
      <template #cell-role="{ item }">
        <Badge v-if="item.is_platform_admin" variant="purple" size="sm">
          <ShieldCheck class="w-3 h-3" />
          Platform Admin
        </Badge>
        <Badge v-else variant="neutral" size="sm">
          Standard User
        </Badge>
      </template>

      <!-- Status Cell -->
      <template #cell-status="{ item }">
        <Badge :variant="item.is_active ? 'success' : 'danger'" size="sm">
          <CheckCircle2 v-if="item.is_active" class="w-3 h-3" />
          <XCircle v-else class="w-3 h-3" />
          {{ item.is_active ? 'Active' : 'Suspended' }}
        </Badge>
      </template>

      <!-- Tenancies Cell -->
      <template #cell-tenancies="{ item }">
        <span class="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
          <Building2 class="w-3.5 h-3.5 text-slate-400" />
          {{ item.orgs?.length || 0 }} organizations
        </span>
      </template>

      <!-- Grants Cell -->
      <template #cell-grants="{ item }">
        <span class="inline-flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
          <KeyRound class="w-3.5 h-3.5 text-slate-400" />
          {{ item.grants?.length || 0 }} grants
        </span>
      </template>

      <!-- Actions Cell -->
      <template #cell-actions="{ item }">
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            @click="openUserDetails(item)"
          >
            <template #icon-left>
              <Eye class="w-3.5 h-3.5" />
            </template>
            Details
          </Button>

          <Button
            :variant="item.is_active ? 'outline' : 'primary'"
            size="sm"
            @click="toggleActive(item)"
          >
            {{ item.is_active ? 'Suspend' : 'Activate' }}
          </Button>
        </div>
      </template>
    </DataTable>

    <!-- User Details Modal -->
    <Modal
      v-model="showDetailsModal"
      title="User Identity & Grant Profile"
      :description="`Details for ${selectedUser?.email}`"
      maxWidth="lg"
    >
      <div v-if="selectedUser" class="space-y-5">
        <!-- Identity Summary -->
        <div class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">User ID</span>
            <span class="font-mono text-xs text-slate-800 dark:text-slate-200 select-all">{{ selectedUser.id }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">Email</span>
            <span class="text-xs text-slate-800 dark:text-slate-200">{{ selectedUser.email }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-500">Display Name</span>
            <span class="text-xs text-slate-800 dark:text-slate-200">{{ selectedUser.display_name || 'Not set' }}</span>
          </div>
        </div>

        <!-- Organizations Table -->
        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Tenant Memberships ({{ selectedUser.orgs?.length || 0 }})
          </h4>
          <div v-if="!selectedUser.orgs?.length" class="text-xs text-slate-500 py-1">
            Not a member of any organization.
          </div>
          <div v-else class="space-y-1.5">
            <div
              v-for="org in selectedUser.orgs"
              :key="org.id"
              class="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 text-xs"
            >
              <div class="flex items-center gap-2">
                <Building2 class="w-3.5 h-3.5 text-slate-400" />
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ org.name }}</span>
              </div>
              <Badge variant="neutral" size="sm">{{ org.role }}</Badge>
            </div>
          </div>
        </div>

        <!-- Product Grants -->
        <div>
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Product Grants & Audience Roles ({{ selectedUser.grants?.length || 0 }})
          </h4>
          <div v-if="!selectedUser.grants?.length" class="text-xs text-slate-500 py-1">
            No specific grants assigned.
          </div>
          <div v-else class="space-y-1.5">
            <div
              v-for="(grant, idx) in selectedUser.grants"
              :key="idx"
              class="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-200/60 dark:border-slate-800 text-xs"
            >
              <div class="flex items-center gap-2">
                <KeyRound class="w-3.5 h-3.5 text-brand-500" />
                <span class="font-medium text-slate-800 dark:text-slate-200">{{ grant.audience }}</span>
              </div>
              <div class="flex items-center gap-2">
                <Badge variant="purple" size="sm">{{ grant.role }}</Badge>
                <Badge v-if="grant.org_id" variant="neutral" size="sm">Org Scoped</Badge>
                <Badge v-else variant="info" size="sm">Platform Wide</Badge>
              </div>
            </div>
          </div>
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
