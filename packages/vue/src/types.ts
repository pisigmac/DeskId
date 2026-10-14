/**
 * @deskid/vue - Types
 */

import type { Ref, ComputedRef } from 'vue'
import type { DeskIdUser, DeskIdSession, DeskIdOrg, LoginOptions, RegisterOptions } from '@deskid/core'

export interface DeskIdVueContext {
  user: Ref<DeskIdUser | null>
  session: Ref<DeskIdSession | null>
  isAuthenticated: ComputedRef<boolean>
  isLoading: Ref<boolean>
  activeOrg: ComputedRef<DeskIdOrg | null>
  isModalOpen: Ref<boolean>
  openSignInModal: () => void
  closeSignInModal: () => void
  login: (options: LoginOptions) => Promise<DeskIdSession>
  register: (options: RegisterOptions) => Promise<{ verificationRequired: boolean; session?: DeskIdSession }>
  requestMagicLink: (email: string) => Promise<{ ok: boolean }>
  verifyOtp: (email: string, code: string) => Promise<DeskIdSession>
  logout: () => Promise<void>
  switchOrg: (orgId: string) => Promise<DeskIdSession>
}
