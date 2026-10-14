/**
 * @deskid/vue - Context Injection Key & Composable
 */

import { inject, type InjectionKey } from 'vue'
import type { DeskIdVueContext } from './types'

export const DESKID_CONTEXT_KEY: InjectionKey<DeskIdVueContext> = Symbol('DESKID_CONTEXT_KEY')

export function useDeskId(): DeskIdVueContext {
  const context = inject(DESKID_CONTEXT_KEY)
  if (!context) {
    throw new Error('useDeskId() must be used within a <DeskIdProvider> component or DeskId plugin')
  }
  return context
}
