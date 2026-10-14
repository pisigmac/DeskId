<script setup lang="ts">
import { ref, computed, provide, onMounted, onUnmounted } from 'vue'
import { DeskIdClient, type DeskIdUser, type DeskIdSession, type DeskIdOrg, type DeskIdClientOptions } from '@deskid/core'
import { DESKID_CONTEXT_KEY } from '../context'
import type { DeskIdVueContext } from '../types'
import DeskIdModal from './DeskIdModal.vue'

interface Props {
  baseUrl: string
  storage?: 'localStorage' | 'sessionStorage' | 'cookie' | 'memory'
  autoRefresh?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  storage: 'localStorage',
  autoRefresh: true
})

const client = new DeskIdClient({
  baseUrl: props.baseUrl,
  storage: props.storage,
  autoRefresh: props.autoRefresh
})

const user = ref<DeskIdUser | null>(null)
const session = ref<DeskIdSession | null>(null)
const isLoading = ref(true)
const isModalOpen = ref(false)

const isAuthenticated = computed(() => {
  return Boolean(session.value && user.value)
})

const activeOrg = computed(() => {
  if (!user.value || !user.value.orgs || user.value.orgs.length === 0) return null
  const orgClaim = session.value?.claims?.org_id
  if (orgClaim) {
    const match = user.value.orgs.find((o: DeskIdOrg) => o.id === orgClaim)
    if (match) return match
  }
  return user.value.orgs[0] || null
})

function openSignInModal() {
  isModalOpen.value = true
}

function closeSignInModal() {
  isModalOpen.value = false
}

let unsubscribe: (() => void) | null = null

onMounted(async () => {
  isLoading.value = true
  unsubscribe = client.onAuthStateChange(async (event, newSession) => {
    session.value = newSession
    if (newSession) {
      user.value = client.getUser()
    } else {
      user.value = null
    }
  })

  session.value = client.getSession()
  user.value = client.getUser()
  isLoading.value = false
})

onUnmounted(() => {
  if (unsubscribe) unsubscribe()
})

const context: DeskIdVueContext = {
  user,
  session,
  isAuthenticated,
  isLoading,
  activeOrg,
  isModalOpen,
  openSignInModal,
  closeSignInModal,
  login: (options) => client.login(options),
  register: (options) => client.register(options),
  requestMagicLink: (email) => client.requestMagicLink(email),
  verifyOtp: (email, code) => client.verifyOtp(email, code),
  logout: () => client.logout(),
  switchOrg: (orgId) => client.switchOrg(orgId)
}

provide(DESKID_CONTEXT_KEY, context)
</script>

<template>
  <slot />
  <DeskIdModal v-model="isModalOpen" :client="client" />
</template>
