# DeskID Downstream Product & Service Onboarding Guide

> **Audience:** Backend engineers, microservice architects, and platform operators.  
> **Target System:** DeskID Authentication & Identity Engine (`deskid`).  
> **Status:** Production Standard.

---

## 1. Overview & Architecture Philosophy

DeskID is a product-agnostic, centralized identity control plane. Consumer and downstream services do not manage user databases, password hashes, or session tables. Instead:

1. **Stateless Verification:** Downstream services validate RS256 JWTs locally using public keys fetched from DeskID's JWKS (`/.well-known/jwks.json`). **No HTTP calls to DeskID are made during individual user requests.**
2. **Audience-Restricted Tokens:** Tokens issued by DeskID specify an `aud` claim containing all service IDs the user is authorized to access. Downstream services strictly reject tokens that do not contain their service audience.
3. **Custom Service Roles:** Each service defines its own allowed role taxonomy (e.g. `catalog-admin`, `data-reader`, `pipeline-runner`), which DeskID enforces and packages into the JWT under `claims["roles"][<service_id>]`.
4. **Dual-Tier Tenancy:** DeskID supports both platform-wide (global) grants and organization-scoped (tenant) grants, allowing downstream services to enforce tenant isolation and role separation effortlessly.

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Application
    participant DeskID as Central DeskID (IAM :8090)
    participant Svc as Downstream Service Backend

    Note over User,DeskID: 1. Service Registration & User Login
    User->>DeskID: POST /v1/auth/login
    DeskID-->>User: JWT Access Token (aud: ["deskid", "service-a"], roles: {"service-a": "operator"})

    Note over User,Svc: 2. Downstream Service Request (Stateless)
    User->>Svc: GET /api/v1/resource (Authorization: Bearer <JWT>)
    Svc->>Svc: Verify JWT signature using cached JWKS (kid match)
    Svc->>Svc: Verify iss, aud ("service-a"), exp, and nbf
    Svc->>Svc: Authorize based on claims.roles["service-a"] & claims.org_id
    Svc-->>User: 200 OK (Data response)
```

---

## 2. Central Platform Deployment vs. Downstream Service Consumption

A common question from engineers is: *"Do downstream or 3rd-party services need to download a DeskID Docker image or proprietary SDK?"*

**No.** DeskID operates on a centralized, two-tier architecture:

| Role | Runs Docker? | Needs DeskID SDK? | What they actually use |
| :--- | :---: | :---: | :--- |
| **Platform / Infra Team** | **Yes** (Centrally) | N/A | Runs `deskid` image once behind `https://auth.company.internal` |
| **Downstream Backend API** | **No** | **No** | Standard open-source JWT/JWKS library (`pyjwt`, `jsonwebtoken`, `golang-jwt`) |
| **Downstream Frontend App** | **No** | **Optional** | Optional `@deskid/react` UI components, or standard OAuth/login redirect |

```mermaid
flowchart TD
    subgraph PlatformInfra["Platform Cloud / Infra (Deployed Once)"]
        direction TB
        CentralDeskID["DeskID Central Container<br>(:8090 / https://auth.company.internal)<br>• Issues RS256 JWTs<br>• Hosts JWKS & Admin Console<br>• Multi-Tenant RBAC"]
        DB[("PostgreSQL<br>(User & Tenancy Store)")]
        Redis[("Redis<br>(Rate Limiting & Sessions)")]
        CentralDeskID --- DB
        CentralDeskID --- Redis
    end

    JWKS["Public JWKS Key Registry<br>GET /.well-known/jwks.json"]
    CentralDeskID -->|Publishes Public Keys| JWKS

    subgraph SvcA["3rd-Party Service A (e.g., Billing API)"]
        direction TB
        BackendA["Backend API (Node.js / Express)"]
        LibA["Standard Lib: jwks-rsa + jsonwebtoken<br>(NO DeskID Docker / NO DeskID SDK)"]
        BackendA --- LibA
    end

    subgraph SvcB["3rd-Party Service B (e.g., Analytics Engine)"]
        direction TB
        BackendB["Backend API (Python / FastAPI)"]
        LibB["Standard Lib: PyJWT<br>(NO DeskID Docker / NO DeskID SDK)"]
        BackendB --- LibB
    end

    subgraph SvcC["3rd-Party Service C (e.g., Data Pipeline)"]
        direction TB
        BackendC["Backend API (Go)"]
        LibC["Standard Lib: lestrrat-go/jwx<br>(NO DeskID Docker / NO DeskID SDK)"]
        BackendC --- LibC
    end

    JWKS -.->|Periodic Fetch & Local Cache| LibA
    JWKS -.->|Periodic Fetch & Local Cache| LibB
    JWKS -.->|Periodic Fetch & Local Cache| LibC
```

