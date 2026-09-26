import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  confirmSlot,
  listNotifications,
  listScheduleItems,
  markNotificationRead,
  requestReschedule,
  sendSessionMessage,
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
  const [notesBySession, setNotesBySession] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError(null)
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

  function noteFor(sessionId: string) {
    return notesBySession[sessionId] || ''
  }

  function setNote(sessionId: string, value: string) {
    setNotesBySession((current) => ({ ...current, [sessionId]: value }))
  }

  async function handleConfirm(sessionId: string, slotId: string) {
    setError(null)
    try {
      await confirmSlot(sessionId, slotId, noteFor(sessionId) || undefined)
      setStatus('Slot confirmed. You can join the interview when it starts.')
      setNote(sessionId, '')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to confirm slot')
    }
  }

  async function handleReschedule(sessionId: string) {
    setError(null)
    try {
      await requestReschedule(sessionId, noteFor(sessionId) || 'Please suggest different times.')
      setStatus('Reschedule requested. Your recruiter will propose new slots.')
      setNote(sessionId, '')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request reschedule')
    }
  }

  async function handleMessage(sessionId: string) {
    const message = noteFor(sessionId).trim()
    if (!message) {
      setError('Write a message before sending it to the recruiter.')
      return
    }
    setError(null)
    try {
      await sendSessionMessage(sessionId, message)
      setStatus('Message sent to your recruiter.')
      setNote(sessionId, '')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message')
    }
  }

  return (
    <div>
      <PageHeader
        title="My Interview Sessions"
        description="Confirm or reschedule proposed slots, message your recruiter, then access your AI interview sessions."
      />

      {loading && <p className="text-sm text-muted">Loading sessions...</p>}
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && <p className="mb-4 text-sm text-sky-700">{status}</p>}

      {notifications.length > 0 && (
        <Card className="mb-6">
          <h3 className="text-sm font-semibold text-ink">Notifications</h3>
          <div className="mt-3 space-y-2">
            {notifications.map((item) => (
              <div key={item.id} className="rounded-xl border border-border bg-surface/60 p-3">
                <p className="text-sm text-ink">{item.title}</p>
                <p className="mt-1 text-xs text-muted">{item.body}</p>
                <button
                  type="button"
                  className="mt-2 text-xs font-semibold text-sky-700"
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

      {!loading && !error && sessions.length === 0 ? (
        <Card>
          <p className="text-sm text-muted">
            No sessions assigned yet. Confirm, reschedule, and recruiter messages appear here once a
            recruiter creates an interview session for you.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => {
            const schedule = scheduleFor(session.id)
            const confirmation = schedule?.confirmation_status || session.confirmation_status
            const canActOnSchedule =
              confirmation !== 'CONFIRMED' &&
              session.status !== 'COMPLETED' &&
              session.status !== 'IN_PROGRESS'
            const hasSlots = Boolean(schedule && schedule.slots.length > 0)
            const confirmationReady = confirmation === 'CONFIRMED'
            const scheduledAtMs = session.scheduled_at
              ? new Date(session.scheduled_at).getTime()
              : schedule?.scheduled_at
                ? new Date(schedule.scheduled_at).getTime()
                : null
            const durationMinutes = session.duration_minutes || 45
            const nowMs = Date.now()
            const withinSlotWindow =
              scheduledAtMs != null &&
              nowMs >= scheduledAtMs - 5 * 60 * 1000 &&
              nowMs <= scheduledAtMs + durationMinutes * 60 * 1000
            const canOpenInterview =
              session.status === 'COMPLETED' ||
              session.status === 'IN_PROGRESS' ||
              (confirmationReady && withinSlotWindow)
            return (
              <Card key={session.id}>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-ink">{session.job_title}</p>
                    <p className="mt-1 text-sm text-muted">{session.plan_title}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      Status: {session.status}
                      {` · Schedule: ${confirmation.replaceAll('_', ' ')}`}
                    </p>
                    {schedule?.candidate_note && (
                      <p className="mt-2 text-xs text-slate-600">
                        Last note sent: {schedule.candidate_note}
                      </p>
                    )}

                    {canActOnSchedule && (
                      <div className="mt-3 space-y-2">
                        <label className="text-xs text-slate-500">
                          Optional message to recruiter (used for confirm, reschedule, or send message)
                        </label>
                        <input
                          value={noteFor(session.id)}
                          onChange={(e) => setNote(session.id, e.target.value)}
                          placeholder="Optional message to recruiter"
                          className="input-field"
                        />

                        {hasSlots && (
                          <>
                            <p className="text-xs text-muted">Suggested slots</p>
                            {schedule!.slots.map((slot) => (
                              <div
                                key={slot.id}
                                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border px-3 py-2"
                              >
                                <span className="text-xs text-slate-700">
                                  {new Date(slot.starts_at).toLocaleString()}
                                </span>
                                <button
                                  type="button"
                                  onClick={() => handleConfirm(session.id, slot.id)}
                                  className="min-h-11 rounded-lg bg-sky-600 px-3 py-1 text-xs font-semibold text-ink hover:bg-sky-500 sm:min-h-0"
                                >
                                  Confirm
                                </button>
                              </div>
                            ))}
                          </>
                        )}

                        {!hasSlots && (
                          <p className="text-xs text-amber-700">
                            No slots proposed yet. You can still message your recruiter or request a
                            reschedule so they send times.
                          </p>
                        )}

                        <div className="flex flex-wrap gap-3 pt-1">
                          <button
                            type="button"
                            onClick={() => handleMessage(session.id)}
                            className="min-h-11 text-xs font-semibold text-sky-700 sm:min-h-0"
                          >
                            Send message to recruiter
                          </button>
                          <button
                            type="button"
                            onClick={() => handleReschedule(session.id)}
                            className="min-h-11 text-xs font-semibold text-amber-700 sm:min-h-0"
                          >
                            Request reschedule
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    {session.status === 'COMPLETED' && (
                      <Link
                        to="/candidate/feedback"
                        className="flex min-h-11 items-center justify-center rounded-xl border border-border px-4 py-2 text-center text-sm font-semibold text-sky-700"
                      >
                        View feedback
                      </Link>
                    )}
                    {canOpenInterview ? (
                      <Link
                        to={`/candidate/interview/${session.id}`}
                        className="flex min-h-11 items-center justify-center rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-ink hover:bg-sky-500"
                      >
                        {session.status === 'COMPLETED' ? 'View transcript' : 'Open interview'}
                      </Link>
                    ) : (
                      <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs font-semibold text-amber-800">
                        {!confirmationReady
                          ? 'Confirm a slot before starting'
                          : scheduledAtMs != null && nowMs < scheduledAtMs - 5 * 60 * 1000
                            ? 'Opens 5 minutes before your slot'
                            : 'Interview slot window has ended'}
                      </p>
                    )}
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
