import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getSession, listSessions, startSession, submitAnswer } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
import { InterviewRecorder } from '../../components/ui/InterviewRecorder'
import { PageHeader } from '../../components/ui/PageHeader'
import {
  createSpeechRecognition,
  isSpeechRecognitionSupported,
  isSpeechSynthesisSupported,
  speakText,
  stopSpeaking,
  type SpeechRecognitionController,
} from '../../lib/speech'
import type { InterviewSession, SessionSummary } from '../../types/sessions'

export function LiveInterviewPage() {
  const { sessionId: routeSessionId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const querySessionId = searchParams.get('sessionId')
  const sessionId = routeSessionId || querySessionId

  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [answer, setAnswer] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const [sttEnabled, setSttEnabled] = useState(true)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [nowMs, setNowMs] = useState(() => Date.now())
  const lastSpokenTurnId = useRef<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionController | null>(null)
  const ttsSupported = useMemo(() => isSpeechSynthesisSupported(), [])
  const sttSupported = useMemo(() => isSpeechRecognitionSupported(), [])

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), 15000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    async function loadList() {
      try {
        const items = await listSessions()
        setSessions(items.filter((item) => item.status !== 'CANCELLED'))
      } catch {
        // ignore for empty state
      }
    }
    loadList()
  }, [])

  useEffect(() => {
    if (!sessionId) {
      setSession(null)
      return
    }

    async function loadSession() {
      setLoading(true)
      setError(null)
      try {
        const data = await getSession(sessionId!)
        setSession(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load session')
        setSession(null)
      } finally {
        setLoading(false)
      }
    }

    loadSession()
  }, [sessionId])

  const latestInterviewerTurn = useMemo(() => {
    if (!session) return null
    const interviewerTurns = session.turns.filter((turn) => turn.role === 'INTERVIEWER')
    return interviewerTurns.length > 0 ? interviewerTurns[interviewerTurns.length - 1] : null
  }, [session])

  const language = session?.language || 'en-GB'

  useEffect(() => {
    if (!session || !ttsEnabled || !ttsSupported || !latestInterviewerTurn) return
    if (session.status !== 'IN_PROGRESS') return
    if (lastSpokenTurnId.current === latestInterviewerTurn.id) return

    lastSpokenTurnId.current = latestInterviewerTurn.id
    setIsSpeaking(true)
    speakText(latestInterviewerTurn.content, {
      lang: language,
      onEnd: () => setIsSpeaking(false),
      onError: (message) => {
        setIsSpeaking(false)
        setStatus(message)
      },
    })
  }, [latestInterviewerTurn, session, ttsEnabled, ttsSupported, language])

  useEffect(() => {
    recognitionRef.current = createSpeechRecognition({
      continuous: true,
      interimResults: true,
      lang: language,
      onResult: (transcript, isFinal) => {
        if (isFinal) {
          setAnswer((prev) => `${prev} ${transcript}`.trim())
          setInterimTranscript('')
        } else {
          setInterimTranscript(transcript)
        }
      },
      onError: (message) => {
        setIsListening(false)
        setStatus(message)
      },
      onEnd: () => {
        setIsListening(false)
        setInterimTranscript('')
      },
    })

    return () => {
      recognitionRef.current?.stop()
      stopSpeaking()
    }
  }, [language])

  function handleSpeakLatest() {
    if (!latestInterviewerTurn || !ttsSupported) return
    setIsSpeaking(true)
    lastSpokenTurnId.current = latestInterviewerTurn.id
    speakText(latestInterviewerTurn.content, {
      lang: language,
      onEnd: () => setIsSpeaking(false),
      onError: (message) => {
        setIsSpeaking(false)
        setStatus(message)
      },
    })
  }

  function handleStopSpeaking() {
    stopSpeaking()
    setIsSpeaking(false)
  }

  function handleToggleListening() {
    if (!sttSupported || !sttEnabled) return

    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      setInterimTranscript('')
      setStatus('Voice capture stopped. Review and edit your answer before submitting.')
      return
    }

    handleStopSpeaking()
    setInterimTranscript('')
    setIsListening(true)
    setStatus('Listening... speak your answer. You can edit the transcript before submit.')
    recognitionRef.current?.start()
  }

  async function handleStart() {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    setStatus('Starting AI interview...')
    try {
      const data = await startSession(sessionId)
      setSession(data)
      setStatus('Interview in progress.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!sessionId || !answer.trim()) return

    recognitionRef.current?.stop()
    setIsListening(false)
    setInterimTranscript('')
    stopSpeaking()
    setIsSpeaking(false)
    setLoading(true)
    setError(null)
    setStatus('Evaluating your answer with GPT-4o...')

    try {
      const data = await submitAnswer(sessionId, answer.trim())
      setSession(data)
      setAnswer('')
      setStatus(
        data.status === 'COMPLETED'
          ? 'Interview completed. Evidence saved for the recruiter report.'
          : 'Answer recorded. Next question ready.',
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit answer')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div>
        <PageHeader
          title="Live AI Interview"
          description="Select a scheduled session to begin your AI-conducted interview."
        />
        <Card>
          {sessions.length === 0 ? (
            <p className="text-sm text-muted">No assigned sessions yet.</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((item) => {
                const canOpen =
                  item.status === 'COMPLETED' ||
                  item.status === 'IN_PROGRESS' ||
                  item.confirmation_status === 'CONFIRMED'
                return (
                  <button
                    key={item.id}
                    type="button"
                    disabled={!canOpen}
                    onClick={() => {
                      if (canOpen) navigate(`/candidate/interview/${item.id}`)
                    }}
                    className="block w-full rounded-xl border border-border bg-surface/60 p-4 text-left hover:border-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <p className="font-medium text-ink">{item.job_title}</p>
                    <p className="mt-1 text-sm text-muted">
                      {item.plan_title} - {item.status}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Schedule: {item.confirmation_status.replaceAll('_', ' ')}
                      {!canOpen ? ' · Confirm a slot on My Sessions before starting' : ''}
                    </p>
                  </button>
                )
              })}
            </div>
          )}
          <Link to="/candidate/sessions" className="mt-4 inline-block text-sm font-semibold text-sky-700">
            View all sessions
          </Link>
        </Card>
      </div>
    )
  }

  if (loading && !session) {
    return <p className="text-sm text-muted">Loading interview room...</p>
  }

  if (error && !session) {
    return (
      <Card>
        <p className="text-sm text-rose-600">{error}</p>
        <Link to="/candidate/sessions" className="mt-3 inline-block text-sm font-semibold text-sky-700">
          Back to sessions
        </Link>
      </Card>
    )
  }

  if (!session) return null

  const slotConfirmed = session.confirmation_status === 'CONFIRMED'
  const waitingForConfirmation = session.status === 'SCHEDULED' && !slotConfirmed
  const durationMinutes = session.duration_minutes || 45
  const scheduledAtMs = session.scheduled_at ? new Date(session.scheduled_at).getTime() : null
  const opensAtMs = scheduledAtMs != null ? scheduledAtMs - 5 * 60 * 1000 : null
  const closesAtMs = scheduledAtMs != null ? scheduledAtMs + durationMinutes * 60 * 1000 : null
  const withinSlotWindow =
    opensAtMs != null && closesAtMs != null && nowMs >= opensAtMs && nowMs <= closesAtMs
  const tooEarly = opensAtMs != null && nowMs < opensAtMs
  const tooLate = closesAtMs != null && nowMs > closesAtMs
  const canStart = session.status === 'SCHEDULED' && slotConfirmed && withinSlotWindow
  const canAnswer = session.status === 'IN_PROGRESS'
  const latestEvaluation = [...session.turns]
    .reverse()
    .find((turn) => turn.role === 'CANDIDATE' && turn.evaluation)?.evaluation
  const displayAnswer = interimTranscript
    ? `${answer}${answer ? ' ' : ''}${interimTranscript}`
    : answer

  return (
    <div>
      <PageHeader
        title="Live AI Interview"
        description={`${session.job_title} - ${session.plan_title}`}
      />

      {waitingForConfirmation && (
        <Card className="mb-6 border-amber-200 bg-amber-50">
          <p className="text-sm font-semibold text-amber-900">Confirm your interview slot first</p>
          <p className="mt-2 text-sm text-amber-800">
            This interview cannot start until you confirm a proposed time on My Sessions.
          </p>
          <Link
            to="/candidate/sessions"
            className="mt-3 inline-block rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-ink"
          >
            Go to My Sessions
          </Link>
        </Card>
      )}

      {slotConfirmed && session.status === 'SCHEDULED' && scheduledAtMs != null && (
        <Card className="mb-6 border-sky-200 bg-sky-50">
          <p className="text-sm font-semibold text-sky-900">Confirmed slot</p>
          <p className="mt-2 text-sm text-sky-800">
            {new Date(scheduledAtMs).toLocaleString()} · {durationMinutes} minutes
          </p>
          <p className="mt-1 text-xs text-sky-700">
            You can join from 5 minutes before the start time until the slot ends.
          </p>
          {tooEarly && opensAtMs != null && (
            <p className="mt-2 text-sm font-semibold text-amber-800">
              Opens at {new Date(opensAtMs).toLocaleString()}
            </p>
          )}
          {tooLate && (
            <p className="mt-2 text-sm font-semibold text-rose-700">
              This slot has ended. Ask your recruiter to reschedule.
            </p>
          )}
        </Card>
      )}

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Card>
          <p className="text-xs text-slate-500">Status</p>
          <p className="mt-1 font-semibold text-ink">{session.status}</p>
          <p className="mt-1 text-xs text-muted">
            Schedule: {session.confirmation_status.replaceAll('_', ' ')}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Progress</p>
          <p className="mt-1 font-semibold text-sky-700">
            Question {session.progress.index} of {session.progress.total}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Current topic</p>
          <p className="mt-1 font-semibold text-ink">{session.progress.topic ?? '-'}</p>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {latestInterviewerTurn && session.status === 'IN_PROGRESS' && (
            <Card className="border-sky-200">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                    Current AI question
                    {latestInterviewerTurn.is_follow_up ? ' (follow-up)' : ''}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-ink">{latestInterviewerTurn.content}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSpeakLatest}
                    disabled={!ttsSupported || isSpeaking}
                    className="min-h-11 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-sky-700 hover:border-sky-300 disabled:opacity-50"
                  >
                    {isSpeaking ? 'Speaking...' : 'Listen'}
                  </button>
                  <button
                    type="button"
                    onClick={handleStopSpeaking}
                    disabled={!isSpeaking}
                    className="min-h-11 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-slate-700 hover:border-slate-400/40 disabled:opacity-50"
                  >
                    Stop
                  </button>
                </div>
              </div>
            </Card>
          )}

          <Card>
            <div className="mb-4 flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wider text-slate-500">Conversation</p>
              <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs text-emerald-300">
                AI interviewer
              </span>
            </div>
            <div className="max-h-[28rem] space-y-3 overflow-y-auto">
              {session.turns.length === 0 ? (
                <p className="text-sm text-muted">Start the session to receive the first question.</p>
              ) : (
                session.turns.map((turn) => (
                  <div
                    key={turn.id}
                    className={`rounded-xl border p-4 ${
                      turn.role === 'INTERVIEWER'
                        ? 'border-sky-200 bg-sky-50'
                        : 'border-border bg-surface/60'
                    }`}
                  >
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      {turn.role === 'INTERVIEWER' ? 'AI Interviewer' : 'You'}
                      {turn.is_follow_up ? ' - follow-up' : ''}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-ink">{turn.content}</p>
                    {turn.evaluation && (
                      <p className="mt-2 text-xs text-slate-500">
                        Evidence saved for report
                        {turn.evaluation.evidence_quotes[0]
                          ? `: "${turn.evaluation.evidence_quotes[0].slice(0, 80)}..."`
                          : ''}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <h3 className="text-lg font-semibold text-ink">Voice settings</h3>
            <label className="mt-3 flex min-h-11 items-center gap-3 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={ttsEnabled}
                onChange={(e) => {
                  setTtsEnabled(e.target.checked)
                  if (!e.target.checked) {
                    handleStopSpeaking()
                  }
                }}
                disabled={!ttsSupported}
                className="h-5 w-5 shrink-0 rounded border-border"
              />
              Read AI questions aloud (text-to-speech)
            </label>
            <label className="mt-3 flex min-h-11 items-center gap-3 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={sttEnabled}
                onChange={(e) => {
                  setSttEnabled(e.target.checked)
                  if (!e.target.checked && isListening) {
                    recognitionRef.current?.stop()
                    setIsListening(false)
                    setInterimTranscript('')
                  }
                }}
                disabled={!sttSupported}
                className="h-5 w-5 shrink-0 rounded border-border"
              />
              Enable voice answers (speech-to-text)
            </label>
            {!ttsSupported && (
              <p className="mt-2 text-xs text-amber-300">
                Text-to-speech is unavailable in this browser. Questions remain readable as text.
              </p>
            )}
            {!sttSupported && (
              <p className="mt-2 text-xs text-amber-300">
                Speech-to-text is unavailable in this browser. Typed answers still work.
              </p>
            )}
          </Card>

          <Card>
            <h3 className="text-lg font-semibold text-ink">Recording</h3>
            <div className="mt-3">
              <InterviewRecorder
                sessionId={session.id}
                active={session.status === 'IN_PROGRESS'}
                completed={session.status === 'COMPLETED'}
              />
            </div>
          </Card>

          {canStart && (
            <Card>
              <h3 className="text-lg font-semibold text-ink">Ready to begin?</h3>
              <p className="mt-2 text-sm text-muted">
                Your confirmed slot is open. Questions are shown as text by default (audio is off).
              </p>
              <button
                type="button"
                onClick={handleStart}
                disabled={loading}
                className="mt-4 min-h-11 w-full rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-semibold text-ink hover:bg-sky-500 disabled:opacity-50"
              >
                Start interview
              </button>
            </Card>
          )}

          {slotConfirmed && session.status === 'SCHEDULED' && !withinSlotWindow && !waitingForConfirmation && (
            <Card>
              <h3 className="text-lg font-semibold text-ink">Interview locked to slot time</h3>
              <p className="mt-2 text-sm text-muted">
                {tooEarly
                  ? 'Come back from 5 minutes before your confirmed start time.'
                  : 'This confirmed slot has ended. Request a reschedule from My Sessions.'}
              </p>
            </Card>
          )}

          {canAnswer && (
            <Card>
              <h3 className="text-lg font-semibold text-ink">Your response</h3>
              <p className="mt-1 text-xs text-slate-500">
                Type or dictate your answer. Review the transcript before submitting.
              </p>
              <form className="mt-3 space-y-3" onSubmit={handleSubmit}>
                <textarea
                  value={displayAnswer}
                  onChange={(e) => {
                    setAnswer(e.target.value)
                    setInterimTranscript('')
                  }}
                  rows={8}
                  placeholder="Type your answer, or use the microphone..."
                  className="input-field"
                  required
                />
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={handleToggleListening}
                    disabled={!sttSupported || !sttEnabled || loading}
                    className={`min-h-11 rounded-xl px-4 py-2.5 text-sm font-semibold disabled:opacity-50 ${
                      isListening
                        ? 'bg-rose-500 text-ink hover:bg-rose-400'
                        : 'border border-border text-sky-700 hover:border-sky-300'
                    }`}
                  >
                    {isListening ? 'Stop mic' : 'Start mic'}
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !answer.trim()}
                    className="min-h-11 rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-semibold text-ink hover:bg-sky-500 disabled:opacity-50"
                  >
                    {loading ? 'Submitting...' : 'Submit answer'}
                  </button>
                </div>
              </form>
            </Card>
          )}

          {latestEvaluation && (
            <Card>
              <h3 className="text-sm font-semibold text-ink">Latest evaluation snapshot</h3>
              <p className="mt-2 text-xs text-muted">
                Technical {latestEvaluation.technical_score ?? '-'} / Communication{' '}
                {latestEvaluation.communication_score ?? '-'}
              </p>
              {latestEvaluation.observations[0] && (
                <p className="mt-2 text-xs text-slate-500">{latestEvaluation.observations[0]}</p>
              )}
            </Card>
          )}

          {session.status === 'COMPLETED' && (
            <Card>
              <h3 className="text-lg font-semibold text-ink">Interview complete</h3>
              <p className="mt-2 text-sm text-muted">
                Your answers and evaluation evidence have been saved for the recruiter report.
              </p>
              <Link to="/candidate/sessions" className="mt-4 inline-block text-sm font-semibold text-sky-700">
                Back to my sessions
              </Link>
            </Card>
          )}

          {status && <p className="text-sm text-sky-700">{status}</p>}
          {error && <p className="text-sm text-rose-600">{error}</p>}
        </div>
      </div>
    </div>
  )
}
