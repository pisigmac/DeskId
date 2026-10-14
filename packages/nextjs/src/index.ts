/**
 * @deskid/nextjs - Next.js Authentication SDK & Drop-in UI Components
 */

export * from '@deskid/core'
export * from './types'

// Client Components & React Hooks
export * from './client'

// Middleware & Server Helpers
export {
  deskIdAuthMiddleware,
  isPublicRoute,
  getAuthTokenFromRequest
} from './middleware'

export {
  getDeskIdSession,
  getDeskIdUser,
  getDeskIdClaims
} from './server'
