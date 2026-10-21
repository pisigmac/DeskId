import type {
  ApiError,
  AuditQueryResponse,
  Org,
  OrgMembersResponse,
  ReconciliationResponse,
  RegisterResponse,
  RoleCreatePayload,
  RolesOverviewResponse,
  ServiceConfigResponse,
  ServiceCreatePayload,
  ServiceDefinition,
  ServiceListResponse,
  ServiceUpdatePayload,
  Session,
  SystemHealth,
  SystemMetrics,
  TokenResponse,
  User,
  UserExportData,
  UserListResponse
} from './types'

class ApiClient {
  private baseUrl = ''
  private isRefreshing = false
  private refreshSubscribers: Array<(token: string) => void> = []

  private getAccessToken(): string | null {
    return localStorage.getItem('deskid_access_token')
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem('deskid_refresh_token')
  }

  private setTokens(access: string, refresh: string) {
    localStorage.setItem('deskid_access_token', access)
    localStorage.setItem('deskid_refresh_token', refresh)
  }

  private clearTokens() {
    localStorage.removeItem('deskid_access_token')
    localStorage.removeItem('deskid_refresh_token')
  }

  private onTokenRefreshed(token: string) {
    this.refreshSubscribers.forEach(cb => cb(token))
    this.refreshSubscribers = []
  }

