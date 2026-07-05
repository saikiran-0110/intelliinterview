import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'
import { StatCard } from '../../components/ui/StatCard'

const quickActions = [
  { label: 'Upload CV & job spec', path: '/recruiter/analysis', tone: 'brand' as const },
  { label: 'Review gap analysis', path: '/recruiter/gap-analysis', tone: 'default' as const },
  { label: 'Plan interview questions', path: '/recruiter/questions', tone: 'default' as const },
  { label: 'Start new session', path: '/recruiter/sessions/new', tone: 'accent' as const },
]

export function RecruiterDashboard() {
  return (
    <div>
      <PageHeader
        title="Recruiter Dashboard"
        description="Central hub for uploading documents, preparing interviews, launching AI sessions, and reviewing structured evaluation reports."
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Open sessions" value="-" change="Placeholder" tone="brand" />
        <StatCard label="Completed reports" value="-" change="Placeholder" />
        <StatCard label="CVs analysed" value="-" change="Placeholder" />
        <StatCard label="Active roles" value="-" change="Placeholder" tone="accent" />
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {quickActions.map((action) => (
          <Link key={action.path} to={action.path}>
            <Card hover className="h-full">
              <p className="text-sm font-semibold text-white">{action.label}</p>
              <p className="mt-2 text-xs text-slate-500">Go to page </p>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Recent interview sessions"
          description="Sessions created from CV and job-spec analysis."
          items={[
            { label: 'Session slot', hint: 'Candidate ,  Role ,  Status' },
            { label: 'Session slot', hint: 'Candidate ,  Role ,  Status' },
            { label: 'Session slot', hint: 'Candidate ,  Role ,  Status' },
          ]}
          columns={1}
        />
        <PlaceholderPanel
          title="Latest evaluation reports"
          description="Structured post-interview assessments with scores and evidence."
          items={[
            { label: 'Report slot', hint: 'Technical fit ,  Recommendation' },
            { label: 'Report slot', hint: 'Communication ,  Strengths' },
          ]}
          columns={1}
        />
      </div>
    </div>
  )
}
