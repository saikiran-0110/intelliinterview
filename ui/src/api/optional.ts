import { apiRequest } from './client'
import type {
  ApplicationContactInput,
  ApplicationItem,
  AssistantResponse,
  EmploymentType,
  JobRequisitionInput,
  MatchPreview,
  NextActionsResponse,
  OpenJob,
  PipelineStage,
  PreparationPack,
  RankingResponse,
  WorkMode,
} from '../types/optional'
import type { CandidateCv, JobSpecification } from '../types/analysis'

export function listOpenJobs() {
  return apiRequest<OpenJob[]>('/api/job-specs/open')
}

export function listMyCvs() {
  return apiRequest<CandidateCv[]>('/api/cvs')
}

export function uploadMyCv(file: File, candidateName?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (candidateName) formData.append('candidate_name', candidateName)
  return apiRequest<CandidateCv>('/api/cvs/upload', { method: 'POST', body: formData })
}

export function downloadCv(cvId: string) {
  return apiRequest<Blob>(`/api/cvs/${cvId}/download`, { raw: true })
}

export function deleteMyCv(cvId: string) {
  return apiRequest<void>(`/api/cvs/${cvId}`, { method: 'DELETE' })
}

export function updateProfile(payload: {
  full_name: string
  phone?: string
  company?: string
  job_title?: string
  location?: string
  linkedin_url?: string
}) {
  return apiRequest('/api/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function listMyApplications() {
  return apiRequest<ApplicationItem[]>('/api/applications/me')
}

export function listRecruiterApplications(jobSpecId?: string) {
  const suffix = jobSpecId ? `?job_spec_id=${jobSpecId}` : ''
  return apiRequest<ApplicationItem[]>(`/api/applications${suffix}`)
}

export function previewJobMatch(jobSpecId: string, cvId?: string) {
  return apiRequest<MatchPreview>('/api/applications/match-preview', {
    method: 'POST',
    body: JSON.stringify({ job_spec_id: jobSpecId, cv_id: cvId || null }),
  })
}

export function applyForJob(jobSpecId: string, contact: ApplicationContactInput, cvId?: string) {
  return apiRequest<ApplicationItem>('/api/applications', {
    method: 'POST',
    body: JSON.stringify({
      job_spec_id: jobSpecId,
      cv_id: cvId || null,
      ...contact,
    }),
  })
}

export function updateApplicationStage(applicationId: string, stage: PipelineStage, notes?: string) {
  return apiRequest<ApplicationItem>(`/api/applications/${applicationId}/stage`, {
    method: 'PATCH',
    body: JSON.stringify({ stage, notes: notes || null }),
  })
}

export function setJobVisibility(jobSpecId: string, isOpen: boolean) {
  return apiRequest<JobSpecification>(`/api/job-specs/${jobSpecId}/visibility`, {
    method: 'PATCH',
    body: JSON.stringify({ is_open: isOpen }),
  })
}

export function createJobSpec(input: JobRequisitionInput) {
  return apiRequest<JobSpecification>('/api/job-specs', {
    method: 'POST',
    body: JSON.stringify({
      is_open: true,
      employment_type: 'FULL_TIME',
      work_mode: 'HYBRID',
      ...input,
    }),
  })
}

export type JobAiDraft = {
  title: string
  description: string
  department?: string | null
  location?: string | null
  employment_type: EmploymentType
  work_mode: WorkMode
  salary_min_gbp?: number | null
  salary_max_gbp?: number | null
  years_experience_min?: number | null
  benefits?: string | null
  model_version?: string | null
}

export function aiDraftJobSpec(prompt: string) {
  return apiRequest<JobAiDraft>('/api/job-specs/ai-draft', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
}

export function rankCandidates(jobSpecId: string) {
  return apiRequest<RankingResponse>(`/api/ranking/${jobSpecId}`)
}

export function listPreparation() {
  return apiRequest<PreparationPack[]>('/api/preparation/me')
}

export function generatePreparation(jobSpecId: string, cvId?: string) {
  return apiRequest<PreparationPack>('/api/preparation/generate', {
    method: 'POST',
    body: JSON.stringify({ job_spec_id: jobSpecId, cv_id: cvId || null }),
  })
}

export function updatePreparationProgress(packId: string, itemId: string, completed: boolean) {
  return apiRequest<PreparationPack>(`/api/preparation/${packId}/progress`, {
    method: 'PATCH',
    body: JSON.stringify({ item_id: itemId, completed }),
  })
}

export function deletePreparationPack(packId: string) {
  return apiRequest<void>(`/api/preparation/${packId}`, { method: 'DELETE' })
}

export function queryAssistant(message: string) {
  return apiRequest<AssistantResponse>('/api/assistant/query', {
    method: 'POST',
    body: JSON.stringify({ message }),
  })
}

export function getNextActions() {
  return apiRequest<NextActionsResponse>('/api/assistant/next-actions')
}

export function formatSalaryGbp(min?: number | null, max?: number | null) {
  const fmt = (value: number) =>
    new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      maximumFractionDigits: 0,
    }).format(value)
  if (min != null && max != null) return `${fmt(min)} – ${fmt(max)}`
  if (min != null) return `From ${fmt(min)}`
  if (max != null) return `Up to ${fmt(max)}`
  return 'Salary on request'
}
