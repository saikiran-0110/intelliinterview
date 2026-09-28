import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getReport } from '../../api/reports'
import { getRecordingBlob } from '../../api/sessions'
import { getUserPhotoBlob, updateApplicationStage } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { ApplicationStage, InterviewReport } from '../../types/reports'

const STAGE_LABELS: Record<ApplicationStage, string> = {
  APPLIED: 'Applied',
  SCREENING: 'Screening',
  SHORTLISTED: 'Shortlisted',
  INTERVIEW: 'Interview',
  OFFER: 'Next stage',
  HIRED: 'Hired',
  REJECTED: 'Rejected',
}

export function ReportDetailPage() {
  const { reportId } = useParams()
  const [report, setReport] = useState<InterviewReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null)
  const [photoUrl, setPhotoUrl] = useState<string | null>(null)
  const [decisionMessage, setDecisionMessage] = useState('')
  const [decisionStatus, setDecisionStatus] = useState<string | null>(null)
  const [decisionError, setDecisionError] = useState<string | null>(null)
  const [decisionPending, setDecisionPending] = useState<ApplicationStage | null>(null)

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

  useEffect(() => {
    if (!report) return
    let objectUrl: string | null = null
    getRecordingBlob(report.session_id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob)
        setRecordingUrl(objectUrl)
      })
      .catch(() => setRecordingUrl(null))
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [report])

  useEffect(() => {
    if (!report?.candidate_has_photo || !report.candidate_user_id) {
      setPhotoUrl(null)
      return
    }
    let objectUrl: string | null = null
    getUserPhotoBlob(report.candidate_user_id)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob)
        setPhotoUrl(objectUrl)
      })
      .catch(() => setPhotoUrl(null))
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [report])

  async function handleDecision(stage: ApplicationStage) {
    if (!report?.application_id) return
    setDecisionPending(stage)
    setDecisionError(null)
    setDecisionStatus(null)
    try {
      await updateApplicationStage(report.application_id, stage, decisionMessage.trim() || undefined)
      setReport({ ...report, application_stage: stage })
      setDecisionStatus(`Candidate notified by email: ${STAGE_LABELS[stage]}.`)
      setDecisionMessage('')
    } catch (err) {
      setDecisionError(err instanceof Error ? err.message : 'Failed to record decision')
    } finally {
      setDecisionPending(null)
    }
  }

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
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => window.print()}
              className="btn-secondary min-h-11 print:hidden"
            >
              Print / Export PDF
            </button>
            <div className="rounded-xl border border-border bg-surface-raised px-4 py-2 text-right">
              <p className="text-xs text-slate-500">Overall</p>
              <p className="text-2xl font-bold text-teal-700">{report.overall_score}/10</p>
            </div>
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

      {recordingUrl && (
        <Card className="mt-6 print:hidden">
          <h3 className="text-lg font-semibold text-ink">Candidate recording</h3>
          <p className="mt-1 text-xs text-muted">
            For human review only - not used in scoring or by the AI evaluation.
          </p>
          <div className="mt-3 flex flex-col gap-4 sm:flex-row">
            <video controls className="w-full min-w-0 flex-1 rounded-xl" src={recordingUrl} />
            {photoUrl && (
              <div className="shrink-0 text-center">
                <img src={photoUrl} alt="Candidate profile" className="h-32 w-32 rounded-xl border border-border object-cover" />
                <p className="mt-1 text-xs text-muted">Profile photo</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {report.application_id && (
        <Card className="mt-6 print:hidden">
          <h3 className="text-lg font-semibold text-ink">Hiring decision</h3>
          <p className="mt-1 text-xs text-muted">
            Current status:{' '}
            <span className="font-semibold text-ink">
              {report.application_stage ? STAGE_LABELS[report.application_stage] : 'Applied'}
            </span>
            . Any decision below emails the candidate automatically.
          </p>
          <textarea
            value={decisionMessage}
            onChange={(e) => setDecisionMessage(e.target.value)}
            placeholder="Optional message to include in the candidate's email"
            className="input-field mt-3 min-h-20 w-full"
          />
          {decisionError && <p className="mt-2 text-sm text-rose-600">{decisionError}</p>}
          {decisionStatus && <p className="mt-2 text-sm text-teal-800">{decisionStatus}</p>}
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => handleDecision('OFFER')}
              disabled={decisionPending !== null}
              className="btn-secondary min-h-11 disabled:opacity-50"
            >
              Advance to next stage
            </button>
            <button
              type="button"
              onClick={() => handleDecision('HIRED')}
              disabled={decisionPending !== null}
              className="btn-primary min-h-11 disabled:opacity-50"
            >
              Hire &amp; send offer
            </button>
            <button
              type="button"
              onClick={() => handleDecision('REJECTED')}
              disabled={decisionPending !== null}
              className="min-h-11 rounded-xl border border-rose-300 px-4 text-sm font-semibold text-rose-700 disabled:opacity-50"
            >
              Reject
            </button>
          </div>
        </Card>
      )}

      <p className="mt-4 text-sm text-slate-500 print:hidden">
        <Link to={`/recruiter/sessions/${report.session_id}`} className="text-teal-700 hover:text-teal-700">
          View session transcript
        </Link>
      </p>
    </div>
  )
}
