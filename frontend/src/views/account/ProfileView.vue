<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { api } from '@/api/client'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Input from '@/components/common/Input.vue'
import Badge from '@/components/common/Badge.vue'
import Modal from '@/components/common/Modal.vue'
import PasswordRequirements from '@/components/common/PasswordRequirements.vue'
import { getHumanErrorMessage } from '@/utils/errors'
import {
  User,
  Mail,
  ShieldCheck,
  KeyRound,
  Download,
  Trash2,
  Lock,
  Copy,
  Check,
  CheckCircle2,
  AlertCircle,
  AlertTriangle
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()

// Profile edit form
const isEditingProfile = ref(false)
const displayName = ref(auth.user?.display_name || '')
const email = ref(auth.user?.email || '')
const isSavingProfile = ref(false)

// Password change form
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isNewPasswordValid = ref(false)
const isChangingPassword = ref(false)
const passwordError = ref('')

const passwordsMatch = computed(() => {
  if (!confirmPassword.value) return null
  return newPassword.value === confirmPassword.value
})

// GDPR export & delete
const isExporting = ref(false)
const showDeleteModal = ref(false)
const deleteConfirmationText = ref('')
const isDeletingAccount = ref(false)

const copiedId = ref(false)

function copyUserId() {
  if (auth.user?.id) {
    navigator.clipboard.writeText(auth.user.id)
    copiedId.value = true
    setTimeout(() => {
      copiedId.value = false
    }, 2000)
  }
}

async function handleSaveProfile() {
  isSavingProfile.value = true
  try {
    await auth.updateProfile({
      display_name: displayName.value.trim() || undefined,
      email: email.value.trim() || undefined
    })
    isEditingProfile.value = false
  } finally {
    isSavingProfile.value = false
  }
}

async function handleChangePassword() {
  if (!currentPassword.value || !newPassword.value) return
  if (!isNewPasswordValid.value) {
    passwordError.value = 'Please ensure your new password satisfies all security requirements.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'The new passwords you entered do not match. Please re-enter them carefully.'
    return
  }

  isChangingPassword.value = true
  passwordError.value = ''
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    ui.showToast({
      type: 'success',
      title: 'Password updated',
      message: 'Your account password has been updated successfully.'
    })
  } catch (err: any) {
    passwordError.value = getHumanErrorMessage(err, { context: 'profile' })
  } finally {
    isChangingPassword.value = false
  }
}

