import { type FormEvent, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getGapAnalysis, listGapAnalyses } from '../../api/analysis'
import {
  addCustomQuestion,
  deleteQuestion,
  generateQuestions,
  getPlanByAnalysis,
  updateQuestion,
} from '../../api/questions'
import { ApiError } from '../../api/client'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { GapAnalysis } from '../../types/analysis'
import type { InterviewQuestion, QuestionPlan } from '../../types/questions'

function QuestionCard({
  question,
  onToggleApproved,
  onDelete,
  busy,
}: {
  question: InterviewQuestion
  onToggleApproved: (question: InterviewQuestion) => void
  onDelete: (question: InterviewQuestion) => void
  busy: boolean
}) {
  const sourceTone =
    question.source === 'AI'
      ? 'bg-teal-50 text-teal-700 ring-teal-500/25'
      : 'bg-indigo-500/15 text-sky-700 ring-indigo-500/25'

  return (
    <div className="rounded-xl border border-border bg-surface/60 p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${sourceTone}`}>
          {question.source}
        </span>
        <span className="rounded-full bg-slate-500/15 px-2.5 py-0.5 text-xs text-slate-700 ring-1 ring-inset ring-slate-500/25">
          {question.topic}
        </span>
        <span className="rounded-full bg-slate-500/10 px-2.5 py-0.5 text-xs text-muted">
          {question.question_type}
        </span>
        {!question.approved && (
          <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs text-amber-300">Pending</span>
        )}
      </div>
      <p className="text-sm leading-relaxed text-ink">{question.text}</p>
      {question.rationale && <p className="mt-2 text-xs text-slate-500">{question.rationale}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => onToggleApproved(question)}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-surface-overlay disabled:opacity-50"
        >
          {question.approved ? 'Unapprove' : 'Approve'}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => onDelete(question)}
          className="rounded-lg border border-rose-500/30 px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-500/10 disabled:opacity-50"
        >
          Remove
        </button>
      </div>
    </div>
  )
}

