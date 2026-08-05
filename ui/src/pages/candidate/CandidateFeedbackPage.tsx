import { useEffect, useState } from 'react'
import { getFeedbackBySession, listMyFeedback } from '../../api/desirable'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateFeedback, CandidateFeedbackSummary } from '../../types/desirable'

export function CandidateFeedbackPage() {
  const [items, setItems] = useState<CandidateFeedbackSummary[]>([])
  const [selected, setSelected] = useState<CandidateFeedback | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const summaries = await listMyFeedback()
        setItems(summaries)
        if (summaries[0]) {
          const detail = await getFeedbackBySession(summaries[0].session_id)
          setSelected(detail)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load feedback')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function openFeedback(sessionId: string) {
    setError(null)
    try {
      const detail = await getFeedbackBySession(sessionId)
      setSelected(detail)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open feedback')
    }
  }

  return (
    <div>
      <PageHeader
        title="Interview Feedback"
        description="AI-written feedback after completed interviews: strong answers, improvement areas, and focus tips for future interviews."
      />

      {loading && <p className="text-sm text-slate-400">Loading feedback...</p>}
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}

      {!loading && items.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-400">
            No feedback yet. Complete an AI interview session to receive your summary.
          </p>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <h3 className="text-sm font-semibold text-white">Completed interviews</h3>
            <div className="mt-3 space-y-2">
              {items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => openFeedback(item.session_id)}
                  className={`block w-full rounded-xl border p-3 text-left ${
                    selected?.session_id === item.session_id
                      ? 'border-violet-500/40 bg-violet-500/10'
                      : 'border-border bg-surface/60'
                  }`}
                >
                  <p className="text-sm font-medium text-white">{item.job_title}</p>
                  <p className="mt-1 text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
                </button>
              ))}
            </div>
          </Card>

          {selected && (
            <div className="space-y-4 lg:col-span-2">
              <Card>
                <h3 className="text-lg font-semibold text-white">{selected.job_title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-300">{selected.summary}</p>
              </Card>
              <div className="grid gap-4 sm:grid-cols-3">
                <Card>
                  <h4 className="text-sm font-semibold text-teal-300">Strong answers</h4>
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-400">
                    {selected.strong_answers.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Card>
                <Card>
                  <h4 className="text-sm font-semibold text-amber-300">Improve</h4>
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-400">
                    {selected.improvement_areas.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Card>
                <Card>
                  <h4 className="text-sm font-semibold text-violet-300">Focus next</h4>
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-400">
                    {selected.focus_tips.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </Card>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
