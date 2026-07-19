import { useEffect, useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { apiRequest, clearAuth, getStoredUser, getToken, setAuth } from '../../api/client'
import type { AuthResponse } from '../../types/analysis'
import { candidateNav } from '../../config/navigation'
import { Sidebar } from '../ui/Sidebar'

export function CandidateLayout() {
  const navigate = useNavigate()
  const [user, setUser] = useState(getStoredUser())
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    async function validateSession() {
      const token = getToken()
      const stored = getStoredUser()

      if (!token || stored?.role !== 'CANDIDATE') {
        clearAuth()
        setChecking(false)
        navigate('/candidate/login', { replace: true })
        return
      }

      try {
        const me = await apiRequest<AuthResponse>('/api/auth/me')
        const nextUser = {
          user_id: me.user_id,
          email: me.email,
          full_name: me.full_name,
          role: me.role,
        }
        setAuth(me.token, nextUser)
        setUser(nextUser)
      } catch {
        clearAuth()
        navigate('/candidate/login', { replace: true })
        return
      } finally {
        setChecking(false)
      }
    }

    validateSession()
  }, [navigate])

  function handleLogout() {
    clearAuth()
    navigate('/candidate/login', { replace: true })
  }

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface text-sm text-slate-400">
        Checking session...
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar
        title="Candidate Portal"
        subtitle="Sessions and interviews"
        items={candidateNav}
        accent="violet"
        homePath="/candidate"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface-raised/80 px-6 py-4 backdrop-blur">
          <div>
            <p className="text-xs text-slate-500">Logged in as</p>
            <p className="text-sm font-medium text-slate-200">{user?.full_name ?? 'Candidate'}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-300 ring-1 ring-violet-500/20">
              {user?.email ?? 'candidate'}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-surface-overlay"
            >
              Log out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
