/**
 * @deskid/core - Main Client Class
 */

import { parseJwtClaims, isJwtExpired } from './jwt'
import {
  LocalStorageAdapter,
  MemoryStorageAdapter,
  CookieStorageAdapter,
  type TokenStorage
} from './storage'
import type {
  DeskIdClientOptions,
  DeskIdUser,
  DeskIdSession,
  DeskIdTokenResponse,
  AuthChangeEvent,
  AuthStateListener,
  LoginOptions,
  RegisterOptions,
  DeskIdError
} from './types'

export class DeskIdClient {
  public readonly baseUrl: string
  private storage: TokenStorage
  private autoRefresh: boolean
  private refreshBufferSeconds: number
  private listeners: Set<AuthStateListener> = new Set()
  private refreshTimeoutId: any = null
  private user: DeskIdUser | null = null
  private session: DeskIdSession | null = null
  private isRefreshing: boolean = false

  constructor(options: DeskIdClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, '')
    this.autoRefresh = options.autoRefresh ?? true
    this.refreshBufferSeconds = options.refreshBufferSeconds ?? 45

    if (options.storage === 'memory') {
      this.storage = new MemoryStorageAdapter()
    } else if (options.storage === 'cookie') {
      this.storage = new CookieStorageAdapter()
    } else {
      this.storage = new LocalStorageAdapter()
    }

    if (options.onAuthStateChange) {
      this.onAuthStateChange(options.onAuthStateChange)
    }

