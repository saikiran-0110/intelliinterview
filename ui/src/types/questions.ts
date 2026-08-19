export type QuestionSource = 'AI' | 'RECRUITER'

export type InterviewQuestion = {
  id: string
  plan_id: string
  text: string
  topic: string
  question_type: string
  source: QuestionSource
  skill_ref: string | null
  rationale: string | null
  sort_order: number
  approved: boolean
  created_at: string
}

export type QuestionPlan = {
  id: string
  gap_analysis_id: string
  title: string
  candidate_name: string
  candidate_email?: string | null
  job_title: string
  job_spec_id?: string | null
  cv_id?: string | null
  questions: InterviewQuestion[]
  ai_question_count: number
  recruiter_question_count: number
  approved_count: number
  created_at: string
  updated_at: string
}
