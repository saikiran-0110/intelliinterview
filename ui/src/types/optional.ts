export type PipelineStage =
  | 'APPLIED'
  | 'SCREENING'
  | 'SHORTLISTED'
  | 'INTERVIEW'
  | 'OFFER'
  | 'HIRED'
  | 'REJECTED'

export type ApplicationItem = {
  id: string
  job_spec_id: string
  job_title: string
  candidate_user_id: string
  candidate_name: string
  candidate_email: string
  cv_id: string | null
  gap_analysis_id: string | null
  recruiter_id: string
  stage: PipelineStage
  match_score: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export type RankedCandidate = {
  application_id: string | null
  candidate_user_id: string | null
  candidate_name: string
  candidate_email: string | null
  cv_id: string
  gap_analysis_id: string | null
  match_score: number
  stage: PipelineStage | null
  strong_matches: string[]
  partial_matches: string[]
  gaps: string[]
  narrative_summary: string
  plain_language_breakdown: string
}

export type RankingResponse = {
  job_spec_id: string
  job_title: string
  candidates: RankedCandidate[]
}

export type PreparationPack = {
  id: string
  job_spec_id: string
  job_title: string
  cv_id: string
  practice_questions: string[]
  guidance: string
  focus_areas: string[]
  model_version: string | null
  created_at: string
}

export type AssistantResponse = {
  answer: string
  structured: Record<string, unknown>
  tools_used: string[]
}

export type OpenJob = {
  id: string
  title: string
  description: string
  is_open: boolean
  created_at: string
}
