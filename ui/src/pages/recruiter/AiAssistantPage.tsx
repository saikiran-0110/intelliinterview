import { type FormEvent, useState } from 'react'
import { queryAssistant } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { AssistantResponse } from '../../types/optional'

const suggestions = [
  'Who are the best candidates for this role?',
  'Summarise the top CV for my latest role',
  'Show recent applications and stages',
]

export function AiAssistantPage() {
  const [message, setMessage] = useState(suggestions[0])
  const [history, setHistory] = useState<{ role: 'user' | 'assistant'; text: string }[]>([])
  const [latest, setLatest] = useState<AssistantResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!message.trim()) return
    setLoading(true)
    setError(null)
    const asked = message.trim()
    setHistory((prev) => [...prev, { role: 'user', text: asked }])
    try {
      const result = await queryAssistant(asked)
      setLatest(result)
      setHistory((prev) => [...prev, { role: 'assistant', text: result.answer }])
      setMessage('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assistant query failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="AI Assistant"
        description="Ask natural language questions about candidates, CV summaries, and role matches. Uses a tool-style agent over your candidate database."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}

      <div className="mb-4 flex flex-wrap gap-2">
        {suggestions.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setMessage(item)}
            className="rounded-full border border-border px-3 py-1 text-xs text-slate-300"
          >
            {item}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 max-h-[24rem] space-y-3 overflow-y-auto">
            {history.length === 0 ? (
              <p className="text-sm text-slate-500">Ask a question to get started.</p>
            ) : (
              history.map((item, index) => (
                <div
                  key={`${item.role}-${index}`}
                  className={`rounded-xl border p-3 text-sm ${
                    item.role === 'user'
                      ? 'border-border bg-surface/60 text-slate-200'
                      : 'border-teal-500/20 bg-teal-500/5 text-slate-100'
                  }`}
                >
                  <p className="text-xs uppercase tracking-wider text-slate-500">{item.role}</p>
                  <p className="mt-1">{item.text}</p>
                </div>
              ))
            )}
          </div>
          <form className="flex gap-2" onSubmit={handleSubmit}>
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="flex-1 rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
              placeholder="Ask about candidates, CVs, or rankings..."
            />
            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-ink disabled:opacity-50"
            >
              {loading ? 'Thinking...' : 'Ask'}
            </button>
          </form>
        </Card>

        <Card>
          <h3 className="text-sm font-semibold text-white">Structured result</h3>
          {!latest ? (
            <p className="mt-3 text-xs text-slate-500">No structured payload yet.</p>
          ) : (
            <div className="mt-3 space-y-3 text-xs text-slate-400">
              <p>Tools: {latest.tools_used.join(', ')}</p>
              <pre className="overflow-x-auto rounded-lg border border-border bg-surface p-3 text-[11px] text-slate-300">
                {JSON.stringify(latest.structured, null, 2)}
              </pre>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
