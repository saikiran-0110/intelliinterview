import { type FormEvent, useEffect, useState } from 'react'
import { getStoredUser } from '../../api/client'
import {
  applyForJob,
  formatSalaryGbp,
  listMyApplications,
  listMyCvs,
  listOpenJobs,
  previewJobMatch,
  uploadMyCv,
} from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { CandidateCv } from '../../types/analysis'
import type { ApplicationItem, MatchPreview, OpenJob } from '../../types/optional'

const inputClass =
  'w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100'

export function ApplicationsPage() {
  const stored = getStoredUser()
  const [jobs, setJobs] = useState<OpenJob[]>([])
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [cvs, setCvs] = useState<CandidateCv[]>([])
  const [selectedCv, setSelectedCv] = useState('')
  const [selectedJobId, setSelectedJobId] = useState('')
  const [matchPreview, setMatchPreview] = useState<MatchPreview | null>(null)
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [contactName, setContactName] = useState(stored?.full_name || '')
  const [contactEmail, setContactEmail] = useState(stored?.email || '')
  const [contactPhone, setContactPhone] = useState('')
  const [contactLinkedin, setContactLinkedin] = useState('')
  const [currentLocation, setCurrentLocation] = useState('')
  const [expectedSalary, setExpectedSalary] = useState('')
  const [rightToWork, setRightToWork] = useState(true)
  const [coverNote, setCoverNote] = useState('')
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
      if (!selectedJobId && openJobs[0]) setSelectedJobId(openJobs[0].id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load applications')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleUpload(event: FormEvent) {
    event.preventDefault()
    if (!resumeFile) return
    setError(null)
    try {
      const cv = await uploadMyCv(resumeFile, contactName || stored?.full_name)
      setSelectedCv(cv.id)
      setResumeFile(null)
      setStatus('Resume uploaded. Check your match against an open role below.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload resume')
    }
  }

  async function handleMatch() {
    if (!selectedJobId) return
    setError(null)
    try {
      const preview = await previewJobMatch(selectedJobId, selectedCv || undefined)
      setMatchPreview(preview)
      setStatus(`Match score for ${preview.job_title}: ${preview.match_score.toFixed(0)}/100`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check match')
    }
  }

  async function handleApply(event: FormEvent) {
    event.preventDefault()
    if (!selectedJobId) return
    setError(null)
    try {
      await applyForJob(
        selectedJobId,
        {
          contact_full_name: contactName,
          contact_email: contactEmail,
          contact_phone: contactPhone,
          contact_linkedin: contactLinkedin || undefined,
          current_location: currentLocation || undefined,
          expected_salary_gbp: expectedSalary ? Number(expectedSalary) : null,
          right_to_work_uk: rightToWork,
          cover_note: coverNote || undefined,
        },
        selectedCv || undefined,
      )
      setStatus('Application submitted with your contact details.')
      setCoverNote('')
      setMatchPreview(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply')
    }
  }

  const appliedIds = new Set(apps.map((item) => item.job_spec_id))
  const selectedJob = jobs.find((job) => job.id === selectedJobId)

  return (
    <div>
      <PageHeader
        title="Applications"
        description="Upload your resume, check how well you match an open role, then apply with your contact details."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-violet-300">{status}</p>}

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-white">1. Upload resume</h3>
          <form className="mt-3 space-y-3" onSubmit={handleUpload}>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-300"
              required
            />
            <button type="submit" className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-white">
              Upload resume
            </button>
          </form>
          <label className="mt-4 block text-xs text-slate-500">Resume for matching and applications</label>
          <select
            value={selectedCv}
            onChange={(e) => setSelectedCv(e.target.value)}
            className={`mt-2 ${inputClass}`}
          >
            <option value="">Latest resume</option>
            {cvs.map((cv) => (
              <option key={cv.id} value={cv.id}>
                {cv.original_filename}
              </option>
            ))}
          </select>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white">2. Check role match</h3>
          <div className="mt-3 space-y-3">
            <select
              value={selectedJobId}
              onChange={(e) => {
                setSelectedJobId(e.target.value)
                setMatchPreview(null)
              }}
              className={inputClass}
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
            {selectedJob && (
              <p className="text-xs text-slate-400">
                {[selectedJob.location, selectedJob.work_mode, formatSalaryGbp(selectedJob.salary_min_gbp, selectedJob.salary_max_gbp)]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
            )}
            <button
              type="button"
              onClick={handleMatch}
              className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-violet-200"
            >
              Check match with my resume
            </button>
            {matchPreview && (
              <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 p-3 text-sm text-slate-300">
                <p className="font-semibold text-white">
                  Match {matchPreview.match_score.toFixed(0)}/100 · {matchPreview.job_title}
                </p>
                <p className="mt-2">{matchPreview.plain_language_breakdown}</p>
                <p className="mt-2 text-xs text-slate-500">
                  Strong: {matchPreview.strong_matches.join(', ') || 'n/a'} · Gaps:{' '}
                  {matchPreview.gaps.join(', ') || 'n/a'}
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card className="mb-8">
        <h3 className="text-lg font-semibold text-white">3. Apply with contact details</h3>
        <form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={handleApply}>
          <input
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            placeholder="Full name"
            className={inputClass}
            required
          />
          <input
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            placeholder="Contact email"
            className={inputClass}
            required
          />
          <input
            value={contactPhone}
            onChange={(e) => setContactPhone(e.target.value)}
            placeholder="Phone number"
            className={inputClass}
            required
          />
          <input
            value={currentLocation}
            onChange={(e) => setCurrentLocation(e.target.value)}
            placeholder="Current location"
            className={inputClass}
          />
          <input
            value={contactLinkedin}
            onChange={(e) => setContactLinkedin(e.target.value)}
            placeholder="LinkedIn URL (optional)"
            className={inputClass}
          />
          <input
            type="number"
            min={0}
            step={1000}
            value={expectedSalary}
            onChange={(e) => setExpectedSalary(e.target.value)}
            placeholder="Expected salary (£)"
            className={inputClass}
          />
          <label className="flex items-center gap-2 text-sm text-slate-300 sm:col-span-2">
            <input
              type="checkbox"
              checked={rightToWork}
              onChange={(e) => setRightToWork(e.target.checked)}
            />
            I have the right to work in the UK
          </label>
          <textarea
            value={coverNote}
            onChange={(e) => setCoverNote(e.target.value)}
            placeholder="Short cover note (optional)"
            rows={3}
            className={`${inputClass} sm:col-span-2`}
          />
          <div className="sm:col-span-2">
            {selectedJobId && appliedIds.has(selectedJobId) ? (
              <p className="text-sm font-semibold text-teal-300">Already applied for this role</p>
            ) : (
              <button
                type="submit"
                className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white"
              >
                Submit application
              </button>
            )}
          </div>
        </form>
      </Card>

      <div className="mb-8 grid gap-4 lg:grid-cols-2">
        {jobs.map((job) => (
          <Card key={job.id}>
            <h3 className="text-lg font-semibold text-white">{job.title}</h3>
            <p className="mt-1 text-xs text-teal-300">
              {formatSalaryGbp(job.salary_min_gbp, job.salary_max_gbp)}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {[job.location, job.employment_type?.replaceAll('_', ' '), job.work_mode]
                .filter(Boolean)
                .join(' · ')}
            </p>
            <p className="mt-2 line-clamp-4 text-sm text-slate-400">{job.description}</p>
            {appliedIds.has(job.id) ? (
              <p className="mt-4 text-xs font-semibold text-teal-300">Already applied</p>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setSelectedJobId(job.id)
                  setMatchPreview(null)
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
                className="mt-4 rounded-xl border border-border px-4 py-2 text-sm text-violet-200"
              >
                Select to match & apply
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
