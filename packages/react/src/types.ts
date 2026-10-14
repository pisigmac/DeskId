/**
 * @deskid/react - Types
 */

import type { DeskIdUser, DeskIdSession, DeskIdOrg, LoginOptions, RegisterOptions } from '@deskid/core'

export interface DeskIdReactContext {
  user: DeskIdUser | null
  session: DeskIdSession | null
  isAuthenticated: boolean
  isLoading: boolean
  activeOrg: DeskIdOrg | null
  isModalOpen: boolean
  openSignInModal: () => void
  closeSignInModal: () => void
  login: (options: LoginOptions) => Promise<DeskIdSession>
  register: (options: RegisterOptions) => Promise<{ verificationRequired: boolean; session?: DeskIdSession }>
  requestMagicLink: (email: string) => Promise<{ ok: boolean }>
  verifyOtp: (email: string, code: string) => Promise<DeskIdSession>
  logout: () => Promise<void>
  switchOrg: (orgId: string) => Promise<DeskIdSession>
}
