/**
 * @deskid/nextjs - Edge-compatible Authentication Middleware
 */

import { parseJwtClaims, isJwtExpired, type DeskIdJwtClaims, type DeskIdUser } from '@deskid/core'
import type { DeskIdMiddlewareOptions, DeskIdAuthResult } from './types'

const DEFAULT_PUBLIC_ROUTES = [
  '/',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/api/health'
]

/**
 * Check if the given pathname matches any of the public route patterns.
 */
export function isPublicRoute(pathname: string, publicRoutes: (string | RegExp)[] = DEFAULT_PUBLIC_ROUTES): boolean {
  for (const pattern of publicRoutes) {
    if (typeof pattern === 'string') {
      if (pattern === pathname || (pattern.endsWith('/*') && pathname.startsWith(pattern.slice(0, -2)))) {
        return true
      }
    } else if (pattern instanceof RegExp) {
      if (pattern.test(pathname)) {
        return true
      }
    }
  }
  return false
}

/**
 * Extract DeskID access token from NextRequest / Request.
 */
export function getAuthTokenFromRequest(
  request: any,
  cookieName: string = 'deskid_access_token'
): string | null {
  // Check NextRequest cookies map
  if (request.cookies?.get) {
    const cookie = request.cookies.get(cookieName)
    if (cookie && typeof cookie === 'object' && cookie.value) {
      return cookie.value
    } else if (typeof cookie === 'string') {
      return cookie
    }
  }

  // Check raw Cookie header
  const cookieHeader = request.headers?.get ? request.headers.get('cookie') : request.headers?.cookie
  if (cookieHeader && typeof cookieHeader === 'string') {
    const match = cookieHeader.match(new RegExp(`(?:^|;\\s*)${cookieName}=([^;]*)`))
    if (match && match[1]) {
      return decodeURIComponent(match[1])
    }
  }

  // Check Authorization Bearer header
  const authHeader = request.headers?.get ? request.headers.get('authorization') : request.headers?.authorization
  if (authHeader && typeof authHeader === 'string' && authHeader.startsWith('Bearer ')) {
    return authHeader.slice(7).trim()
  }

  return null
}

/**
 * Create DeskID Next.js Edge Auth Middleware.
 *
 * Usage:
 * ```ts
 * import { deskIdAuthMiddleware } from '@deskid/nextjs/middleware'
 *
 * export default deskIdAuthMiddleware({
 *   publicRoutes: ['/', '/about', '/pricing', '/login'],
 *   loginUrl: '/login'
 * })
 *
 * export const config = {
 *   matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
 * }
 * ```
 */
export function deskIdAuthMiddleware(options: DeskIdMiddlewareOptions = {}) {
  const {
    publicRoutes = DEFAULT_PUBLIC_ROUTES,
    loginUrl = '/login',
    cookieName = 'deskid_access_token',
    apiAuthRequired = true,
    afterAuth
  } = options

  return async function middleware(request: any) {
    const url = request.nextUrl || new URL(request.url)
    const pathname = url.pathname

    const token = getAuthTokenFromRequest(request, cookieName)
    let claims: DeskIdJwtClaims | null = null
    let isAuthenticated = false

    if (token) {
      try {
        claims = parseJwtClaims(token)
        if (claims && !isJwtExpired(token)) {
          isAuthenticated = true
        }
      } catch {
        claims = null
        isAuthenticated = false
      }
    }

    const user: DeskIdUser | null = (isAuthenticated && claims) ? {
      id: claims.sub,
      email: claims.email || '',
      display_name: claims.name || claims.display_name || null,
      is_platform_admin: Boolean(claims.is_platform_admin),
      is_active: true,
      orgs: [],
      grants: []
    } : null

    const authResult: DeskIdAuthResult = {
      isAuthenticated,
      token: isAuthenticated ? token : null,
      claims: isAuthenticated ? claims : null,
      user
    }

    // Call custom hook if provided
    if (afterAuth) {
      const customResponse = await afterAuth(authResult, request)
      if (customResponse) {
        return customResponse
      }
    }

    // If route is public, allow access regardless of auth
    if (isPublicRoute(pathname, publicRoutes)) {
      return createNextResponse(request, claims)
    }

    // Unauthenticated user attempting to access protected route
    if (!isAuthenticated) {
      // For API routes, return 401 JSON
      if (pathname.startsWith('/api/') && apiAuthRequired) {
        return new Response(
          JSON.stringify({
            error: 'unauthorized',
            message: 'Authentication required to access this resource'
          }),
          {
            status: 401,
            headers: { 'Content-Type': 'application/json' }
          }
        )
      }

      // For page routes, redirect to login URL with return path
      const redirectUrl = new URL(loginUrl, request.url)
      redirectUrl.searchParams.set('redirect_url', pathname + (url.search || ''))

      // Support NextResponse.redirect or standard Response.redirect
      if (typeof (globalThis as any).NextResponse?.redirect === 'function') {
        return (globalThis as any).NextResponse.redirect(redirectUrl)
      }
      return Response.redirect(redirectUrl.toString(), 307)
    }

    // Authenticated: forward request with claims attached to headers
    return createNextResponse(request, claims)
  }
}

/**
 * Creates a next() response with DeskID claims injected as headers
 */
function createNextResponse(request: any, claims: DeskIdJwtClaims | null) {
  // If Next.js global NextResponse exists
  const NextResponseClass = (globalThis as any).NextResponse
  const requestHeaders = new Headers(request.headers)

  if (claims) {
    requestHeaders.set('x-deskid-user-id', claims.sub)
    if (claims.email) requestHeaders.set('x-deskid-email', claims.email)
    if (claims.org_id) requestHeaders.set('x-deskid-org-id', claims.org_id)
    if (claims.roles && typeof claims.roles === 'object') {
      requestHeaders.set('x-deskid-roles', JSON.stringify(claims.roles))
    }
  }

  if (NextResponseClass && typeof NextResponseClass.next === 'function') {
    return NextResponseClass.next({
      request: {
        headers: requestHeaders
      }
    })
  }

  // Fallback for standard environments
  return new Response(null, {
    headers: requestHeaders
  })
}
