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
  const nextReady =
    sessions.find((item) => {
      if (item.status === 'IN_PROGRESS') return true
      if (item.status !== 'SCHEDULED' || item.confirmation_status !== 'CONFIRMED' || !item.scheduled_at) {
        return false
      }
      const start = new Date(item.scheduled_at).getTime()
      const duration = item.duration_minutes || 45
      const now = Date.now()
      return now >= start - 5 * 60 * 1000 && now <= start + duration * 60 * 1000
    }) ?? null
  const nextPending =
    sessions.find(
      (item) =>
        item.status === 'SCHEDULED' &&
        (item.confirmation_status !== 'CONFIRMED' ||
          !item.scheduled_at ||
          Date.now() < new Date(item.scheduled_at).getTime() - 5 * 60 * 1000),
    ) ?? null

  return (
    <div>
      <PageHeader
        title="Candidate Dashboard"
        description="Confirm your interview slot first, then join the live AI interview."
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Upcoming', value: String(upcoming.length), color: 'text-sky-700' },
          { label: 'Completed', value: String(completed.length), color: 'text-ink' },
          { label: 'Total sessions', value: String(sessions.length), color: 'text-sky-700' },
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
            <p className="font-semibold text-ink">My Sessions</p>
            <p className="mt-1 text-sm text-muted">Confirm slots and manage interviews</p>
          </Card>
        </Link>
        <Link
          to={
            nextReady
              ? `/candidate/interview/${nextReady.id}`
              : '/candidate/sessions'
          }
        >
          <Card hover className="border-sky-200">
            <p className="font-semibold text-sky-700">
              {nextReady ? 'Enter Live Interview' : 'Confirm slot to interview'}
            </p>
            <p className="mt-1 text-sm text-muted">
              {nextReady
                ? 'Join your confirmed AI session room'
                : 'Choose and confirm a time before starting'}
            </p>
          </Card>
        </Link>
      </div>

      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}

      <Card>
        <h3 className="text-lg font-semibold text-ink">Next interview</h3>
        {nextReady ? (
          <div className="mt-3">
            <p className="text-sm text-ink">{nextReady.job_title}</p>
            <p className="mt-1 text-sm text-muted">{nextReady.plan_title}</p>
            <p className="mt-1 text-xs text-slate-500">
              Status: {nextReady.status} · Schedule: {nextReady.confirmation_status.replaceAll('_', ' ')}
            </p>
            <Link
              to={`/candidate/interview/${nextReady.id}`}
              className="mt-4 inline-block rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-ink hover:bg-sky-500"
            >
              Open interview
            </Link>
          </div>
        ) : nextPending ? (
          <div className="mt-3">
            <p className="text-sm text-ink">{nextPending.job_title}</p>
            <p className="mt-1 text-sm text-muted">{nextPending.plan_title}</p>
            <p className="mt-1 text-xs text-amber-700">
              {nextPending.confirmation_status !== 'CONFIRMED'
                ? `Slot not confirmed yet (${nextPending.confirmation_status.replaceAll('_', ' ')}). Confirm a time before the interview can start.`
                : nextPending.scheduled_at
                  ? `Confirmed for ${new Date(nextPending.scheduled_at).toLocaleString()}. You can join from 5 minutes before that time.`
                  : 'Waiting for a confirmed interview time.'}
            </p>
            <Link
              to="/candidate/sessions"
              className="mt-4 inline-block rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-ink hover:bg-sky-500"
            >
              {nextPending.confirmation_status !== 'CONFIRMED'
                ? 'Confirm slot on My Sessions'
                : 'View My Sessions'}
            </Link>
          </div>
        ) : (
          <p className="mt-3 text-sm text-slate-500">No upcoming sessions assigned yet.</p>
        )}
      </Card>
    </div>
  )
}
