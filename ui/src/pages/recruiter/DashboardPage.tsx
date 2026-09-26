import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAnalyticsOverview } from '../../api/desirable'
import { Card } from '../../components/ui/Card'
import { NextActionsPanel } from '../../components/ui/NextActionsPanel'
import { PageHeader } from '../../components/ui/PageHeader'
import { StatCard } from '../../components/ui/StatCard'
import type { AnalyticsOverview } from '../../types/desirable'

const QUICK_LINKS = [
  { label: 'Hiring Board', description: 'Open roles and manage applicants', path: '/recruiter/jobs' },
  { label: 'Candidate Ranking', description: 'Match scores and shortlisting', path: '/recruiter/ranking' },
  { label: 'Question Planning', description: 'Build and approve interview questions', path: '/recruiter/questions' },
  { label: 'Scheduling', description: 'Propose and confirm interview slots', path: '/recruiter/scheduling' },
] as const

export function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const overview = await getAnalyticsOverview()
        setAnalytics(overview)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics')
      }
    }
    load()
  }, [])

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Your hiring pipeline at a glance: what needs attention, and where to go next."
      />

      {error && <p className="mb-4 text-sm text-rose-600">{error}</p>}

      <NextActionsPanel />

      {analytics && (
        <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Open roles" value={String(analytics.total_roles)} tone="brand" />
          <StatCard label="Applications" value={String(analytics.total_applications)} />
          <StatCard label="Interview sessions" value={String(analytics.total_sessions)} />
          <StatCard label="Completed reports" value={String(analytics.completed_reports)} tone="accent" />
        </div>
      )}

      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-ink">Quick links</h3>
        <Link to="/recruiter/analytics" className="text-sm font-semibold text-teal-700">
          View full analytics →
        </Link>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {QUICK_LINKS.map((link) => (
          <Link key={link.path} to={link.path}>
            <Card hover>
              <p className="font-semibold text-ink">{link.label}</p>
              <p className="mt-1 text-sm text-muted">{link.description}</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
