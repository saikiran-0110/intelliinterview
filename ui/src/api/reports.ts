import { apiRequest } from './client'
import type { InterviewReport, InterviewReportSummary } from '../types/reports'

export function listReports() {
  return apiRequest<InterviewReportSummary[]>('/api/reports')
}

export function getReport(reportId: string) {
  return apiRequest<InterviewReport>(`/api/reports/${reportId}`)
}

export function getReportBySession(sessionId: string) {
  return apiRequest<InterviewReport>(`/api/reports/by-session/${sessionId}`)
}

export function generateReport(sessionId: string) {
  return apiRequest<InterviewReport>(`/api/reports/generate/${sessionId}`, {
    method: 'POST',
  })
}
