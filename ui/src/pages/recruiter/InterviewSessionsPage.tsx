import { Link } from 'react-router-dom'
import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function InterviewSessionsPage() {
  return (
    <div>
      <PageHeader
        title="Interview Sessions"
        description="Create, schedule, and monitor AI-conducted interview sessions. The agent follows the approved question plan with bounded follow-ups."
        action={
          <Link
            to="/recruiter/sessions/new"
            className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400"
          >
            New session
          </Link>
        }
      />

      <PlaceholderPanel
        title="Session list"
        description="All sessions with status: Scheduled, In Progress, Completed, Cancelled."
        items={[
          { label: 'Session row', hint: 'Candidate ,  Role ,  Status ,  Actions' },
          { label: 'Session row', hint: 'Candidate ,  Role ,  Status ,  Actions' },
          { label: 'Session row', hint: 'Candidate ,  Role ,  Status ,  Actions' },
        ]}
        columns={1}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Live session monitor"
          description="Real-time view of in-progress interviews and agent state."
          columns={1}
        />
        <PlaceholderPanel
          title="Session evidence store"
          description="Transcript and response capture for post-interview reporting."
          columns={1}
        />
      </div>
    </div>
  )
}
