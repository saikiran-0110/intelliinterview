import { type FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listQuestionPlans } from '../../api/questions'
import { createSession } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { QuestionPlan } from '../../types/questions'

export function NewSessionPage() {
  const navigate = useNavigate()
  const [plans, setPlans] = useState<QuestionPlan[]>([])
  const [planId, setPlanId] = useState('')
  const [candidateEmail, setCandidateEmail] = useState('')
  const [followUpLimit, setFollowUpLimit] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadPlans() {
      try {
        const items = await listQuestionPlans()
        setPlans(items)
        const withApproved = items.find((item) => item.approved_count > 0)
        if (withApproved) setPlanId(withApproved.id)
        else if (items[0]) setPlanId(items[0].id)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load question plans')
      }
    }
    loadPlans()
  }, [])

  const selectedPlan = plans.find((item) => item.id === planId) ?? null

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    if (!planId) {
      setError('Select a question plan first.')
      return
    }
    if (!selectedPlan || selectedPlan.approved_count < 1) {
      setError('Selected plan needs at least one approved question.')
      return
    }

    setLoading(true)
    setError(null)
    setStatus('Creating interview session...')

    try {
      const session = await createSession(planId, candidateEmail.trim(), followUpLimit)
      setStatus('Session created. Redirecting...')
      navigate('/recruiter/sessions')
      return session
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
        description="Link an approved question plan to a registered candidate to start an AI-conducted interview."
      />

      <Card>
        <form className="space-y-4" onSubmit={handleCreate}>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-500">Question plan</label>
            <select
              value={planId}
              onChange={(e) => setPlanId(e.target.value)}
              className="input-field"
            >
              {plans.length === 0 ? (
                <option value="">No question plans yet</option>
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
              type="email"
              value={candidateEmail}
              onChange={(e) => setCandidateEmail(e.target.value)}
              className="input-field"
              required
            />
            <p className="mt-1 text-xs text-slate-500">
              Candidate must already be registered in the candidate portal.
            </p>
          </div>

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
              disabled={loading || !planId}
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
