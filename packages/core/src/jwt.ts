/**
 * @deskid/core - JWT utility functions
 * Decodes RS256 JWT payloads safely without third-party dependencies.
 */

import type { DeskIdJwtClaims } from './types'

export function parseJwtClaims(token: string): DeskIdJwtClaims {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      throw new Error('Invalid JWT format')
    }

    const base64Url = parts[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')

    let jsonPayload: string
    if (typeof atob === 'function') {
      const raw = atob(base64)
      jsonPayload = decodeURIComponent(
        raw
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      )
    } else if (typeof (globalThis as any).Buffer !== 'undefined') {
      jsonPayload = (globalThis as any).Buffer.from(base64, 'base64').toString('utf-8')
    } else {
      throw new Error('No base64 decoder available in environment')
    }

    return JSON.parse(jsonPayload) as DeskIdJwtClaims
  } catch (err: any) {
    throw new Error(`Failed to decode JWT claims: ${err.message}`)
  }
}

export function isJwtExpired(token: string, bufferSeconds: number = 30): boolean {
  try {
    const claims = parseJwtClaims(token)
    if (!claims.exp) return false
    const nowInSeconds = Math.floor(Date.now() / 1000)
    return claims.exp - bufferSeconds <= nowInSeconds
  } catch {
    return true
  }
}
