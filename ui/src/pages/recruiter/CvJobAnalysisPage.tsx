import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createJobSpec,
  listCvs,
  listJobSpecs,
  runGapAnalysis,
  uploadCv,
  uploadJobSpec,
} from '../../api/analysis'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateCv, JobSpecification } from '../../types/analysis'

type JobMode = 'existing' | 'text' | 'file'

export function CvJobAnalysisPage() {
  const navigate = useNavigate()

  const [cvs, setCvs] = useState<CandidateCv[]>([])
  const [jobSpecs, setJobSpecs] = useState<JobSpecification[]>([])
  const [selectedCvId, setSelectedCvId] = useState('')
  const [selectedJobSpecId, setSelectedJobSpecId] = useState('')

  const [candidateName, setCandidateName] = useState('')
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [uploadedCv, setUploadedCv] = useState<CandidateCv | null>(null)

  const [jobMode, setJobMode] = useState<JobMode>('text')
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState(
    `We are hiring a senior full stack engineer.

Requirements:
- 5+ years of software engineering experience
- Strong Python and FastAPI backend development
- React and TypeScript frontend experience
- PostgreSQL and Docker in production
- Kubernetes and system design knowledge
- Bachelor's degree in Computer Science`,
  )
  const [jobFile, setJobFile] = useState<File | null>(null)
  const [createdJobSpec, setCreatedJobSpec] = useState<JobSpecification | null>(null)

  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function loadData() {
      try {
        const [cvList, jobList] = await Promise.all([listCvs(), listJobSpecs()])
        setCvs(cvList)
        setJobSpecs(jobList)
        if (cvList[0]) setSelectedCvId(cvList[0].id)
        if (jobList[0]) setSelectedJobSpecId(jobList[0].id)
      } catch {
        // Fresh account may have no records yet.
      }
    }
    loadData()
  }, [])

  async function handleCvUpload() {
    if (!cvFile || !candidateName.trim()) {
      setError('Enter a candidate name and choose a CV file.')
      return
    }

    setLoading(true)
    setError(null)
    setStatus('Uploading CV and extracting text with Apache Tika...')

    try {
      const cv = await uploadCv(candidateName.trim(), cvFile)
      setUploadedCv(cv)
      setSelectedCvId(cv.id)
      setCvs((current) => [cv, ...current.filter((item) => item.id !== cv.id)])
      setStatus('CV uploaded and parsed successfully.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'CV upload failed')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleJobSpecSave() {
    setLoading(true)
    setError(null)
    setStatus('Saving job specification and extracting requirements...')

    try {
      let jobSpec: JobSpecification
      if (jobMode === 'file') {
        if (!jobFile || !jobTitle.trim()) {
          throw new Error('Enter a job title and choose a job specification file.')
        }
        jobSpec = await uploadJobSpec(jobTitle.trim(), jobFile)
      } else if (jobMode === 'text') {
        if (!jobTitle.trim() || !jobDescription.trim()) {
          throw new Error('Enter a job title and description.')
        }
        jobSpec = await createJobSpec(jobTitle.trim(), jobDescription.trim())
      } else {
        setStatus('Using selected existing job specification.')
        setLoading(false)
        return
      }

      setCreatedJobSpec(jobSpec)
      setSelectedJobSpecId(jobSpec.id)
      setJobSpecs((current) => [jobSpec, ...current.filter((item) => item.id !== jobSpec.id)])
      setStatus('Job specification saved and parsed successfully.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Job specification save failed')
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleRunAnalysis() {
    const cvId = uploadedCv?.id ?? selectedCvId
    const jobSpecId = createdJobSpec?.id ?? selectedJobSpecId

    if (!cvId || !jobSpecId) {
      setError('Select or upload both a CV and a job specification before running analysis.')
      return
    }

    setLoading(true)
    setError(null)
    setStatus('Comparing CV against job specification and building gap analysis...')

    try {
      const analysis = await runGapAnalysis(cvId, jobSpecId)
      navigate(`/recruiter/gap-analysis?analysisId=${analysis.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Gap analysis failed')
      setStatus(null)
      setLoading(false)
    }
  }

  const activeCv = uploadedCv ?? cvs.find((cv) => cv.id === selectedCvId) ?? null
  const activeJobSpec = createdJobSpec ?? jobSpecs.find((spec) => spec.id === selectedJobSpecId) ?? null

  return (
    <div>
      <PageHeader
        title="CV and Job Specification Analysis"
        description="Upload a candidate CV and job specification, extract skills, experience, and qualifications, then run a structured gap analysis."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-ink">Upload candidate CV</h3>
          <p className="mt-1 text-sm text-muted">Supported formats: PDF, DOCX, DOC, TXT</p>

          <div className="mt-4 space-y-3">
            <input
              type="text"
              value={candidateName}
              onChange={(e) => setCandidateName(e.target.value)}
              placeholder="Candidate name"
              className="input-field"
            />
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => setCvFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-slate-700 file:mr-4 file:rounded-lg file:border-0 file:bg-teal-500 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950"
            />
            <button
              type="button"
              onClick={handleCvUpload}
              disabled={loading}
              className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400 disabled:opacity-50"
            >
              Upload and parse CV
            </button>
          </div>

          {cvs.length > 0 && (
            <div className="mt-5">
              <label className="mb-1.5 block text-xs font-medium text-slate-500">Or select an existing CV</label>
              <select
                value={selectedCvId}
                onChange={(e) => {
                  setSelectedCvId(e.target.value)
                  setUploadedCv(null)
                }}
                className="input-field"
              >
                {cvs.map((cv) => (
                  <option key={cv.id} value={cv.id}>
                    {cv.candidate_name} ({cv.original_filename})
                  </option>
                ))}
              </select>
            </div>
          )}

          {activeCv?.parsed_profile && (
            <div className="mt-5 rounded-xl border border-border bg-surface/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Extracted profile</p>
              <p className="mt-2 text-sm text-slate-700">
                <span className="font-medium text-ink">Skills:</span>{' '}
                {activeCv.parsed_profile.skills.join(', ') || 'None detected'}
              </p>
              <p className="mt-2 text-sm text-slate-700">
                <span className="font-medium text-ink">Experience:</span>{' '}
                {activeCv.parsed_profile.years_experience ?? 'Not detected'} years
                {activeCv.parsed_profile.seniority ? ` (${activeCv.parsed_profile.seniority})` : ''}
              </p>
              <p className="mt-2 text-sm text-slate-700">
                <span className="font-medium text-ink">Qualifications:</span>{' '}
                {activeCv.parsed_profile.qualifications.join(', ') || 'None detected'}
              </p>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-ink">Job specification</h3>
          <p className="mt-1 text-sm text-muted">Create a new role or select an existing job specification.</p>

          <div className="mt-4 flex flex-wrap gap-2">
            {(['text', 'file', 'existing'] as JobMode[]).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setJobMode(mode)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                  jobMode === mode
                    ? 'bg-indigo-500/20 text-indigo-200 ring-1 ring-indigo-500/30'
                    : 'bg-surface text-muted ring-1 ring-border'
                }`}
              >
                {mode === 'text' ? 'Paste description' : mode === 'file' ? 'Upload file' : 'Use existing'}
              </button>
            ))}
          </div>

          {jobMode === 'existing' ? (
            <div className="mt-4">
              <select
                value={selectedJobSpecId}
                onChange={(e) => {
                  setSelectedJobSpecId(e.target.value)
                  setCreatedJobSpec(null)
                }}
                className="input-field"
              >
                {jobSpecs.length === 0 ? (
                  <option value="">No saved job specifications yet</option>
                ) : (
                  jobSpecs.map((spec) => (
                    <option key={spec.id} value={spec.id}>
                      {spec.title}
                    </option>
                  ))
                )}
              </select>
            </div>
          ) : (
            <div className="mt-4 space-y-3">
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="Job title"
                className="input-field"
              />
              {jobMode === 'text' ? (
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={10}
                  className="input-field"
                />
              ) : (
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(e) => setJobFile(e.target.files?.[0] ?? null)}
                  className="w-full text-sm text-slate-700 file:mr-4 file:rounded-lg file:border-0 file:bg-indigo-500 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
                />
              )}
              <button
                type="button"
                onClick={handleJobSpecSave}
                disabled={loading}
                className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-ink hover:bg-surface-overlay disabled:opacity-50"
              >
                Save job specification
              </button>
            </div>
          )}

          {activeJobSpec?.parsed_requirements && (
            <div className="mt-5 rounded-xl border border-border bg-surface/60 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Parsed requirements</p>
              <p className="mt-2 text-sm text-slate-700">
                <span className="font-medium text-ink">Required skills:</span>{' '}
                {activeJobSpec.parsed_requirements.required_skills.join(', ') || 'None detected'}
              </p>
              <p className="mt-2 text-sm text-slate-700">
                <span className="font-medium text-ink">Experience:</span>{' '}
                {activeJobSpec.parsed_requirements.years_experience_required ?? 'Not specified'} years
                {activeJobSpec.parsed_requirements.seniority_required
                  ? ` (${activeJobSpec.parsed_requirements.seniority_required})`
                  : ''}
              </p>
            </div>
          )}
        </Card>
      </div>

      <Card className="mt-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-ink">Run gap analysis</h3>
            <p className="mt-1 text-sm text-muted">
              Compare the selected CV and job specification to identify strong matches, partial matches, and gaps.
            </p>
          </div>
          <button
            type="button"
            onClick={handleRunAnalysis}
            disabled={loading}
            className="rounded-xl bg-teal-500 px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-teal-400 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Run gap analysis'}
          </button>
        </div>

        {status && <p className="mt-4 text-sm text-teal-700">{status}</p>}
        {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
      </Card>
    </div>
  )
}
