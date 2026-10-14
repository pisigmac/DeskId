# DeskID React Demo Application

An interactive, live demonstration showcasing how to embed **DeskID drop-in components** (`@deskid/react`) and the universal core client (`@deskid/core`) into a modern React application.

---

## Features Demonstrated

1. **Root `<DeskIdProvider>`:** Automatic auth state synchronization, background token refresh, and storage adapters (`localStorage`, `cookie`, `sessionStorage`).
2. **`<SignInButton mode="modal">`:** Drop-in button that launches the fully accessible DeskID modal with Password and OTP / Magic Link tabs.
3. **`<UserButton />`:** Drop-in avatar component displaying the user's initials, email, role, and dynamic multi-tenant organization switching.
4. **`useDeskId()` Hook:** Reactive access to `isAuthenticated`, `isLoading`, `user`, `session`, `activeOrg`, and auth actions.
5. **Downstream API Simulator:** Live simulator making authenticated HTTP calls (`GET /v1/auth/me`) with `Authorization: Bearer <token>`.
6. **JWT Claims Inspector:** Live decoded RS256 token claims viewer (`sub`, `iss`, `aud`, `roles`, `org_id`).

---

## Running the Demo

### 1. Ensure DeskID Backend is Running
```bash
# From workspace root
docker compose up -d
# or
deskid
# (Running on http://127.0.0.1:8090)
```

### 2. Start the Demo Application
```bash
cd examples/react-demo
pnpm run dev
```

Visit **`http://localhost:3000`** in your browser.
