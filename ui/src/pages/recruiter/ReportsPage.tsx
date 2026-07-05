import { Link } from 'react-router-dom'
import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function ReportsPage() {
  return (
    <div>
      <PageHeader
        title="Evaluation Reports"
        description="Detailed post-interview assessments covering technical fit, communication, problem-solving, and role alignment with evidence-linked observations."
      />

      <PlaceholderPanel
        title="Completed reports"
        description="Browse and filter reports by candidate, role, date, and recommendation."
        items={[
          { label: 'Report card', hint: 'Scores ,  Recommendation ,  View detail' },
          { label: 'Report card', hint: 'Scores ,  Recommendation ,  View detail' },
          { label: 'Report card', hint: 'Scores ,  Recommendation ,  View detail' },
        ]}
        columns={3}
      />

      <p className="mt-4 text-center text-sm text-slate-500">
        <Link to="/recruiter/reports/sample" className="text-teal-400 hover:text-teal-300">
          View sample report
        </Link>
      </p>
    </div>
  )
}
