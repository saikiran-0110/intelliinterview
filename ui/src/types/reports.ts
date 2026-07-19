export type HiringRecommendation = 'STRONG_HIRE' | 'HIRE' | 'HOLD' | 'NO_HIRE'

export type EvidenceItem = {
  turn_id: string
  question_text: string | null
  topic: string | null
  answer_excerpt: string | null
  observations: string[]
  evidence_quotes: string[]
  technical_score: number | null
  communication_score: number | null
}

export type InterviewReportSummary = {
  id: string
  session_id: string
  candidate_name: string
  job_title: string
  overall_score: number
  recommendation: HiringRecommendation
  technical_fit_score: number
  communication_score: number
  problem_solving_score: number
  role_alignment_score: number
  generated_at: string
}

export type InterviewReport = {
  id: string
  session_id: string
  candidate_name: string
  candidate_email: string
  job_title: string
  plan_title: string
  technical_fit_score: number
  communication_score: number
  problem_solving_score: number
  role_alignment_score: number
  overall_score: number
  recommendation: HiringRecommendation
  recommendation_summary: string
  strengths: string[]
  weaknesses: string[]
  evidence_items: EvidenceItem[]
  dimension_notes: Record<string, string> | null
  model_version: string | null
  generated_at: string
  created_at: string
}
