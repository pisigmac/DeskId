import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import type { User, Org, Grant, TokenResponse } from '@/api/types'
import { useUiStore } from './ui'

export const useAuthStore = defineStore('auth', () => {
  const ui = useUiStore()

  const accessToken = ref<string | null>(localStorage.getItem('deskid_access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('deskid_refresh_token'))
  const user = ref<User | null>(null)
  const activeOrgId = ref<string | null>(localStorage.getItem('deskid_active_org_id'))
  const isInitializing = ref(true)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isPlatformAdmin = computed(() => !!user.value?.is_platform_admin)

  const activeOrg = computed<Org | null>(() => {
    if (!user.value || !user.value.orgs.length) return null
    if (activeOrgId.value) {
      const match = user.value.orgs.find(o => o.id === activeOrgId.value)
      if (match) return match
    }
    return user.value.orgs[0] || null
  })

  const userGrants = computed<Grant[]>(() => {
    return user.value?.grants || []
  })

  async function fetchProfile(): Promise<User | null> {
    try {
      const u = await api.getMe()
      user.value = u

      // Sync active org
      if (u.orgs && u.orgs.length > 0) {
        if (!activeOrgId.value || !u.orgs.find(o => o.id === activeOrgId.value)) {
          activeOrgId.value = u.orgs[0].id
          localStorage.setItem('deskid_active_org_id', u.orgs[0].id)
        }
      } else {
        activeOrgId.value = null
        localStorage.removeItem('deskid_active_org_id')
      }

      return u
    } catch {
      // If fetching me fails, clear tokens
      user.value = null
      accessToken.value = null
      refreshToken.value = null
      localStorage.removeItem('deskid_access_token')
      localStorage.removeItem('deskid_refresh_token')
      return null
    }
  }

  async function initAuth() {
    isInitializing.value = true
    if (accessToken.value) {
      await fetchProfile()
    }
    isInitializing.value = false
  }

  async function login(credentials: { email: string; password: string }) {
    try {
      const res = await api.login(credentials)
      accessToken.value = res.access_token
      refreshToken.value = res.refresh_token
      await fetchProfile()
      ui.showToast({
        type: 'success',
        title: 'Welcome back!',
        message: `Logged in as ${user.value?.email}`
      })
      return true
    } catch (err: any) {
      const msg = err?.error || 'Invalid credentials or login failed.'
      ui.showToast({
        type: 'error',
        title: 'Login failed',
        message: msg
      })
      throw err
    }
  }

  async function register(payload: {
    email: string
    password: string
    display_name?: string
    bootstrap_token?: string
  }) {
    try {
      const res = await api.register(payload)
      if (res.verification_required) {
        ui.showToast({
          type: 'info',
          title: 'Verification email sent',
          message: 'Please check your email to activate your account.'
        })
        return { verificationRequired: true }
      }
      if (res.access_token && res.refresh_token) {
        accessToken.value = res.access_token
        refreshToken.value = res.refresh_token
        await fetchProfile()
        ui.showToast({
          type: 'success',
          title: 'Account created!',
          message: `Welcome to DeskID, ${user.value?.display_name || user.value?.email}`
        })
      }
      return { verificationRequired: false }
    } catch (err: any) {
      const msg = err?.error || 'Registration failed. Please check your inputs.'
      ui.showToast({
        type: 'error',
        title: 'Registration failed',
        message: msg
      })
      throw err
    }
  }

  async function switchOrg(orgId: string) {
    try {
      const tokens = await api.switchOrg(orgId)
      accessToken.value = tokens.access_token
      refreshToken.value = tokens.refresh_token
      activeOrgId.value = orgId
      localStorage.setItem('deskid_active_org_id', orgId)
      await fetchProfile()
      ui.showToast({
        type: 'success',
        title: 'Organization Switched',
        message: `Active tenant context updated to ${activeOrg.value?.name || orgId}`
      })
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Failed to switch organization',
        message: err?.error || 'Organization access denied'
      })
      throw err
    }
  }

  function handleAuthTokens(tokens: TokenResponse) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    localStorage.setItem('deskid_access_token', tokens.access_token)
    localStorage.setItem('deskid_refresh_token', tokens.refresh_token)
    return fetchProfile()
  }

  async function loginWithMagicLink(token: string) {
    const res = await api.verifyMagicLink(token)
    await handleAuthTokens(res)
    ui.showToast({
      type: 'success',
      title: 'Welcome back!',
      message: `Signed in as ${user.value?.email}`
    })
    return res
  }

  async function loginWithOtp(email: string, code: string) {
    const res = await api.verifyOtp(email, code)
    await handleAuthTokens(res)
    ui.showToast({
      type: 'success',
      title: 'Welcome back!',
      message: `Signed in as ${user.value?.email}`
    })
    return res
  }

  async function logout() {
    try {
      await api.logout()
    } finally {
      accessToken.value = null
      refreshToken.value = null
      user.value = null
      activeOrgId.value = null
      localStorage.removeItem('deskid_access_token')
      localStorage.removeItem('deskid_refresh_token')
      localStorage.removeItem('deskid_active_org_id')
      ui.showToast({
        type: 'info',
        title: 'Logged out',
        message: 'You have been successfully signed out.'
      })
    }
  }

  async function updateProfile(payload: { display_name?: string; email?: string }) {
    try {
      const updated = await api.updateProfile(payload)
      user.value = updated
      ui.showToast({
        type: 'success',
        title: 'Profile updated',
        message: 'Your profile changes have been saved.'
      })
      return updated
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Update failed',
        message: err?.error || 'Failed to update profile.'
      })
      throw err
    }
  }

  async function changePassword(currentPass: string, newPass: string) {
    try {
      await api.changePassword(currentPass, newPass)
      ui.showToast({
        type: 'success',
        title: 'Password updated',
        message: 'Your password has been changed successfully.'
      })
    } catch (err: any) {
      ui.showToast({
        type: 'error',
        title: 'Password change failed',
        message: err?.error || 'Failed to change password.'
      })
      throw err
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    activeOrgId,
    activeOrg,
    userGrants,
    isAuthenticated,
    isPlatformAdmin,
    isInitializing,
    initAuth,
    login,
    register,
    logout,
    switchOrg,
    fetchProfile,
    handleAuthTokens,
    loginWithMagicLink,
    loginWithOtp,
    updateProfile,
    changePassword
  }
})
