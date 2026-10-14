<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useAdminStore } from '@/stores/admin'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import {
  KeyRound,
  Building2,
  Globe
} from 'lucide-vue-next'

const admin = useAdminStore()

// Grant Form
const targetUserId = ref('')
const selectedAudience = ref('')
const customAudience = ref('')
const selectedRole = ref('')
const grantScope = ref<'platform' | 'org'>('platform')
const selectedOrgId = ref('')
const isSubmitting = ref(false)

const isCustomAudience = computed(() => selectedAudience.value === '__custom__')

const activeAudience = computed(() => {
  return isCustomAudience.value ? customAudience.value.trim() : selectedAudience.value
})

const matchedService = computed(() => {
  return admin.services.find(s => s.id === selectedAudience.value)
})

const availableRoles = computed(() => {
  if (matchedService.value && matchedService.value.allowed_roles?.length) {
    return matchedService.value.allowed_roles
  }
  return ['admin', 'operator', 'viewer']
})

watch(matchedService, (svc) => {
  if (svc) {
    selectedRole.value = svc.default_role || svc.allowed_roles[0] || 'viewer'
  } else {
    selectedRole.value = 'viewer'
  }
})

async function loadDependencies() {
  await Promise.all([
    admin.fetchServices(),
    admin.fetchOrganizations(),
    admin.fetchUsers('', 0, 50)
  ])
  if (admin.services.length > 0) {
    selectedAudience.value = admin.services[0].id
  }
  if (admin.organizations.length > 0) {
    selectedOrgId.value = admin.organizations[0].id
  }
}

onMounted(() => {
  loadDependencies()
})

async function handleAssignGrant() {
  if (!targetUserId.value.trim() || !activeAudience.value) return

  isSubmitting.value = true
  try {
    await admin.assignGrant({
      user_id: targetUserId.value.trim(),
      audience: activeAudience.value,
      role: selectedRole.value,
      org_id: grantScope.value === 'org' ? selectedOrgId.value : null
    })

    // Reset user ID
    targetUserId.value = ''
  } finally {
    isSubmitting.value = false
  }
}

function selectUserForGrant(userId: string) {
  targetUserId.value = userId
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Product Grants Manager
        </h1>
        <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Issue platform-wide or tenant-scoped capability grants and authorized roles for microservices.
        </p>
      </div>
    </div>

    <!-- Main Assignment Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Grant Assignment Form Card -->
      <Card
        title="Assign New Product Grant"
        description="Grants authorize users to perform scoped actions within integrated microservices."
        class="lg:col-span-2"
      >
        <form @submit.prevent="handleAssignGrant" class="space-y-5">
          <!-- Target User ID -->
          <div>
            <Input
              v-model="targetUserId"
              label="Target User UUID"
              placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
              required
              hint="Paste UUID of user from directory or select from list on right."
            />
          </div>

          <!-- Service Audience Picker -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Target Service / Audience <span class="text-rose-500">*</span>
              </label>
              <select
                v-model="selectedAudience"
                class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option
                  v-for="svc in admin.services"
                  :key="svc.id"
                  :value="svc.id"
                >
                  {{ svc.name }} ({{ svc.id }})
                </option>
                <option value="__custom__">+ Custom Audience Identifier</option>
              </select>
            </div>

            <!-- Custom Audience Identifier input if selected -->
            <div v-if="isCustomAudience">
              <Input
                v-model="customAudience"
                label="Custom Audience ID"
                placeholder="e.g. billing-service"
                required
              />
            </div>

            <!-- Role Selector -->
            <div>
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Assigned Role <span class="text-rose-500">*</span>
              </label>
              <select
                v-model="selectedRole"
                class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono text-xs"
              >
                <option
                  v-for="role in availableRoles"
                  :key="role"
                  :value="role"
                >
                  {{ role }}
                </option>
              </select>
            </div>
          </div>

          <!-- Scope Tier Selection -->
          <div class="space-y-3 pt-2">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Grant Scope Tier
            </label>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                @click="grantScope = 'platform'"
                :class="[
                  'p-4 rounded-xl border text-left flex items-start gap-3 transition-all',
                  grantScope === 'platform'
                    ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/30 ring-2 ring-brand-500/20'
                    : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40'
                ]"
              >
                <Globe class="w-5 h-5 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <div class="text-xs font-bold text-slate-900 dark:text-slate-100">
                    Platform-Wide Grant
                  </div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Valid across all workspaces & tenants (`org_id = null`).
                  </div>
                </div>
              </button>

              <button
                type="button"
                @click="grantScope = 'org'"
                :class="[
                  'p-4 rounded-xl border text-left flex items-start gap-3 transition-all',
                  grantScope === 'org'
                    ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/30 ring-2 ring-brand-500/20'
                    : 'border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40'
                ]"
              >
                <Building2 class="w-5 h-5 text-brand-600 dark:text-brand-400 shrink-0 mt-0.5" />
                <div>
                  <div class="text-xs font-bold text-slate-900 dark:text-slate-100">
                    Tenant-Scoped Grant
                  </div>
                  <div class="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Restricted exclusively to a specific organization.
                  </div>
                </div>
              </button>
            </div>

            <!-- Organization Selector if Tenant-Scoped -->
            <div v-if="grantScope === 'org'" class="pt-2">
              <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Select Tenant Organization
              </label>
              <select
                v-model="selectedOrgId"
                class="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option
                  v-for="org in admin.organizations"
                  :key="org.id"
                  :value="org.id"
                >
                  {{ org.name }} (ID: {{ org.id }})
                </option>
              </select>
            </div>
          </div>

          <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
            <Button
              type="submit"
              :loading="isSubmitting"
              :disabled="!targetUserId.trim() || !activeAudience || !selectedRole"
            >
              <template #icon-left>
                <KeyRound class="w-4 h-4" />
              </template>
              Commit Product Grant
            </Button>
          </div>
        </form>
      </Card>

      <!-- Quick User Directory Selector Card -->
      <Card
        title="Quick User Selector"
        description="Click any user to paste their UUID into the grant form."
        class="lg:col-span-1"
      >
        <div class="space-y-2 max-h-[420px] overflow-y-auto pr-1">
          <div
            v-for="u in admin.users"
            :key="u.id"
            @click="selectUserForGrant(u.id)"
            class="p-2.5 rounded-xl border border-slate-200/70 dark:border-slate-800 hover:bg-brand-50 dark:hover:bg-brand-950/30 hover:border-brand-300 dark:hover:border-brand-700 cursor-pointer transition-colors"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate max-w-[140px]">
                {{ u.display_name || u.email }}
              </span>
              <Badge :variant="u.is_active ? 'success' : 'danger'" size="sm">
                {{ u.is_active ? 'Active' : 'Suspended' }}
              </Badge>
            </div>
            <div class="text-[11px] font-mono text-slate-400 truncate mt-1">
              {{ u.id }}
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>
