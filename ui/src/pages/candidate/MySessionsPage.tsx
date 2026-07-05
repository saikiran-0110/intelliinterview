import { Link } from 'react-router-dom'
import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function MySessionsPage() {
  return (
    <div>
      <PageHeader
        title="My Interview Sessions"
        description="Access scheduled AI interview sessions assigned by your recruiter. Confirm or reschedule slots when scheduling is enabled."
      />

      <PlaceholderPanel
        title="Session list"
        description="Scheduled, in-progress, and completed sessions."
        items={[
          { label: 'Upcoming session', hint: 'Role ,  Date ,  Confirm / Reschedule' },
          { label: 'Past session', hint: 'Role ,  Date ,  View feedback' },
        ]}
        columns={1}
      />

      <p className="mt-6 text-center">
        <Link
          to="/candidate/interview"
          className="text-sm font-semibold text-violet-400 hover:text-violet-300"
        >
          Open live interview room
        </Link>
      </p>
    </div>
  )
}
