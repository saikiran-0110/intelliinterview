import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  confirmSlot,
  listNotifications,
  listScheduleItems,
  markNotificationRead,
  requestReschedule,
} from '../../api/desirable'
import { listSessions } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { AppNotification, ScheduleItem } from '../../types/desirable'
import type { SessionSummary } from '../../types/sessions'

export function MySessionsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [scheduleItems, setScheduleItems] = useState<ScheduleItem[]>([])
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const [sessionItems, schedule, notes] = await Promise.all([
        listSessions(),
        listScheduleItems(),
        listNotifications(),
      ])
      setSessions(sessionItems)
      setScheduleItems(schedule)
      setNotifications(notes.filter((item) => !item.is_read).slice(0, 5))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  function scheduleFor(sessionId: string) {
    return scheduleItems.find((item) => item.session_id === sessionId)
  }

  async function handleConfirm(sessionId: string, slotId: string) {
    setError(null)
    try {
      await confirmSlot(sessionId, slotId, note || undefined)
      setStatus('Slot confirmed. You can join the interview when it starts.')
      setNote('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to confirm slot')
    }
  }

  async function handleReschedule(sessionId: string) {
    setError(null)
    try {
      await requestReschedule(sessionId, note || 'Please suggest different times.')
      setStatus('Reschedule requested. Your recruiter will propose new slots.')
      setNote('')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request reschedule')
    }
  }

  return (
    <div>
      <PageHeader
        title="My Interview Sessions"
        description="Confirm or reschedule proposed slots, then access your AI interview sessions."
      />

      {loading && <p className="text-sm text-slate-400">Loading sessions...</p>}
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-violet-300">{status}</p>}

      {notifications.length > 0 && (
        <Card className="mb-6">
          <h3 className="text-sm font-semibold text-white">Notifications</h3>
          <div className="mt-3 space-y-2">
            {notifications.map((item) => (
              <div key={item.id} className="rounded-xl border border-border bg-surface/60 p-3">
                <p className="text-sm text-white">{item.title}</p>
                <p className="mt-1 text-xs text-slate-400">{item.body}</p>
                <button
                  type="button"
                  className="mt-2 text-xs font-semibold text-violet-300"
                  onClick={async () => {
                    await markNotificationRead(item.id)
                    await load()
                  }}
                >
                  Mark read
                </button>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card className="mb-6">
        <label className="text-xs text-slate-500">Note for confirm / reschedule</label>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Optional message to recruiter"
          className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
        />
      </Card>

      {!loading && sessions.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-400">No sessions assigned yet.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => {
            const schedule = scheduleFor(session.id)
            return (
              <Card key={session.id}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-white">{session.job_title}</p>
                    <p className="mt-1 text-sm text-slate-400">{session.plan_title}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      Status: {session.status}
                      {schedule
                        ? ` · Schedule: ${schedule.confirmation_status.replaceAll('_', ' ')}`
                        : ''}
                    </p>

                    {schedule && schedule.slots.length > 0 && schedule.confirmation_status !== 'CONFIRMED' && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs text-slate-400">Suggested slots</p>
                        {schedule.slots.map((slot) => (
                          <div
                            key={slot.id}
                            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border px-3 py-2"
                          >
                            <span className="text-xs text-slate-300">
                              {new Date(slot.starts_at).toLocaleString()}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleConfirm(session.id, slot.id)}
                              className="rounded-lg bg-violet-500 px-3 py-1 text-xs font-semibold text-white hover:bg-violet-400"
                            >
                              Confirm
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => handleReschedule(session.id)}
                          className="text-xs font-semibold text-amber-300"
                        >
                          Request reschedule
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    {session.status === 'COMPLETED' && (
                      <Link
                        to="/candidate/feedback"
                        className="rounded-xl border border-border px-4 py-2 text-center text-sm font-semibold text-violet-200"
                      >
                        View feedback
                      </Link>
                    )}
                    <Link
                      to={`/candidate/interview/${session.id}`}
                      className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400"
                    >
                      {session.status === 'COMPLETED' ? 'View transcript' : 'Open interview'}
                    </Link>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
