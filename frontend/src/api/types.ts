export interface Grant {
  audience: string
  role: string
  org_id: string | null
}

export interface Org {
  id: string
  name: string
  role: string
  workspace_id?: string | null
}

export interface User {
  id: string
  email: string
  display_name: string | null
  is_platform_admin: boolean
  is_active: boolean
  orgs: Org[]
  grants: Grant[]
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface RegisterResponse {
  access_token?: string | null
  refresh_token?: string | null
  token_type?: string | null
  expires_in?: number | null
  verification_required: boolean
}

export interface Session {
  id: string
  created_at: string
  expires_at: string
  revoked: boolean
  ip_address?: string | null
  user_agent?: string | null
}

export interface ServiceDefinition {
  id: string
  name: string
  description?: string | null
  allowed_roles: string[]
  default_role?: string | null
  created_at: string
  updated_at: string
}

export interface ServiceCreatePayload {
  id: string
  name: string
  description?: string | null
  allowed_roles: string[]
  default_role?: string | null
}

export interface ServiceUpdatePayload {
  name?: string | null
  description?: string | null
  allowed_roles?: string[] | null
  default_role?: string | null
}

export interface AuditLogEvent {
  id: string
  occurred_at: string
  actor_type: string
  actor_id: string | null
  action: string
  resource_type: string
  resource_id: string | null
  ip_address?: string | null
  user_agent?: string | null
  previous_hash: string | null
  integrity_hash: string
  details?: Record<string, any> | null
}

export interface AuditQueryResponse {
  total: number
  offset: number
  limit: number
  events: AuditLogEvent[]
}

export interface ReconciliationResponse {
  events: AuditLogEvent[]
  next_cursor: string | null
  has_more: boolean
}

export interface UserListResponse {
  total: number
  offset: number
  limit: number
  users: User[]
}

export interface ServiceListResponse {
  total: number
  offset: number
  limit: number
  services: ServiceDefinition[]
}

export interface OrgMembersResponse {
  members: Array<{
    user_id: string
    role: string
    workspace_id?: string | null
  }>
}

export interface ApiError {
  error: string
  code: string
  request_id?: string
  detail?: any
}

export interface UserExportData {
  user: User
  identities: any[]
  memberships: any[]
  grants: any[]
  refresh_tokens: any[]
  audit_events: any[]
}

export interface SystemHealth {
  status: 'ok' | 'degraded'
  service: string
  version: string
  checks: {
    database: boolean
    keys: boolean
  }
}

export interface SystemMetrics {
  service: string
  counters: Record<string, number>
}
