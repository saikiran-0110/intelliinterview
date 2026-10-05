export type PipelineStage =
  | 'APPLIED'
  | 'SCREENING'
  | 'SHORTLISTED'
  | 'INTERVIEW'
  | 'OFFER'
  | 'HIRED'
  | 'REJECTED'

export type EmploymentType = 'FULL_TIME' | 'PART_TIME' | 'CONTRACT' | 'INTERNSHIP'
export type WorkMode = 'ONSITE' | 'HYBRID' | 'REMOTE'

export type JobRequisitionInput = {
  title: string
  description: string
  department?: string
  location?: string
  employment_type?: EmploymentType
  work_mode?: WorkMode
  salary_min_gbp?: number | null
  salary_max_gbp?: number | null
  years_experience_min?: number | null
  closing_date?: string | null
  benefits?: string
  is_open?: boolean
}

export type ApplicationContactInput = {
  contact_full_name: string
  contact_email: string
  contact_phone: string
  contact_linkedin?: string
  current_location?: string
  expected_salary_gbp?: number | null
  right_to_work_uk: boolean
  cover_note?: string
}

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
  contact_full_name?: string | null
  contact_email?: string | null
  contact_phone?: string | null
  contact_linkedin?: string | null
  current_location?: string | null
  expected_salary_gbp?: number | null
  right_to_work_uk?: boolean | null
  cover_note?: string | null
  has_completed_interview?: boolean
  created_at: string
  updated_at: string
}

export type MatchPreview = {
  job_spec_id: string
  job_title: string
  cv_id: string
  match_score: number
  strong_matches: string[]
  partial_matches: string[]
  gaps: string[]
  plain_language_breakdown: string
  narrative_summary: string
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
  semantic_skill_names?: string[]
  narrative_summary: string
  plain_language_breakdown: string
}

export type RankingResponse = {
  job_spec_id: string
  job_title: string
  candidates: RankedCandidate[]
}

export type PreparationQuestion = {
  id: string
  question: string
  difficulty: string
  topic: string
  talking_points: string[]
  technical_context: string
}

export type PreparationStudyModule = {
  id: string
  title: string
  summary: string
  technical_details: string
  topic: string
  estimated_minutes: number
}

export type PreparationChecklistItem = {
  id: string
  label: string
  category: string
  technical_hint: string
}

export type PreparationPack = {
  id: string
  job_spec_id: string
  job_title: string
  cv_id: string
  practice_questions: PreparationQuestion[]
  guidance: string
  focus_areas: string[]
  study_modules: PreparationStudyModule[]
  checklist_items: PreparationChecklistItem[]
  completed_item_ids: string[]
  progress_percent: number
  model_version: string | null
  created_at: string
}

export type AssistantResponse = {
  answer: string
  structured: Record<string, unknown>
  tools_used: string[]
}

export type NextActionItem = {
  id: string
  priority: number
  title: string
  detail: string
  cta_label: string | null
  cta_path: string | null
}

export type NextActionsResponse = {
  items: NextActionItem[]
  generated_from: string
}

export type OpenJob = {
  id: string
  title: string
  description: string
  department?: string | null
  location?: string | null
  employment_type?: EmploymentType
  work_mode?: WorkMode
  salary_min_gbp?: number | null
  salary_max_gbp?: number | null
  years_experience_min?: number | null
  closing_date?: string | null
  benefits?: string | null
  is_open: boolean
  created_at: string
}
