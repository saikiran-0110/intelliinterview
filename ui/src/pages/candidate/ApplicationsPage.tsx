import { useEffect, useState } from 'react'
import { applyForJob, listMyApplications, listMyCvs, listOpenJobs } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateCv } from '../../types/analysis'
import type { ApplicationItem, OpenJob } from '../../types/optional'

export function ApplicationsPage() {
  const [jobs, setJobs] = useState<OpenJob[]>([])
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [cvs, setCvs] = useState<CandidateCv[]>([])
  const [selectedCv, setSelectedCv] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

  async function load() {
    try {
      const [openJobs, myApps, myCvs] = await Promise.all([
        listOpenJobs(),
        listMyApplications(),
        listMyCvs(),
      ])
      setJobs(openJobs)
      setApps(myApps)
      setCvs(myCvs)
      if (!selectedCv && myCvs[0]) setSelectedCv(myCvs[0].id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleApply(jobId: string) {
    setError(null)
    try {
      await applyForJob(jobId, selectedCv || undefined)
      setStatus('Application submitted.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply')
    }
  }

  const appliedIds = new Set(apps.map((item) => item.job_spec_id))

  return (
    <div>
      <PageHeader
        title="Applications"
        description="Browse open software roles, apply with your uploaded CV, and track application status."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-violet-300">{status}</p>}

      <Card className="mb-6">
        <label className="text-xs text-slate-500">CV for new applications</label>
        <select
          value={selectedCv}
          onChange={(e) => setSelectedCv(e.target.value)}
          className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
        >
          <option value="">Latest CV</option>
          {cvs.map((cv) => (
            <option key={cv.id} value={cv.id}>
              {cv.original_filename}
            </option>
          ))}
        </select>
      </Card>

      <div className="mb-8 grid gap-4 lg:grid-cols-2">
        {jobs.map((job) => (
          <Card key={job.id}>
            <h3 className="text-lg font-semibold text-white">{job.title}</h3>
            <p className="mt-2 line-clamp-4 text-sm text-slate-400">{job.description}</p>
            {appliedIds.has(job.id) ? (
              <p className="mt-4 text-xs font-semibold text-teal-300">Already applied</p>
            ) : (
              <button
                type="button"
                onClick={() => handleApply(job.id)}
                className="mt-4 rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white"
              >
                Apply
              </button>
            )}
          </Card>
        ))}
      </div>

      <Card>
        <h3 className="text-lg font-semibold text-white">My application status</h3>
        <div className="mt-4 space-y-3">
          {apps.length === 0 ? (
            <p className="text-sm text-slate-500">No applications yet.</p>
          ) : (
            apps.map((app) => (
              <div key={app.id} className="rounded-xl border border-border bg-surface/60 p-3">
                <p className="font-medium text-white">{app.job_title}</p>
                <p className="mt-1 text-xs text-slate-400">
                  Stage: {app.stage.replaceAll('_', ' ')}
                  {app.match_score != null ? ` · Match ${app.match_score.toFixed(0)}/100` : ''}
                </p>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}