  private addRefreshSubscriber(cb: (token: string) => void) {
    this.refreshSubscribers.push(cb)
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requiresAuth: boolean = true
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = new Headers(options.headers || {})

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    if (requiresAuth) {
      const token = this.getAccessToken()
      if (token) {
        headers.set('Authorization', `Bearer ${token}`)
      }
    }

    const response = await fetch(url, {
      ...options,
      headers
    })

    // Handle 401 Unauthorized with token refresh
    if (response.status === 401 && requiresAuth && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
      const refreshToken = this.getRefreshToken()
      if (!refreshToken) {
        this.clearTokens()
        throw new Error('Authentication expired')
      }

      if (!this.isRefreshing) {
        this.isRefreshing = true
        try {
          const res = await fetch(`${this.baseUrl}/v1/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          })

          if (!res.ok) {
            this.clearTokens()
            this.isRefreshing = false
            throw new Error('Session expired')
          }

          const tokenData: TokenResponse = await res.json()
          this.setTokens(tokenData.access_token, tokenData.refresh_token)
          this.isRefreshing = false
          this.onTokenRefreshed(tokenData.access_token)
        } catch (err) {
          this.clearTokens()
          this.isRefreshing = false
          throw err
        }
      }

      // Wait for the ongoing refresh
      return new Promise<T>((resolve, reject) => {
        this.addRefreshSubscriber(async (newToken: string) => {
          headers.set('Authorization', `Bearer ${newToken}`)
          try {
            const retryRes = await fetch(url, { ...options, headers })
            if (!retryRes.ok) {
              const errData: ApiError = await retryRes.json().catch(() => ({
                error: retryRes.statusText,
                code: `HTTP_${retryRes.status}`
              }))
              return reject(errData)
            }
            resolve(await retryRes.json())
          } catch (e) {
            reject(e)
          }
        })
      })
    }

    if (!response.ok) {
      let errData: ApiError
      try {
        errData = await response.json()
      } catch {
        errData = {
          error: response.statusText || 'An unexpected error occurred',
          code: `HTTP_${response.status}`
        }
      }
      throw errData
    }

    // Handle 204 No Content or empty bodies
    if (response.status === 204) {
      return {} as T
    }

    return response.json()
  }

  // --- Auth Endpoints ---
  async login(payload: { email: string; password: string }): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, false)
    this.setTokens(res.access_token, res.refresh_token)
    return res
  }

  async register(payload: {
    email: string
    password: string
    display_name?: string
    bootstrap_token?: string
  }): Promise<RegisterResponse> {
    const res = await this.request<RegisterResponse>('/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload)
    }, false)
    if (res.access_token && res.refresh_token) {
      this.setTokens(res.access_token, res.refresh_token)
    }
    return res
  }

  async logout(): Promise<void> {
    const refreshToken = this.getRefreshToken()
    if (refreshToken) {
      try {
        await this.request('/v1/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken })
        }, false)
      } catch {
        // ignore logout errors on the backend
      }
    }
    this.clearTokens()
  }

  async switchOrg(orgId: string): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/v1/auth/switch-org', {
      method: 'POST',
      body: JSON.stringify({ org_id: orgId })
    })
    this.setTokens(res.access_token, res.refresh_token)
    return res
  }

  async forgotPassword(email: string): Promise<{ ok: boolean }> {
    return this.request('/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email })
    }, false)
  }

  async resetPassword(token: string, password: string): Promise<{ ok: boolean }> {
    return this.request('/v1/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password })
    }, false)
  }

  async verifyEmail(token: string): Promise<{ ok: boolean; email?: string }> {
    return this.request('/v1/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ token })
    }, false)
  }

  // --- Passwordless Magic Link & OTP ---
  async requestMagicLink(email: string): Promise<{ ok: boolean; message?: string }> {
    return this.request('/v1/auth/magic-link/request', {
      method: 'POST',
      body: JSON.stringify({ email })
    }, false)
  }

  async verifyMagicLink(token: string): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/v1/auth/magic-link/verify', {
      method: 'POST',
      body: JSON.stringify({ token })
    }, false)
    this.setTokens(res.access_token, res.refresh_token)
    return res
  }

  async verifyOtp(email: string, code: string): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/v1/auth/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code })
    }, false)
    this.setTokens(res.access_token, res.refresh_token)
    return res
  }

  // --- Profile & Sessions (/v1/auth/me, /v1/me) ---
  async getMe(): Promise<User> {
    return this.request<User>('/v1/auth/me')
  }

  async updateProfile(payload: { display_name?: string; email?: string }): Promise<User> {
    return this.request<User>('/v1/auth/me', {
      method: 'PATCH',
      body: JSON.stringify(payload)
    })
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<{ ok: boolean }> {
    return this.request('/v1/auth/me/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    })
  }

  async getSessions(): Promise<Session[]> {
    return this.request<Session[]>('/v1/auth/me/sessions')
  }

  async revokeSession(sessionId: string): Promise<{ ok: boolean }> {
    return this.request(`/v1/auth/me/sessions/${sessionId}`, {
      method: 'DELETE'
    })
  }

  async revokeAllSessions(): Promise<{ ok: boolean; revoked: number }> {
    return this.request('/v1/auth/me/sessions', {
      method: 'DELETE'
    })
  }

  async exportMyData(): Promise<UserExportData> {
    return this.request<UserExportData>('/v1/me/export')
  }

  async deleteMyAccount(): Promise<{ ok: boolean }> {
    const res = await this.request<{ ok: boolean }>('/v1/me/delete', {
      method: 'POST'
    })
    this.clearTokens()
    return res
  }

  // --- Tenancy / Orgs ---
  async getMyOrgs(): Promise<Org[]> {
    return this.request<Org[]>('/v1/orgs')
  }

  async createOrg(name: string): Promise<Org> {
    return this.request<Org>('/v1/orgs', {
      method: 'POST',
      body: JSON.stringify({ name })
    })
  }

  async getOrgMembers(orgId: string): Promise<OrgMembersResponse> {
    return this.request<OrgMembersResponse>(`/v1/orgs/${orgId}/members`)
  }

  async addOrgMember(orgId: string, payload: { user_id: string; role?: string; workspace_id?: string }): Promise<{ ok: boolean }> {
    return this.request(`/v1/orgs/${orgId}/members`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }

  async removeOrgMember(orgId: string, userId: string): Promise<{ ok: boolean }> {
    return this.request(`/v1/orgs/${orgId}/members/${userId}`, {
      method: 'DELETE'
    })
  }

  async deleteOrg(orgId: string): Promise<{ ok: boolean }> {
    return this.request(`/v1/orgs/${orgId}`, {
      method: 'DELETE'
    })
  }

  // --- Admin API ---
  async listUsers(params?: { q?: string; limit?: number; offset?: number }): Promise<UserListResponse> {
    const sp = new URLSearchParams()
    if (params?.q) sp.set('q', params.q)
    if (params?.limit) sp.set('limit', params.limit.toString())
    if (params?.offset) sp.set('offset', params.offset.toString())
    const qStr = sp.toString() ? `?${sp.toString()}` : ''
    return this.request<UserListResponse>(`/v1/admin/users${qStr}`)
  }

  async setUserActive(userId: string, isActive: boolean): Promise<{ ok: boolean; user_id: string; is_active: boolean }> {
    return this.request(`/v1/admin/users/${userId}/active`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive })
    })
  }

  async setGrant(payload: {
    user_id: string
    audience: string
    role?: string
    org_id?: string | null
  }): Promise<{ ok: boolean; user_id: string; audience: string; role: string }> {
    return this.request('/v1/admin/grants', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }

  async listAuditLogs(params?: {
    action?: string
    actor_id?: string
    resource_type?: string
    resource_id?: string
    limit?: number
    offset?: number
  }): Promise<AuditQueryResponse> {
    const sp = new URLSearchParams()
    if (params?.action) sp.set('action', params.action)
    if (params?.actor_id) sp.set('actor_id', params.actor_id)
    if (params?.resource_type) sp.set('resource_type', params.resource_type)
    if (params?.resource_id) sp.set('resource_id', params.resource_id)
    if (params?.limit) sp.set('limit', params.limit.toString())
    if (params?.offset) sp.set('offset', params.offset.toString())
    const qStr = sp.toString() ? `?${sp.toString()}` : ''
    return this.request<AuditQueryResponse>(`/v1/admin/audit${qStr}`)
  }

  async getReconciliationEvents(params?: {
    since_id?: string
    since_timestamp?: string
    limit?: number
  }): Promise<ReconciliationResponse> {
    const sp = new URLSearchParams()
    if (params?.since_id) sp.set('since_id', params.since_id)
    if (params?.since_timestamp) sp.set('since_timestamp', params.since_timestamp)
    if (params?.limit) sp.set('limit', params.limit.toString())
    const qStr = sp.toString() ? `?${sp.toString()}` : ''
    return this.request<ReconciliationResponse>(`/v1/admin/reconciliation/events${qStr}`)
  }

  async listServices(params?: { q?: string; limit?: number; offset?: number }): Promise<ServiceListResponse> {
    const sp = new URLSearchParams()
    if (params?.q) sp.set('q', params.q)
    if (params?.limit) sp.set('limit', params.limit.toString())
    if (params?.offset) sp.set('offset', params.offset.toString())
    const qStr = sp.toString() ? `?${sp.toString()}` : ''
    return this.request<ServiceListResponse>(`/v1/admin/services${qStr}`)
  }

  async getService(serviceId: string): Promise<ServiceDefinition> {
    return this.request<ServiceDefinition>(`/v1/admin/services/${serviceId}`)
  }

  async getServiceConfig(serviceId: string): Promise<ServiceConfigResponse> {
    return this.request<ServiceConfigResponse>(`/v1/admin/services/${serviceId}/config`)
  }

  async createService(payload: ServiceCreatePayload): Promise<ServiceDefinition> {
    return this.request<ServiceDefinition>('/v1/admin/services', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }

  async updateService(serviceId: string, payload: ServiceUpdatePayload): Promise<ServiceDefinition> {
    return this.request<ServiceDefinition>(`/v1/admin/services/${serviceId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    })
  }

  async deleteService(serviceId: string): Promise<{ ok: boolean; deleted: boolean; service_id: string }> {
    return this.request(`/v1/admin/services/${serviceId}`, {
      method: 'DELETE'
    })
  }

  // --- Roles & Permissions Overview ---
  async listRoles(serviceId?: string): Promise<RolesOverviewResponse> {
    const query = serviceId ? `?service_id=${encodeURIComponent(serviceId)}` : ''
    return this.request<RolesOverviewResponse>(`/v1/admin/roles${query}`)
  }

  async createRole(payload: RoleCreatePayload): Promise<any> {
    return this.request('/v1/admin/roles', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  }

  async deleteRole(serviceId: string, role: string): Promise<any> {
    return this.request(`/v1/admin/roles?service_id=${encodeURIComponent(serviceId)}&role=${encodeURIComponent(role)}`, {
      method: 'DELETE'
    })
  }

  // --- Health & Metrics ---
  async getHealth(): Promise<SystemHealth> {
    return this.request<SystemHealth>('/health', {}, false)
  }

  async getMetrics(): Promise<SystemMetrics> {
    return this.request<SystemMetrics>('/metrics', {}, false)
  }
}

export const api = new ApiClient()
