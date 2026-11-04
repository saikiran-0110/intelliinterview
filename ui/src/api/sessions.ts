import { apiRequest } from './client'
import type { InterviewSession, ProctoringCheckResponse, SessionSummary } from '../types/sessions'

export function createSession(questionPlanId: string, candidateEmail: string, followUpLimit = 1, language?: string) {
  return apiRequest<InterviewSession>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({
      question_plan_id: questionPlanId,
      candidate_email: candidateEmail,
      follow_up_limit: followUpLimit,
      ...(language ? { language } : {}),
    }),
  })
}

export function listSessions() {
  return apiRequest<SessionSummary[]>('/api/sessions')
}

export function getSession(sessionId: string) {
  return apiRequest<InterviewSession>(`/api/sessions/${sessionId}`)
}

export function startSession(sessionId: string) {
  return apiRequest<InterviewSession>(`/api/sessions/${sessionId}/start`, {
    method: 'POST',
  })
}

export function submitAnswer(sessionId: string, answer: string) {
  return apiRequest<InterviewSession>(`/api/sessions/${sessionId}/answer`, {
    method: 'POST',
    body: JSON.stringify({ answer }),
  })
}

export function uploadRecording(sessionId: string, blob: Blob, durationSeconds?: number) {
  const formData = new FormData()
  const extension = blob.type.includes('mp4') ? 'mp4' : 'webm'
  formData.append('file', blob, `interview.${extension}`)
  if (durationSeconds != null) formData.append('duration_seconds', String(Math.round(durationSeconds)))
  return apiRequest(`/api/sessions/${sessionId}/recording`, { method: 'POST', body: formData })
}

export function getRecordingBlob(sessionId: string) {
  return apiRequest<Blob>(`/api/sessions/${sessionId}/recording`, { raw: true })
}

export function checkProctoringFrame(sessionId: string, blob: Blob) {
  const formData = new FormData()
  formData.append('frame', blob, 'frame.jpg')
  return apiRequest<ProctoringCheckResponse>(`/api/sessions/${sessionId}/proctoring-check`, {
    method: 'POST',
    body: formData,
  })
}
