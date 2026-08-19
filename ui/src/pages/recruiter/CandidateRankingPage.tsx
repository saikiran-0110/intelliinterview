import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listJobSpecs } from '../../api/analysis'
import { listRecruiterApplications, rankCandidates, updateApplicationStage } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { JobSpecification } from '../../types/analysis'
import type { ApplicationItem, RankingResponse } from '../../types/optional'

export function CandidateRankingPage() {
  const [jobs, setJobs] = useState<JobSpecification[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [ranking, setRanking] = useState<RankingResponse | null>(null)
  const [shortlisted, setShortlisted] = useState<ApplicationItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => {
    async function loadJobs() {
      try {
        const items = await listJobSpecs()
        setJobs(items)
        if (items[0]) setSelectedJobId(items[0].id)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load roles')
      }
    }
    loadJobs()
  }, [])

  async function refreshShortlisted(jobId: string) {
    const apps = await listRecruiterApplications(jobId)
    setShortlisted(
      apps.filter((item) => item.stage === 'SHORTLISTED' || item.stage === 'INTERVIEW'),
    )
  }

  async function handleRank() {
    if (!selectedJobId) return
    setError(null)
    try {
      const result = await rankCandidates(selectedJobId)
      setRanking(result)
      await refreshShortlisted(selectedJobId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rank candidates')
    }
  }

  async function handleShortlist(applicationId: string | null) {
    if (!applicationId) return
    setBusyId(applicationId)
    setError(null)
    try {
      await updateApplicationStage(applicationId, 'SHORTLISTED')
      setStatus('Candidate shortlisted. Next: generate questions, then create an interview session.')
      await handleRank()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to shortlist')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Candidate Ranking"
        description="Score applicants still awaiting a decision. After shortlisting, plan questions before creating an interview session."
      />
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}
      {status && (
        <p className="mb-4 text-sm text-teal-700">
          {status}{' '}
          <Link to="/recruiter/questions" className="font-semibold underline">
            Go to Question Planning
          </Link>
        </p>
      )}

      <Card className="mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-[16rem] flex-1">
            <label className="text-xs text-slate-500">Role</label>
            <select
              value={selectedJobId}
              onChange={(e) => {
                setSelectedJobId(e.target.value)
                setRanking(null)
                setShortlisted([])
                setStatus(null)
              }}
              className="mt-2 input-field"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
          </div>
          <button type="button" onClick={handleRank} className="rounded-xl btn-primary">
            Rank applicants
          </button>
        </div>
      </Card>

      {ranking && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-ink">Ready to shortlist · {ranking.job_title}</h3>
          {ranking.candidates.length === 0 ? (
            <Card>
              <p className="text-sm text-slate-500">
                No applicants waiting for a shortlist decision. Already shortlisted candidates appear below
                and on Scheduling.
              </p>
            </Card>
          ) : (
            ranking.candidates.map((item, index) => (
              <Card key={`${item.cv_id}-${index}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-ink">
                      #{index + 1} {item.candidate_name} · {item.match_score.toFixed(0)}/100
                    </p>
                    <p className="mt-1 text-xs text-muted">Stage: {item.stage || 'APPLIED'}</p>
                    <p className="mt-2 text-sm text-slate-700">{item.plain_language_breakdown}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      Strong: {item.strong_matches.join(', ') || 'n/a'} · Gaps:{' '}
                      {item.gaps.join(', ') || 'n/a'}
                    </p>
                  </div>
                  {item.application_id && (
                    <button
                      type="button"
                      disabled={busyId === item.application_id}
                      onClick={() => handleShortlist(item.application_id)}
                      className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-teal-700 disabled:opacity-50"
                    >
                      {busyId === item.application_id ? 'Shortlisting…' : 'Shortlist'}
                    </button>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {shortlisted.length > 0 && (
        <div className="mt-8 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-lg font-semibold text-ink">Already shortlisted</h3>
            <Link to="/recruiter/questions" className="text-sm font-semibold text-sky-700">
              Plan questions →
            </Link>
          </div>
          {shortlisted.map((item) => (
            <Card key={item.id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{item.candidate_name}</p>
                  <p className="mt-1 text-xs text-muted">
                    {item.stage.replaceAll('_', ' ')}
                    {item.match_score != null ? ` · Match ${item.match_score.toFixed(0)}/100` : ''}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link
                    to={
                      item.gap_analysis_id
                        ? `/recruiter/questions?analysisId=${item.gap_analysis_id}`
                        : '/recruiter/questions'
                    }
                    className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-sky-800"
                  >
                    Plan questions
                  </Link>
                  <Link
                    to="/recruiter/sessions/new"
                    className="rounded-lg bg-teal-50 px-2.5 py-1 text-xs font-semibold text-teal-800"
                  >
                    Create session
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
