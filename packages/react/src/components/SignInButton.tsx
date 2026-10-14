/**
 * @deskid/react - SignInButton Component
 */

import React from 'react'
import { useDeskId } from '../context'

export interface SignInButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  mode?: 'modal' | 'redirect'
  redirectUrl?: string
}

export const SignInButton: React.FC<SignInButtonProps> = ({
  mode = 'modal',
  redirectUrl = '',
  children = 'Sign In',
  className = '',
  style,
  onClick,
  ...rest
}) => {
  const { openSignInModal } = useDeskId()

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (onClick) onClick(e)
    if (e.defaultPrevented) return

    if (mode === 'modal') {
      openSignInModal()
    } else {
      window.location.href = redirectUrl || '/login'
    }
  }

  const defaultStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    padding: '0.5rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 600,
    borderRadius: '0.5rem',
    backgroundColor: '#4f46e5',
    color: '#ffffff',
    border: '1px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.15s ease-in-out',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    fontFamily: 'inherit',
    ...style
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`deskid-signin-btn ${className}`}
      style={defaultStyle}
      {...rest}
    >
      {children}
    </button>
  )
}
