import { apiRequest } from './client'
import type { AuthResponse, CandidateCv, GapAnalysis, JobSpecification } from '../types/analysis'

export function login(email: string, password: string) {
  return apiRequest<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function registerRecruiter(email: string, password: string, fullName: string) {
  return apiRequest<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
      role: 'RECRUITER',
    }),
  })
}

export function listCvs() {
  return apiRequest<CandidateCv[]>('/api/cvs')
}

export function uploadCv(candidateName: string, file: File) {
  const formData = new FormData()
  formData.append('candidate_name', candidateName)
  formData.append('file', file)
  return apiRequest<CandidateCv>('/api/cvs/upload', {
    method: 'POST',
    body: formData,
  })
}

export function listJobSpecs() {
  return apiRequest<JobSpecification[]>('/api/job-specs')
}

export function createJobSpec(title: string, description: string) {
  return apiRequest<JobSpecification>('/api/job-specs', {
    method: 'POST',
    body: JSON.stringify({ title, description }),
  })
}

export function uploadJobSpec(title: string, file: File) {
  const formData = new FormData()
  formData.append('title', title)
  formData.append('file', file)
  return apiRequest<JobSpecification>('/api/job-specs/upload', {
    method: 'POST',
    body: formData,
  })
}

export function runGapAnalysis(cvId: string, jobSpecId: string) {
  return apiRequest<GapAnalysis>('/api/analysis/gap', {
    method: 'POST',
    body: JSON.stringify({ cv_id: cvId, job_spec_id: jobSpecId }),
  })
}

export function getGapAnalysis(analysisId: string) {
  return apiRequest<GapAnalysis>(`/api/analysis/gap/${analysisId}`)
}

export function listGapAnalyses() {
  return apiRequest<GapAnalysis[]>('/api/analysis/gap')
}
