# Auth — Features & Gaps (Resolved & Hardened)

> **Audit Date:** 2026-08-25 · **Status:** All core P0 and P1 gaps resolved; Full Auth UI & Devops utilities shipped.  
> **Scope:** OpenDesk Auth (`src/opendesk_auth`, `client.ts`, `static/`, `scripts/`, `tests/`, `migrations/`, deploy files).  
> **Test Suite:** 67/67 passing tests (`pytest tests/ -v`).

Read with [`AGENTS.md`](AGENTS.md) (invariants) and [`code_map.md`](code_map.md) (file map).

---

## 1. Product Position & Architecture

Auth is a **high-performance, product-agnostic identity microservice** for OpenDesk. It issues RS256 JWTs that consumer product backends validate locally and statelessly via JWKS (`/.well-known/jwks.json`). Product access is managed through granular product grants (`audience` + role), avoiding hardcoded product dependencies.

---

## 2. Capability Matrix & Implementation Status

| Capability | Status | Location | Notes |
|------------|--------|----------|-------|
| **Email/Password Register & Login** | ✅ Production | `routes/auth.py` | Closed registration + bootstrap token gate |
| **Public Auth UI (Hosted)** | ✅ Production | `static/auth.html` | Split-layout monochrome UI (`#login`, `#register`, `#reset`, `#verify`) |
| **Email Verification** | ✅ Production | `services.py`, `mail_client.py` | Tokens hashed at rest; login blocked until verified |
| **Email Re-Verification on Change** | ✅ Resolved | `services.update_user_profile` | Clears `email_verified_at` and sends re-verification token |
| **Password Reset (Enum-Safe)** | ✅ Resolved | `routes/auth.py` | Consumes token, resets password, revokes all active sessions |
| **Session Revocation on Reset/Change** | ✅ Resolved | `services.revoke_all_user_sessions`| Revokes all active refresh tokens on credential change |
| **Google & GitHub OAuth** | ✅ Production | `routes/oauth.py`, `oauth_providers.py`| URL fragment handoff; safe account linking |
| **RS256 JWT & JWKS** | ✅ Production | `crypto.py`, `routes/jwks.py` | Deterministic fail-closed keys; standard JWKS schema |
| **Refresh Rotation & Revocation** | ✅ Production | `services.rotate_refresh` | Single-use rotation; suspended users blocked |
| **Session Metadata & Revoke All** | ✅ Resolved | `models.RefreshToken`, `routes/auth.py`| IP and User-Agent captured; single/all session revocation |
| **Account Lockout** | ✅ Production | `services.authenticate_password` | 5 failed attempts locks account for 15 minutes |
| **Rate Limiting** | ✅ Production | `rate_limit.py` | Per-IP in-memory buckets with sliding windows |
| **Organizations & Multi-Tenancy** | ✅ Production | `routes/orgs.py` | Create/list orgs, list/add/remove members, delete org |
| **Product Grants** | ✅ Production | `routes/admin.py` | `admin\|operator\|viewer` mapped to JWT `roles.<product>` |
| **Admin Console UI** | ✅ Production | `static/admin.html` | Full dashboard for users, grants, and audit logs |
| **Admin User Search & Pagination** | ✅ Resolved | `routes/admin.py` | Supports search query `?q=` and pagination `?limit=&offset=` |
| **Admin Suspend / Activate** | ✅ Production | `routes/admin.py` | Instantly revokes all refresh tokens |
| **Immutable Audit Log** | ✅ Resolved | `models.AuditLogEvent` | Append-only integrity hash; IP & User-Agent recorded |
| **GDPR Export & Delete** | ✅ Production | `routes/me.py` | Complete data export and account purging |
| **Deep Healthcheck** | ✅ Resolved | `app.py` | Returns HTTP 503 when DB or JWT keys are unhealthy |
| **Metrics Endpoint** | ✅ Resolved | `metrics.py`, `app.py` | Live counters at `GET /metrics` |
| **TypeScript SDK** | ✅ Complete | `client.ts` | Complete coverage of all 20+ Auth and Admin endpoints |
| **DevOps & Lifecycle Tooling** | ✅ Complete | `scripts/`, `./start_all.sh` | Start, stop, restart, status, JWT tool, admin seed, migrations |

---

## 3. Defects Audit & Resolutions Log

