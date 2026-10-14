/**
 * @deskid/nextjs - Type Definitions
 */

import type { DeskIdJwtClaims, DeskIdUser, DeskIdSession } from '@deskid/core'

export type DeskIdTokenClaims = DeskIdJwtClaims

export interface DeskIdMiddlewareOptions {
  /**
   * Routes that are accessible without authentication.
   * Can be path strings (e.g. '/login', '/pricing', '/') or RegExp instances.
   * Default: ['/login', '/register', '/forgot-password', '/reset-password']
   */
  publicRoutes?: (string | RegExp)[]

  /**
   * URL to redirect unauthenticated users to.
   * Default: '/login'
   */
  loginUrl?: string

  /**
   * Cookie name where DeskID access token is stored.
   * Default: 'deskid_access_token'
   */
  cookieName?: string

  /**
   * Cookie name where DeskID refresh token is stored.
   * Default: 'deskid_refresh_token'
   */
  refreshTokenCookieName?: string

  /**
   * Whether unauthenticated API routes return 401 JSON instead of redirecting.
   * Default: true
   */
  apiAuthRequired?: boolean

  /**
   * Custom hook called after authentication verification in middleware.
   */
  afterAuth?: (auth: DeskIdAuthResult, request: any) => any
}

export interface DeskIdAuthResult {
  isAuthenticated: boolean
  token: string | null
  claims: DeskIdJwtClaims | null
  user: DeskIdUser | null
}

export interface DeskIdServerSession {
  session: DeskIdSession | null
  user: DeskIdUser | null
  claims: DeskIdJwtClaims | null
}
