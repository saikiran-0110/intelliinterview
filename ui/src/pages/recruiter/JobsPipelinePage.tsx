import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listJobSpecs } from '../../api/analysis'
import {
  aiDraftJobSpec,
  createJobSpec,
  downloadCv,
  formatSalaryGbp,
  listRecruiterApplications,
  setJobVisibility,
  updateApplicationStage,
} from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { JobSpecification } from '../../types/analysis'
import type { ApplicationItem, EmploymentType, PipelineStage, WorkMode } from '../../types/optional'

const stages: PipelineStage[] = [
  'APPLIED',
  'SCREENING',
  'SHORTLISTED',
  'INTERVIEW',
  'OFFER',
  'HIRED',
  'REJECTED',
]

const emptyForm = {
  title: '',
  description: '',
  department: '',
  location: '',
  employment_type: 'FULL_TIME' as EmploymentType,
  work_mode: 'HYBRID' as WorkMode,
  salary_min_gbp: '',
  salary_max_gbp: '',
  years_experience_min: '',
  closing_date: '',
  benefits: '',
}

const inputClass = 'input-field'

export function JobsPipelinePage() {
  const [jobs, setJobs] = useState<JobSpecification[]>([])
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [aiPrompt, setAiPrompt] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  async function load(jobId?: string) {
    try {
      const [jobItems, appItems] = await Promise.all([
        listJobSpecs(),
        listRecruiterApplications(jobId || undefined),
      ])
      setJobs(jobItems)
      setApps(appItems)
      if (!selectedJobId && jobItems[0]) setSelectedJobId(jobItems[0].id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs pipeline')
    }
  }

  useEffect(() => {
    load()
  }, [])

  function updateField<K extends keyof typeof emptyForm>(key: K, value: (typeof emptyForm)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleAiDraft() {
    if (aiPrompt.trim().length < 10) {
      setError('Add a short hiring brief (at least 10 characters) for AI drafting.')
      return
    }
    setError(null)
    setAiLoading(true)
    try {
      const draft = await aiDraftJobSpec(aiPrompt.trim())
      setForm({
        title: draft.title || '',
        description: draft.description || '',
        department: draft.department || '',
        location: draft.location || '',
        employment_type: draft.employment_type || 'FULL_TIME',
        work_mode: draft.work_mode || 'HYBRID',
        salary_min_gbp: draft.salary_min_gbp != null ? String(Math.round(draft.salary_min_gbp)) : '',
        salary_max_gbp: draft.salary_max_gbp != null ? String(Math.round(draft.salary_max_gbp)) : '',
        years_experience_min:
          draft.years_experience_min != null ? String(draft.years_experience_min) : '',
        closing_date: '',
        benefits: draft.benefits || '',
      })
      setStatus(
        draft.model_version === 'baseline'
          ? 'Draft filled from your brief. Review and publish when ready.'
          : `AI enhanced draft ready (${draft.model_version}). Review and publish when ready.`,
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI drafting failed')
    } finally {
      setAiLoading(false)
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await createJobSpec({
        title: form.title,
        description: form.description,
        department: form.department || undefined,
        location: form.location || undefined,
        employment_type: form.employment_type,
        work_mode: form.work_mode,
        salary_min_gbp: form.salary_min_gbp ? Number(form.salary_min_gbp) : null,
        salary_max_gbp: form.salary_max_gbp ? Number(form.salary_max_gbp) : null,
        years_experience_min: form.years_experience_min ? Number(form.years_experience_min) : null,
        closing_date: form.closing_date || null,
        benefits: form.benefits || undefined,
        is_open: true,
      })
      setForm(emptyForm)
      setAiPrompt('')
      setStatus('Recruitment request published and open for applications.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post role')
    }
  }

  async function handleStage(appId: string, stage: PipelineStage) {
    try {
      await updateApplicationStage(appId, stage)
      if (stage === 'SHORTLISTED') {
        setStatus('Candidate shortlisted and interview session prepared. Next: propose slots on Scheduling.')
      }
      await load(selectedJobId || undefined)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update stage')
    }
  }

  async function handleDownload(cvId: string, filename: string) {
    try {
      const blob = await downloadCv(cvId)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename || 'candidate-cv'
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download CV')
    }
  }

  const filtered = selectedJobId ? apps.filter((item) => item.job_spec_id === selectedJobId) : apps

  return (
    <div>
      <PageHeader
        title="Hiring Board"
        description="Start here: publish open roles with salary in £, then manage applicants through your hiring stages."
      />
      <div className="animate-fade-up-delay-1 mb-6 grid gap-2 sm:grid-cols-4">
        {[
          { label: '1. Open role', to: null },
          { label: '2. Rank applicants', to: '/recruiter/ranking' },
          { label: '3. Shortlist', to: '/recruiter/ranking' },
          { label: '4. Schedule interview', to: '/recruiter/scheduling' },
        ].map((step) =>
          step.to ? (
            <Link
              key={step.label}
              to={step.to}
              className="rounded-xl border border-teal-200 bg-teal-100/80 px-3 py-2 text-xs font-semibold text-teal-900 hover:bg-teal-200/80"
            >
              {step.label}
            </Link>
          ) : (
            <div
              key={step.label}
              className="rounded-xl border border-teal-200 bg-teal-100/80 px-3 py-2 text-xs font-semibold text-teal-900"
            >
              {step.label}
            </div>
          ),
        )}
      </div>
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && (
        <p className="mb-4 text-sm text-teal-700">
          {status}
          {status.includes('Scheduling') && (
            <>
              {' '}
              <Link to="/recruiter/scheduling" className="font-semibold underline">
                Open Scheduling
              </Link>
            </>
          )}
        </p>
      )}

      <div className="mb-6 grid gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-ink">Open recruitment request</h3>

          <div className="mt-3 rounded-2xl border border-teal-200 bg-teal-50/60 p-4">
            <p className="text-sm font-bold text-teal-900">AI help</p>
            <p className="mt-1 text-sm text-muted">
              Describe the role in plain language. AI fills title, salary (£), location, description, and benefits.
            </p>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              placeholder="Example: Senior backend engineer in London, hybrid, 5+ years Python/FastAPI, £75k–£95k, fintech experience preferred"
              rows={3}
              className={`mt-3 ${inputClass}`}
            />
            <button
              type="button"
              onClick={handleAiDraft}
              disabled={aiLoading}
              className="btn-primary mt-3 disabled:opacity-60"
            >
              {aiLoading ? 'Drafting with AI...' : 'Enhance & fill form with AI'}
            </button>
          </div>

          <form className="mt-5 space-y-3" onSubmit={handleCreate}>
            <input
              value={form.title}
              onChange={(e) => updateField('title', e.target.value)}
              placeholder="Role title"
              className={inputClass}
              required
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <input
                value={form.department}
                onChange={(e) => updateField('department', e.target.value)}
                placeholder="Department (e.g. Engineering)"
                className={inputClass}
              />
              <input
                value={form.location}
                onChange={(e) => updateField('location', e.target.value)}
                placeholder="Location (e.g. London, UK)"
                className={inputClass}
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <select
                value={form.employment_type}
                onChange={(e) => updateField('employment_type', e.target.value as EmploymentType)}
                className={inputClass}
              >
                <option value="FULL_TIME">Full time</option>
                <option value="PART_TIME">Part time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERNSHIP">Internship</option>
              </select>
              <select
                value={form.work_mode}
                onChange={(e) => updateField('work_mode', e.target.value as WorkMode)}
                className={inputClass}
              >
                <option value="HYBRID">Hybrid</option>
                <option value="ONSITE">On-site</option>
                <option value="REMOTE">Remote</option>
              </select>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <input
                type="number"
                min={0}
                step={1000}
                value={form.salary_min_gbp}
                onChange={(e) => updateField('salary_min_gbp', e.target.value)}
                placeholder="Min salary (£)"
                className={inputClass}
                required
              />
              <input
                type="number"
                min={0}
                step={1000}
                value={form.salary_max_gbp}
                onChange={(e) => updateField('salary_max_gbp', e.target.value)}
                placeholder="Max salary (£)"
                className={inputClass}
                required
              />
              <input
                type="number"
                min={0}
                value={form.years_experience_min}
                onChange={(e) => updateField('years_experience_min', e.target.value)}
                placeholder="Min years exp."
                className={inputClass}
              />
            </div>
            <input
              type="date"
              value={form.closing_date}
              onChange={(e) => updateField('closing_date', e.target.value)}
              className={inputClass}
              aria-label="Application closing date"
            />
            <p className="-mt-1 text-xs text-muted">
              Application closing date (optional) — last day candidates can apply
            </p>
            <textarea
              value={form.description}
              onChange={(e) => updateField('description', e.target.value)}
              placeholder="Job description and requirements"
              rows={5}
              className={inputClass}
              required
            />
            <textarea
              value={form.benefits}
              onChange={(e) => updateField('benefits', e.target.value)}
              placeholder="Benefits (pension, bonus, remote days, etc.)"
              rows={2}
              className={inputClass}
            />
            <button type="submit" className="rounded-xl btn-primary">
              Publish recruitment request
            </button>
          </form>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-ink">Open roles</h3>
          <div className="mt-3 space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="rounded-xl border border-border p-3">
                <div className="flex items-start justify-between gap-2">
                  <button
                    type="button"
                    className="text-left"
                    onClick={() => {
                      setSelectedJobId(job.id)
                      load(job.id)
                    }}
                  >
                    <p className="text-sm font-medium text-ink">{job.title}</p>
                    <p className="mt-1 text-xs text-muted">
                      {[job.location, job.department, job.employment_type?.replaceAll('_', ' ')]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    <p className="mt-1 text-xs text-teal-700">
                      {formatSalaryGbp(job.salary_min_gbp, job.salary_max_gbp)}
                    </p>
                  </button>
                  <button
                    type="button"
                    className="text-xs text-teal-700"
                    onClick={async () => {
                      await setJobVisibility(job.id, !(job.is_open ?? true))
                      await load(selectedJobId || undefined)
                    }}
                  >
                    {(job.is_open ?? true) ? 'Open' : 'Closed'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-ink">Applications</h3>
        <div className="mt-4 space-y-3">
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-500">No applications for this filter.</p>
          ) : (
            filtered.map((app) => (
              <div key={app.id} className="rounded-xl border border-border bg-surface/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-ink">
                      {app.candidate_name} · {app.job_title}
                    </p>
                    <p className="mt-1 text-xs text-muted">
                      {app.contact_email || app.candidate_email}
                      {app.contact_phone ? ` · ${app.contact_phone}` : ''}
                      {app.match_score != null ? ` · Match ${app.match_score.toFixed(0)}/100` : ''}
                      {app.expected_salary_gbp != null
                        ? ` · Expects ${formatSalaryGbp(app.expected_salary_gbp, null)}`
                        : ''}
                    </p>
                    {app.current_location && (
                      <p className="mt-1 text-xs text-slate-500">Location: {app.current_location}</p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <select
                      value={app.stage}
                      onChange={(e) => handleStage(app.id, e.target.value as PipelineStage)}
                      className="rounded-lg border border-border bg-white px-2 py-1 text-xs text-ink"
                    >
                      {stages.map((stage) => (
                        <option key={stage} value={stage}>
                          {stage}
                        </option>
                      ))}
                    </select>
                    {app.cv_id && (
                      <button
                        type="button"
                        onClick={() => handleDownload(app.cv_id!, `${app.candidate_name}-cv`)}
                        className="rounded-lg border border-border px-3 py-1 text-xs text-teal-700"
                      >
                        Download CV
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
