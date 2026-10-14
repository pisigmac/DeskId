/**
 * @deskid/react - UserButton Component
 */

import React, { useState, useEffect, useRef } from 'react'
import { useDeskId } from '../context'

export interface UserButtonProps {
  className?: string
  style?: React.CSSProperties
}

export const UserButton: React.FC<UserButtonProps> = ({ className = '', style }) => {
  const { user, activeOrg, isAuthenticated, switchOrg, logout } = useDeskId()
  const [isOpen, setIsOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  if (!isAuthenticated || !user) return null

  const initial = (user.display_name || user.email || 'U').charAt(0).toUpperCase()

  return (
    <div
      ref={menuRef}
      className={`deskid-user-menu ${className}`}
      style={{ position: 'relative', display: 'inline-block', fontFamily: 'system-ui, -apple-system, sans-serif', ...style }}
    >
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        style={{
          width: '2rem',
          height: '2rem',
          borderRadius: '9999px',
          background: 'linear-gradient(135deg, #4f46e5, #6366f1)',
          color: '#ffffff',
          border: '2px solid #e0e7ff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          padding: 0
        }}
      >
        <span style={{ fontWeight: 700, fontSize: '0.75rem' }}>{initial}</span>
      </button>

      {isOpen && (
        <div
          role="menu"
          style={{
            position: 'absolute',
            right: 0,
            marginTop: '0.5rem',
            width: '14rem',
            backgroundColor: '#ffffff',
            borderRadius: '0.75rem',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
            zIndex: 1000,
            fontSize: '0.75rem'
          }}
        >
          <div style={{ padding: '0.75rem', borderBottom: '1px solid #f1f5f9' }}>
            <div style={{ fontWeight: 600, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user.display_name || 'DeskID User'}
            </div>
            <div style={{ color: '#64748b', marginTop: '0.125rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user.email}
            </div>
            {activeOrg && (
              <div style={{ display: 'inline-block', marginTop: '0.375rem', padding: '0.125rem 0.375rem', borderRadius: '0.25rem', backgroundColor: '#f1f5f9', color: '#475569', fontSize: '0.625rem', fontWeight: 600 }}>
                Tenant: {activeOrg.name}
              </div>
            )}
          </div>

          {user.orgs && user.orgs.length > 1 && (
            <div style={{ padding: '0.375rem', borderBottom: '1px solid #f1f5f9' }}>
              <div style={{ padding: '0.25rem 0.375rem', color: '#94a3b8', fontSize: '0.625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Switch Tenant
              </div>
              {user.orgs.map((org) => (
                <button
                  key={org.id}
                  type="button"
                  onClick={async () => {
                    await switchOrg(org.id)
                    setIsOpen(false)
                  }}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.375rem',
                    borderRadius: '0.375rem',
                    border: 'none',
                    background: 'transparent',
                    color: '#334155',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  <span>{org.name}</span>
                  {org.id === activeOrg?.id && <span style={{ color: '#4f46e5', fontWeight: 700 }}>✓</span>}
                </button>
              ))}
            </div>
          )}

          <div style={{ padding: '0.375rem' }}>
            <button
              type="button"
              onClick={async () => {
                await logout()
                setIsOpen(false)
              }}
              role="menuitem"
              style={{
                width: '100%',
                padding: '0.375rem',
                borderRadius: '0.375rem',
                border: 'none',
                background: 'transparent',
                color: '#e11d48',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
