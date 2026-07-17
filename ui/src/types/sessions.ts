export type InterviewSessionStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED'
export type TurnRole = 'INTERVIEWER' | 'CANDIDATE'

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
  follow_up_limit: number
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
  candidate_name: string
  candidate_email: string
  job_title: string
  plan_title: string
  current_question_index: number
  total_questions: number
  created_at: string
  started_at: string | null
  completed_at: string | null
}
