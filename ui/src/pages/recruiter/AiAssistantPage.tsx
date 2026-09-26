import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listJobSpecs } from '../../api/analysis'
import { getNextActions, queryAssistant } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { JobSpecification } from '../../types/analysis'
import type { NextActionItem } from '../../types/optional'

const ACTIONS = [
  {
    id: 'top',
    label: 'Top matches',
    prompt: (job: string) => `Who are the best candidates for ${job}?`,
  },
  {
    id: 'pipeline',
    label: 'Pipeline stages',
    prompt: (job: string) => `Show recent applications and stages for ${job}`,
  },
  {
    id: 'summary',
    label: 'Top CV summary',
    prompt: (job: string) => `Summarise the top CV for ${job}`,
  },
] as const

export function AiAssistantPage() {
  const [jobs, setJobs] = useState<JobSpecification[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [message, setMessage] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [nextActions, setNextActions] = useState<NextActionItem[] | null>(null)

  useEffect(() => {
    async function loadJobs() {
      try {
        const items = await listJobSpecs()
        setJobs(items)
        if (items[0]) setSelectedJobId(items[0].id)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load roles')
      }
    }
    loadJobs()
  }, [])

  useEffect(() => {
    async function loadNextActions() {
      try {
        const result = await getNextActions()
        setNextActions(result.items)
      } catch {
        // Next-actions is a nice-to-have panel; never let it break the assistant below it.
        setNextActions(null)
      }
    }
    loadNextActions()
  }, [])

  const selectedJob = jobs.find((job) => job.id === selectedJobId)
  const jobTitle = selectedJob?.title || 'my latest role'

  async function ask(question: string) {
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    setAnswer(null)
    try {
      const result = await queryAssistant(question.trim())
      setAnswer(result.answer)
      setMessage('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assistant query failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    await ask(message)
  }

  return (
    <div>
      <PageHeader
        title="AI Assistant"
        description="Quick answers about one role — top matches, pipeline status, or a CV summary. For full scoring and shortlisting, use Candidate Ranking."
      />
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}

      {nextActions && nextActions.length > 0 && nextActions[0]?.id !== 'nothing-blocked' && (
        <Card className="mb-6">
          <h3 className="text-sm font-semibold text-ink">Next actions</h3>
          <ul className="mt-3 space-y-3">
            {nextActions.map((item) => (
              <li
                key={item.id}
                className="flex flex-col gap-2 rounded-xl border border-border p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    {item.priority === 0 && (
                      <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-rose-700">
                        Blocked
                      </span>
                    )}
                    <p className="text-sm font-semibold text-ink">{item.title}</p>
                  </div>
                  <p className="mt-1 text-xs text-muted">{item.detail}</p>
                </div>
                {item.cta_label && item.cta_path && (
                  <Link
                    to={item.cta_path}
                    className="shrink-0 rounded-xl border border-border px-3 py-2 text-center text-xs font-semibold text-sky-800"
                  >
                    {item.cta_label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}

      <Card className="mb-6">
        <label className="text-xs text-slate-500">Role to ask about</label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="mt-2 input-field"
        >
          {jobs.length === 0 && <option value="">No roles yet</option>}
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title}
            </option>
          ))}
        </select>

        <div className="mt-4 flex flex-wrap gap-2">
          {ACTIONS.map((action) => (
            <button
              key={action.id}
              type="button"
              disabled={!selectedJobId || loading}
              onClick={() => ask(action.prompt(jobTitle))}
              className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-sky-800 disabled:opacity-50"
            >
              {action.label}
            </button>
          ))}
        </div>

        <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={handleSubmit}>
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="flex-1 input-field"
            placeholder={`Ask something about ${jobTitle}…`}
          />
          <button type="submit" disabled={loading || !message.trim()} className="btn-primary disabled:opacity-50">
            {loading ? 'Thinking…' : 'Ask'}
          </button>
        </form>
      </Card>

      <Card>
        <h3 className="text-sm font-semibold text-ink">Answer</h3>
        {!answer ? (
          <p className="mt-3 text-sm text-muted">
            Pick a role, tap a quick action, or type a short question. For shortlisting and scheduling, go to{' '}
            <Link to="/recruiter/ranking" className="font-semibold text-sky-700">
              Candidate Ranking
            </Link>
            .
          </p>
        ) : (
          <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{answer}</p>
        )}
      </Card>
    </div>
  )
}
