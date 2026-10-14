/**
 * @deskid/vue
 * Drop-in authentication components and Vue 3 composables for DeskID
 */

import type { App } from 'vue'
import DeskIdProvider from './components/DeskIdProvider.vue'
import DeskIdModal from './components/DeskIdModal.vue'
import SignInButton from './components/SignInButton.vue'
import UserButton from './components/UserButton.vue'

export { DeskIdProvider, DeskIdModal, SignInButton, UserButton }
export { useDeskId, DESKID_CONTEXT_KEY } from './context'
export type { DeskIdVueContext } from './types'
export * from '@deskid/core'

/**
 * Global Vue Plugin Installer
 */
export function createDeskIdPlugin() {
  return {
    install(app: App) {
      app.component('DeskIdProvider', DeskIdProvider)
      app.component('DeskIdModal', DeskIdModal)
      app.component('SignInButton', SignInButton)
      app.component('UserButton', UserButton)
    }
  }
}
