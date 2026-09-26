export type ScheduleConfirmationStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'RESCHEDULE_REQUESTED'
  | 'DECLINED'

export type SlotSuggestion = {
  id: string
  session_id: string
  starts_at: string
  ends_at: string
  is_selected: boolean
  created_at: string
}

export type ScheduleItem = {
  session_id: string
  candidate_name: string
  candidate_email: string
  job_title: string
  confirmation_status: ScheduleConfirmationStatus
  scheduled_at: string | null
  duration_minutes: number
  timezone: string
  candidate_note: string | null
  slots: SlotSuggestion[]
}

export type CalendarLinks = {
  google_url: string
  outlook_url: string
  ics_url: string
}

export type AppNotification = {
  id: string
  title: string
  body: string
  link: string | null
  channel: 'IN_APP' | 'EMAIL'
  is_read: boolean
  email_sent: boolean
  related_session_id: string | null
  created_at: string
}

export type AnalyticsOverview = {
  total_roles: number
  total_applications: number
  total_sessions: number
  completed_reports: number
  applications_per_role: { job_title: string; count: number }[]
  pipeline_stages: { stage: string; count: number }[]
  open_positions: {
    job_spec_id: string
    job_title: string
    applications: number
    interviews: number
    completed_interviews: number
    hired: number
    progress_percent: number
  }[]
}

export type CandidateFeedbackSummary = {
  id: string
  session_id: string
  job_title: string
  summary: string
  created_at: string
}

export type CandidateFeedback = {
  id: string
  session_id: string
  job_title: string
  summary: string
  strong_answers: string[]
  improvement_areas: string[]
  focus_tips: string[]
  model_version: string | null
  created_at: string
}

export type BiasAlert = {
  id: string
  alert_type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH'
  title: string
  description: string
  metric_payload: Record<string, unknown>
  acknowledged: boolean
  acknowledged_at: string | null
  created_at: string
}

export type BiasOverview = {
  alert_count: number
  unacknowledged_count: number
  alerts: BiasAlert[]
  notes: string[]
}