    this.initialize()
  }

  private async initialize(): Promise<void> {
    const accessToken = this.storage.getAccessToken()
    const refreshToken = this.storage.getRefreshToken()

    if (accessToken && refreshToken) {
      try {
        const claims = parseJwtClaims(accessToken)
        this.session = {
          accessToken,
          refreshToken,
          claims,
          expiresAt: claims.exp * 1000
        }

        if (isJwtExpired(accessToken, this.refreshBufferSeconds)) {
          await this.refreshToken()
        } else {
          await this.fetchUser()
          this.scheduleTokenRefresh()
          this.notifyListeners('INITIAL_SESSION')
        }
      } catch {
        this.storage.clearTokens()
        this.session = null
        this.user = null
      }
    }
  }

  public onAuthStateChange(listener: AuthStateListener): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  private notifyListeners(event: AuthChangeEvent): void {
    this.listeners.forEach(fn => fn(event, this.session))
  }

  private scheduleTokenRefresh(): void {
    if (!this.autoRefresh || !this.session) return

    if (this.refreshTimeoutId) {
      clearTimeout(this.refreshTimeoutId)
      this.refreshTimeoutId = null
    }

    const timeUntilExpiryMs = this.session.expiresAt - Date.now()
    const refreshDelayMs = Math.max(1000, timeUntilExpiryMs - this.refreshBufferSeconds * 1000)

    this.refreshTimeoutId = setTimeout(() => {
      this.refreshToken().catch(() => {
        // failed refresh will be handled on next request
      })
    }, refreshDelayMs)
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, requiresAuth: boolean = true): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = new Headers(options.headers || {})

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    if (requiresAuth && this.session?.accessToken) {
      headers.set('Authorization', `Bearer ${this.session.accessToken}`)
    }

    let res = await fetch(url, { ...options, headers })

    if (res.status === 401 && requiresAuth && this.session?.refreshToken) {
      const refreshed = await this.refreshToken()
      if (refreshed) {
        headers.set('Authorization', `Bearer ${this.session?.accessToken}`)
        res = await fetch(url, { ...options, headers })
      }
    }

    if (!res.ok) {
      let err: DeskIdError
      try {
        err = await res.json()
      } catch {
        err = {
          error: res.statusText || 'Request failed',
          code: `HTTP_${res.status}`,
          status: res.status
        }
      }
      err.status = res.status
      throw err
    }

    if (res.status === 204) {
      return {} as T
    }

    return res.json()
  }

  public async login(options: LoginOptions): Promise<DeskIdSession> {
    const res = await this.request<DeskIdTokenResponse>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(options)
    }, false)

    return this.handleNewTokens(res, 'SIGNED_IN')
  }

  public async register(options: RegisterOptions): Promise<{ verificationRequired: boolean; session?: DeskIdSession }> {
    const res = await this.request<{
      access_token?: string
      refresh_token?: string
      token_type?: string
      expires_in?: number
      verification_required: boolean
    }>('/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: options.email,
        password: options.password,
        display_name: options.displayName,
        bootstrap_token: options.bootstrapToken
      })
    }, false)

    if (res.access_token && res.refresh_token) {
      const session = await this.handleNewTokens(
        {
          access_token: res.access_token,
          refresh_token: res.refresh_token,
          token_type: res.token_type || 'Bearer',
          expires_in: res.expires_in || 900
        },
        'SIGNED_IN'
      )
      return { verificationRequired: false, session }
    }

    return { verificationRequired: Boolean(res.verification_required) }
  }

  public async requestMagicLink(email: string): Promise<{ ok: boolean }> {
    return this.request('/v1/auth/magic-link/request', {
      method: 'POST',
      body: JSON.stringify({ email })
    }, false)
  }

  public async verifyMagicLink(token: string): Promise<DeskIdSession> {
    const res = await this.request<DeskIdTokenResponse>('/v1/auth/magic-link/verify', {
      method: 'POST',
      body: JSON.stringify({ token })
    }, false)

    return this.handleNewTokens(res, 'SIGNED_IN')
  }

  public async verifyOtp(email: string, code: string): Promise<DeskIdSession> {
    const res = await this.request<DeskIdTokenResponse>('/v1/auth/otp/verify', {
      method: 'POST',
      body: JSON.stringify({ email, code })
    }, false)

    return this.handleNewTokens(res, 'SIGNED_IN')
  }

  public async refreshToken(): Promise<boolean> {
    if (this.isRefreshing) return false
    const token = this.session?.refreshToken || this.storage.getRefreshToken()
    if (!token) {
      this.clearSession()
      return false
    }

    this.isRefreshing = true
    try {
      const res = await fetch(`${this.baseUrl}/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: token })
      })

      if (!res.ok) {
        this.clearSession()
        return false
      }

      const data: DeskIdTokenResponse = await res.json()
      await this.handleNewTokens(data, 'TOKEN_REFRESHED')
      return true
    } catch {
      return false
    } finally {
      this.isRefreshing = false
    }
  }

  private async handleNewTokens(res: DeskIdTokenResponse, event: AuthChangeEvent): Promise<DeskIdSession> {
    this.storage.setTokens(res.access_token, res.refresh_token)
    const claims = parseJwtClaims(res.access_token)

    this.session = {
      accessToken: res.access_token,
      refreshToken: res.refresh_token,
      claims,
      expiresAt: claims.exp * 1000
    }

    await this.fetchUser()
    this.scheduleTokenRefresh()
    this.notifyListeners(event)

    return this.session
  }

  public async fetchUser(): Promise<DeskIdUser | null> {
    try {
      this.user = await this.request<DeskIdUser>('/v1/auth/me')
      return this.user
    } catch {
      return null
    }
  }

  public async switchOrg(orgId: string): Promise<DeskIdSession> {
    const res = await this.request<DeskIdTokenResponse>('/v1/auth/switch-org', {
      method: 'POST',
      body: JSON.stringify({ org_id: orgId })
    })

    return this.handleNewTokens(res, 'ORG_CHANGED')
  }

  public async logout(): Promise<void> {
    const token = this.session?.refreshToken
    if (token) {
      try {
        await this.request('/v1/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: token })
        }, false)
      } catch {
        // ignore logout errors on backend
      }
    }
    this.clearSession()
  }

  private clearSession(): void {
    if (this.refreshTimeoutId) {
      clearTimeout(this.refreshTimeoutId)
      this.refreshTimeoutId = null
    }
    this.storage.clearTokens()
    this.session = null
    this.user = null
    this.notifyListeners('SIGNED_OUT')
  }

  public getUser(): DeskIdUser | null {
    return this.user
  }

  public getSession(): DeskIdSession | null {
    return this.session
  }

  public isAuthenticated(): boolean {
    return Boolean(this.session && !isJwtExpired(this.session.accessToken))
  }
}
