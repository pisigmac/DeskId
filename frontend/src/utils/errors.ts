/**
 * Plain-Language Error Explanations
 *
 * Converts technical microservice error payloads, HTTP codes, and raw exceptions
 * into human-centered, clear, empathetic plain-language copy with actionable advice.
 * Meets WCAG 3.3 (Input Assistance) standards.
 */

export interface ErrorFormattingOptions {
  context?: 'login' | 'register' | 'forgot-password' | 'reset-password' | 'magic-link' | 'otp' | 'profile' | 'general'
}

export function getHumanErrorMessage(err: unknown, options: ErrorFormattingOptions = {}): string {
  if (!err) {
    return 'An unexpected issue occurred. Please try again.'
  }

  // Extract raw string representation from various error shapes
  let raw = ''
  let status: number | null = null
  let code = ''

  if (typeof err === 'string') {
    raw = err
  } else if (typeof err === 'object') {
    const errorObj = err as Record<string, any>
    raw = errorObj.error || errorObj.detail || errorObj.message || ''
    code = errorObj.code || ''
    status = errorObj.status || (code.startsWith('HTTP_') ? parseInt(code.replace('HTTP_', ''), 10) : null)

    // Handle FastAPI / Pydantic validation error lists
    if (Array.isArray(errorObj.detail)) {
      const first = errorObj.detail[0]
      if (first && first.msg) {
        raw = first.msg
      }
    }
  }

  const rawLower = raw.toLowerCase()
  const context = options.context || 'general'

  // 1. Rate Limit Exceeded (HTTP 429)
  if (
    status === 429 ||
    code === 'HTTP_429' ||
    rawLower.includes('rate limit') ||
    rawLower.includes('too many requests')
  ) {
    if (context === 'login') {
      return 'Too many login attempts. For security, please wait 3 minutes before trying again or reset your password.'
    }
    if (context === 'register') {
      return 'Too many registration attempts. Please wait a few minutes before trying again.'
    }
    if (context === 'magic-link' || context === 'otp') {
      return 'Too many sign-in attempts. For security, please wait a few minutes before requesting a new sign-in code.'
    }
    return 'Too many requests. For system protection, please wait a couple of minutes before trying again.'
  }

  // 2. Account Lockout
  if (rawLower.includes('lockout') || rawLower.includes('locked')) {
    return 'This account is temporarily locked due to multiple failed login attempts. Please check your email or wait 15 minutes before trying again.'
  }

  // 3. Credentials & Authentication Failures (HTTP 401)
  if (
    status === 401 ||
    code === 'HTTP_401' ||
    rawLower.includes('invalid credentials') ||
    rawLower.includes('incorrect password') ||
    rawLower.includes('bad credentials')
  ) {
    return 'Incorrect email or password. Please verify your credentials or use "Forgot password" to reset access.'
  }

  // 4. Email Verification Status
  if (rawLower.includes('not verified') || rawLower.includes('verify your email')) {
    return 'Your email address is not verified yet. Please check your inbox and click the verification link sent to your email.'
  }

  // 5. Verification & Reset Tokens
  if (rawLower.includes('verification token')) {
    return 'This verification link is invalid or has expired. Please sign in to request a fresh verification link.'
  }
  if (rawLower.includes('reset token')) {
    return 'This password reset link is invalid or has expired. Please request a new recovery link using the Forgot Password page.'
  }
  if (rawLower.includes('refresh token') || rawLower.includes('session expired') || rawLower.includes('token expired')) {
    return 'Your session has expired for security. Please sign in again to continue.'
  }

  // 6. Magic Link & OTP Codes
  if (rawLower.includes('otp exhausted') || rawLower.includes('too many incorrect attempts')) {
    return 'Too many incorrect code attempts. For your security, this sign-in session has expired. Please request a new link.'
  }
  if (rawLower.includes('magic link') && (rawLower.includes('invalid') || rawLower.includes('expired'))) {
    return 'This sign-in link is invalid or has already been used. Please request a new one.'
  }
  if (rawLower.includes('otp') || rawLower.includes('code is invalid') || rawLower.includes('incorrect code')) {
    return 'The 6-digit code entered is incorrect or has expired. Please check your email and try again.'
  }

  // 7. Duplicate / Existing Accounts (HTTP 409)
  if (
    status === 409 ||
    code === 'HTTP_409' ||
    rawLower.includes('already exists') ||
    rawLower.includes('already registered')
  ) {
    return 'An account with this email address already exists. Please sign in instead.'
  }

  // 8. Open Registration Disabled
  if (rawLower.includes('registration is closed') || rawLower.includes('open registration')) {
    return 'Public registration is currently disabled on this platform. Please contact your organization administrator for an invitation.'
  }

  // 9. Bootstrap Setup Token
  if (rawLower.includes('bootstrap token')) {
    return 'The bootstrap administrator setup token is invalid. Please verify your configuration secret.'
  }

  // 10. Account Suspension
  if (rawLower.includes('suspended') || rawLower.includes('inactive account')) {
    return 'This account is currently suspended. Please contact your platform administrator for support.'
  }

  // 11. Password Mismatch & Form Constraints
  if (rawLower.includes('passwords do not match')) {
    return 'The passwords you entered do not match. Please re-enter them carefully.'
  }
  if (rawLower.includes('at least 8 characters') || rawLower.includes('password must be')) {
    return 'Password must be at least 8 characters long and satisfy security requirements.'
  }
  if (rawLower.includes('valid email')) {
    return 'Please enter a valid email address (e.g. name@company.com).'
  }

  // 12. Network / Connectivity Failures
  if (
    rawLower.includes('failed to fetch') ||
    rawLower.includes('networkerror') ||
    rawLower.includes('network request failed')
  ) {
    return 'Unable to reach the DeskID authentication server. Please check your network connection and try again.'
  }

  // Fallback: If raw message is clean and readable, return it; otherwise return friendly default
  if (raw && raw.length < 120 && !raw.includes('{') && !raw.includes('Traceback')) {
    return raw
  }

  return 'An unexpected issue occurred while processing your request. Please try again or contact support.'
}
