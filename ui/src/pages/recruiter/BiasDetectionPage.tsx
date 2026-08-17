import { useEffect, useState } from 'react'
import { acknowledgeBiasAlert, getBiasOverview } from '../../api/desirable'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import type { BiasOverview } from '../../types/desirable'

const severityColor: Record<string, string> = {
  LOW: 'text-slate-700 border-slate-500/30',
  MEDIUM: 'text-amber-300 border-amber-500/30',
  HIGH: 'text-rose-600 border-rose-500/30',
}

export function BiasDetectionPage() {
  const [data, setData] = useState<BiasOverview | null>(null)
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

  useEffect(() => {
    load()
  }, [])

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

      {loading && <p className="text-sm text-muted">Analysing patterns...</p>}
      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}

      {data && (
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
                      className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-ink hover:border-teal-400/40"
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
    </div>
  )
}
