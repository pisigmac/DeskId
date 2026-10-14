/**
 * @deskid/nextjs - Server-Side Helpers for Server Components & Route Handlers
 */

import { parseJwtClaims, isJwtExpired, type DeskIdUser, type DeskIdSession, type DeskIdJwtClaims } from '@deskid/core'
import type { DeskIdServerSession } from './types'

/**
 * Extract token string from various cookie sources (Next.js cookies(), NextRequest, or raw string).
 */
async function extractTokenFromSource(
  source?: any,
  cookieName: string = 'deskid_access_token'
): Promise<string | null> {
  // 1. Explicit source passed as string
  if (typeof source === 'string') {
    // Check if it's the raw token or a cookie header string
    if (source.includes('=')) {
      const match = source.match(new RegExp(`(?:^|;\\s*)${cookieName}=([^;]*)`))
      return match && match[1] ? decodeURIComponent(match[1]) : null
    }
    return source
  }

  // 2. Explicit source has cookies.get() (NextRequest or Next.js ReadonlyRequestCookies)
  if (source?.cookies?.get) {
    const val = source.cookies.get(cookieName)
    return typeof val === 'object' ? val?.value || null : (val || null)
  }

  // 3. Explicit source has get() method (ReadonlyRequestCookies from next/headers)
  if (source?.get && typeof source.get === 'function') {
    const val = source.get(cookieName)
    return typeof val === 'object' ? val?.value || null : (val || null)
  }

  // 4. Fallback: Try dynamic import of 'next/headers' cookies() if in App Router
  try {
    // Dynamic import with ignore for optional peer dependency
    // @ts-ignore
    const nextHeaders = await import('next/headers').catch(() => null)
    if (nextHeaders && typeof nextHeaders.cookies === 'function') {
      const cookieStore: any = await nextHeaders.cookies()
      const cookie = cookieStore.get(cookieName)
      return cookie?.value || null
    }
  } catch {
    // next/headers not available or not in request context
  }

  return null
}

/**
 * Retrieve DeskID session on the server (Server Components, Route Handlers, Server Actions).
 *
 * Usage:
 * ```ts
 * import { getDeskIdSession } from '@deskid/nextjs/server'
 *
 * export default async function DashboardPage() {
 *   const session = await getDeskIdSession()
 *   if (!session) {
 *     // Handle unauthenticated
 *   }
 *   return <div>Welcome {session.user.display_name || session.user.email}</div>
 * }
 * ```
 */
export async function getDeskIdSession(
  cookieSource?: any,
  cookieName: string = 'deskid_access_token'
): Promise<DeskIdServerSession | null> {
  const token = await extractTokenFromSource(cookieSource, cookieName)
  if (!token) return null

  try {
    const claims = parseJwtClaims(token)
    if (!claims || isJwtExpired(token)) {
      return null
    }

    const user: DeskIdUser = {
      id: claims.sub,
      email: claims.email || '',
      display_name: claims.name || claims.display_name || null,
      is_platform_admin: Boolean(claims.is_platform_admin),
      is_active: true,
      orgs: [],
      grants: []
    }

    const session: DeskIdSession = {
      accessToken: token,
      refreshToken: '',
      claims,
      expiresAt: (claims.exp || 0) * 1000
    }

    return {
      session,
      user,
      claims
    }
  } catch {
    return null
  }
}

/**
 * Retrieve the current authenticated DeskID user on the server.
 */
export async function getDeskIdUser(
  cookieSource?: any,
  cookieName: string = 'deskid_access_token'
): Promise<DeskIdUser | null> {
  const session = await getDeskIdSession(cookieSource, cookieName)
  return session ? session.user : null
}

/**
 * Retrieve the current DeskID JWT claims on the server.
 */
export async function getDeskIdClaims(
  cookieSource?: any,
  cookieName: string = 'deskid_access_token'
): Promise<DeskIdJwtClaims | null> {
  const session = await getDeskIdSession(cookieSource, cookieName)
  return session ? session.claims : null
}
