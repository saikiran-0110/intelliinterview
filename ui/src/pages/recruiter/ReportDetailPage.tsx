import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getReport } from '../../api/reports'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { InterviewReport } from '../../types/reports'

export function ReportDetailPage() {
  const { reportId } = useParams()
  const [report, setReport] = useState<InterviewReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!reportId) return
    async function load() {
      try {
        const data = await getReport(reportId!)
        setReport(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [reportId])

  if (!reportId) {
    return (
      <Card>
        <p className="text-sm text-muted">Select a report from the reports list.</p>
        <Link to="/recruiter/reports" className="mt-3 inline-block text-sm font-semibold text-teal-700">
          Back to reports
        </Link>
      </Card>
    )
  }

  if (loading) return <p className="text-sm text-muted">Loading report...</p>

  if (error || !report) {
    return (
      <Card>
        <p className="text-sm text-rose-600">{error ?? 'Report not found'}</p>
        <Link to="/recruiter/reports" className="mt-3 inline-block text-sm font-semibold text-teal-700">
          Back to reports
        </Link>
      </Card>
    )
  }

  const dimensions = [
    { name: 'Technical fit', score: report.technical_fit_score },
    { name: 'Communication', score: report.communication_score },
    { name: 'Problem-solving', score: report.problem_solving_score },
    { name: 'Role alignment', score: report.role_alignment_score },
  ]

  return (
    <div>
      <PageHeader
        title="Interview Evaluation Report"
        description={`${report.candidate_name} for ${report.job_title}`}
        action={
          <div className="rounded-xl border border-border bg-surface-raised px-4 py-2 text-right">
            <p className="text-xs text-slate-500">Overall</p>
            <p className="text-2xl font-bold text-teal-700">{report.overall_score}/10</p>
          </div>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {dimensions.map((dim) => (
          <div key={dim.name} className="rounded-2xl border border-border bg-surface-raised p-5">
            <p className="text-xs text-slate-500">{dim.name}</p>
            <p className="mt-1 text-2xl font-bold text-teal-700">{dim.score}/10</p>
          </div>
        ))}
      </div>

      <div className="mb-6 rounded-2xl border border-teal-200 bg-teal-50 p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">Recommendation</p>
        <p className="mt-1 text-lg font-semibold text-ink">{report.recommendation.replaceAll('_', ' ')}</p>
        <p className="mt-2 text-sm leading-relaxed text-slate-700">{report.recommendation_summary}</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-ink">Strengths</h3>
          {report.strengths.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No strengths recorded.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {report.strengths.map((item) => (
                <li key={item} className="text-sm text-slate-700">
                  {item}
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <h3 className="text-lg font-semibold text-ink">Areas for improvement</h3>
          {report.weaknesses.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No weaknesses recorded.</p>
          ) : (
            <ul className="mt-3 space-y-2">
              {report.weaknesses.map((item) => (
                <li key={item} className="text-sm text-slate-700">
                  {item}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card className="mt-6">
        <h3 className="text-lg font-semibold text-ink">Evidence by answer</h3>
        <p className="mt-1 text-sm text-muted">Observations linked to specific interview responses.</p>
        <div className="mt-4 space-y-3">
          {report.evidence_items.length === 0 ? (
            <p className="text-sm text-slate-500">No evidence items available.</p>
          ) : (
            report.evidence_items.map((item) => (
              <div key={item.turn_id} className="rounded-xl border border-border bg-surface/60 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  {item.topic ?? 'Question'} | Tech {item.technical_score ?? '-'} | Comm{' '}
                  {item.communication_score ?? '-'}
                </p>
                {item.question_text && <p className="mt-2 text-sm text-slate-700">{item.question_text}</p>}
                {item.answer_excerpt && (
                  <p className="mt-2 text-sm text-muted">Answer: {item.answer_excerpt}</p>
                )}
                {item.evidence_quotes.length > 0 && (
                  <p className="mt-2 text-xs text-teal-700">Quotes: {item.evidence_quotes.join(' | ')}</p>
                )}
                {item.observations.length > 0 && (
                  <p className="mt-1 text-xs text-slate-500">{item.observations.join(' ')}</p>
                )}
              </div>
            ))
          )}
        </div>
      </Card>

      <p className="mt-4 text-sm text-slate-500">
        <Link to={`/recruiter/sessions/${report.session_id}`} className="text-teal-700 hover:text-teal-700">
          View session transcript
        </Link>
      </p>
    </div>
  )
}
