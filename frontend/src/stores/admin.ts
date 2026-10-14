import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import type {
  User,
  ServiceDefinition,
  ServiceCreatePayload,
  ServiceUpdatePayload,
  AuditLogEvent,
  SystemHealth,
  SystemMetrics,
  Org
} from '@/api/types'
import { useUiStore } from './ui'

export const useAdminStore = defineStore('admin', () => {
  const ui = useUiStore()

  // Users State
  const users = ref<User[]>([])
  const totalUsers = ref(0)
  const usersLoading = ref(false)
  const usersOffset = ref(0)
  const usersLimit = ref(20)
  const usersSearch = ref('')

  async function fetchUsers(q?: string, offset: number = 0, limit: number = 20) {
    usersLoading.value = true
    try {
      usersSearch.value = q || ''
      usersOffset.value = offset
      usersLimit.value = limit
      const res = await api.listUsers({ q, offset, limit })
      users.value = res.users
      totalUsers.value = res.total
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Failed to load users',
        message: err?.error || 'Could not fetch user directory'
      })
    } finally {
      usersLoading.value = false
    }
  }

  async function toggleUserActive(userId: string, currentActive: boolean) {
    try {
      await api.setUserActive(userId, !currentActive)
      ui.showToast({
        type: 'success',
        title: !currentActive ? 'User Activated' : 'User Suspended',
        message: `Account status successfully updated.`
      })
      // Update local state
      const target = users.value.find(u => u.id === userId)
      if (target) target.is_active = !currentActive
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Action failed',
        message: err?.error || 'Failed to update user status'
      })
      throw err
    }
  }

  // Organizations State
  const organizations = ref<Org[]>([])
  const orgsLoading = ref(false)

  async function fetchOrganizations() {
    orgsLoading.value = true
    try {
      organizations.value = await api.getMyOrgs()
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Failed to load organizations',
        message: err?.error || 'Could not fetch organizations'
      })
    } finally {
      orgsLoading.value = false
    }
  }

  async function createOrganization(name: string) {
    try {
      const newOrg = await api.createOrg(name)
      organizations.value.push(newOrg)
      ui.showToast({
        type: 'success',
        title: 'Organization Created',
        message: `Created organization "${newOrg.name}"`
      })
      return newOrg
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Failed to create organization',
        message: err?.error || 'Organization creation failed'
      })
      throw err
    }
  }

  async function deleteOrganization(orgId: string) {
    try {
      await api.deleteOrg(orgId)
      organizations.value = organizations.value.filter(o => o.id !== orgId)
      ui.showToast({
        type: 'success',
        title: 'Organization Deleted',
        message: 'Organization removed successfully.'
      })
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Deletion Failed',
        message: err?.error || 'Could not delete organization'
      })
      throw err
    }
  }

  // Services State
  const services = ref<ServiceDefinition[]>([])
  const totalServices = ref(0)
  const servicesLoading = ref(false)

  async function fetchServices(q?: string) {
    servicesLoading.value = true
    try {
      const res = await api.listServices({ q, limit: 100 })
      services.value = res.services
      totalServices.value = res.total
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Failed to load services',
        message: err?.error || 'Could not fetch service registry'
      })
    } finally {
      servicesLoading.value = false
    }
  }

  async function createService(payload: ServiceCreatePayload) {
    try {
      const newSvc = await api.createService(payload)
      services.value.push(newSvc)
      totalServices.value++
      ui.showToast({
        type: 'success',
        title: 'Service Registered',
        message: `Successfully registered service "${newSvc.name}" (${newSvc.id})`
      })
      return newSvc
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Registration failed',
        message: err?.error || 'Could not register service'
      })
      throw err
    }
  }

  async function updateService(serviceId: string, payload: ServiceUpdatePayload) {
    try {
      const updated = await api.updateService(serviceId, payload)
      const idx = services.value.findIndex(s => s.id === serviceId)
      if (idx !== -1) services.value[idx] = updated
      ui.showToast({
        type: 'success',
        title: 'Service Updated',
        message: `Updated service configuration for "${updated.name}"`
      })
      return updated
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Update failed',
        message: err?.error || 'Could not update service'
      })
      throw err
    }
  }

  async function deleteService(serviceId: string) {
    try {
      await api.deleteService(serviceId)
      services.value = services.value.filter(s => s.id !== serviceId)
      totalServices.value = Math.max(0, totalServices.value - 1)
      ui.showToast({
        type: 'success',
        title: 'Service Removed',
        message: `Service definition "${serviceId}" removed.`
      })
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Deletion failed',
        message: err?.error || 'Could not delete service'
      })
      throw err
    }
  }

  // Product Grants
  async function assignGrant(payload: {
    user_id: string
    audience: string
    role?: string
    org_id?: string | null
  }) {
    try {
      const res = await api.setGrant(payload)
      ui.showToast({
        type: 'success',
        title: 'Grant Assigned',
        message: `Role "${res.role}" assigned for audience "${res.audience}"`
      })
      return res
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Grant failed',
        message: err?.error || 'Could not set grant'
      })
      throw err
    }
  }

  // Cryptographic Audit Stream
  const auditEvents = ref<AuditLogEvent[]>([])
  const totalAuditEvents = ref(0)
  const auditLoading = ref(false)
  const auditFilters = ref<{
    action?: string
    actor_id?: string
    resource_type?: string
    resource_id?: string
  }>({})

  async function fetchAuditLogs(filters?: {
    action?: string
    actor_id?: string
    resource_type?: string
    resource_id?: string
    offset?: number
    limit?: number
  }) {
    auditLoading.value = true
    try {
      if (filters) {
        auditFilters.value = {
          action: filters.action,
          actor_id: filters.actor_id,
          resource_type: filters.resource_type,
          resource_id: filters.resource_id
        }
      }
      const res = await api.listAuditLogs({
        ...auditFilters.value,
        offset: filters?.offset ?? 0,
        limit: filters?.limit ?? 25
      })
      auditEvents.value = res.events
      totalAuditEvents.value = res.total
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Audit query failed',
        message: err?.error || 'Failed to fetch audit log stream'
      })
    } finally {
      auditLoading.value = false
    }
  }

  // System Health & Metrics
  const health = ref<SystemHealth | null>(null)
  const metrics = ref<SystemMetrics | null>(null)
  const systemLoading = ref(false)

  async function fetchSystemStats() {
    systemLoading.value = true
    try {
      const [h, m] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getMetrics().catch(() => null)
      ])
      health.value = h
      metrics.value = m
    } finally {
      systemLoading.value = false
    }
  }

  return {
    // Users
    users,
    totalUsers,
    usersLoading,
    usersOffset,
    usersLimit,
    usersSearch,
    fetchUsers,
    toggleUserActive,
    // Orgs
    organizations,
    orgsLoading,
    fetchOrganizations,
    createOrganization,
    deleteOrganization,
    // Services
    services,
    totalServices,
    servicesLoading,
    fetchServices,
    createService,
    updateService,
    deleteService,
    // Grants
    assignGrant,
    // Audit
    auditEvents,
    totalAuditEvents,
    auditLoading,
    auditFilters,
    fetchAuditLogs,
    // Stats
    health,
    metrics,
    systemLoading,
    fetchSystemStats
  }
})
