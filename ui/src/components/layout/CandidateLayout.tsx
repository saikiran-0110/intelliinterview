import { Outlet } from 'react-router-dom'
import { candidateNav } from '../../config/navigation'
import { Sidebar } from '../ui/Sidebar'

export function CandidateLayout() {
  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar
        title="Candidate Portal"
        subtitle="Sessions & interviews"
        items={candidateNav}
        accent="violet"
        homePath="/candidate"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-surface-raised/80 px-6 py-4 backdrop-blur">
          <div>
            <p className="text-xs text-slate-500">Logged in as</p>
            <p className="text-sm font-medium text-slate-200">Candidate (demo)</p>
          </div>
          <span className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-300 ring-1 ring-violet-500/20">
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
