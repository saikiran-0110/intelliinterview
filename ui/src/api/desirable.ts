import { apiRequest } from './client'
import type {
  AnalyticsOverview,
  AppNotification,
  BiasOverview,
  CalendarLinks,
  CandidateFeedback,
  CandidateFeedbackSummary,
  ScheduleItem,
} from '../types/desirable'

export function listScheduleItems() {
  return apiRequest<ScheduleItem[]>('/api/scheduling/sessions')
}

export function proposeSlots(sessionId: string, slotCount = 5, durationMinutes = 45) {
  return apiRequest<ScheduleItem>('/api/scheduling/propose', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      slot_count: slotCount,
      duration_minutes: durationMinutes,
      timezone: 'UTC',
    }),
  })
}

export function forceScheduleSession(
  sessionId: string,
  payload: { starts_at?: string | null; duration_minutes?: number; notify_candidate?: boolean } = {},
) {
  return apiRequest<ScheduleItem>(`/api/scheduling/${sessionId}/force-schedule`, {
    method: 'POST',
    body: JSON.stringify({
      starts_at: payload.starts_at ?? null,
      duration_minutes: payload.duration_minutes ?? 45,
      notify_candidate: payload.notify_candidate ?? true,
    }),
  })
}

export function confirmSlot(sessionId: string, slotId: string, candidateNote?: string) {
  return apiRequest<ScheduleItem>(`/api/scheduling/${sessionId}/confirm`, {
    method: 'POST',
    body: JSON.stringify({ slot_id: slotId, candidate_note: candidateNote || null }),
  })
}

export function requestReschedule(sessionId: string, candidateNote?: string) {
  return apiRequest<ScheduleItem>(`/api/scheduling/${sessionId}/reschedule`, {
    method: 'POST',
    body: JSON.stringify({ candidate_note: candidateNote || null }),
  })
}

export function sendSessionMessage(sessionId: string, candidateNote: string) {
  return apiRequest<ScheduleItem>(`/api/scheduling/${sessionId}/message`, {
    method: 'POST',
    body: JSON.stringify({ candidate_note: candidateNote }),
  })
}

export function getCalendarLinks(sessionId: string) {
  return apiRequest<CalendarLinks>(`/api/scheduling/sessions/${sessionId}/calendar-links`)
}

export function downloadCalendarIcs(sessionId: string) {
  return apiRequest<Blob>(`/api/scheduling/sessions/${sessionId}/calendar.ics`, { raw: true })
}

export function listNotifications() {
  return apiRequest<AppNotification[]>('/api/scheduling/notifications')
}

export function markNotificationRead(notificationId: string) {
  return apiRequest<AppNotification>(`/api/scheduling/notifications/${notificationId}/read`, {
    method: 'POST',
  })
}

export function getAnalyticsOverview() {
  return apiRequest<AnalyticsOverview>('/api/analytics/overview')
}

export function listMyFeedback() {
  return apiRequest<CandidateFeedbackSummary[]>('/api/feedback/me')
}

export function getFeedbackBySession(sessionId: string) {
  return apiRequest<CandidateFeedback>(`/api/feedback/by-session/${sessionId}`)
}

export function getBiasOverview() {
  return apiRequest<BiasOverview>('/api/bias/overview')
}

export function acknowledgeBiasAlert(alertId: string) {
  return apiRequest(`/api/bias/alerts/${alertId}/acknowledge`, { method: 'POST' })
}
