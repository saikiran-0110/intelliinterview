import { type FormEvent, useEffect, useState } from 'react'
import { listJobSpecs } from '../../api/analysis'
import {
  createJobSpec,
  downloadCv,
  listRecruiterApplications,
  setJobVisibility,
  updateApplicationStage,
} from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { JobSpecification } from '../../types/analysis'
import type { ApplicationItem, PipelineStage } from '../../types/optional'

const stages: PipelineStage[] = [
  'APPLIED',
  'SCREENING',
  'SHORTLISTED',
  'INTERVIEW',
  'OFFER',
  'HIRED',
  'REJECTED',
]

export function JobsPipelinePage() {
  const [jobs, setJobs] = useState<JobSpecification[]>([])
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
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

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await createJobSpec(title, description, true)
      setTitle('')
      setDescription('')
      setStatus('Role posted and open for applications.')
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
        description="Post software roles, review applications, update pipeline stages, and download candidate CVs."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-300">{status}</p>}

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-white">Post a role</h3>
          <form className="mt-3 space-y-3" onSubmit={handleCreate}>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Role title"
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
              required
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Job description"
              rows={5}
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
              required
            />
            <button type="submit" className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-ink">
              Publish role
            </button>
          </form>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white">Open roles</h3>
          <div className="mt-3 space-y-2">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between gap-2 rounded-xl border border-border p-3">
                <button
                  type="button"
                  className="text-left text-sm text-white"
                  onClick={() => {
                    setSelectedJobId(job.id)
                    load(job.id)
                  }}
                >
                  {job.title}
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
                      {app.candidate_email}
                      {app.match_score != null ? ` · Match ${app.match_score.toFixed(0)}/100` : ''}
                    </p>
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
