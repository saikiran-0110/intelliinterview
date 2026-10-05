import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getGapAnalysis } from '../../api/analysis'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { GapAnalysis } from '../../types/analysis'

function MatchList({
  title,
  items,
  tone,
}: {
  title: string
  items: GapAnalysis['strong_matches']
  tone: 'teal' | 'amber' | 'rose'
}) {
  const toneClasses = {
    teal: 'border-teal-200 bg-teal-50 text-teal-700',
    amber: 'border-amber-500/20 bg-amber-500/5 text-amber-200',
    rose: 'border-rose-500/20 bg-rose-500/5 text-rose-200',
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-ink">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">None identified.</p>
      ) : (
        <ul className="mt-4 space-y-2">
          {items.map((item) => (
            <li
              key={`${title}-${item.name}`}
              className={`rounded-xl border px-3 py-2 text-sm ${toneClasses[tone]}`}
            >
              <span className="font-medium capitalize">{item.name}</span>
              {item.match_source === 'semantic' && (
                <span
                  className="ml-2 rounded-full bg-sky-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-sky-700"
                  title={
                    item.similarity != null
                      ? `Matched by passage similarity (${item.similarity.toFixed(2)}), not the keyword catalogue`
                      : 'Matched by passage similarity, not the keyword catalogue'
                  }
                >
                  semantic
                </span>
              )}
              {item.related_cv_skill && (
                <span className="mt-1 block text-xs opacity-80">
                  Related CV skill: {item.related_cv_skill}
                </span>
              )}
              {item.rationale && <span className="mt-1 block text-xs opacity-80">{item.rationale}</span>}
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}

export function GapAnalysisPage() {
  const [searchParams] = useSearchParams()
  const analysisId = searchParams.get('analysisId')

  const [analysis, setAnalysis] = useState<GapAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!analysisId) return

    async function loadAnalysis() {
      setLoading(true)
      setError(null)
      try {
        const result = await getGapAnalysis(analysisId!)
        setAnalysis(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load gap analysis')
      } finally {
        setLoading(false)
      }
    }

    loadAnalysis()
  }, [analysisId])

  if (!analysisId) {
    return (
      <div>
        <PageHeader
          title="Gap Analysis"
          description="Run an analysis from the CV and job specification page to view structured match results here."
        />
        <Card>
          <p className="text-sm text-muted">No analysis selected yet.</p>
          <Link to="/recruiter/analysis" className="mt-4 inline-block text-sm font-semibold text-teal-700">
            Go to CV and job analysis
          </Link>
        </Card>
      </div>
    )
  }

  if (loading) {
    return <p className="text-sm text-muted">Loading gap analysis...</p>
  }

  if (error || !analysis) {
    return (
      <div>
        <PageHeader title="Gap Analysis" description="Structured comparison results." />
        <Card>
          <p className="text-sm text-rose-600">{error ?? 'Analysis not found.'}</p>
          <Link to="/recruiter/analysis" className="mt-4 inline-block text-sm font-semibold text-teal-700">
            Back to analysis
          </Link>
        </Card>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Gap Analysis"
        description={`${analysis.candidate_name} compared against ${analysis.job_title}.`}
        action={
          <div className="rounded-xl border border-border bg-surface-raised px-4 py-2 text-right">
            <p className="text-xs text-slate-500">Match score</p>
            <p className="text-2xl font-bold text-teal-700">{analysis.match_score ?? '-'}%</p>
          </div>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Strong match', value: analysis.strong_match_count, tone: 'text-teal-700' },
          { label: 'Partial match', value: analysis.partial_match_count, tone: 'text-amber-300' },
          { label: 'Gap identified', value: analysis.gap_count, tone: 'text-rose-600' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-border bg-surface-raised p-5 text-center">
            <p className="text-xs uppercase tracking-wider text-slate-500">{stat.label}</p>
            <p className={`mt-2 text-3xl font-bold ${stat.tone}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <MatchList title="Strong matches" items={analysis.strong_matches} tone="teal" />
        <MatchList title="Partial matches" items={analysis.partial_matches} tone="amber" />
        <MatchList title="Gaps to probe" items={analysis.gaps} tone="rose" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold text-ink">Experience alignment</h3>
          <p className="mt-2 text-sm capitalize text-slate-700">
            Alignment: <span className="font-medium text-ink">{analysis.experience_analysis.alignment}</span>
          </p>
          <ul className="mt-4 space-y-2">
            {analysis.experience_analysis.notes.map((note) => (
              <li key={note} className="text-sm text-muted">
                {note}
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-ink">Qualifications</h3>
          <p className="mt-2 text-sm capitalize text-slate-700">
            Alignment:{' '}
            <span className="font-medium text-ink">{analysis.qualifications_analysis.alignment}</span>
          </p>
          <p className="mt-3 text-sm text-muted">
            Matched: {analysis.qualifications_analysis.matched_qualifications.join(', ') || 'None'}
          </p>
          <p className="mt-2 text-sm text-muted">
            Missing: {analysis.qualifications_analysis.missing_qualifications.join(', ') || 'None'}
          </p>
        </Card>
      </div>

      <Card className="mt-6">
        <h3 className="text-lg font-semibold text-ink">Evidence passages</h3>
        <p className="mt-1 text-sm text-muted">CV excerpts linked to matched or missing skills.</p>
        {analysis.evidence_passages.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">No evidence passages available.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {analysis.evidence_passages.map((item) => (
              <div key={`${item.skill}-${item.match_type}`} className="rounded-xl border border-border bg-surface/60 p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                  {item.skill} ({item.match_type})
                </p>
                <p className="mt-2 text-sm text-slate-700">{item.passage}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <h3 className="text-lg font-semibold text-ink">Summary for recruiters</h3>
        <p className="mt-3 text-sm leading-relaxed text-slate-700">{analysis.narrative_summary}</p>
        <Link to={`/recruiter/questions?analysisId=${analysis.id}`} className="mt-5 inline-block text-sm font-semibold text-teal-700">
          Continue to question planning
        </Link>
      </Card>
    </div>
  )
}
