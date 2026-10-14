/**
 * @deskid/core - Storage Adapters
 */

export interface TokenStorage {
  getAccessToken(): string | null
  getRefreshToken(): string | null
  setTokens(accessToken: string, refreshToken: string): void
  clearTokens(): void
}

export class LocalStorageAdapter implements TokenStorage {
  private accessKey: string
  private refreshKey: string

  constructor(prefix: string = 'deskid_') {
    this.accessKey = `${prefix}access_token`
    this.refreshKey = `${prefix}refresh_token`
  }

  getAccessToken(): string | null {
    if (typeof localStorage === 'undefined') return null
    return localStorage.getItem(this.accessKey)
  }

  getRefreshToken(): string | null {
    if (typeof localStorage === 'undefined') return null
    return localStorage.getItem(this.refreshKey)
  }

  setTokens(accessToken: string, refreshToken: string): void {
    if (typeof localStorage === 'undefined') return
    localStorage.setItem(this.accessKey, accessToken)
    localStorage.setItem(this.refreshKey, refreshToken)
  }

  clearTokens(): void {
    if (typeof localStorage === 'undefined') return
    localStorage.removeItem(this.accessKey)
    localStorage.removeItem(this.refreshKey)
  }
}

export class MemoryStorageAdapter implements TokenStorage {
  private accessToken: string | null = null
  private refreshToken: string | null = null

  getAccessToken(): string | null {
    return this.accessToken
  }

  getRefreshToken(): string | null {
    return this.refreshToken
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken
    this.refreshToken = refreshToken
  }

  clearTokens(): void {
    this.accessToken = null
    this.refreshToken = null
  }
}

export class CookieStorageAdapter implements TokenStorage {
  private accessKey: string
  private refreshKey: string

  constructor(prefix: string = 'deskid_') {
    this.accessKey = `${prefix}access_token`
    this.refreshKey = `${prefix}refresh_token`
  }

  private getCookie(name: string): string | null {
    if (typeof document === 'undefined') return null
    const match = document.cookie.match(new RegExp('(^|;\\s*)(' + name + ')=([^;]*)'))
    return match ? decodeURIComponent(match[3]) : null
  }

  private setCookie(name: string, value: string, days: number = 7): void {
    if (typeof document === 'undefined') return
    const expires = new Date(Date.now() + days * 864e5).toUTCString()
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`
  }

  private deleteCookie(name: string): void {
    if (typeof document === 'undefined') return
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`
  }

  getAccessToken(): string | null {
    return this.getCookie(this.accessKey)
  }

  getRefreshToken(): string | null {
    return this.getCookie(this.refreshKey)
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.setCookie(this.accessKey, accessToken, 1) // 1 day access token cookie
    this.setCookie(this.refreshKey, refreshToken, 30) // 30 day refresh cookie
  }

  clearTokens(): void {
    this.deleteCookie(this.accessKey)
    this.deleteCookie(this.refreshKey)
  }
}
