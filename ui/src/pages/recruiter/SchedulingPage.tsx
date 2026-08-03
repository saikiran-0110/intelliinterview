import { useEffect, useState } from 'react'
import { listSessions } from '../../api/sessions'
import { listNotifications, listScheduleItems, proposeSlots } from '../../api/desirable'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { AppNotification, ScheduleItem } from '../../types/desirable'
import type { SessionSummary } from '../../types/sessions'

function formatSlot(value: string) {
  return new Date(value).toLocaleString()
}

export function SchedulingPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [items, setItems] = useState<ScheduleItem[]>([])
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [sessionItems, scheduleItems, notes] = await Promise.all([
        listSessions(),
        listScheduleItems(),
        listNotifications(),
      ])
      setSessions(sessionItems.filter((item) => item.status === 'SCHEDULED' || item.status === 'IN_PROGRESS'))
      setItems(scheduleItems)
      setNotifications(notes.slice(0, 8))
      if (!selectedSessionId && sessionItems[0]) {
        setSelectedSessionId(sessionItems[0].id)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scheduling data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handlePropose() {
    if (!selectedSessionId) return
    setStatus('Suggesting available slots and notifying candidate...')
    setError(null)
    try {
      await proposeSlots(selectedSessionId)
      setStatus('Slots proposed. Candidate notified by email/in-app.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to propose slots')
      setStatus(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Interview Scheduling"
        description="Suggest available slots when shortlisting a candidate, send email or in-app notifications, and track confirm or reschedule responses."
      />

      {loading && <p className="text-sm text-slate-400">Loading scheduling workspace...</p>}
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-300">{status}</p>}

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-white">Suggest slots</h3>
          <p className="mt-2 text-sm text-slate-400">
            Select a shortlisted interview session. The system proposes weekday slots and notifies the candidate.
          </p>
          <select
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            className="mt-4 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
          >
            <option value="">Select session</option>
            {sessions.map((session) => (
              <option key={session.id} value={session.id}>
                {session.candidate_name} - {session.job_title}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handlePropose}
            disabled={!selectedSessionId}
            className="mt-4 rounded-xl bg-teal-500 px-4 py-2.5 text-sm font-semibold text-ink hover:bg-teal-400 disabled:opacity-50"
          >
            Propose slots and notify
          </button>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white">Recent notifications</h3>
          <div className="mt-3 space-y-3">
            {notifications.length === 0 ? (
              <p className="text-sm text-slate-500">No notifications yet.</p>
            ) : (
              notifications.map((note) => (
                <div key={note.id} className="rounded-xl border border-border bg-surface/60 p-3">
                  <p className="text-sm font-medium text-white">{note.title}</p>
                  <p className="mt-1 text-xs text-slate-400">{note.body}</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {note.email_sent ? 'Email sent' : 'In-app only'} · {new Date(note.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-white">Confirmation status</h3>
        <div className="mt-4 space-y-3">
          {items.length === 0 ? (
            <p className="text-sm text-slate-500">No scheduled sessions yet.</p>
          ) : (
            items.map((item) => (
              <div key={item.session_id} className="rounded-xl border border-border bg-surface/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-white">
                      {item.candidate_name} - {item.job_title}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Status: {item.confirmation_status.replaceAll('_', ' ')}
                      {item.scheduled_at ? ` · Confirmed: ${formatSlot(item.scheduled_at)}` : ''}
                    </p>
                  </div>
                  <span className="rounded-full bg-teal-500/15 px-2.5 py-0.5 text-xs text-teal-300">
                    {item.slots.length} slots
                  </span>
                </div>
                {item.slots.length > 0 && (
                  <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                    {item.slots.map((slot) => (
                      <div
                        key={slot.id}
                        className={`rounded-lg border px-3 py-2 text-xs ${
                          slot.is_selected
                            ? 'border-teal-500/40 bg-teal-500/10 text-teal-200'
                            : 'border-border text-slate-400'
                        }`}
                      >
                        {formatSlot(slot.starts_at)}
                      </div>
                    ))}
                  </div>
                )}
                {item.candidate_note && (
                  <p className="mt-2 text-xs text-slate-500">Candidate note: {item.candidate_note}</p>
                )}
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