All previously identified defects (A1–A21) have been addressed:

| ID | Issue | Resolution / Current State |
|----|-------|----------------------------|
| **A1** | Multi-worker rate limiter consistency | In-process rate limiter with memory window resets; documented single-replica topology for standalone deployments. |
| **A2** | `/health` returning 200 when degraded | **Fixed**: `/health` now returns HTTP 503 whenever DB check fails or JWT key material is missing. |
| **A3** | Email change omitting re-verification | **Fixed**: `PATCH /v1/auth/me` email updates clear `email_verified_at` and issue a new verification email. |
| **A4** | Password reset not revoking sessions | **Fixed**: `reset_user_password` and `change_password` revoke all active refresh tokens for the user. |
| **A5** | Single signing `kid` / key management | **Fixed**: Deterministic key loading via `AUTH_JWT_PRIVATE_KEY_FILE`, fail-closed crypto, and `./jwt_tool.sh` verification. |
| **A6** | OIDC Authorization Server scope | **Resolved**: Explicit architectural decision documented; Auth is a lightweight RS256 JWT issuer for microservices. |
| **A7** | OAuth provider configuration | **Fixed**: Provider authorize, token, and userinfo URLs configurable in settings. |
| **A8** | Audit log immutability & metadata | **Fixed**: IP and User-Agent captured, SHA-256 integrity hashes computed per event, ORM blocks mutations. |
| **A9** | GDPR user data deletion | **Fixed**: Cascade deletion of user tokens, identities, grants, and memberships. |
| **A10**| Rate limit memory growth | **Fixed**: Automatic window sliding and eviction. |
| **A11**| `docker-compose.yml` configuration | **Fixed**: Key mounts, issuer, ports, and environment variables fully wired. |
| **A12**| `.env.example` missing knobs | **Fixed**: Complete `.env.example` created with all configuration defaults. |
| **A13**| Incomplete SDK & README tables | **Fixed**: `client.ts` and documentation updated with profile, sessions, user search, orgs, and admin actions. |
| **A14**| Token introspection validation | **Fixed**: `/introspect` validates token signature, expiration, and returns active status. |
| **A15**| Token claims model | **Fixed**: Standardized claims (`sub`, `email`, `org_id`, `workspace_id`, `aud`, `roles`, `iss`, `iat`, `exp`). |
| **A16**| Org membership API coverage | **Fixed**: Added list members, remove member, and delete organization routes. |
| **A17**| Admin user list pagination & search | **Fixed**: Search by email/display name (`?q=`) and pagination (`?limit=&offset=`) implemented. |
| **A18**| Security headers & CORS | **Fixed**: CSP headers on static UI, configurable CORS origins list. |
| **A19**| Mail callback URLs | **Fixed**: Fully configurable via `AUTH_SPA_CALLBACK_URL`. |
| **A20**| `.gitignore` security assets | **Fixed**: `*.pem`, `*.key`, `*.log`, `*.db` properly ignored in `.gitignore`. |
| **A21**| Test coverage gaps | **Fixed**: Test suite expanded to 67 tests covering all hardening gates, UI endpoints, and admin workflows. |

---

## 4. UI & Tooling Ecosystem

1. **Public Auth UI (`static/auth.html`)**:
   - Split-screen layout (Monochrome Zinc/White).
   - Seamless hash router (`#login`, `#register`, `#forgot-password`, `#reset-password`, `#verify-email`).
   - Show/hide password toggles, OAuth buttons, server error toasts.

2. **Admin Console UI (`static/admin.html`)**:
   - Live metrics, user search and pagination.
   - User suspension and activation controls.
   - Granular product grant assignment (`admin`, `operator`, `viewer`).
   - Audit log explorer with filtering.

3. **Developer CLI Tooling**:
   - `./start_all.sh` / `./stop_all.sh` / `./restart_all.sh` / `./status.sh`
   - `./jwt_tool.sh` (Generate, decode, verify against local/remote JWKS, run live test suites).
   - `./scripts/seed_admin.sh` (Platform admin bootstrapping).
   - `./scripts/export_audit_logs.sh` (SOC2/Compliance audit exporter).
   - `./scripts/generate_keys.sh` (RSA 2048-bit keypair generator).
   - `./scripts/run_migrations.sh` (Database schema migration runner).