### 2.1 For the Platform / Infra Team: Central Deployment Steps
1. **Generate Cryptographic Keys (RS256):**
   ```bash
   openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
   openssl rsa -pubout -in private.pem -out public.pem
   chmod 600 private.pem && chmod 644 public.pem
   ```
2. **Provision Core Environment:**
   Set `AUTH_ISSUER=https://auth.company.internal`, `AUTH_DATABASE_URL`, `AUTH_RATE_LIMIT_REDIS_URL`, and point `AUTH_JWT_PRIVATE_KEY_FILE` / `AUTH_JWT_PUBLIC_KEY_FILE` to the generated keys.
3. **Run Central Docker Image:**
   Deploy the `deskid` container once in Kubernetes, AWS ECS, or Docker Compose behind an HTTPS reverse proxy (Nginx, Traefik, or ALB).
4. **Register Services:**
   Log into `https://auth.company.internal/admin` and register downstream service audiences (e.g. `analytics-engine`, `billing-api`) with their allowed role taxonomies.

### 2.2 For Third-Party / Downstream Teams: Consumption Steps
1. **Zero Infrastructure:** Do not run DeskID containers.
2. **Configuration Hand-off:** Obtain the `AUTH_ISSUER` (`https://auth.company.internal`), `AUTH_JWKS_URL` (`https://auth.company.internal/.well-known/jwks.json`), and assigned `AUTH_AUDIENCE` ID from the platform team.
3. **Local Validation:** Use standard JWT libraries in your language (see [Backend Implementation Examples](#6-backend-implementation-examples)) to validate incoming tokens locally without making round-trips to DeskID.

---

## 3. Step 1: Register Your Service & Custom Role Taxonomy

Before your service can accept DeskID tokens, it must be registered in DeskID's **Service Registry**.

### Option A: Using the Hosted Admin Console
1. Navigate to `http://127.0.0.1:8090/admin/console` and sign in with a platform-admin account.
2. Click the **Services** tab in the sidebar navigation.
3. Click **+ Register service**.
4. Fill in:
   - **Audience ID:** A slug identifying your service (e.g. `analytics-engine`, `storage-api`).
   - **Service Name:** Human-readable name (e.g. `Analytics Engine`).
   - **Allowed Roles:** Comma-separated list of valid roles (e.g. `admin, analyst, viewer`).
   - **Default Role:** The role automatically assigned when granting access without an explicit role (must be one of the allowed roles).
5. Click **Create service**.

### Option B: Using the Admin REST API
Send an authenticated request (`Bearer <platform_admin_jwt>`):

```bash
curl -X POST http://127.0.0.1:8090/v1/admin/services \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "analytics-engine",
    "name": "Analytics Engine",
    "description": "Distributed query and reporting engine",
    "allowed_roles": ["admin", "analyst", "viewer"],
    "default_role": "viewer"
  }'
```

**Response (`201 Created`):**
```json
{
  "id": "analytics-engine",
  "name": "Analytics Engine",
  "description": "Distributed query and reporting engine",
  "allowed_roles": ["admin", "analyst", "viewer"],
  "default_role": "viewer",
  "created_at": "2026-09-23T12:00:00Z",
  "updated_at": "2026-09-23T12:00:00Z",
  "integration_files": {
    "env_path": "integrations/analytics-engine.env",
    "json_path": "integrations/analytics-engine.json"
  }
}
```

> **Automated Client File Generation:**  
> Whenever a service is registered or updated, DeskID automatically writes client integration files into `integrations/<service_id>.env` and `integrations/<service_id>.json`.  
> Downstream teams can also fetch their configuration via API:
> - `GET /v1/admin/services/{service_id}/env` (raw `.env` file download)
> - `GET /v1/admin/services/{service_id}/config` (JSON configuration payload)
> Or click **Client Config** in the Admin Portal to view, copy, or download the configuration.

### Option C: Using the TypeScript SDK
```typescript
import { DeskID } from './client'

const auth = new DeskID({ baseUrl: 'http://127.0.0.1:8090' })

const result = await auth.registerService(adminToken, {
  id: 'analytics-engine',
  name: 'Analytics Engine',
  description: 'Distributed query and reporting engine',
  allowed_roles: ['admin', 'analyst', 'viewer'],
  default_role: 'viewer'
})
```

---

## 4. Step 2: Configure Grants & Global Access

Users can only access your service if they hold a **Product Grant** for your service ID.

### 1. Default Grants for All New Users
To automatically grant all newly registered users access to your service, add your audience to the DeskID environment configuration:

```env
# .env in DeskID deployment
AUTH_DEFAULT_AUDIENCES="deskid,analytics-engine"
AUTH_DEFAULT_ROLE="viewer"
```

### 2. Explicit User Grants (Platform-Wide or Organization-Scoped)
To grant an individual user access or assign elevated roles:

```bash
# Platform-Wide Grant (effective across all organizations):
curl -X POST http://127.0.0.1:8090/v1/admin/grants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_948a28f1",
    "audience": "analytics-engine",
    "role": "analyst",
    "org_id": null
  }'

# Organization-Scoped Grant (effective only within org_tenant_1):
curl -X POST http://127.0.0.1:8090/v1/admin/grants \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "usr_948a28f1",
    "audience": "analytics-engine",
    "role": "admin",
    "org_id": "org_tenant_1"
  }'
```

*Note: If `role` is omitted in the grant request, DeskID will automatically resolve it to your service's configured `default_role`.*

---

## 5. Step 3: Implement Stateless Backend Token Verification

Your backend service must validate incoming JWTs locally without making round-trip network calls to DeskID.

### Verification Checklist:
1. **Fetch & Cache Public Keys:** Retrieve the JWKS from `http://<deskid-host>:8090/.well-known/jwks.json`.
   - Cache keys in-memory.
   - If an incoming token specifies a `kid` not present in your cache, refresh the cache once before rejecting.
2. **Cryptographic Signature:** Validate the RS256 signature using the public key matching `header.kid`.
3. **Issuer (`iss`):** Validate that `iss` strictly matches DeskID's configured `AUTH_ISSUER` (e.g. `https://auth.company.internal`).
4. **Audience (`aud`):** Validate that your service ID (e.g. `"analytics-engine"`) is in the `aud` array.
5. **Expiration (`exp`):** Validate `exp > current_timestamp`.
6. **Role Extraction:** Extract the user's role for your service from `claims["roles"]["<your_service_id>"]`.
7. **Tenant Scoping:** Use `claims["org_id"]` and `claims["workspace_id"]` to isolate multi-tenant database queries.

### Example Token Payload:
```json
{
  "sub": "usr_948a28f1",
  "email": "analyst@example.com",
  "org_id": "org_tenant_1",
  "workspace_id": "ws_analytics",
  "aud": ["deskid", "analytics-engine"],
  "roles": {
    "analytics-engine": "analyst"
  },
  "token_version": 1,
  "iss": "https://auth.company.internal",
  "iat": 1725634800,
  "exp": 1725638400
}
```

---

## 6. Backend Implementation Examples

### Python (FastAPI + PyJWT)

```python
import jwt
from jwt import PyJWKClient
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

AUTH_ISSUER = "https://auth.company.internal"
JWKS_URL = "http://deskid:8090/.well-known/jwks.json"
SERVICE_AUDIENCE = "analytics-engine"

jwks_client = PyJWKClient(JWKS_URL)
security = HTTPBearer()
app = FastAPI()

def get_current_user_claims(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=AUTH_ISSUER,
            audience=SERVICE_AUDIENCE,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

    # Verify role assignment
    user_roles = claims.get("roles", {})
    if SERVICE_AUDIENCE not in user_roles:
        raise HTTPException(status_code=403, detail="No granted role for this service")

    return claims

@app.get("/api/v1/reports")
def list_reports(claims: dict = Depends(get_current_user_claims)):
    role = claims["roles"][SERVICE_AUDIENCE]
    org_id = claims.get("org_id")
    user_id = claims["sub"]
    return {
        "user_id": user_id,
        "org_id": org_id,
        "role": role,
        "reports": ["sales_q3", "marketing_attribution"]
    }
```

### Node.js / TypeScript (Express + `jwks-rsa`)

```typescript
import express, { Request, Response, NextFunction } from 'express'
import jwt from 'jsonwebtoken'
import jwksClient from 'jwks-rsa'

const SERVICE_AUDIENCE = 'analytics-engine'
const AUTH_ISSUER = 'https://auth.company.internal'

const client = jwksClient({
  jwksUri: 'http://deskid:8090/.well-known/jwks.json',
  cache: true,
  rateLimit: true,
  jwksRequestsPerMinute: 10
})

function getKey(header: jwt.JwtHeader, callback: jwt.SigningKeyCallback) {
  client.getSigningKey(header.kid, (err, key) => {
    callback(err, key?.getPublicKey())
  })
}

export function requireAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or malformed Authorization header' })
  }

  const token = authHeader.split(' ')[1]
  jwt.verify(
    token,
    getKey,
    { audience: SERVICE_AUDIENCE, issuer: AUTH_ISSUER, algorithms: ['RS256'] },
    (err, decoded: any) => {
      if (err) return res.status(401).json({ error: 'Token validation failed', details: err.message })

      const role = decoded.roles?.[SERVICE_AUDIENCE]
      if (!role) return res.status(403).json({ error: 'No permissions for this service' })

      req.user = decoded
      req.userRole = role
      req.orgId = decoded.org_id
      next()
    }
  )
}
```

### Go (Golang + `lestrrat-go/jwx/v2`)

```go
package main

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/lestrrat-go/jwx/v2/jwk"
	"github.com/lestrrat-go/jwx/v2/jwt"
)

const (
	jwksURL         = "https://auth.company.internal/.well-known/jwks.json"
	expectedIssuer  = "https://auth.company.internal"
	serviceAudience = "analytics-engine"
)

func AuthMiddleware(cache *jwk.Cache) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if !strings.HasPrefix(authHeader, "Bearer ") {
				http.Error(w, `{"error":"missing authorization header"}`, http.StatusUnauthorized)
				return
			}
			tokenStr := strings.TrimPrefix(authHeader, "Bearer ")

			// Fetch public keys from local cache
			set, err := cache.Get(r.Context(), jwksURL)
			if err != nil {
				http.Error(w, `{"error":"failed to fetch jwks"}`, http.StatusInternalServerError)
				return
			}

			// Validate signature, issuer, audience, and exp statelessly
			token, err := jwt.Parse([]byte(tokenStr),
				jwt.WithKeySet(set),
				jwt.WithValidate(true),
				jwt.WithIssuer(expectedIssuer),
				jwt.WithAudience(serviceAudience),
			)
			if err != nil {
				http.Error(w, fmt.Sprintf(`{"error":"invalid token: %s"}`, err.Error()), http.StatusUnauthorized)
				return
			}

			// Extract service roles
			rolesClaim, _ := token.Get("roles")
			rolesMap, ok := rolesClaim.(map[string]interface{})
			if !ok || rolesMap[serviceAudience] == nil {
				http.Error(w, `{"error":"insufficient service permissions"}`, http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}
```

---

## 7. Step 4: Real-Time Synchronization via Reconciliation Feed

If your service caches local permissions, usernames, or tenant memberships, you must synchronize state changes using DeskID's **chronological reconciliation feed**.

### Polling Endpoint:
```bash
GET /v1/admin/reconciliation/events?since_id=<last_processed_event_id>&limit=100
```
*(Requires Platform Admin token or dedicated service API key).*

### Example Feed Response:
```json
{
  "events": [
    {
      "id": "evt_0191c49b-7341-7a2e-839f-7f722a48bc92",
      "occurred_at": "2026-09-23T14:32:00Z",
      "action": "admin.set_grant",
      "resource_type": "product_grant",
      "resource_id": "usr_948a28f1",
      "previous_hash": "a4f89d...01",
      "integrity_hash": "e3b0c4...85",
      "details": {
        "audience": "analytics-engine",
        "role": "admin",
        "org_id": "org_tenant_1"
      }
    },
    {
      "id": "evt_0191c49c-8510-7b3f-912b-3129ba04a112",
      "occurred_at": "2026-09-23T14:35:10Z",
      "action": "user.delete",
      "resource_type": "user",
      "resource_id": "usr_b287ac99",
      "previous_hash": "e3b0c4...85",
      "integrity_hash": "c88f19...2a",
      "details": {
        "email": "deleted_user@example.com"
      }
    }
  ],
  "next_cursor": "evt_0191c49c-8510-7b3f-912b-3129ba04a112",
  "has_more": false
}
```

### Downstream Synchronization Loop:
1. Store the last processed `next_cursor` in your local database.
2. Poll `GET /v1/admin/reconciliation/events?since_id=<last_cursor>` periodically (e.g. every 10–30 seconds) or when webhook notifications fire.
3. Handle event types:
   - `admin.set_grant`: Update user's role in your local database for `details.audience`.
   - `admin.suspend_user` / `admin.activate_user`: Toggle user's active status.
   - `user.delete`: Purge or anonymize user-owned resources (GDPR compliance).
   - `org.delete` / `org.remove_member`: Invalidate cached tenant sessions.

```mermaid
sequenceDiagram
    autonumber
    participant Worker as Downstream Sync Worker
    participant LocalDB as Local Service DB
    participant DeskID as DeskID Reconciliation API

    Note over Worker,LocalDB: 1. Read last processed checkpoint
    Worker->>LocalDB: SELECT last_cursor FROM sync_checkpoints
    LocalDB-->>Worker: last_cursor = "evt_0191c49b..."

    Note over Worker,DeskID: 2. Fetch new chronological events
    Worker->>DeskID: GET /v1/admin/reconciliation/events?since_id=evt_0191c49b...
    DeskID-->>Worker: 200 OK: { events: [...], next_cursor: "evt_0191c49c...", has_more: false }

    Note over Worker,LocalDB: 3. Apply state changes locally
    loop For each event in events array
        alt action == "admin.set_grant"
            Worker->>LocalDB: UPDATE user_roles SET role = details.role
        else action == "admin.suspend_user"
            Worker->>LocalDB: UPDATE users SET is_active = false
        else action == "user.delete"
            Worker->>LocalDB: DELETE FROM users / anonymize PII
        end
    end

    Note over Worker,LocalDB: 4. Advance cursor checkpoint
    Worker->>LocalDB: UPDATE sync_checkpoints SET last_cursor = next_cursor
```

---

## 8. Zero-Downtime Key Rotation Runbook

DeskID supports continuous cryptographic key rotation without service downtime:
1. DeskID advertises both current and historical keys on `/.well-known/jwks.json`.
2. When rotating signing keys:
   - Your service's JWKS client will receive the new `kid` in token headers.
   - Your client must automatically fetch the updated JWKS and verify the token.
   - Tokens signed by the previous key remain valid until their expiration (`exp`).
3. Ensure your local JWKS cache has a minimum TTL of **5 minutes** or implements cache invalidation on unknown `kid`.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Platform Admin
    participant DeskID as DeskID IAM (:8090)
    participant Client as User / Client
    participant Service as Downstream Service (JWKS Cache)

    Note over Admin,DeskID: 1. Deploy New Key Pair (Key Rotation)
    Admin->>DeskID: Rotate signing key to "kid-2" (retain "kid-1" in JWKS)
    DeskID-->>DeskID: Signs new tokens with "kid-2"<br/>Serves both "kid-1" & "kid-2" at /.well-known/jwks.json

    Note over Client,DeskID: 2. Client Authenticates
    Client->>DeskID: POST /v1/auth/login
    DeskID-->>Client: Returns JWT (header: kid="kid-2")

    Note over Client,Service: 3. Downstream API Request
    Client->>Service: GET /api/data (Authorization: Bearer <JWT kid-2>)

    alt kid-2 is not in local JWKS cache
        Service->>DeskID: Refresh GET /.well-known/jwks.json
        DeskID-->>Service: 200 OK: [{kid: "kid-1"}, {kid: "kid-2"}]
        Service->>Service: Update in-memory JWKS cache
    end

    Service->>Service: Validate RS256 signature using cached "kid-2" public key
    Service-->>Client: 200 OK (Zero-Downtime Response)
```

---

## 9. Frontend & Full-Stack Application Integration

For web frontend applications and full-stack frameworks (Next.js, React, Vue 3), DeskID provides drop-in SDKs in the [`packages/`](../packages/README.md) monorepo to authenticate users and obtain tokens:

### A. Next.js App Router (`@deskid/nextjs`)
Protect routes via Edge middleware and access session data in Server Components:

```typescript
// middleware.ts
import { deskIdAuthMiddleware } from '@deskid/nextjs/middleware'

export default deskIdAuthMiddleware({
  publicRoutes: ['/', '/about', '/pricing', '/login'],
  loginUrl: '/login'
})
```

```tsx
// app/dashboard/page.tsx
import { getDeskIdSession } from '@deskid/nextjs/server'

export default async function Dashboard() {
  const session = await getDeskIdSession()
  return <div>Welcome, {session?.user.display_name}!</div>
}
```

### B. React & Vue 3 Drop-in UI
Drop in pre-built UI components with zero styling overhead:
- `<DeskIdProvider>`: Root context provider with auto-refresh timers.
- `<SignInButton mode="modal">`: Triggers accessible sign-in modal with password and OTP magic link tabs.
- `<UserButton showTenantSwitch={true}>`: Avatar dropdown with tenant switching and sign out.

See the complete guide in **[packages/README.md](../packages/README.md)**.

---

## 10. Pre-Flight Integration Checklist

Before promoting your integration to production, verify the following:

- [ ] Service audience ID registered in DeskID via `POST /v1/admin/services` or Admin Console.
- [ ] Allowed roles taxonomy and default role defined.
- [ ] Backend JWKS client configured with automatic `kid` refresh.
- [ ] Backend checks `iss`, `aud`, `exp`, and `claims["roles"][service_id]`.
- [ ] Data queries partition by `claims["org_id"]` for multi-tenant isolation.
- [ ] Tokens with missing or unexpected audience are rejected with `401/403`.
- [ ] Frontend uses `@deskid/nextjs`, `@deskid/react`, or `@deskid/vue` for token lifecycle and session persistence.
- [ ] Synchronization worker configured to consume `/v1/admin/reconciliation/events` (if maintaining local state).

