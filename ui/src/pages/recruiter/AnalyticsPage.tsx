import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'
import { StatCard } from '../../components/ui/StatCard'

export function AnalyticsPage() {
  return (
    <div>
      <PageHeader
        title="Recruitment Analytics"
        description="Visual summary of hiring activity - applications per role, candidates at each pipeline stage, and progress of open positions."
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Applications received" value="-" tone="brand" />
        <StatCard label="Interviews completed" value="-" />
        <StatCard label="Open positions" value="-" tone="accent" />
        <StatCard label="Avg. time to hire" value="-" tone="warning" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Applications per role"
          description="Bar chart of application volume by job specification."
          columns={1}
        />
        <PlaceholderPanel
          title="Pipeline stage breakdown"
          description="Funnel view: Applied  Shortlisted  Interviewed  Offered."
          columns={1}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Open position progress"
          description="Timeline and status of each active recruitment."
          columns={1}
        />
      </div>
    </div>
  )
}
