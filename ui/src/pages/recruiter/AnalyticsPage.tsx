import { useEffect, useState } from 'react'
import { getAnalyticsOverview } from '../../api/desirable'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { StatCard } from '../../components/ui/StatCard'
import type { AnalyticsOverview } from '../../types/desirable'

export function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const overview = await getAnalyticsOverview()
        setData(overview)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div>
      <PageHeader
        title="Recruitment Analytics"
        description="Visual summary of hiring activity: applications per role, candidates at each pipeline stage, and open position progress."
      />

      {loading && <p className="text-sm text-muted">Loading analytics...</p>}
      {error && <p className="text-sm text-rose-600">{error}</p>}

      {data && (
        <>
          <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Open roles" value={String(data.total_roles)} tone="brand" />
            <StatCard label="Applications" value={String(data.total_applications)} />
            <StatCard label="Interview sessions" value={String(data.total_sessions)} />
            <StatCard label="Completed reports" value={String(data.completed_reports)} tone="accent" />
          </div>

          <div className="mb-6 grid gap-6 lg:grid-cols-2">
            <Card>
              <h3 className="text-lg font-semibold text-ink">Applications per role</h3>
              <div className="mt-4 space-y-3">
                {data.applications_per_role.length === 0 ? (
                  <p className="text-sm text-slate-500">No roles yet.</p>
                ) : (
                  data.applications_per_role.map((item) => (
                    <div key={item.job_title}>
                      <div className="mb-1 flex justify-between text-sm">
                        <span className="text-slate-700">{item.job_title}</span>
                        <span className="text-teal-700">{item.count}</span>
                      </div>
                      <div className="h-2 rounded-full bg-surface">
                        <div
                          className="h-2 rounded-full bg-teal-500"
                          style={{
                            width: `${Math.min(100, item.count * 20 || 4)}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            <Card>
              <h3 className="text-lg font-semibold text-ink">Pipeline stages</h3>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {data.pipeline_stages.map((item) => (
                  <div key={item.stage} className="rounded-xl border border-border bg-surface/60 p-3">
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      {item.stage.replaceAll('_', ' ')}
                    </p>
                    <p className="mt-1 text-2xl font-bold text-ink">{item.count}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card>
            <h3 className="text-lg font-semibold text-ink">Open positions progress</h3>
            <div className="mt-4 space-y-4">
              {data.open_positions.length === 0 ? (
                <p className="text-sm text-slate-500">No open positions.</p>
              ) : (
                data.open_positions.map((item) => (
                  <div key={item.job_spec_id}>
                    <div className="mb-1 flex flex-wrap items-center justify-between gap-2 text-sm">
                      <span className="font-medium text-ink">{item.job_title}</span>
                      <span className="text-xs text-slate-500">
                        Apps {item.applications} · Interviews {item.interviews} · Done{' '}
                        {item.completed_interviews} · Hired {item.hired}
                      </span>
                    </div>
                    <div className="h-2.5 rounded-full bg-surface">
                      <div
                        className="h-2.5 rounded-full bg-sky-600"
                        style={{ width: `${item.progress_percent}%` }}
                      />
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{item.progress_percent}% progress</p>
                  </div>
                ))
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
