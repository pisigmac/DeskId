/**
 * @deskid/react - Context & DeskIdProvider
 */

import React, { createContext, useContext, useState, useEffect, useMemo, useRef } from 'react'
import { DeskIdClient, type DeskIdUser, type DeskIdSession, type DeskIdOrg } from '@deskid/core'
import type { DeskIdReactContext } from './types'
import { DeskIdModal } from './components/DeskIdModal'

const DeskIdContext = createContext<DeskIdReactContext | null>(null)

export function useDeskId(): DeskIdReactContext {
  const context = useContext(DeskIdContext)
  if (!context) {
    throw new Error('useDeskId() must be used within a <DeskIdProvider> component')
  }
  return context
}

export interface DeskIdProviderProps {
  baseUrl: string
  storage?: 'localStorage' | 'sessionStorage' | 'cookie' | 'memory'
  autoRefresh?: boolean
  children: React.ReactNode
}

export const DeskIdProvider: React.FC<DeskIdProviderProps> = ({
  baseUrl,
  storage = 'localStorage',
  autoRefresh = true,
  children
}) => {
  const clientRef = useRef<DeskIdClient | null>(null)
  if (!clientRef.current) {
    clientRef.current = new DeskIdClient({
      baseUrl,
      storage,
      autoRefresh
    })
  }
  const client = clientRef.current

  const [user, setUser] = useState<DeskIdUser | null>(null)
  const [session, setSession] = useState<DeskIdSession | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false)

  useEffect(() => {
    setIsLoading(true)
    const unsubscribe = client.onAuthStateChange((_event, newSession) => {
      setSession(newSession)
      if (newSession) {
        setUser(client.getUser())
      } else {
        setUser(null)
      }
    })

    setSession(client.getSession())
    setUser(client.getUser())
    setIsLoading(false)

    return () => {
      unsubscribe()
    }
  }, [client])

  const isAuthenticated = useMemo(() => {
    return Boolean(session && user)
  }, [session, user])

  const activeOrg = useMemo<DeskIdOrg | null>(() => {
    if (!user || !user.orgs || user.orgs.length === 0) return null
    const orgClaim = session?.claims?.org_id
    if (orgClaim) {
      const match = user.orgs.find(o => o.id === orgClaim)
      if (match) return match
    }
    return user.orgs[0] || null
  }, [user, session])

  const contextValue: DeskIdReactContext = useMemo(() => ({
    user,
    session,
    isAuthenticated,
    isLoading,
    activeOrg,
    isModalOpen,
    openSignInModal: () => setIsModalOpen(true),
    closeSignInModal: () => setIsModalOpen(false),
    login: (options) => client.login(options),
    register: (options) => client.register(options),
    requestMagicLink: (email) => client.requestMagicLink(email),
    verifyOtp: (email, code) => client.verifyOtp(email, code),
    logout: () => client.logout(),
    switchOrg: (orgId) => client.switchOrg(orgId)
  }), [user, session, isAuthenticated, isLoading, activeOrg, isModalOpen, client])

  return (
    <DeskIdContext.Provider value={contextValue}>
      {children}
      <DeskIdModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        client={client}
      />
    </DeskIdContext.Provider>
  )
}
