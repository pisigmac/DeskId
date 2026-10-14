# DeskID Client SDKs & Drop-in UI Components

> **Drop-in authentication for modern web apps.** Go from zero to complete authentication, multi-tenancy, and organization switching in under 5 minutes.

---

## Packages in this Monorepo

| Package | Framework / Target | Key Exports | Size |
| :--- | :--- | :--- | :--- |
| **`@deskid/core`** | Universal (Browser/Node/Edge) | `DeskIdClient`, `parseJwtClaims`, `isJwtExpired`, `StorageAdapters` | ~3 KB |
| **`@deskid/react`** | React 18 & 19 | `<DeskIdProvider />`, `<SignInButton />`, `<DeskIdModal />`, `<UserButton />`, `useDeskId` | ~6 KB |
| **`@deskid/vue`** | Vue 3 Composition API | `createDeskId`, `<DeskIdProvider />`, `<SignInButton />`, `<DeskIdModal />`, `<UserButton />`, `useDeskId` | ~6 KB |
| **`@deskid/nextjs`** | Next.js 13, 14, 15 (App & Pages) | `deskIdAuthMiddleware`, `getDeskIdSession`, `getDeskIdUser`, Client UI Components | ~8 KB |

---

## 1. React Quickstart (`@deskid/react`)

### Installation
```bash
npm install @deskid/react
# or
pnpm add @deskid/react
```

### Setup Provider (`App.tsx` or `main.tsx`)
```tsx
import React from 'react'
import { DeskIdProvider, SignInButton, UserButton, useDeskId } from '@deskid/react'

export function App() {
  return (
    <DeskIdProvider baseUrl="https://auth.yourdomain.com" storage="cookie">
      <Navbar />
      <MainContent />
    </DeskIdProvider>
  )
}

function Navbar() {
  const { isAuthenticated, user } = useDeskId()

  return (
    <header style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem' }}>
      <h1>My SaaS App</h1>
      <div>
        {isAuthenticated ? (
          <UserButton showTenantSwitch={true} />
        ) : (
          <SignInButton mode="modal">Sign In</SignInButton>
        )}
      </div>
    </header>
  )
}

function MainContent() {
  const { isAuthenticated, user, activeOrg } = useDeskId()

  if (!isAuthenticated) {
    return <p>Please sign in to access your dashboard.</p>
  }

  return (
    <main>
      <h2>Welcome back, {user?.display_name || user?.email}!</h2>
      <p>Active Organization: {activeOrg?.name} (Role: {activeOrg?.role})</p>
    </main>
  )
}
```

---

## 2. Next.js Quickstart (`@deskid/nextjs`)

### Installation
```bash
npm install @deskid/nextjs
# or
pnpm add @deskid/nextjs
```

### Route Protection via Edge Middleware (`middleware.ts`)
Protect all private routes with a single middleware file:

```typescript
// middleware.ts
import { deskIdAuthMiddleware } from '@deskid/nextjs/middleware'

export default deskIdAuthMiddleware({
  publicRoutes: ['/', '/about', '/pricing', '/login'],
  loginUrl: '/login'
})

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
}
```

### Server Components (`app/dashboard/page.tsx`)
Zero-latency session reading in App Router server components:

```tsx
import { getDeskIdSession } from '@deskid/nextjs/server'
import { redirect } from 'next/navigation'

export default async function DashboardPage() {
  const session = await getDeskIdSession()

  if (!session) {
    redirect('/login')
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <p>Logged in as: {session.user.email}</p>
      <p>User ID: {session.user.id}</p>
    </div>
  )
}
```

### Route Handlers (`app/api/data/route.ts`)
```typescript
import { NextResponse } from 'next/server'
import { getDeskIdSession } from '@deskid/nextjs/server'

export async function GET() {
  const session = await getDeskIdSession()
  if (!session) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  return NextResponse.json({ data: 'Protected confidential data', userId: session.user.id })
}
```

---

## 3. Vue 3 Quickstart (`@deskid/vue`)

### Installation
```bash
npm install @deskid/vue
# or
pnpm add @deskid/vue
```

### App Registration (`main.ts`)
```typescript
import { createApp } from 'vue'
import { createDeskId } from '@deskid/vue'
import App from './App.vue'

const app = createApp(App)

app.use(createDeskId({
  baseUrl: 'https://auth.yourdomain.com',
  storage: 'cookie',
  autoRefresh: true
}))

app.mount('#app')
```

### Component Usage (`App.vue`)
```vue
<template>
  <DeskIdProvider>
    <header class="navbar">
      <h1>My Vue App</h1>
      <div v-if="isAuthenticated">
        <UserButton :show-tenant-switch="true" />
      </div>
      <div v-else>
        <SignInButton mode="modal">Sign In</SignInButton>
      </div>
    </header>

    <main v-if="isAuthenticated">
      <h2>Hello, {{ user?.display_name || user?.email }}</h2>
      <p>Active Organization: {{ activeOrg?.name }}</p>
    </main>
  </DeskIdProvider>
</template>

<script setup lang="ts">
import { DeskIdProvider, SignInButton, UserButton, useDeskId } from '@deskid/vue'

const { isAuthenticated, user, activeOrg } = useDeskId()
</script>
```

---

## 4. Headless Core SDK (`@deskid/core`)

For custom integrations or non-React/non-Vue frameworks (Svelte, Solid, vanilla JavaScript, React Native, Node.js scripts):

```typescript
import { DeskIdClient, CookieStorageAdapter } from '@deskid/core'

const auth = new DeskIdClient({
  baseUrl: 'https://auth.yourdomain.com',
  storage: new CookieStorageAdapter({ secure: true }),
  autoRefresh: true,
  refreshBufferSeconds: 60
})

// Listen to reactive authentication state changes
auth.onAuthStateChange((event, session) => {
  console.log('Auth event:', event, 'Current user:', session?.user)
})

// Password login
await auth.login({ email: 'user@example.com', password: 'secretpassword' })

// Passwordless Magic Link / OTP login
await auth.requestMagicLink('user@example.com')
await auth.verifyOtp('user@example.com', '123456')

// Multi-tenant Org Switching (exchanges token for scoped org token)
await auth.switchOrg('org_456')

// Sign out
await auth.logout()
```
