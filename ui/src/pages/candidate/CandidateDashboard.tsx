import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listSessions } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { SessionSummary } from '../../types/sessions'

export function CandidateDashboard() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const items = await listSessions()
        setSessions(items)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sessions')
      }
    }
    load()
  }, [])

  const upcoming = sessions.filter((item) => item.status === 'SCHEDULED' || item.status === 'IN_PROGRESS')
  const completed = sessions.filter((item) => item.status === 'COMPLETED')
  const nextSession = upcoming[0] ?? null

  return (
    <div>
      <PageHeader
        title="Candidate Dashboard"
        description="Access scheduled AI interviews and submit responses during live sessions."
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Upcoming', value: String(upcoming.length), color: 'text-violet-300' },
          { label: 'Completed', value: String(completed.length), color: 'text-slate-200' },
          { label: 'Total sessions', value: String(sessions.length), color: 'text-indigo-300' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-border bg-surface-raised p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">{stat.label}</p>
            <p className={`mt-2 text-3xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2">
        <Link to="/candidate/sessions">
          <Card hover>
            <p className="font-semibold text-white">My Sessions</p>
            <p className="mt-1 text-sm text-slate-400">View scheduled and past interviews</p>
          </Card>
        </Link>
        <Link to={nextSession ? `/candidate/interview/${nextSession.id}` : '/candidate/interview'}>
          <Card hover className="border-violet-500/20">
            <p className="font-semibold text-violet-200">Enter Live Interview</p>
            <p className="mt-1 text-sm text-slate-400">Join your active AI session room</p>
          </Card>
        </Link>
      </div>

      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}

      <Card>
        <h3 className="text-lg font-semibold text-white">Next scheduled interview</h3>
        {!nextSession ? (
          <p className="mt-3 text-sm text-slate-500">No upcoming sessions assigned yet.</p>
        ) : (
          <div className="mt-3">
            <p className="text-sm text-slate-200">{nextSession.job_title}</p>
            <p className="mt-1 text-sm text-slate-400">{nextSession.plan_title}</p>
            <p className="mt-1 text-xs text-slate-500">Status: {nextSession.status}</p>
            <Link
              to={`/candidate/interview/${nextSession.id}`}
              className="mt-4 inline-block rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400"
            >
              Open interview
            </Link>
          </div>
        )}
      </Card>
    </div>
  )
}
