import { useEffect, useState } from 'react'
import { acknowledgeBiasAlert, getBiasOverview, getOrganisationBias } from '../../api/desirable'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { BiasOverview, OrganisationBias } from '../../types/desirable'

const severityColor: Record<string, string> = {
  LOW: 'text-slate-700 border-slate-500/30',
  MEDIUM: 'text-amber-300 border-amber-500/30',
  HIGH: 'text-rose-600 border-rose-500/30',
}

type Tab = 'mine' | 'organisation'

export function BiasDetectionPage() {
  const [tab, setTab] = useState<Tab>('mine')
  const [data, setData] = useState<BiasOverview | null>(null)
  const [orgData, setOrgData] = useState<OrganisationBias | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const overview = await getBiasOverview()
      setData(overview)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bias overview')
    } finally {
      setLoading(false)
    }
  }

  async function loadOrganisation() {
    setLoading(true)
    try {
      const overview = await getOrganisationBias()
      setOrgData(overview)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load organisation bias overview')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'mine' && !data) load()
    if (tab === 'organisation' && !orgData) loadOrganisation()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  async function handleAcknowledge(alertId: string) {
    try {
      await acknowledgeBiasAlert(alertId)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to acknowledge alert')
    }
  }

  return (
    <div>
      <PageHeader
        title="Bias Detection"
        description="Monitor shortlisting and interview scoring patterns over time. Alerts are advisory and do not use demographic inference from CV text."
      />

      <div className="mb-6 flex gap-2">
        <button
          type="button"
          onClick={() => setTab('mine')}
          className={`min-h-11 rounded-xl border px-4 py-2 text-sm font-semibold ${
            tab === 'mine' ? 'border-teal-400 bg-teal-50 text-teal-900' : 'border-border text-slate-700'
          }`}
        >
          My pipeline
        </button>
        <button
          type="button"
          onClick={() => setTab('organisation')}
          className={`min-h-11 rounded-xl border px-4 py-2 text-sm font-semibold ${
            tab === 'organisation' ? 'border-teal-400 bg-teal-50 text-teal-900' : 'border-border text-slate-700'
          }`}
        >
          Organisation
        </button>
      </div>

      {loading && <p className="text-sm text-muted">Analysing patterns...</p>}
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}

      {tab === 'mine' && data && (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2">
            <Card>
              <p className="text-xs text-slate-500">Total alerts</p>
              <p className="mt-1 text-3xl font-bold text-ink">{data.alert_count}</p>
            </Card>
            <Card>
              <p className="text-xs text-slate-500">Unacknowledged</p>
              <p className="mt-1 text-3xl font-bold text-amber-300">{data.unacknowledged_count}</p>
            </Card>
          </div>

          <Card className="mb-6">
            <h3 className="text-sm font-semibold text-ink">Monitoring notes</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted">
              {data.notes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </Card>

          <div className="space-y-3">
            {data.alerts.map((alert) => (
              <Card key={alert.id} className={`border ${severityColor[alert.severity] || ''}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-slate-500">{alert.severity}</p>
                    <h3 className="mt-1 text-lg font-semibold text-ink">{alert.title}</h3>
                    <p className="mt-2 text-sm text-slate-700">{alert.description}</p>
                    <p className="mt-2 text-xs text-slate-500">
                      Metrics: {JSON.stringify(alert.metric_payload)}
                    </p>
                  </div>
                  {!alert.acknowledged && (
                    <button
                      type="button"
                      onClick={() => handleAcknowledge(alert.id)}
                      className="min-h-11 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-ink hover:border-teal-400/40"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {tab === 'organisation' && orgData && (
        <>
          {orgData.insufficient_sample ? (
            <Card>
              <p className="text-sm font-semibold text-ink">Not enough organisation-wide data yet</p>
              <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-muted">
                {orgData.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </Card>
          ) : (
            <>
              <Card className="mb-6">
                <p className="text-xs text-slate-500">Company</p>
                <p className="mt-1 text-lg font-semibold text-ink">{orgData.company || 'n/a'}</p>
                <p className="mt-1 text-xs text-muted">{orgData.recruiter_count} recruiters in view</p>
              </Card>

              <Card className="mb-6">
                <h3 className="text-sm font-semibold text-ink">Monitoring notes</h3>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted">
                  {orgData.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </Card>

              {orgData.recruiter_figures.length > 0 && (
                <Card className="mb-6">
                  <h3 className="text-sm font-semibold text-ink">Anonymised shortlist rates</h3>
                  <div className="mt-3 space-y-2">
                    {orgData.recruiter_figures.map((figure) => (
                      <div key={figure.label}>
                        <div className="flex items-center justify-between text-xs text-muted">
                          <span>{figure.label}</span>
                          <span>
                            {(figure.shortlist_rate * 100).toFixed(0)}% · {figure.scored_applications} scored
                          </span>
                        </div>
                        <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-200">
                          <div
                            className="h-full rounded-full bg-teal-500"
                            style={{ width: `${Math.min(figure.shortlist_rate * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              <div className="space-y-3">
                {orgData.alerts.map((alert, index) => (
                  <Card key={`${alert.alert_type}-${index}`} className={`border ${severityColor[alert.severity] || ''}`}>
                    <p className="text-xs uppercase tracking-wider text-slate-500">
                      {alert.severity} · {alert.recruiter_label}
                    </p>
                    <h3 className="mt-1 text-lg font-semibold text-ink">{alert.title}</h3>
                    <p className="mt-2 text-sm text-slate-700">{alert.description}</p>
                  </Card>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
