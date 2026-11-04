export type InterviewSessionStatus =
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'DISQUALIFIED'

export type ProctoringEventKind =
  | 'LOOKING_AWAY'
  | 'PROHIBITED_OBJECT'
  | 'NO_FACE_DETECTED'
  | 'MULTIPLE_PEOPLE'

export type ProctoringCheckResponse = {
  violation: boolean
  kind: ProctoringEventKind | null
  detail: string
  warning_count: number
  warning_limit: number
  disqualified: boolean
  session_status: InterviewSessionStatus
}
export type ScheduleConfirmationStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'RESCHEDULE_REQUESTED'
  | 'DECLINED'
export type TurnRole = 'INTERVIEWER' | 'CANDIDATE'

export type InterviewLanguage = 'en-GB' | 'en-US' | 'es-ES' | 'fr-FR' | 'de-DE' | 'hi-IN' | 'zh-CN'

export const INTERVIEW_LANGUAGES: { value: InterviewLanguage; label: string }[] = [
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'en-US', label: 'English (US)' },
  { value: 'es-ES', label: 'Spanish' },
  { value: 'fr-FR', label: 'French' },
  { value: 'de-DE', label: 'German' },
  { value: 'hi-IN', label: 'Hindi' },
  { value: 'zh-CN', label: 'Chinese (Simplified)' },
]

export type TurnEvaluation = {
  technical_score: number | null
  communication_score: number | null
  observations: string[]
  evidence_quotes: string[]
  strengths: string[]
  weaknesses: string[]
  should_follow_up: boolean
  follow_up_question: string | null
  advance_question: boolean
  model_version: string | null
}

export type InterviewTurn = {
  id: string
  sequence: number
  role: TurnRole
  content: string
  plan_question_id: string | null
  is_follow_up: boolean
  follow_up_index: number
  created_at: string
  evaluation: TurnEvaluation | null
}

export type SessionProgress = {
  index: number
  total: number
  question_id: string | null
  question_text: string | null
  topic: string | null
}

export type InterviewSession = {
  id: string
  question_plan_id: string
  gap_analysis_id: string
  cv_id: string
  job_spec_id: string
  recruiter_id: string
  candidate_user_id: string
  candidate_name: string
  candidate_email: string
  job_title: string
  plan_title: string
  status: InterviewSessionStatus
  confirmation_status: ScheduleConfirmationStatus
  follow_up_limit: number
  duration_minutes?: number
  language?: InterviewLanguage
  proctoring_warning_count: number
  current_question_index: number
  current_follow_up_count: number
  current_plan_question_id: string | null
  progress: SessionProgress
  turns: InterviewTurn[]
  scheduled_at: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export type SessionSummary = {
  id: string
  status: InterviewSessionStatus
  confirmation_status: ScheduleConfirmationStatus
  candidate_name: string
  candidate_email: string
  job_title: string
  plan_title: string
  current_question_index: number
  total_questions: number
  duration_minutes?: number
  language?: InterviewLanguage
  created_at: string
  started_at: string | null
  completed_at: string | null
  scheduled_at?: string | null
}