async function handleExportData() {
  isExporting.value = true
  try {
    const data = await api.exportMyData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `deskid-user-data-${auth.user?.id || 'export'}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    ui.showToast({
      type: 'success',
      title: 'Export Downloaded',
      message: 'Your personal data export JSON is ready.'
    })
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Export Failed',
      message: err?.error || 'Could not export user data'
    })
  } finally {
    isExporting.value = false
  }
}

async function handleDeleteAccount() {
  if (deleteConfirmationText.value !== 'DELETE') return
  isDeletingAccount.value = true
  try {
    await api.deleteMyAccount()
    ui.showToast({
      type: 'info',
      title: 'Account Deleted',
      message: 'Your account and all associated data have been purged.'
    })
    showDeleteModal.value = false
    router.push({ name: 'login' })
  } catch (err: any) {
    ui.showToast({
      type: 'error',
      title: 'Deletion Failed',
      message: err?.error || 'Could not delete account'
    })
  } finally {
    isDeletingAccount.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
        Profile & Security
      </h1>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
        Manage your personal identity credentials, security settings, and product permissions.
      </p>
    </div>

    <!-- Identity & Profile Info Card -->
    <Card title="User Identity">
      <template #actions>
        <Button
          variant="outline"
          size="sm"
          @click="isEditingProfile = true"
        >
          Edit Profile
        </Button>
      </template>

      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6">
        <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white font-bold text-2xl flex items-center justify-center shadow-md shadow-brand-500/20 shrink-0">
          {{ (auth.user?.display_name || auth.user?.email || 'U').charAt(0).toUpperCase() }}
        </div>

        <div class="flex-1 min-w-0 space-y-2">
          <div class="flex items-center gap-2 flex-wrap">
            <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">
              {{ auth.user?.display_name || 'No display name set' }}
            </h3>
            <Badge v-if="auth.user?.is_platform_admin" variant="purple">
              <ShieldCheck class="w-3 h-3" />
              Platform Admin
            </Badge>
            <Badge v-if="auth.user?.is_active" variant="success">
              Active
            </Badge>
            <Badge v-else variant="danger">
              Suspended
            </Badge>
          </div>

          <div class="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
            <span class="flex items-center gap-1.5">
              <Mail class="w-3.5 h-3.5" />
              {{ auth.user?.email }}
            </span>
            <button
              type="button"
              @click="copyUserId"
              class="flex items-center gap-1.5 hover:text-slate-800 dark:hover:text-slate-200 transition-colors font-mono"
            >
              <span>ID: {{ auth.user?.id }}</span>
              <Check v-if="copiedId" class="w-3 h-3 text-emerald-500" />
              <Copy v-else class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </Card>

    <!-- Product Grants Card -->
    <Card
      title="My Product Grants & Roles"
      description="List of product services and authorized roles assigned to your identity."
    >
      <div v-if="!auth.user?.grants?.length" class="text-xs text-slate-500 dark:text-slate-400 py-2">
        No specific product grants assigned. You operate under default role permissions.
      </div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="(grant, idx) in auth.user.grants"
          :key="idx"
          class="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-800 flex items-start gap-3"
        >
          <div class="p-2 rounded-lg bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 shrink-0">
            <KeyRound class="w-4 h-4" />
          </div>
          <div class="min-w-0">
            <div class="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
              {{ grant.audience }}
            </div>
            <div class="flex items-center gap-1.5 mt-1">
              <Badge variant="purple" size="sm">
                {{ grant.role }}
              </Badge>
              <Badge v-if="grant.org_id" variant="neutral" size="sm">
                Org Scoped
              </Badge>
              <Badge v-else variant="info" size="sm">
                Platform Wide
              </Badge>
            </div>
          </div>
        </div>
      </div>
    </Card>

    <!-- Change Password Card -->
    <Card
      title="Change Password"
      description="Ensure your account is using a secure, long password."
    >
      <form @submit.prevent="handleChangePassword" class="space-y-4 max-w-md">
        <div
          v-if="passwordError"
          role="alert"
          aria-live="assertive"
          class="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300"
        >
          {{ passwordError }}
        </div>

        <Input
          v-model="currentPassword"
          label="Current Password"
          type="password"
          required
        >
          <template #icon-left>
            <Lock class="w-4 h-4" />
          </template>
        </Input>

        <div>
          <Input
            v-model="newPassword"
            label="New Password"
            type="password"
            placeholder="Min. 8 characters"
            required
          >
            <template #icon-left>
              <Lock class="w-4 h-4" />
            </template>
          </Input>

          <!-- Live Password Requirements Checklist -->
          <PasswordRequirements
            v-if="newPassword.length > 0"
            :password="newPassword"
            @valid="isNewPasswordValid = $event"
          />
        </div>

        <div>
          <Input
            v-model="confirmPassword"
            label="Confirm New Password"
            type="password"
            required
          >
            <template #icon-left>
              <Lock class="w-4 h-4" />
            </template>
          </Input>

          <p
            v-if="confirmPassword"
            class="mt-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors"
            :class="passwordsMatch ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-500'"
          >
            <CheckCircle2 v-if="passwordsMatch" class="w-3.5 h-3.5" />
            <AlertCircle v-else class="w-3.5 h-3.5" />
            <span>{{ passwordsMatch ? 'Passwords match' : 'Passwords do not match' }}</span>
          </p>
        </div>

        <Button
          type="submit"
          :loading="isChangingPassword"
          :disabled="!currentPassword || !newPassword || !confirmPassword || !isNewPasswordValid || !passwordsMatch"
        >
          Update Password
        </Button>
      </form>
    </Card>

    <!-- Data Privacy & GDPR Section -->
    <Card
      title="Privacy & Data Management"
      description="Download your personal data archive or request account deletion under GDPR."
    >
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-800">
        <div>
          <h4 class="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Export Personal Data
          </h4>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Receive a complete JSON export of your identities, grants, audit history, and sessions.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          :loading="isExporting"
          @click="handleExportData"
        >
          <template #icon-left>
            <Download class="w-4 h-4" />
          </template>
          Export Data (JSON)
        </Button>
      </div>

      <!-- Danger Zone: Delete Account -->
      <div class="mt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40">
        <div>
          <h4 class="text-sm font-semibold text-rose-800 dark:text-rose-300">
            Delete Account
          </h4>
          <p class="text-xs text-rose-600/80 dark:text-rose-400/80 mt-0.5">
            Permanently delete your account and revoke all tokens. This action is irreversible.
          </p>
        </div>
        <Button
          variant="danger"
          size="sm"
          @click="showDeleteModal = true"
        >
          <template #icon-left>
            <Trash2 class="w-4 h-4" />
          </template>
          Delete Account
        </Button>
      </div>
    </Card>

    <!-- Edit Profile Modal -->
    <Modal
      v-model="isEditingProfile"
      title="Edit Profile Details"
      description="Update your display name or primary email address."
    >
      <form @submit.prevent="handleSaveProfile" class="space-y-4">
        <Input
          v-model="displayName"
          label="Display Name"
          placeholder="e.g. John Doe"
        >
          <template #icon-left>
            <User class="w-4 h-4" />
          </template>
        </Input>

        <Input
          v-model="email"
          label="Email Address"
          type="email"
          placeholder="name@company.com"
          required
          hint="Changing your email may require re-verification."
        >
          <template #icon-left>
            <Mail class="w-4 h-4" />
          </template>
        </Input>

        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="isEditingProfile = false">
            Cancel
          </Button>
          <Button type="submit" :loading="isSavingProfile">
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>

    <!-- Delete Account Confirmation Modal -->
    <Modal
      v-model="showDeleteModal"
      title="Confirm Account Deletion"
      description="Are you sure you want to permanently delete your account?"
    >
      <div class="space-y-4">
        <div class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2.5">
          <AlertTriangle class="w-5 h-5 shrink-0 text-rose-500 mt-0.5" />
          <span>
            All your tokens, grants, and personal records will be permanently erased. This operation cannot be undone.
          </span>
        </div>

        <p class="text-xs text-slate-600 dark:text-slate-400">
          Type <span class="font-bold text-rose-600 select-all">DELETE</span> below to confirm:
        </p>

        <Input
          v-model="deleteConfirmationText"
          placeholder="DELETE"
        />

        <div class="flex justify-end gap-3 pt-2">
          <Button variant="outline" @click="showDeleteModal = false">
            Cancel
          </Button>
          <Button
            variant="danger"
            :loading="isDeletingAccount"
            :disabled="deleteConfirmationText !== 'DELETE'"
            @click="handleDeleteAccount"
          >
            Permanently Delete
          </Button>
        </div>
      </div>
    </Modal>
  </div>
</template>
