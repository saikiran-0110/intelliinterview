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

  const inProgress = sessions.filter((item) => item.status === 'IN_PROGRESS')
  const scheduled = sessions.filter((item) => item.status === 'SCHEDULED')
  const completed = sessions.filter((item) => item.status === 'COMPLETED')

  return (
    <div>
      <PageHeader
        title="Interview Sessions"
        description="Create sessions only from approved question plans. Use Scheduling next to propose time slots — do not create duplicate sessions here."
        action={
          <div className="flex flex-wrap gap-2">
            <Link
              to="/recruiter/questions"
              className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-teal-800"
            >
              Question planning
            </Link>
            <Link
              to="/recruiter/sessions/new"
              className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
            >
              New session
            </Link>
          </div>
        }
      />

      {loading && <p className="text-sm text-muted">Loading sessions...</p>}
      {error && <p className="text-sm text-rose-600">{error}</p>}

      {!loading && sessions.length === 0 ? (
        <Card>
          <p className="text-sm text-muted">No sessions yet.</p>
          <p className="mt-2 text-sm text-muted">
            First generate and approve questions, then create one interview session per candidate/role.
          </p>
          <div className="mt-3 flex flex-wrap gap-3">
            <Link to="/recruiter/questions" className="text-sm font-semibold text-teal-700">
              Go to Question Planning
            </Link>
            <Link to="/recruiter/sessions/new" className="text-sm font-semibold text-teal-700">
              Create session
            </Link>
          </div>
        </Card>
      ) : (
        <div className="space-y-6">
          {inProgress.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-semibold text-amber-800">In progress</h3>
              <div className="space-y-3">
                {inProgress.map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </section>
          )}
          {scheduled.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-semibold text-sky-800">
                Scheduled — propose slots on Scheduling
              </h3>
              <div className="space-y-3">
                {scheduled.map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </section>
          )}
          {completed.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-semibold text-slate-600">Completed</h3>
              <div className="space-y-3">
                {completed.map((session) => (
                  <SessionCard key={session.id} session={session} />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

function SessionCard({ session }: { session: SessionSummary }) {
  return (
    <Card>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-semibold text-ink">
            {session.candidate_name} - {session.job_title}
          </p>
          <p className="mt-1 text-sm text-muted">{session.plan_title}</p>
          <p className="mt-1 text-xs text-slate-500">
            Status: {session.status} | Progress:{' '}
            {Math.min(session.current_question_index + 1, session.total_questions)}/
            {session.total_questions}
            {session.confirmation_status
              ? ` · Schedule: ${session.confirmation_status.replaceAll('_', ' ')}`
              : ''}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          {session.status === 'SCHEDULED' && (
            <Link to="/recruiter/scheduling" className="text-sm font-semibold text-sky-700">
              Propose slots
            </Link>
          )}
          <Link
            to={`/recruiter/sessions/${session.id}`}
            className="text-sm font-semibold text-teal-700 hover:text-teal-700"
          >
            View session
          </Link>
        </div>
      </div>
    </Card>
  )
}
