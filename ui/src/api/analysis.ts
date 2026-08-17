import { apiRequest } from './client'
import type {
  AuthResponse,
  CandidateCv,
  GapAnalysis,
  JobSpecification,
  OtpStartResponse,
  RegisterProfileInput,
} from '../types/analysis'

export function startRegister(role: 'RECRUITER' | 'CANDIDATE', profile: RegisterProfileInput) {
  return apiRequest<OtpStartResponse>('/api/auth/register/start', {
    method: 'POST',
    body: JSON.stringify({ ...profile, role }),
  })
}

export function startLogin(email: string) {
  return apiRequest<OtpStartResponse>('/api/auth/login/start', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export function verifyOtp(email: string, otp: string, purpose: 'REGISTER' | 'LOGIN') {
  return apiRequest<AuthResponse>('/api/auth/otp/verify', {
    method: 'POST',
    body: JSON.stringify({ email, otp, purpose }),
  })
}

/** Legacy helpers retained for older screens/tests */
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

export function registerCandidate(email: string, password: string, fullName: string) {
  return apiRequest<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
      role: 'CANDIDATE',
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

export function listGapAnalyses() {
  return apiRequest<GapAnalysis[]>('/api/analysis/gap')
}

export function getGapAnalysis(analysisId: string) {
  return apiRequest<GapAnalysis>(`/api/analysis/gap/${analysisId}`)
}
