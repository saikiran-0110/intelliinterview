import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listSessions } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { SessionSummary } from '../../types/sessions'

export function InterviewSessionsPage() {
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
        title="Interview Sessions"
        description="Create and monitor AI-conducted interview sessions based on approved question plans."
        action={
          <Link
            to="/recruiter/sessions/new"
            className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
          >
            New session
          </Link>
        }
      />

      {loading && <p className="text-sm text-slate-400">Loading sessions...</p>}
      {error && <p className="text-sm text-rose-300">{error}</p>}

      {!loading && sessions.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-400">No sessions yet.</p>
          <Link to="/recruiter/sessions/new" className="mt-3 inline-block text-sm font-semibold text-teal-300">
            Create your first session
          </Link>
        </Card>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <Card key={session.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-white">
                    {session.candidate_name} - {session.job_title}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">{session.plan_title}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Status: {session.status} | Progress: {Math.min(session.current_question_index + 1, session.total_questions)}/
                    {session.total_questions}
                  </p>
                </div>
                <Link
                  to={`/recruiter/sessions/${session.id}`}
                  className="text-sm font-semibold text-teal-300 hover:text-teal-200"
                >
                  View session
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
