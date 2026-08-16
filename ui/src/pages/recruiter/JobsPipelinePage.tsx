import { type FormEvent, useEffect, useState } from 'react'
import { listJobSpecs } from '../../api/analysis'
import {
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

const inputClass =
  'w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100'

export function JobsPipelinePage() {
  const [jobs, setJobs] = useState<JobSpecification[]>([])
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [form, setForm] = useState(emptyForm)
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
      setStatus('Recruitment request published and open for applications.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to post role')
    }
  }

  async function handleStage(appId: string, stage: PipelineStage) {
    try {
      await updateApplicationStage(appId, stage)
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
        title="Jobs & Pipeline"
        description="Open a recruitment request with salary and role details, then manage applicants through the hiring pipeline."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-300">{status}</p>}

      <div className="mb-6 grid gap-6 xl:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-white">Open recruitment request</h3>
          <form className="mt-3 space-y-3" onSubmit={handleCreate}>
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
            />
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
            <button type="submit" className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-ink">
              Publish recruitment request
            </button>
          </form>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white">Open roles</h3>
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
                    <p className="text-sm font-medium text-white">{job.title}</p>
                    <p className="mt-1 text-xs text-slate-400">
                      {[job.location, job.department, job.employment_type?.replaceAll('_', ' ')]
                        .filter(Boolean)
                        .join(' · ')}
                    </p>
                    <p className="mt-1 text-xs text-teal-300">
                      {formatSalaryGbp(job.salary_min_gbp, job.salary_max_gbp)}
                    </p>
                  </button>
                  <button
                    type="button"
                    className="text-xs text-teal-300"
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
        <h3 className="text-lg font-semibold text-white">Applications</h3>
        <div className="mt-4 space-y-3">
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-500">No applications for this filter.</p>
          ) : (
            filtered.map((app) => (
              <div key={app.id} className="rounded-xl border border-border bg-surface/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-white">
                      {app.candidate_name} · {app.job_title}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
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
                      className="rounded-lg border border-border bg-surface px-2 py-1 text-xs text-slate-100"
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
                        className="rounded-lg border border-border px-3 py-1 text-xs text-teal-200"
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
