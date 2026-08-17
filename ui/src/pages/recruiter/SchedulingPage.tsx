import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
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
      const active = sessionItems.filter(
        (item) => item.status === 'SCHEDULED' || item.status === 'IN_PROGRESS',
      )
      setSessions(active)
      setItems(scheduleItems)
      setNotifications(notes.slice(0, 8))
      if (!selectedSessionId && active[0]) {
        setSelectedSessionId(active[0].id)
      } else if (selectedSessionId && !active.some((item) => item.id === selectedSessionId)) {
        setSelectedSessionId(active[0]?.id || '')
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

  const selectedSchedule = items.find((item) => item.session_id === selectedSessionId)

  return (
    <div>
      <PageHeader
        title="Interview Scheduling"
        description="After shortlisting, propose weekday slots here. Candidates confirm or request a reschedule from their portal."
      />

      {loading && <p className="text-sm text-muted">Loading scheduling workspace...</p>}
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-700">{status}</p>}

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-ink">Propose slots</h3>
          <p className="mt-2 text-sm text-muted">
            Shortlisted candidates appear here automatically. Choose one, propose slots, and they get notified.
          </p>

          {sessions.length === 0 ? (
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p>No shortlisted interview sessions yet.</p>
              <p className="mt-2">
                Rank applicants and click <strong>Shortlist</strong> first — that creates the session for
                scheduling.
              </p>
              <Link to="/recruiter/ranking" className="mt-3 inline-block font-semibold text-sky-800 underline">
                Go to Candidate Ranking →
              </Link>
            </div>
          ) : (
            <>
              <select
                value={selectedSessionId}
                onChange={(e) => setSelectedSessionId(e.target.value)}
                className="mt-4 input-field"
              >
                {sessions.map((session) => (
                  <option key={session.id} value={session.id}>
                    {session.candidate_name} - {session.job_title}
                  </option>
                ))}
              </select>
              {selectedSchedule && (
                <p className="mt-2 text-xs text-muted">
                  Current status: {selectedSchedule.confirmation_status.replaceAll('_', ' ')}
                  {selectedSchedule.slots.length
                    ? ` · ${selectedSchedule.slots.length} slot(s) proposed`
                    : ' · no slots proposed yet'}
                </p>
              )}
              <button
                type="button"
                onClick={handlePropose}
                disabled={!selectedSessionId}
                className="mt-4 rounded-xl btn-primary hover:bg-teal-400 disabled:opacity-50"
              >
                Propose slots and notify
              </button>
            </>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-ink">Recent notifications</h3>
          <div className="mt-3 space-y-3">
            {notifications.length === 0 ? (
              <p className="text-sm text-slate-500">No notifications yet.</p>
            ) : (
              notifications.map((note) => (
                <div key={note.id} className="rounded-xl border border-border bg-surface/60 p-3">
                  <p className="text-sm font-medium text-ink">{note.title}</p>
                  <p className="mt-1 text-xs text-muted">{note.body}</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    {note.email_sent ? 'Email sent' : 'In-app only'} ·{' '}
                    {new Date(note.created_at).toLocaleString()}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-ink">Confirmation status</h3>
        <div className="mt-4 space-y-3">
          {items.length === 0 ? (
            <p className="text-sm text-slate-500">
              No sessions to track yet. Shortlist a candidate, then propose slots above.
            </p>
          ) : (
            items.map((item) => (
              <div key={item.session_id} className="rounded-xl border border-border bg-surface/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-ink">
                      {item.candidate_name} - {item.job_title}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Status: {item.confirmation_status.replaceAll('_', ' ')}
                      {item.scheduled_at ? ` · Confirmed: ${formatSlot(item.scheduled_at)}` : ''}
                    </p>
                  </div>
                  <span className="rounded-full bg-teal-50 px-2.5 py-0.5 text-xs text-teal-700">
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
                            ? 'border-teal-500/40 bg-teal-50 text-teal-700'
                            : 'border-border text-muted'
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
