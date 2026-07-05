import { Outlet } from 'react-router-dom'
import { recruiterNav } from '../../config/navigation'
import { Sidebar } from '../ui/Sidebar'

export function RecruiterLayout() {
  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar
        title="Recruiter Portal"
        subtitle="Prepare, conduct & review"
        items={recruiterNav}
        accent="teal"
        homePath="/recruiter"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface-raised/80 px-6 py-4 backdrop-blur">
          <div>
            <p className="text-xs text-slate-500">Logged in as</p>
            <p className="text-sm font-medium text-slate-200">Recruiter (demo)</p>
          </div>
          <span className="rounded-full bg-teal-500/10 px-3 py-1 text-xs font-medium text-teal-300 ring-1 ring-teal-500/20">
            Demo mode
          </span>
        </header>
        <main className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
