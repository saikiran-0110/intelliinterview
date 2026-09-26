import { apiRequest } from './client'
import type { InterviewSession, SessionSummary } from '../types/sessions'

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
