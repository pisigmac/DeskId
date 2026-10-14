/**
 * @deskid/core
 * Core types for DeskID SDK
 */

export interface DeskIdUser {
  id: string
  email: string
  display_name: string | null
  is_platform_admin: boolean
  is_active: boolean
  orgs: DeskIdOrg[]
  grants: DeskIdGrant[]
}

export interface DeskIdOrg {
  id: string
  name: string
  role: string
  workspace_id?: string | null
}

export interface DeskIdGrant {
  audience: string
  role: string
  org_id: string | null
}

export interface DeskIdTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface DeskIdJwtClaims {
  sub: string
  email: string
  iss: string
  aud: string | string[]
  exp: number
  iat: number
  org_id?: string | null
  workspace_id?: string | null
  roles?: Record<string, string>
  token_version?: number
  [key: string]: any
}

export interface DeskIdSession {
  accessToken: string
  refreshToken: string
  claims: DeskIdJwtClaims
  expiresAt: number
}

export type AuthChangeEvent =
  | 'INITIAL_SESSION'
  | 'SIGNED_IN'
  | 'SIGNED_OUT'
  | 'TOKEN_REFRESHED'
  | 'ORG_CHANGED'

export type AuthStateListener = (event: AuthChangeEvent, session: DeskIdSession | null) => void

export interface DeskIdClientOptions {
  baseUrl: string
  storage?: 'localStorage' | 'sessionStorage' | 'cookie' | 'memory'
  autoRefresh?: boolean
  refreshBufferSeconds?: number
  onAuthStateChange?: AuthStateListener
}

export interface LoginOptions {
  email: string
  password: string
}

export interface RegisterOptions {
  email: string
  password: string
  displayName?: string
  bootstrapToken?: string
}

export interface DeskIdError {
  error: string
  code: string
  detail?: any
  status?: number
}
