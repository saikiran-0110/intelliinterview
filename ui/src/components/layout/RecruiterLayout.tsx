import { useEffect, useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { apiRequest, clearAuth, getStoredUser, getToken, setAuth } from '../../api/client'
import type { AuthResponse } from '../../types/analysis'
import { recruiterNav } from '../../config/navigation'
import { Sidebar } from '../ui/Sidebar'

export function RecruiterLayout() {
  const navigate = useNavigate()
  const [user, setUser] = useState(getStoredUser())
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    async function validateSession() {
      const token = getToken()
      const stored = getStoredUser()

      if (!token || stored?.role !== 'RECRUITER') {
        clearAuth()
        setChecking(false)
        navigate('/recruiter/login', { replace: true })
        return
      }

      try {
        const me = await apiRequest<AuthResponse>('/api/auth/me')
        setAuth(me.token, {
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
        })
        setUser({
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
        })
      } catch {
        clearAuth()
        navigate('/recruiter/login', { replace: true })
        return
      } finally {
        setChecking(false)
      }
    }

    validateSession()
  }, [navigate])

  function handleLogout() {
    clearAuth()
    navigate('/recruiter/login', { replace: true })
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
        title="Recruiter Portal"
        subtitle="Hire end to end"
        items={recruiterNav}
        accent="teal"
        homePath="/recruiter/jobs"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-teal-200/70 bg-teal-50/70 px-6 py-4 backdrop-blur">
          <div>
            <p className="text-sm text-muted">Logged in as</p>
            <p className="text-base font-bold text-ink">{user?.full_name ?? 'Recruiter'}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-teal-100 px-3 py-1.5 text-sm font-semibold text-teal-900 ring-1 ring-teal-300">
              {user?.email ?? 'recruiter'}
            </span>
            <button type="button" onClick={handleLogout} className="btn-secondary !px-3.5 !py-2 !text-sm">
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
