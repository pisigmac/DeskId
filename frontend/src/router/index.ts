import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'root',
    redirect: () => {
      const auth = useAuthStore()
      if (!auth.isAuthenticated) {
        return { name: 'login' }
      }
      if (auth.isPlatformAdmin) {
        return { name: 'admin-dashboard' }
      }
      return { name: 'account-profile' }
    }
  },
  // Auth routes (guest only)
  {
    path: '/auth',
    component: () => import('@/layouts/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { guestOnly: true, title: 'Sign In' }
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('@/views/auth/RegisterView.vue'),
        meta: { guestOnly: true, title: 'Create Account' }
      },
      {
        path: 'forgot-password',
        name: 'forgot-password',
        component: () => import('@/views/auth/ForgotPasswordView.vue'),
        meta: { guestOnly: true, title: 'Forgot Password' }
      },
      {
        path: 'reset-password',
        name: 'reset-password',
        component: () => import('@/views/auth/ResetPasswordView.vue'),
        meta: { guestOnly: true, title: 'Reset Password' }
      },
      {
        path: 'verify-email',
        name: 'verify-email',
        component: () => import('@/views/auth/VerifyEmailView.vue'),
        meta: { title: 'Verify Email' }
      },
      {
        path: 'magic-link',
        name: 'magic-link-verify',
        component: () => import('@/views/auth/MagicLinkVerifyView.vue'),
        meta: { title: 'Verifying Magic Link...' }
      },
      {
        path: 'callback',
        name: 'auth-callback',
        component: () => import('@/views/auth/OAuthCallbackView.vue'),
        meta: { title: 'Authenticating...' }
      }
    ]
  },
  // App Main Routes (Authenticated)
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // Account user self-service
      {
        path: 'account/profile',
        name: 'account-profile',
        component: () => import('@/views/account/ProfileView.vue'),
        meta: { title: 'Profile & Security' }
      },
      {
        path: 'account/sessions',
        name: 'account-sessions',
        component: () => import('@/views/account/SessionsView.vue'),
        meta: { title: 'Active Sessions' }
      },
      // Platform Admin Console
      {
        path: 'admin',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { requiresAdmin: true, title: 'Platform Dashboard' }
      },
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { requiresAdmin: true, title: 'User Directory' }
      },
      {
        path: 'admin/organizations',
        name: 'admin-organizations',
        component: () => import('@/views/admin/OrganizationsView.vue'),
        meta: { requiresAdmin: true, title: 'Organizations & Tenancy' }
      },
      {
        path: 'admin/roles',
        name: 'admin-roles',
        component: () => import('@/views/admin/RolesView.vue'),
        meta: { requiresAdmin: true, title: 'Roles & Permissions' }
      },
      {
        path: 'admin/grants',
        name: 'admin-grants',
        component: () => import('@/views/admin/GrantsView.vue'),
        meta: { requiresAdmin: true, title: 'Product Grants' }
      },
      {
        path: 'admin/services',
        name: 'admin-services',
        component: () => import('@/views/admin/ServicesView.vue'),
        meta: { requiresAdmin: true, title: 'Service Registry' }
      },
      {
        path: 'admin/audit',
        name: 'admin-audit',
        component: () => import('@/views/admin/AuditLogsView.vue'),
        meta: { requiresAdmin: true, title: 'Audit Stream' }
      }
    ]
  },
  // Catch-all
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Navigation Guards
router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  // Wait for initial auth state if app just loaded
  if (auth.isInitializing) {
    await auth.initAuth()
  }

  // Update document title
  if (to.meta.title) {
    document.title = `${to.meta.title} — DeskID`
  } else {
    document.title = 'DeskID — Unified Identity & Admin Portal'
  }

  // Check guest-only routes
  if (to.meta.guestOnly && auth.isAuthenticated) {
    if (auth.isPlatformAdmin) {
      return next({ name: 'admin-dashboard' })
    }
    return next({ name: 'account-profile' })
  }

  // Check requiresAuth
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!auth.isAuthenticated) {
      return next({
        name: 'login',
        query: { redirect: to.fullPath }
      })
    }
  }

  // Check requiresAdmin
  if (to.matched.some(record => record.meta.requiresAdmin)) {
    if (!auth.isPlatformAdmin) {
      return next({ name: 'account-profile' })
    }
  }

  next()
})

export default router
