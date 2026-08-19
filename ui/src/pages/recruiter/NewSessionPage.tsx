import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { listQuestionPlans } from '../../api/questions'
import { createSession, listSessions } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { QuestionPlan } from '../../types/questions'
import type { SessionSummary } from '../../types/sessions'

export function NewSessionPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const presetPlanId = searchParams.get('planId') || ''

  const [plans, setPlans] = useState<QuestionPlan[]>([])
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [planId, setPlanId] = useState(presetPlanId)
  const [candidateEmail, setCandidateEmail] = useState('')
  const [followUpLimit, setFollowUpLimit] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const [items, sessionItems] = await Promise.all([listQuestionPlans(), listSessions()])
        const approvedPlans = items.filter((item) => item.approved_count > 0)
        setPlans(approvedPlans)
        setSessions(sessionItems)

        const preferred =
          approvedPlans.find((item) => item.id === presetPlanId) ||
          approvedPlans[0] ||
          null
        if (preferred) {
          setPlanId(preferred.id)
          setCandidateEmail(preferred.candidate_email || '')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load question plans')
      }
    }
    load()
  }, [presetPlanId])

  const selectedPlan = plans.find((item) => item.id === planId) ?? null

  function blockingSessionForPlan(plan: QuestionPlan | null) {
    if (!plan) return null
    return (
      sessions.find((session) => {
        if (session.job_title !== plan.job_title) return false
        const sameCandidate =
          session.candidate_email?.toLowerCase() === (plan.candidate_email || '').toLowerCase() ||
          session.candidate_name === plan.candidate_name
        if (!sameCandidate) return false
        return session.status === 'IN_PROGRESS' || session.status === 'SCHEDULED'
      }) || null
    )
  }

  const blocking = blockingSessionForPlan(selectedPlan)

  useEffect(() => {
    if (!selectedPlan) return
    setCandidateEmail(selectedPlan.candidate_email || '')
  }, [selectedPlan?.id])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    if (!planId) {
      setError('Select a question plan first. Generate and approve questions on Question Planning.')
      return
    }
    if (!selectedPlan || selectedPlan.approved_count < 1) {
      setError('Selected plan needs at least one approved question.')
      return
    }
    if (!candidateEmail.trim()) {
      setError('Candidate email is required.')
      return
    }
    if (blocking?.status === 'IN_PROGRESS') {
      setError('An interview is already in progress for this candidate and role.')
      return
    }
    if (blocking?.status === 'SCHEDULED') {
      setError('A scheduled session already exists. Use Scheduling to propose slots instead.')
      return
    }

    setLoading(true)
    setError(null)
    setStatus('Creating interview session...')

    try {
      await createSession(planId, candidateEmail.trim(), followUpLimit)
      setStatus('Session created. Next: propose slots on Scheduling.')
      navigate('/recruiter/scheduling')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Create Interview Session"
        description="Use an approved question plan. Candidate email is filled from the application when available. Then schedule slots separately."
      />

      {plans.length === 0 && (
        <Card className="mb-6 border-amber-200 bg-amber-50">
          <p className="text-sm font-semibold text-amber-900">Question plan required</p>
          <p className="mt-2 text-sm text-amber-800">
            Generate and approve interview questions first, then come back to create a session.
          </p>
          <Link
            to="/recruiter/questions"
            className="mt-3 inline-block rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-ink"
          >
            Go to Question Planning
          </Link>
        </Card>
      )}

      <Card>
        <form className="space-y-4" onSubmit={handleCreate}>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-500">Question plan</label>
            <select
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              className="input-field"
              required
            >
              {plans.length === 0 ? (
                <option value="">No approved question plans yet</option>
              ) : (
                plans.map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.title} ({plan.approved_count} approved)
                  </option>
                ))
              )}
            </select>
            {selectedPlan && (
              <p className="mt-2 text-xs text-slate-500">
                {selectedPlan.candidate_name} for {selectedPlan.job_title}
              </p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-500">Candidate email</label>
            <input
              type="text"
              inputMode="email"
              value={candidateEmail}
              onChange={(e) => setCandidateEmail(e.target.value)}
              className="input-field"
              required
              placeholder="Auto-filled from application when available"
            />
            <p className="mt-1 text-xs text-slate-500">
              Auto-filled from the shortlisted application when possible. Candidate must already be
              registered.
            </p>
          </div>

          {blocking && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              {blocking.status === 'IN_PROGRESS'
                ? 'An interview is already in progress for this candidate and role.'
                : 'A scheduled session already exists for this candidate and role.'}{' '}
              <Link to={`/recruiter/sessions/${blocking.id}`} className="font-semibold underline">
                Open existing session
              </Link>
              {blocking.status === 'SCHEDULED' && (
                <>
                  {' '}
                  or{' '}
                  <Link to="/recruiter/scheduling" className="font-semibold underline">
                    propose slots
                  </Link>
                  .
                </>
              )}
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-500">
              Max follow-ups per question
            </label>
            <select
              value={followUpLimit}
              onChange={(e) => setFollowUpLimit(Number(e.target.value))}
              className="input-field"
            >
              <option value={0}>0</option>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
          </div>

          {status && <p className="text-sm text-teal-700">{status}</p>}
          {error && <p className="text-sm text-rose-600">{error}</p>}

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={loading || !planId || Boolean(blocking)}
              className="rounded-xl bg-teal-500 px-6 py-2.5 text-sm font-semibold text-slate-950 hover:bg-teal-400 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create session'}
            </button>
            <Link
              to="/recruiter/questions"
              className="rounded-xl border border-border px-6 py-2.5 text-sm font-medium text-slate-700 hover:bg-surface-overlay"
            >
              Back to question planning
            </Link>
          </div>
        </form>
      </Card>
    </div>
  )
}
