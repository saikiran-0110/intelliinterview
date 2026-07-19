import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listSessions } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { SessionSummary } from '../../types/sessions'

export function MySessionsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const items = await listSessions()
        setSessions(items)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load sessions')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div>
      <PageHeader
        title="My Interview Sessions"
        description="Access scheduled AI interview sessions assigned by your recruiter."
      />

      {loading && <p className="text-sm text-slate-400">Loading sessions...</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}

      {!loading && sessions.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-400">No sessions assigned yet.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <Card key={session.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-white">{session.job_title}</p>
                  <p className="mt-1 text-sm text-slate-400">{session.plan_title}</p>
                  <p className="mt-1 text-xs text-slate-500">Status: {session.status}</p>
                </div>
                <Link
                  to={`/candidate/interview/${session.id}`}
                  className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400"
                >
                  {session.status === 'COMPLETED' ? 'View transcript' : 'Open interview'}
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
