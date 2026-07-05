import { PageHeader } from '../../components/ui/PageHeader'
import { PlaceholderPanel } from '../../components/ui/PlaceholderPanel'

export function SchedulingPage() {
  return (
    <div>
      <PageHeader
        title="Interview Scheduling"
        description="Suggest available slots when shortlisting a candidate, send email or in-app notifications, and allow candidates to confirm or reschedule."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <PlaceholderPanel
          title="Available time slots"
          description="Recruiter calendar with suggested interview windows."
          items={[
            { label: 'Calendar view', hint: 'Week ,  Month navigation' },
            { label: 'Slot picker', hint: 'Duration ,  Timezone' },
          ]}
        />
        <PlaceholderPanel
          title="Notifications"
          description="Email and in-app alerts to candidates."
          items={[
            { label: 'Invitation email template', hint: 'Slot ,  Role ,  Portal link' },
            { label: 'In-app notification feed', hint: 'Pending ,  Confirmed ,  Rescheduled' },
          ]}
        />
      </div>

      <div className="mt-6">
        <PlaceholderPanel
          title="Candidate confirmation status"
          description="Track confirm, reschedule, and decline actions from the candidate portal."
          items={[
            { label: 'Pending confirmation', hint: 'Awaiting candidate response' },
            { label: 'Confirmed session', hint: 'Locked slot' },
            { label: 'Reschedule request', hint: 'New slot proposal' },
          ]}
          columns={3}
        />
      </div>
    </div>
  )
}
