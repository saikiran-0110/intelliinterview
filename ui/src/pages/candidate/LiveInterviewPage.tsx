import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { getSession, listSessions, startSession, submitAnswer } from '../../api/sessions'
import { Card } from '../../components/ui/Card'
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
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const [sttEnabled, setSttEnabled] = useState(true)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const lastSpokenTurnId = useRef<string | null>(null)
  const recognitionRef = useRef<SpeechRecognitionController | null>(null)
  const ttsSupported = useMemo(() => isSpeechSynthesisSupported(), [])
  const sttSupported = useMemo(() => isSpeechRecognitionSupported(), [])

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

  useEffect(() => {
    if (!session || !ttsEnabled || !ttsSupported || !latestInterviewerTurn) return
    if (session.status !== 'IN_PROGRESS') return
    if (lastSpokenTurnId.current === latestInterviewerTurn.id) return

    lastSpokenTurnId.current = latestInterviewerTurn.id
    setIsSpeaking(true)
    speakText(latestInterviewerTurn.content, {
      onEnd: () => setIsSpeaking(false),
      onError: (message) => {
        setIsSpeaking(false)
        setStatus(message)
      },
    })
  }, [latestInterviewerTurn, session, ttsEnabled, ttsSupported])

  useEffect(() => {
    recognitionRef.current = createSpeechRecognition({
      continuous: true,
      interimResults: true,
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
  }, [])

  function handleSpeakLatest() {
    if (!latestInterviewerTurn || !ttsSupported) return
    setIsSpeaking(true)
    lastSpokenTurnId.current = latestInterviewerTurn.id
    speakText(latestInterviewerTurn.content, {
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
            <p className="text-sm text-slate-400">No assigned sessions yet.</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => navigate(`/candidate/interview/${item.id}`)}
                  className="block w-full rounded-xl border border-border bg-surface/60 p-4 text-left hover:border-violet-500/40"
                >
                  <p className="font-medium text-white">{item.job_title}</p>
                  <p className="mt-1 text-sm text-slate-400">
                    {item.plan_title} - {item.status}
                  </p>
                </button>
              ))}
            </div>
          )}
          <Link to="/candidate/sessions" className="mt-4 inline-block text-sm font-semibold text-violet-300">
            View all sessions
          </Link>
        </Card>
      </div>
    )
  }

  if (loading && !session) {
    return <p className="text-sm text-slate-400">Loading interview room...</p>
  }

  if (error && !session) {
    return (
      <Card>
        <p className="text-sm text-rose-300">{error}</p>
        <Link to="/candidate/sessions" className="mt-3 inline-block text-sm font-semibold text-violet-300">
          Back to sessions
        </Link>
      </Card>
    )
  }

  if (!session) return null

  const canAnswer = session.status === 'IN_PROGRESS'
  const canStart = session.status === 'SCHEDULED'
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

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <Card>
          <p className="text-xs text-slate-500">Status</p>
          <p className="mt-1 font-semibold text-white">{session.status}</p>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Progress</p>
          <p className="mt-1 font-semibold text-violet-300">
            Question {session.progress.index} of {session.progress.total}
          </p>
        </Card>
        <Card>
          <p className="text-xs text-slate-500">Current topic</p>
          <p className="mt-1 font-semibold text-white">{session.progress.topic ?? '-'}</p>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {latestInterviewerTurn && session.status === 'IN_PROGRESS' && (
            <Card className="border-violet-500/30">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                    Current AI question
                    {latestInterviewerTurn.is_follow_up ? ' (follow-up)' : ''}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-100">{latestInterviewerTurn.content}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSpeakLatest}
                    disabled={!ttsSupported || isSpeaking}
                    className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-violet-200 hover:border-violet-400/40 disabled:opacity-50"
                  >
                    {isSpeaking ? 'Speaking...' : 'Listen'}
                  </button>
                  <button
                    type="button"
                    onClick={handleStopSpeaking}
                    disabled={!isSpeaking}
                    className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-slate-300 hover:border-slate-400/40 disabled:opacity-50"
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
                <p className="text-sm text-slate-400">Start the session to receive the first question.</p>
              ) : (
                session.turns.map((turn) => (
                  <div
                    key={turn.id}
                    className={`rounded-xl border p-4 ${
                      turn.role === 'INTERVIEWER'
                        ? 'border-violet-500/20 bg-violet-500/5'
                        : 'border-border bg-surface/60'
                    }`}
                  >
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      {turn.role === 'INTERVIEWER' ? 'AI Interviewer' : 'You'}
                      {turn.is_follow_up ? ' - follow-up' : ''}
                    </p>
                    <p className="mt-2 text-sm leading-relaxed text-slate-200">{turn.content}</p>
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
            <h3 className="text-lg font-semibold text-white">Voice settings</h3>
            <label className="mt-3 flex items-center gap-3 text-sm text-slate-300">
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
                className="h-4 w-4 rounded border-border"
              />
              Read AI questions aloud (text-to-speech)
            </label>
            <label className="mt-3 flex items-center gap-3 text-sm text-slate-300">
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
                className="h-4 w-4 rounded border-border"
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

          {canStart && (
            <Card>
              <h3 className="text-lg font-semibold text-white">Ready to begin?</h3>
              <p className="mt-2 text-sm text-slate-400">
                The AI interviewer will ask role-specific questions from your approved plan.
              </p>
              <button
                type="button"
                onClick={handleStart}
                disabled={loading}
                className="mt-4 w-full rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400 disabled:opacity-50"
              >
                Start interview
              </button>
            </Card>
          )}

          {canAnswer && (
            <Card>
              <h3 className="text-lg font-semibold text-white">Your response</h3>
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
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-slate-100"
                  required
                />
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={handleToggleListening}
                    disabled={!sttSupported || !sttEnabled || loading}
                    className={`rounded-xl px-4 py-2.5 text-sm font-semibold disabled:opacity-50 ${
                      isListening
                        ? 'bg-rose-500 text-white hover:bg-rose-400'
                        : 'border border-border text-violet-200 hover:border-violet-400/40'
                    }`}
                  >
                    {isListening ? 'Stop mic' : 'Start mic'}
                  </button>
                  <button
                    type="submit"
                    disabled={loading || !answer.trim()}
                    className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400 disabled:opacity-50"
                  >
                    {loading ? 'Submitting...' : 'Submit answer'}
                  </button>
                </div>
              </form>
            </Card>
          )}

          {latestEvaluation && (
            <Card>
              <h3 className="text-sm font-semibold text-white">Latest evaluation snapshot</h3>
              <p className="mt-2 text-xs text-slate-400">
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
              <h3 className="text-lg font-semibold text-white">Interview complete</h3>
              <p className="mt-2 text-sm text-slate-400">
                Your answers and evaluation evidence have been saved for the recruiter report.
              </p>
              <Link to="/candidate/sessions" className="mt-4 inline-block text-sm font-semibold text-violet-300">
                Back to my sessions
              </Link>
            </Card>
          )}

          {status && <p className="text-sm text-violet-300">{status}</p>}
          {error && <p className="text-sm text-rose-300">{error}</p>}
        </div>
      </div>
    </div>
  )
}