export function QuestionPlanningPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const analysisId = searchParams.get('analysisId')

  const [analyses, setAnalyses] = useState<GapAnalysis[]>([])
  const [selectedAnalysisId, setSelectedAnalysisId] = useState(analysisId ?? '')
  const [analysis, setAnalysis] = useState<GapAnalysis | null>(null)
  const [plan, setPlan] = useState<QuestionPlan | null>(null)
  const [customText, setCustomText] = useState('')
  const [customTopic, setCustomTopic] = useState('custom')
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadAnalyses() {
      try {
        const items = await listGapAnalyses()
        setAnalyses(items)
        if (!selectedAnalysisId && items[0]) {
          setSelectedAnalysisId(items[0].id)
        }
      } catch {
        // Fresh accounts may have no analyses yet.
      }
    }
    loadAnalyses()
  }, [selectedAnalysisId])

  useEffect(() => {
    if (!analysisId) return
    setSelectedAnalysisId(analysisId)
  }, [analysisId])

  useEffect(() => {
    if (!selectedAnalysisId) {
      setAnalysis(null)
      setPlan(null)
      return
    }

    async function loadContext() {
      setError(null)
      try {
        const gap = await getGapAnalysis(selectedAnalysisId)
        setAnalysis(gap)
        try {
          const existing = await getPlanByAnalysis(selectedAnalysisId)
          setPlan(existing)
        } catch (err) {
          if (err instanceof ApiError && err.status === 404) {
            setPlan(null)
          } else {
            throw err
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analysis context')
        setAnalysis(null)
        setPlan(null)
      }
    }

    loadContext()
  }, [selectedAnalysisId])

  function selectAnalysis(id: string) {
    setSelectedAnalysisId(id)
    setSearchParams(id ? { analysisId: id } : {})
  }

  async function handleGenerate() {
    if (!selectedAnalysisId) {
      setError('Select a gap analysis before generating questions.')
      return
    }

    setLoading(true)
    setError(null)
    setStatus('Generating tailored interview questions from the gap analysis...')

    try {
      const generated = await generateQuestions(selectedAnalysisId)
      setPlan(generated)
      setStatus(`Generated ${generated.questions.length} role-specific questions.`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Question generation failed')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddCustom(event: FormEvent) {
    event.preventDefault()
    if (!plan) {
      setError('Generate or open a question plan before adding custom questions.')
      return
    }
    if (!customText.trim()) {
      setError('Enter a custom question.')
      return
    }

    setLoading(true)
    setError(null)
    try {
      await addCustomQuestion(plan.id, customText.trim(), customTopic.trim() || 'custom')
      const refreshed = await getPlanByAnalysis(plan.gap_analysis_id)
      setPlan(refreshed)
      setCustomText('')
      setStatus('Custom question added to the plan.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add custom question')
    } finally {
      setLoading(false)
    }
  }

  async function handleToggleApproved(question: InterviewQuestion) {
    if (!plan) return
    setLoading(true)
    setError(null)
    try {
      await updateQuestion(question.id, { approved: !question.approved })
      const refreshed = await getPlanByAnalysis(plan.gap_analysis_id)
      setPlan(refreshed)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update question')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(question: InterviewQuestion) {
    if (!plan) return
    setLoading(true)
    setError(null)
    try {
      await deleteQuestion(question.id)
      const refreshed = await getPlanByAnalysis(plan.gap_analysis_id)
      setPlan(refreshed)
      setStatus('Question removed from the plan.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove question')
    } finally {
      setLoading(false)
    }
  }

  const aiQuestions = plan?.questions.filter((item) => item.source === 'AI') ?? []
  const recruiterQuestions = plan?.questions.filter((item) => item.source === 'RECRUITER') ?? []
  const approvedQuestions = plan?.questions.filter((item) => item.approved) ?? []

  return (
    <div>
      <PageHeader
        title="Interview Question Planning"
        description="Plan questions before creating an interview session. Approve at least one question, then continue to create the session."
        action={
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading || !selectedAnalysisId}
            className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400 disabled:opacity-50"
          >
            {loading ? 'Working...' : 'Generate AI questions'}
          </button>
        }
      />

      <Card className="mb-6">
        <h3 className="text-lg font-semibold text-ink">Gap analysis context</h3>
        <p className="mt-1 text-sm text-muted">
          Questions are generated from strong matches, partial matches, and gaps in the selected analysis.
        </p>

        {analyses.length === 0 ? (
          <div className="mt-4">
            <p className="text-sm text-muted">No gap analyses found yet.</p>
            <Link to="/recruiter/analysis" className="mt-3 inline-block text-sm font-semibold text-teal-700">
              Run CV and job analysis first
            </Link>
          </div>
        ) : (
          <div className="mt-4">
            <label className="mb-1.5 block text-xs font-medium text-slate-500">Select gap analysis</label>
            <select
              value={selectedAnalysisId}
              onChange={(e) => selectAnalysis(e.target.value)}
              className="input-field"
            >
              {analyses.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.candidate_name} vs {item.job_title} (score {item.match_score ?? '-'}%)
                </option>
              ))}
            </select>
          </div>
        )}

        {analysis && (
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border bg-surface/60 p-3">
              <p className="text-xs text-slate-500">Strong matches</p>
              <p className="mt-1 text-xl font-bold text-teal-700">{analysis.strong_match_count}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface/60 p-3">
              <p className="text-xs text-slate-500">Partial matches</p>
              <p className="mt-1 text-xl font-bold text-amber-300">{analysis.partial_match_count}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface/60 p-3">
              <p className="text-xs text-slate-500">Gaps</p>
              <p className="mt-1 text-xl font-bold text-rose-600">{analysis.gap_count}</p>
            </div>
          </div>
        )}
      </Card>

      {status && <p className="mb-4 text-sm text-teal-700">{status}</p>}
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}

      {!plan ? (
        <Card>
          <p className="text-sm text-muted">
            No question plan yet for this analysis. Click Generate AI questions to create a tailored set.
          </p>
        </Card>
      ) : (
        <>
          <div className="mb-4 flex flex-wrap gap-3 text-sm text-muted">
            <span>{plan.title}</span>
            <span>AI: {plan.ai_question_count}</span>
            <span>Recruiter: {plan.recruiter_question_count}</span>
            <span>Approved: {plan.approved_count}</span>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <h3 className="text-lg font-semibold text-ink">AI-generated questions</h3>
              <p className="mt-1 text-sm text-muted">
                Built from gap analysis for {plan.candidate_name} and {plan.job_title}.
              </p>
              <div className="mt-4 space-y-3">
                {aiQuestions.length === 0 ? (
                  <p className="text-sm text-slate-500">No AI questions in this plan.</p>
                ) : (
                  aiQuestions.map((question) => (
                    <QuestionCard
                      key={question.id}
                      question={question}
                      onToggleApproved={handleToggleApproved}
                      onDelete={handleDelete}
                      busy={loading}
                    />
                  ))
                )}
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-ink">Recruiter custom questions</h3>
              <p className="mt-1 text-sm text-muted">Add your own questions alongside the AI set.</p>

              <form className="mt-4 space-y-3" onSubmit={handleAddCustom}>
                <input
                  type="text"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                  placeholder="Topic"
                  className="input-field"
                />
                <textarea
                  value={customText}
                  onChange={(e) => setCustomText(e.target.value)}
                  rows={4}
                  placeholder="Enter a custom interview question"
                  className="input-field"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-ink hover:bg-surface-overlay disabled:opacity-50"
                >
                  Add custom question
                </button>
              </form>

              <div className="mt-4 space-y-3">
                {recruiterQuestions.length === 0 ? (
                  <p className="text-sm text-slate-500">No recruiter questions yet.</p>
                ) : (
                  recruiterQuestions.map((question) => (
                    <QuestionCard
                      key={question.id}
                      question={question}
                      onToggleApproved={handleToggleApproved}
                      onDelete={handleDelete}
                      busy={loading}
                    />
                  ))
                )}
              </div>
            </Card>
          </div>

          <Card className="mt-6">
            <h3 className="text-lg font-semibold text-ink">Combined session plan</h3>
            <p className="mt-1 text-sm text-muted">
              Approve questions first, then create one interview session. Scheduling comes after that.
            </p>
            <div className="mt-4 space-y-3">
              {approvedQuestions.length === 0 ? (
                <p className="text-sm text-slate-500">Approve at least one question to build the session plan.</p>
              ) : (
                approvedQuestions.map((question, index) => (
                  <div key={question.id} className="rounded-xl border border-border bg-surface/60 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Question {index + 1} - {question.source} - {question.topic}
                    </p>
                    <p className="mt-2 text-sm text-ink">{question.text}</p>
                  </div>
                ))
              )}
            </div>
            {approvedQuestions.length > 0 ? (
              <Link
                to={`/recruiter/sessions/new?planId=${plan.id}`}
                className="mt-5 inline-block rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
              >
                Create interview session (email auto-filled)
              </Link>
            ) : (
              <p className="mt-5 text-sm text-amber-700">
                Approve at least one question before creating an interview session.
              </p>
            )}
          </Card>
        </>
      )}
    </div>
  )
}
