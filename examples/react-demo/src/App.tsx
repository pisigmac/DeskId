import { useState } from 'react'
import { useDeskId, SignInButton, UserButton } from '@deskid/react'

export default function App() {
  const {
    isAuthenticated,
    isLoading,
    user,
    session,
    activeOrg,
    openSignInModal,
    logout
  } = useDeskId()

  const [apiResult, setApiResult] = useState<{ status: number | null; data: any; error: string | null } | null>(null)
  const [isCallingApi, setIsCallingApi] = useState(false)

  const handleCallProtectedApi = async () => {
    if (!session?.accessToken) {
      setApiResult({ status: 401, data: null, error: 'No access token available. Please sign in first!' })
      return
    }

    setIsCallingApi(true)
    setApiResult(null)

    try {
      const res = await fetch('http://127.0.0.1:8090/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${session.accessToken}`
        }
      })
      const data = await res.json()
      setApiResult({
        status: res.status,
        data,
        error: res.ok ? null : (data.error || 'Request failed')
      })
    } catch (err: any) {
      setApiResult({
        status: 0,
        data: null,
        error: `Network error (is DeskID running on :8090?): ${err.message}`
      })
    } finally {
      setIsCallingApi(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navbar */}
      <header
        style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          padding: '0.875rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              backgroundColor: '#4f46e5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '1.125rem'
            }}
          >
            D
          </div>
          <div>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 700, margin: 0, color: '#0f172a' }}>
              Acme SaaS Portal
            </h1>
            <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Powered by @deskid/react Drop-in Components
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.25rem 0.625rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 600,
              backgroundColor: isAuthenticated ? '#ecfdf5' : '#f1f5f9',
              color: isAuthenticated ? '#059669' : '#64748b',
              border: `1px solid ${isAuthenticated ? '#a7f3d0' : '#e2e8f0'}`
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isAuthenticated ? '#10b981' : '#94a3b8'
              }}
            />
            {isLoading ? 'Loading...' : isAuthenticated ? 'Authenticated' : 'Guest'}
          </div>

          {isAuthenticated ? (
            <UserButton />
          ) : (
            <SignInButton mode="modal">Sign In with DeskID</SignInButton>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ maxWidth: '1100px', margin: '0 auto', padding: '2rem 1.5rem', width: '100%', boxSizing: 'border-box' }}>
        {/* Banner */}
        <section
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            padding: '1.5rem 2rem',
            border: '1px solid #e2e8f0',
            marginBottom: '2rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.05)'
          }}
        >
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: '#0f172a' }}>
            5-Minute Drop-in Authentication Demo
          </h2>
          <p style={{ margin: 0, color: '#475569', fontSize: '0.9375rem', lineHeight: 1.5 }}>
            This application demonstrates how consumer React and Next.js applications embed DeskID with
            zero custom authentication state logic. Components adapt automatically based on the user's
            session, providing instant sign-in modals, passwordless OTP tabs, and multi-tenant organization switching.
          </p>
        </section>

        {/* Grid of feature showcase cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {/* Card 1: Reactive State */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '1.5rem',
              border: '1px solid #e2e8f0',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
            }}
          >
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#1e293b' }}>
              1. Reactive State (`useDeskId()`)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem', fontSize: '0.875rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.375rem' }}>
                <span style={{ color: '#64748b' }}>isAuthenticated:</span>
                <span style={{ fontWeight: 600, color: isAuthenticated ? '#16a34a' : '#dc2626' }}>
                  {String(isAuthenticated)}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.375rem' }}>
                <span style={{ color: '#64748b' }}>User Email:</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{user?.email || '(none)'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.375rem' }}>
                <span style={{ color: '#64748b' }}>Display Name:</span>
                <span style={{ fontWeight: 600, color: '#0f172a' }}>{user?.display_name || '(none)'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.375rem' }}>
                <span style={{ color: '#64748b' }}>Active Tenant:</span>
                <span style={{ fontWeight: 600, color: '#4f46e5' }}>
                  {activeOrg ? `${activeOrg.name} (${activeOrg.role})` : '(none)'}
                </span>
              </div>
            </div>

            <div style={{ marginTop: '1.25rem', display: 'flex', gap: '0.75rem' }}>
              {!isAuthenticated ? (
                <button
                  type="button"
                  onClick={openSignInModal}
                  style={{
                    backgroundColor: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '0.5rem 1rem',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  openSignInModal()
                </button>
              ) : (
                <button
                  type="button"
                  onClick={logout}
                  style={{
                    backgroundColor: '#ef4444',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '0.5rem 1rem',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  logout()
                </button>
              )}
            </div>
          </div>

          {/* Card 2: Drop-in Components */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '1.5rem',
              border: '1px solid #e2e8f0',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
            }}
          >
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#1e293b' }}>
              2. Drop-in Component Variants
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: '0 0 1rem 0' }}>
              Test different modes and styling overrides supported out of the box:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '0.25rem' }}>
                  Default Modal Trigger:
                </span>
                <SignInButton mode="modal">Sign In (Modal Mode)</SignInButton>
              </div>

              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', display: 'block', marginBottom: '0.25rem' }}>
                  Custom Theme Override:
                </span>
                <SignInButton
                  mode="modal"
                  style={{
                    backgroundColor: '#059669',
                    borderRadius: '9999px',
                    padding: '0.5rem 1.25rem'
                  }}
                >
                  🌿 Custom Green Button
                </SignInButton>
              </div>
            </div>
          </div>

          {/* Card 3: Protected API Simulator */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '1.5rem',
              border: '1px solid #e2e8f0',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
            }}
          >
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '0 0 1rem 0', color: '#1e293b' }}>
              3. Downstream API Simulator
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: '0 0 1rem 0' }}>
              Calls the DeskID backend with <code>Authorization: Bearer &lt;token&gt;</code>:
            </p>

            <button
              type="button"
              onClick={handleCallProtectedApi}
              disabled={isCallingApi}
              style={{
                backgroundColor: isAuthenticated ? '#0284c7' : '#94a3b8',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '0.5rem 1rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: isAuthenticated ? 'pointer' : 'not-allowed',
                width: '100%',
                marginBottom: '0.75rem'
              }}
            >
              {isCallingApi ? 'Calling GET /v1/auth/me...' : 'Call GET /v1/auth/me'}
            </button>

            {apiResult && (
              <div
                style={{
                  padding: '0.75rem',
                  borderRadius: '6px',
                  backgroundColor: apiResult.status === 200 ? '#f0fdf4' : '#fef2f2',
                  border: `1px solid ${apiResult.status === 200 ? '#bbf7d0' : '#fecaca'}`,
                  fontSize: '0.75rem',
                  color: apiResult.status === 200 ? '#15803d' : '#b91c1c',
                  maxHeight: '160px',
                  overflowY: 'auto'
                }}
              >
                <div>
                  <strong>Status:</strong> {apiResult.status}
                </div>
                {apiResult.error && <div><strong>Error:</strong> {apiResult.error}</div>}
                {apiResult.data && (
                  <pre style={{ margin: '0.5rem 0 0 0', whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(apiResult.data, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </div>

          {/* Card 4: JWT Claims Inspector */}
          <div
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '12px',
              padding: '1.5rem',
              border: '1px solid #e2e8f0',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
              gridColumn: '1 / -1'
            }}
          >
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, margin: '0 0 0.5rem 0', color: '#1e293b' }}>
              4. JWT Claims & Session Inspector
            </h3>
            <p style={{ fontSize: '0.8125rem', color: '#64748b', margin: '0 0 1rem 0' }}>
              Isomorphically parsed by <code>@deskid/core</code> without external cryptography dependencies:
            </p>

            {session?.claims ? (
              <pre
                style={{
                  backgroundColor: '#0f172a',
                  color: '#38bdf8',
                  padding: '1rem',
                  borderRadius: '8px',
                  fontSize: '0.8125rem',
                  overflowX: 'auto',
                  margin: 0
                }}
              >
                {JSON.stringify(session.claims, null, 2)}
              </pre>
            ) : (
              <div
                style={{
                  padding: '1.5rem',
                  textAlign: 'center',
                  backgroundColor: '#f8fafc',
                  border: '1px dashed #cbd5e1',
                  borderRadius: '8px',
                  color: '#64748b',
                  fontSize: '0.875rem'
                }}
              >
                No active session. Click <strong>Sign In</strong> above to authenticate and inspect claims.
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer
        style={{
          marginTop: 'auto',
          borderTop: '1px solid #e2e8f0',
          backgroundColor: '#ffffff',
          padding: '1.25rem 2rem',
          textAlign: 'center',
          fontSize: '0.8125rem',
          color: '#64748b'
        }}
      >
        DeskID Authentication Monorepo — Ready for Production.
      </footer>
    </div>
  )
}
