import { Link } from 'react-router-dom'
import { Card } from '../../components/ui/Card'
import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function CandidateDashboard() {
  return (
    <div>
      <PageHeader
        title="Candidate Dashboard"
        description="Your personal hub for scheduled AI interviews, session access, and post-interview feedback."
      />

      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Upcoming', value: '-', color: 'text-violet-300' },
          { label: 'Completed', value: '-', color: 'text-slate-200' },
          { label: 'Applications', value: '-', color: 'text-indigo-300' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-2xl border border-border bg-surface-raised p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">{stat.label}</p>
            <p className={`mt-2 text-3xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="mb-8 grid gap-4 sm:grid-cols-2">
        <Link to="/candidate/sessions">
          <Card hover>
            <p className="font-semibold text-white">My Sessions</p>
            <p className="mt-1 text-sm text-slate-400">View scheduled and past interviews</p>
          </Card>
        </Link>
        <Link to="/candidate/interview">
          <Card hover className="border-violet-500/20">
            <p className="font-semibold text-violet-200">Enter Live Interview</p>
            <p className="mt-1 text-sm text-slate-400">Join your active AI session room</p>
          </Card>
        </Link>
      </div>

      <PlaceholderPanel
        title="Next scheduled interview"
        description="Upcoming session details with role, date, and join link."
        columns={1}
      />
    </div>
  )
}
