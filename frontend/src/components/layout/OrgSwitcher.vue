<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { Building2, Check, ChevronsUpDown, Plus } from 'lucide-vue-next'
import Dropdown from '@/components/common/Dropdown.vue'
import Modal from '@/components/common/Modal.vue'
import Input from '@/components/common/Input.vue'
import Button from '@/components/common/Button.vue'
import { api } from '@/api/client'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()

const showCreateModal = ref(false)
const newOrgName = ref('')
const isCreating = ref(false)

const userOrgs = computed(() => auth.user?.orgs || [])
const activeOrg = computed(() => auth.activeOrg)

async function selectOrg(orgId: string) {
  if (orgId === auth.activeOrgId) return
  await auth.switchOrg(orgId)
}

async function handleCreateOrg() {
  if (!newOrgName.value.trim()) return
  isCreating.value = true
  try {
    const org = await api.createOrg(newOrgName.value.trim())
    ui.showToast({
      type: 'success',
      title: 'Organization Created',
      message: `Organization "${org.name}" created successfully.`
    })
    showCreateModal.value = false
    newOrgName.value = ''
    await auth.fetchProfile()
    await auth.switchOrg(org.id)
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Failed to create org',
      message: err?.error || 'Could not create organization'
    })
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="relative">
    <Dropdown align="left" width="w-64">
      <template #trigger="{ isOpen }">
        <button
          type="button"
          :class="[
            'flex items-center gap-2.5 px-3 py-1.5 rounded-xl border transition-all text-xs font-medium',
            isOpen
              ? 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700'
              : 'bg-white/80 dark:bg-slate-900/80 border-slate-200/80 dark:border-slate-800 hover:bg-slate-100/80 dark:hover:bg-slate-800/80'
          ]"
        >
          <div class="p-1 rounded-lg bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400">
            <Building2 class="w-3.5 h-3.5" />
          </div>
          <div class="text-left min-w-[100px] max-w-[140px] truncate">
            <div class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider">Tenant</div>
            <div class="text-slate-800 dark:text-slate-200 truncate font-semibold">
              {{ activeOrg?.name || 'Personal Space' }}
            </div>
          </div>
          <ChevronsUpDown class="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1" />
        </button>
      </template>

      <div class="p-2">
        <div class="px-2 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Switch Organization
        </div>
        <div class="space-y-1 mt-1 max-h-48 overflow-y-auto">
          <button
            v-for="org in userOrgs"
            :key="org.id"
            type="button"
            @click="selectOrg(org.id)"
            class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-left"
          >
            <div class="flex items-center gap-2 min-w-0">
              <Building2 class="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <div class="truncate">
                <span class="font-medium text-slate-900 dark:text-slate-100">{{ org.name }}</span>
                <span class="ml-1.5 text-[10px] text-slate-400">({{ org.role }})</span>
              </div>
            </div>
            <Check v-if="org.id === activeOrg?.id" class="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 shrink-0 ml-2" />
          </button>
        </div>

        <div class="border-t border-slate-100 dark:border-slate-800 mt-2 pt-2">
          <button
            type="button"
            @click="showCreateModal = true"
            class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950/40 transition-colors text-left"
          >
            <Plus class="w-3.5 h-3.5" />
            Create Organization
          </button>
        </div>
      </div>
    </Dropdown>

    <!-- Create Org Modal -->
    <Modal
      v-model="showCreateModal"
      title="Create New Organization"
      description="Create a dedicated tenant workspace for your team and services."
    >
      <form @submit.prevent="handleCreateOrg" class="space-y-4">
        <Input
          v-model="newOrgName"
          label="Organization Name"
          placeholder="e.g. Acme Cloud Corp"
          required
          hint="Must be unique within your tenant registry."
        />
        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="showCreateModal = false">
            Cancel
          </Button>
          <Button type="submit" :loading="isCreating" :disabled="!newOrgName.trim()">
            Create Organization
          </Button>
        </div>
      </form>
    </Modal>
  </div>
</template>
