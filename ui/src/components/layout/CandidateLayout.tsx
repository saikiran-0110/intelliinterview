import { useEffect, useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { apiRequest, clearAuth, getStoredUser, getToken, setAuth } from '../../api/client'
import type { AuthResponse } from '../../types/analysis'
import { candidateNav } from '../../config/navigation'
import { NotificationBell } from '../ui/NotificationBell'
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
          phone: me.phone,
          company: me.company,
          job_title: me.job_title,
          location: me.location,
          linkedin_url: me.linkedin_url,
          email_verified: me.email_verified,
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
      <div className="flex min-h-screen items-center justify-center text-sm text-muted">
        Checking session...
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar
        title="Candidate Portal"
        subtitle="Apply and interview"
        items={candidateNav}
        accent="sky"
        homePath="/candidate/applications"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-col gap-3 border-b border-sky-200/70 bg-sky-50/70 px-4 py-4 pl-16 backdrop-blur sm:flex-row sm:items-center sm:justify-between sm:px-6 md:pl-6">
          <div>
            <p className="text-sm text-muted">Logged in as</p>
            <p className="text-base font-bold text-ink">{user?.full_name ?? 'Candidate'}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-sky-100 px-3 py-1.5 text-sm font-semibold text-sky-900 ring-1 ring-sky-300">
              {user?.email ?? 'candidate'}
            </span>
            <NotificationBell />
            <button
              type="button"
              onClick={handleLogout}
              className="btn-secondary min-h-11 !px-3.5 !py-2 !text-sm"
            >
              Log out
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-x-hidden overflow-y-auto px-4 py-6 sm:px-6 sm:py-8 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
