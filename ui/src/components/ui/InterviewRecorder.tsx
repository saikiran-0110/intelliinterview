import { useEffect, useRef, useState } from 'react'
import { deleteRecording, uploadRecording } from '../../api/sessions'

type Props = {
  sessionId: string
  /** Interview is actively in progress: recording should be capturing while this is true. */
  active: boolean
  /** Interview has finished: stop capture and upload. */
  completed: boolean
}

function isRecordingSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    'MediaRecorder' in window &&
    Boolean(navigator.mediaDevices?.getUserMedia)
  )
}

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === 'undefined' || !MediaRecorder.isTypeSupported) return undefined
  for (const type of ['video/webm;codecs=vp8,opus', 'video/webm']) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return undefined
}

/**
 * Opt-in, candidate-side interview recording. Never required to complete an interview:
 * every failure path (unsupported browser, denied permission, upload error) just disables
 * the feature and lets the interview continue normally. The recording is for human review
 * only - it is never sent to any model, and the AI evaluation reads typed/transcribed
 * answers only.
 */
export function InterviewRecorder({ sessionId, active, completed }: Props) {
  const supported = useRef(isRecordingSupported()).current
  const [enabled, setEnabled] = useState(false)
  const [permissionDenied, setPermissionDenied] = useState(false)
  const [recording, setRecording] = useState(false)
  const [uploadState, setUploadState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const startedAtRef = useRef<number | null>(null)
  const uploadedRef = useRef(false)

  function stopStream() {
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
  }

  async function startCapture() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      streamRef.current = stream
      if (videoRef.current) videoRef.current.srcObject = stream

      const mimeType = pickMimeType()
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => {
        void finishAndUpload(recorder.mimeType || 'video/webm')
      }
      recorderRef.current = recorder
      startedAtRef.current = Date.now()
      uploadedRef.current = false
      recorder.start()
      setRecording(true)
      setPermissionDenied(false)
    } catch {
      setPermissionDenied(true)
      setEnabled(false)
      stopStream()
    }
  }

  function stopCapture() {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop()
    } else {
      stopStream()
    }
    setRecording(false)
  }

  async function finishAndUpload(mimeType: string) {
    stopStream()
    if (uploadedRef.current || chunksRef.current.length === 0) return
    uploadedRef.current = true

    const blob = new Blob(chunksRef.current, { type: mimeType })
    const durationSeconds = startedAtRef.current ? (Date.now() - startedAtRef.current) / 1000 : undefined
    setUploadState('uploading')
    setUploadMessage('Uploading your recording...')
    try {
      await uploadRecording(sessionId, blob, durationSeconds)
      setUploadState('success')
      setUploadMessage('Recording uploaded for your recruiter to review.')
    } catch (err) {
      setUploadState('error')
      setUploadMessage(err instanceof Error ? err.message : 'Failed to upload recording.')
    }
  }

  useEffect(() => {
    if (enabled && active && !recording && uploadState === 'idle') {
      void startCapture()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, active])

  useEffect(() => {
    if (completed && recording) {
      stopCapture()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [completed])

  useEffect(() => stopStream, [])

  async function handleDelete() {
    try {
      await deleteRecording(sessionId)
      setUploadState('idle')
      setUploadMessage('Recording deleted.')
    } catch (err) {
      setUploadMessage(err instanceof Error ? err.message : 'Failed to delete recording.')
    }
  }

  if (!supported) {
    return (
      <p className="text-xs text-amber-700">
        Recording is not supported in this browser. The interview will proceed normally without it.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <label className="flex min-h-11 items-center gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          disabled={completed}
          className="h-5 w-5 shrink-0 rounded border-border"
        />
        Record this interview
      </label>
      <p className="text-xs text-muted">
        Off by default. If enabled, your camera and microphone are captured for the length of the
        interview and shared with your recruiter for human review only - it is not used in scoring,
        and you can complete the interview without it. A visible indicator shows whenever capture is
        active, and you can delete your recording afterwards.
      </p>
      {permissionDenied && (
        <p className="text-xs text-amber-700">
          Camera/microphone permission was denied, so recording is off. The interview will proceed
          normally.
        </p>
      )}
      {recording && (
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-full bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-rose-600" />
            Recording
          </span>
          <video ref={videoRef} autoPlay muted playsInline className="h-16 w-24 rounded-lg bg-black object-cover" />
        </div>
      )}
      {uploadMessage && (
        <p className={`text-xs ${uploadState === 'error' ? 'text-rose-600' : 'text-sky-700'}`}>
          {uploadMessage}
        </p>
      )}
      {uploadState === 'success' && (
        <button
          type="button"
          onClick={handleDelete}
          className="min-h-11 text-xs font-semibold text-rose-600"
        >
          Delete my recording
        </button>
      )}
    </div>
  )
}
