import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getReportBySession } from '../../api/reports'
import { getSession } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { InterviewReport } from '../../types/reports'
import type { InterviewSession } from '../../types/sessions'

export function SessionDetailPage() {
  const { sessionId } = useParams()
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [report, setReport] = useState<InterviewReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) return
    async function load() {
      try {
        const data = await getSession(sessionId!)
        setSession(data)
        if (data.status === 'COMPLETED') {
          try {
            const reportData = await getReportBySession(sessionId!)
            setReport(reportData)
          } catch {
            setReport(null)
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [sessionId])

  if (loading) return <p className="text-sm text-muted">Loading session...</p>
  if (error || !session) {
    return (
      <Card>
        <p className="text-sm text-rose-600">{error ?? 'Session not found'}</p>
        <Link to="/recruiter/sessions" className="mt-3 inline-block text-sm font-semibold text-teal-700">
          Back to sessions
        </Link>
      </Card>
    )
  }

  return (
    <div>
      <PageHeader
        title="Session detail"
        description={`${session.candidate_name} interviewing for ${session.job_title}`}
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Card>
          <p className="text-xs text-slate-500">Status</p>
          <p className="mt-1 text-lg font-semibold text-ink">{session.status}</p>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Progress</p>
          <p className="mt-1 text-lg font-semibold text-teal-700">
            {session.progress.index} / {session.progress.total}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Follow-up limit</p>
          <p className="mt-1 text-lg font-semibold text-ink">{session.follow_up_limit}</p>
        </Card>
      </div>

      {session.status === 'COMPLETED' && report && (
        <Card className="mb-6 border-teal-200">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-ink">Evaluation report ready</p>
              <p className="mt-1 text-xs text-muted">
                Overall {report.overall_score}/10 - {report.recommendation.replaceAll('_', ' ')}
              </p>
            </div>
            <Link
              to={`/recruiter/reports/${report.id}`}
              className="rounded-xl btn-primary hover:bg-teal-400"
            >
              View report
            </Link>
          </div>
        </Card>
      )}

      <Card>
        <h3 className="text-lg font-semibold text-ink">Transcript and evidence</h3>
        <div className="mt-4 space-y-3">
          {session.turns.length === 0 ? (
            <p className="text-sm text-slate-500">No turns yet. Waiting for candidate to start.</p>
          ) : (
            session.turns.map((turn) => (
              <div key={turn.id} className="rounded-xl border border-border bg-surface/60 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  {turn.role}
                  {turn.is_follow_up ? ' (follow-up)' : ''}
                </p>
                <p className="mt-2 text-sm text-ink">{turn.content}</p>
                {turn.evaluation && (
                  <div className="mt-3 rounded-lg border border-border bg-surface p-3 text-xs text-muted">
                    <p>
                      Scores: technical {turn.evaluation.technical_score ?? '-'} / communication{' '}
                      {turn.evaluation.communication_score ?? '-'}
                    </p>
                    {turn.evaluation.observations.length > 0 && (
                      <p className="mt-1">Observations: {turn.evaluation.observations.join(' ')}</p>
                    )}
                    {turn.evaluation.evidence_quotes.length > 0 && (
                      <p className="mt-1">Evidence: {turn.evaluation.evidence_quotes.join(' | ')}</p>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
