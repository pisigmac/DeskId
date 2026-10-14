/**
 * @deskid/react - DeskIdModal Component
 */

import React, { useState, useEffect, useRef } from 'react'
import type { DeskIdClient } from '@deskid/core'

export interface DeskIdModalProps {
  isOpen: boolean
  onClose: () => void
  client: DeskIdClient
}

export const DeskIdModal: React.FC<DeskIdModalProps> = ({ isOpen, onClose, client }) => {
  const modalRef = useRef<HTMLDivElement>(null)
  const previousActiveElement = useRef<HTMLElement | null>(null)

  const [mode, setMode] = useState<'password' | 'otp'>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [otpCode, setOtpCode] = useState('')
  const [otpStep, setOtpStep] = useState<'request' | 'verify'>('request')
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [resendCooldown, setResendCooldown] = useState(0)

  // Focus trap & Escape key
  useEffect(() => {
    if (!isOpen) return

    previousActiveElement.current = document.activeElement as HTMLElement | null
    setErrorMessage('')

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
        return
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusable = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        if (focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]

        if (e.shiftKey && document.activeElement === first) {
          last.focus()
          e.preventDefault()
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus()
          e.preventDefault()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    // Initial focus
    setTimeout(() => {
      const input = modalRef.current?.querySelector('input')
      if (input) input.focus()
    }, 50)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      if (previousActiveElement.current && typeof previousActiveElement.current.focus === 'function') {
        previousActiveElement.current.focus()
      }
    }
  }, [isOpen, onClose])

  // Cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setInterval(() => {
      setResendCooldown(prev => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldown])

  if (!isOpen) return null

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) return
    setIsLoading(true)
    setErrorMessage('')

    try {
      await client.login({ email: email.trim(), password })
      onClose()
    } catch (err: any) {
      setErrorMessage(err?.error || err?.detail || 'Incorrect email or password. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return
    setIsLoading(true)
    setErrorMessage('')

    try {
      await client.requestMagicLink(email.trim())
      setOtpStep('verify')
      setResendCooldown(60)
    } catch (err: any) {
      setErrorMessage(err?.error || 'Failed to send sign-in link. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || otpCode.length !== 6) return
    setIsLoading(true)
    setErrorMessage('')

    try {
      await client.verifyOtp(email.trim(), otpCode.trim())
      onClose()
    } catch (err: any) {
      setErrorMessage(err?.error || 'Incorrect code. Please check your email or request a new code.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        backgroundColor: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="deskid-react-modal-title"
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: '26rem',
          backgroundColor: '#ffffff',
          borderRadius: '1rem',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          border: '1px solid #e2e8f0',
          padding: '1.5rem',
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div>
            <h2 id="deskid-react-modal-title" style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Sign In
            </h2>
            <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.25rem', marginBottom: 0 }}>
              Authenticate via DeskID secure identity
            </p>
          </div>
          <button
            type="button"
            aria-label="Close dialog"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '1.5rem',
              color: '#94a3b8',
              cursor: 'pointer',
              lineHeight: 1,
              padding: '0.25rem'
            }}
          >
            &times;
          </button>
        </div>

        {/* Mode Selector Tabs */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem', backgroundColor: '#f1f5f9', padding: '0.25rem', borderRadius: '0.5rem', marginBottom: '1rem' }}>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'password'}
            onClick={() => { setMode('password'); setErrorMessage('') }}
            style={{
              background: mode === 'password' ? '#ffffff' : 'transparent',
              border: 'none',
              padding: '0.375rem 0.5rem',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: mode === 'password' ? '#0f172a' : '#64748b',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              boxShadow: mode === 'password' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none'
            }}
          >
            Password
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'otp'}
            onClick={() => { setMode('otp'); setErrorMessage('') }}
            style={{
              background: mode === 'otp' ? '#ffffff' : 'transparent',
              border: 'none',
              padding: '0.375rem 0.5rem',
              fontSize: '0.75rem',
              fontWeight: 600,
              color: mode === 'otp' ? '#0f172a' : '#64748b',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              boxShadow: mode === 'otp' ? '0 1px 2px rgba(0,0,0,0.05)' : 'none'
            }}
          >
            Email Link / OTP
          </button>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div
            role="alert"
            aria-live="assertive"
            style={{
              padding: '0.625rem',
              borderRadius: '0.5rem',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              fontSize: '0.75rem',
              marginBottom: '1rem'
            }}
          >
            {errorMessage}
          </div>
        )}

        {/* Password Form */}
        {mode === 'password' ? (
          <form onSubmit={handlePasswordLogin} style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
              <label htmlFor="react-deskid-email" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
                Email Address
              </label>
              <input
                id="react-deskid-email"
                type="email"
                required
                autoComplete="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.875rem',
                  borderRadius: '0.5rem',
                  border: '1px solid #cbd5e1',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
              <label htmlFor="react-deskid-pwd" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
                Password
              </label>
              <input
                id="react-deskid-pwd"
                type="password"
                required
                autoComplete="current-password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem 0.75rem',
                  fontSize: '0.875rem',
                  borderRadius: '0.5rem',
                  border: '1px solid #cbd5e1',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !email || !password}
              style={{
                width: '100%',
                padding: '0.625rem 1rem',
                fontSize: '0.875rem',
                fontWeight: 600,
                borderRadius: '0.5rem',
                backgroundColor: '#4f46e5',
                color: '#ffffff',
                border: 'none',
                cursor: 'pointer',
                opacity: (isLoading || !email || !password) ? 0.5 : 1
              }}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        ) : (
          /* OTP Form */
          otpStep === 'request' ? (
            <form onSubmit={handleRequestOtp} style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                <label htmlFor="react-deskid-otp-email" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
                  Email Address
                </label>
                <input
                  id="react-deskid-otp-email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.875rem',
                    borderRadius: '0.5rem',
                    border: '1px solid #cbd5e1',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={isLoading || !email}
                style={{
                  width: '100%',
                  padding: '0.625rem 1rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  borderRadius: '0.5rem',
                  backgroundColor: '#4f46e5',
                  color: '#ffffff',
                  border: 'none',
                  cursor: 'pointer',
                  opacity: (isLoading || !email) ? 0.5 : 1
                }}
              >
                {isLoading ? 'Sending Link...' : 'Send Sign-in Link & Code'}
              </button>
            </form>
          ) : (
            <div>
              <div style={{ padding: '0.625rem', borderRadius: '0.5rem', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', color: '#15803d', fontSize: '0.75rem', marginBottom: '1rem' }}>
                Code sent to <strong>{email}</strong>. Check your inbox!
              </div>

              <form onSubmit={handleVerifyOtp} style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                  <label htmlFor="react-deskid-otp-code" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#334155' }}>
                    6-Digit Code
                  </label>
                  <input
                    id="react-deskid-otp-code"
                    type="text"
                    maxLength={6}
                    required
                    autoComplete="one-time-code"
                    placeholder="123456"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      fontFamily: 'monospace',
                      fontSize: '1.125rem',
                      letterSpacing: '0.25em',
                      textAlign: 'center',
                      borderRadius: '0.5rem',
                      border: '1px solid #cbd5e1',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || otpCode.length !== 6}
                  style={{
                    width: '100%',
                    padding: '0.625rem 1rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    borderRadius: '0.5rem',
                    backgroundColor: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    cursor: 'pointer',
                    opacity: (isLoading || otpCode.length !== 6) ? 0.5 : 1
                  }}
                >
                  {isLoading ? 'Verifying...' : 'Verify & Sign In'}
                </button>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.25rem' }}>
                  <button
                    type="button"
                    onClick={() => setOtpStep('request')}
                    style={{ background: 'transparent', border: 'none', fontSize: '0.75rem', color: '#4f46e5', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                  >
                    Change email
                  </button>

                  <button
                    type="button"
                    onClick={(e) => handleRequestOtp(e)}
                    disabled={resendCooldown > 0 || isLoading}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      fontSize: '0.75rem',
                      color: resendCooldown > 0 ? '#94a3b8' : '#4f46e5',
                      cursor: resendCooldown > 0 ? 'not-allowed' : 'pointer',
                      padding: 0
                    }}
                  >
                    {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                  </button>
                </div>
              </form>
            </div>
          )
        )}
      </div>
    </div>
  )
}
