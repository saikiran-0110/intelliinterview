export type ParsedProfile = {
  skills: string[]
  years_experience: number | null
  seniority: string | null
  qualifications: string[]
}

export type ParsedRequirements = {
  required_skills: string[]
  years_experience_required: number | null
  seniority_required: string | null
  qualifications_required: string[]
}

export type CandidateCv = {
  id: string
  candidate_name: string
  original_filename: string
  extracted_text: string | null
  parsed_profile: ParsedProfile | null
  created_at: string
}

export type JobSpecification = {
  id: string
  title: string
  description: string
  extracted_text: string | null
  parsed_requirements: ParsedRequirements | null
  is_open?: boolean
  created_at: string
}

export type SkillMatchItem = {
  name: string
  category?: string
  related_cv_skill?: string | null
  rationale?: string | null
}

export type EvidencePassage = {
  skill: string
  match_type: string
  passage: string
}

export type ExperienceAnalysis = {
  alignment: string
  cv_years_experience: number | null
  required_years_experience: number | null
  cv_seniority: string | null
  required_seniority: string | null
  notes: string[]
}

export type QualificationsAnalysis = {
  alignment: string
  matched_qualifications: string[]
  missing_qualifications: string[]
  additional_qualifications: string[]
  notes: string[]
}

export type GapAnalysis = {
  id: string
  cv_id: string
  job_spec_id: string
  candidate_name: string
  job_title: string
  strong_match_count: number
  partial_match_count: number
  gap_count: number
  match_score: number | null
  strong_matches: SkillMatchItem[]
  partial_matches: SkillMatchItem[]
  gaps: SkillMatchItem[]
  experience_analysis: ExperienceAnalysis
  qualifications_analysis: QualificationsAnalysis
  evidence_passages: EvidencePassage[]
  narrative_summary: string
  created_at: string
}

export type AuthResponse = {
  user_id: string
  email: string
  full_name: string
  role: 'RECRUITER' | 'CANDIDATE'
  token: string
}
