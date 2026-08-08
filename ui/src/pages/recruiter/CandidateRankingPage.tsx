import { useEffect, useState } from 'react'
import { listJobSpecs } from '../../api/analysis'
import { rankCandidates, updateApplicationStage } from '../../api/optional'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { JobSpecification } from '../../types/analysis'
import type { RankingResponse } from '../../types/optional'

export function CandidateRankingPage() {
  const [jobs, setJobs] = useState<JobSpecification[]>([])
  const [selectedJobId, setSelectedJobId] = useState('')
  const [ranking, setRanking] = useState<RankingResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)

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

  async function handleRank() {
    if (!selectedJobId) return
    setError(null)
    try {
      const result = await rankCandidates(selectedJobId)
      setRanking(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rank candidates')
    }
  }

  async function handleShortlist(applicationId: string | null) {
    if (!applicationId) return
    try {
      await updateApplicationStage(applicationId, 'SHORTLISTED')
      setStatus('Candidate marked as shortlisted.')
      await handleRank()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to shortlist')
    }
  }

  return (
    <div>
      <PageHeader
        title="Candidate Ranking"
        description="Automatically score applicants against the job description and review a plain-language match breakdown before scheduling interviews."
      />
      {error && <p className="mb-4 text-sm text-rose-300">{error}</p>}
      {status && <p className="mb-4 text-sm text-teal-300">{status}</p>}

      <Card className="mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-[16rem] flex-1">
            <label className="text-xs text-slate-500">Role</label>
            <select
              value={selectedJobId}
              onChange={(e) => setSelectedJobId(e.target.value)}
              className="mt-2 w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm text-slate-100"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={handleRank}
            className="rounded-xl bg-teal-500 px-4 py-2.5 text-sm font-semibold text-ink"
          >
            Rank applicants
          </button>
        </div>
      </Card>

      {ranking && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-white">{ranking.job_title}</h3>
          {ranking.candidates.length === 0 ? (
            <Card>
              <p className="text-sm text-slate-500">No applicants to rank yet.</p>
            </Card>
          ) : (
            ranking.candidates.map((item, index) => (
              <Card key={`${item.cv_id}-${index}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      #{index + 1} {item.candidate_name} · {item.match_score.toFixed(0)}/100
                    </p>
                    <p className="mt-2 text-sm text-slate-300">{item.plain_language_breakdown}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      Strong: {item.strong_matches.join(', ') || 'n/a'} · Gaps:{' '}
                      {item.gaps.join(', ') || 'n/a'}
                    </p>
                  </div>
                  {item.application_id && (
                    <button
                      type="button"
                      onClick={() => handleShortlist(item.application_id)}
                      className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-teal-200"
                    >
                      Shortlist
                    </button>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  )
}
